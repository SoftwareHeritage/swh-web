# Copyright (C) 2018-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from collections import defaultdict
from datetime import datetime
import random

from hypothesis import assume, settings
from hypothesis.extra.dateutil import timezones
from hypothesis.strategies import (
    binary,
    characters,
    composite,
    datetimes,
    just,
    lists,
    sampled_from,
    text,
)

from swh.model.hashutil import hash_to_bytes, hash_to_hex
from swh.model.hypothesis_strategies import origins as new_origin_strategy
from swh.model.hypothesis_strategies import snapshots as new_snapshot
from swh.model.model import (
    Directory,
    Person,
    Revision,
    RevisionType,
    TimestampWithTimezone,
)
from swh.model.swhids import ObjectType
from swh.storage.algos.revisions_walker import get_revisions_walker
from swh.storage.algos.snapshot import snapshot_get_latest
from swh.web.tests.data import get_tests_data

# Module dedicated to the generation of input data for tests through
# the use of hypothesis.
# Some of these data are sampled from a test archive created and populated
# in the swh.web.tests.data module.

# Set the swh-web hypothesis profile if none has been explicitly set
hypothesis_default_settings = settings.get_profile("default")
if repr(settings()) == repr(hypothesis_default_settings):
    settings.load_profile("swh-web")


# The following strategies exploit the hypothesis capabilities


def _known_swh_object(object_type):
    return sampled_from(get_tests_data()[object_type])


def sha1():
    """
    Hypothesis strategy returning a valid hexadecimal sha1 value.
    """
    return binary(min_size=20, max_size=20).map(hash_to_hex)


def invalid_sha1():
    """
    Hypothesis strategy returning an invalid sha1 representation.
    """
    return binary(min_size=50, max_size=50).map(hash_to_hex)


def sha256():
    """
    Hypothesis strategy returning a valid hexadecimal sha256 value.
    """
    return binary(min_size=32, max_size=32).map(hash_to_hex)


@composite
def new_content(draw):
    blake2s256_hex = draw(sha256())
    sha1_hex = draw(sha1())
    sha1_git_hex = draw(sha1())
    sha256_hex = draw(sha256())

    assume(sha1_hex != sha1_git_hex)
    assume(blake2s256_hex != sha256_hex)

    return {
        "blake2S256": blake2s256_hex,
        "sha1": sha1_hex,
        "sha1_git": sha1_git_hex,
        "sha256": sha256_hex,
    }


def unknown_content():
    """
    Hypothesis strategy returning a random content not ingested
    into the test archive.
    """
    return new_content().filter(
        lambda c: get_tests_data()["storage"].content_get_data(hash_to_bytes(c["sha1"]))
        is None
    )


def unknown_contents():
    """
    Hypothesis strategy returning random contents not ingested
    into the test archive.
    """
    return lists(unknown_content(), min_size=2, max_size=8)


def directory():
    """
    Hypothesis strategy returning a random directory ingested
    into the test archive.
    """
    return _known_swh_object("directories")


def _directory_with_entry_type(type_):
    return directory().filter(
        lambda d: any(
            [
                e["type"] == type_
                for e in list(
                    get_tests_data()["storage"].directory_ls(hash_to_bytes(d))
                )
            ]
        )
    )


def directory_with_subdirs():
    """
    Hypothesis strategy returning a random directory containing
    sub directories ingested into the test archive.
    """
    return _directory_with_entry_type("dir")


def directory_with_files():
    """
    Hypothesis strategy returning a random directory containing
    at least one regular file
    """
    return _directory_with_entry_type("file")


def empty_directory():
    """
    Hypothesis strategy returning the empty directory ingested
    into the test archive.
    """
    return just(Directory(entries=()).id.hex())


def unknown_directory():
    """
    Hypothesis strategy returning a random directory not ingested
    into the test archive.
    """
    return sha1().filter(
        lambda s: len(
            list(get_tests_data()["storage"].directory_missing([hash_to_bytes(s)]))
        )
        > 0
    )


def origin():
    """
    Hypothesis strategy returning a random origin ingested
    into the test archive.
    """
    return _known_swh_object("origins")


def origin_with_multiple_visits():
    """
    Hypothesis strategy returning a random origin ingested
    into the test archive.
    """
    ret = []
    tests_data = get_tests_data()
    storage = tests_data["storage"]
    for origin in tests_data["origins"]:
        visit_page = storage.origin_visit_get(origin["url"])
        if len(visit_page.results) > 1:
            ret.append(origin)
    return sampled_from(ret)


def origin_with_releases():
    """
    Hypothesis strategy returning a random origin ingested
    into the test archive.
    """
    ret = []
    tests_data = get_tests_data()
    for origin in tests_data["origins"]:
        snapshot = snapshot_get_latest(tests_data["storage"], origin["url"])
        if any([b.target_type.value == "release" for b in snapshot.branches.values()]):
            ret.append(origin)
    return sampled_from(ret)


def origin_with_pull_request_branches():
    """
    Hypothesis strategy returning a random origin with pull request branches
    ingested into the test archive.
    """
    ret = []
    tests_data = get_tests_data()
    storage = tests_data["storage"]
    origins = storage.origin_list(limit=1000)
    for origin in origins.results:
        snapshot = snapshot_get_latest(storage, origin.url)
        if any([b"refs/pull/" in b for b in snapshot.branches]):
            ret.append(origin)
    return sampled_from(ret)


def new_origin():
    """
    Hypothesis strategy returning a random origin not ingested
    into the test archive.
    """
    return new_origin_strategy()


def new_origins(nb_origins=None):
    """
    Hypothesis strategy returning random origins not ingested
    into the test archive.
    """
    min_size = nb_origins if nb_origins is not None else 2
    max_size = nb_origins if nb_origins is not None else 8
    size = random.randint(min_size, max_size)
    return lists(
        new_origin(),
        min_size=size,
        max_size=size,
        unique_by=lambda o: tuple(sorted(o.items())),
    )


def visit_dates(nb_dates=None):
    """
    Hypothesis strategy returning a list of visit dates.
    """
    min_size = nb_dates if nb_dates else 2
    max_size = nb_dates if nb_dates else 8
    return lists(
        datetimes(
            min_value=datetime(2015, 1, 1, 0, 0),
            max_value=datetime(2018, 12, 31, 0, 0),
            timezones=timezones(),
        ),
        min_size=min_size,
        max_size=max_size,
        unique=True,
    ).map(sorted)


def release():
    """
    Hypothesis strategy returning a random release ingested
    into the test archive.
    """
    return _known_swh_object("releases")


def releases(min_size=2, max_size=8):
    """
    Hypothesis strategy returning random releases ingested
    into the test archive.
    """
    return lists(release(), min_size=min_size, max_size=max_size)


def unknown_release():
    """
    Hypothesis strategy returning a random revision not ingested
    into the test archive.
    """
    return sha1().filter(
        lambda s: get_tests_data()["storage"].release_get([s])[0] is None
    )


def revision():
    """
    Hypothesis strategy returning a random revision ingested
    into the test archive.
    """
    return _known_swh_object("revisions")


def unknown_revision():
    """
    Hypothesis strategy returning a random revision not ingested
    into the test archive.
    """
    return sha1().filter(
        lambda s: get_tests_data()["storage"].revision_get([hash_to_bytes(s)])[0]
        is None
    )


@composite
def new_person(draw):
    """
    Hypothesis strategy returning random raw swh person data.
    """
    name = draw(
        text(
            min_size=5,
            max_size=30,
            alphabet=characters(min_codepoint=0, max_codepoint=255),
        )
    )
    email = "%s@company.org" % name
    return Person(
        name=name.encode(),
        email=email.encode(),
        fullname=("%s <%s>" % (name, email)).encode(),
    )


@composite
def new_swh_date(draw):
    """
    Hypothesis strategy returning random raw swh date data.
    """
    timestamp = draw(
        datetimes(
            min_value=datetime(2015, 1, 1, 0, 0), max_value=datetime(2018, 12, 31, 0, 0)
        ).map(lambda d: int(d.timestamp()))
    )
    return {
        "timestamp": timestamp,
        "offset": 0,
        "negative_utc": False,
    }


@composite
def new_revision(draw):
    """
    Hypothesis strategy returning random raw swh revision data
    not ingested into the test archive.
    """
    return Revision(
        directory=draw(sha1().map(hash_to_bytes)),
        author=draw(new_person()),
        committer=draw(new_person()),
        message=draw(text(min_size=20, max_size=100).map(lambda t: t.encode())),
        date=TimestampWithTimezone.from_datetime(draw(new_swh_date())),
        committer_date=TimestampWithTimezone.from_datetime(draw(new_swh_date())),
        synthetic=False,
        type=RevisionType.GIT,
    )


def revisions(min_size=2, max_size=8):
    """
    Hypothesis strategy returning random revisions ingested
    into the test archive.
    """
    return lists(revision(), min_size=min_size, max_size=max_size)


def unknown_revisions(min_size=2, max_size=8):
    """
    Hypothesis strategy returning random revisions not ingested
    into the test archive.
    """
    return lists(unknown_revision(), min_size=min_size, max_size=max_size)


def snapshot():
    """
    Hypothesis strategy returning a random snapshot ingested
    into the test archive.
    """
    return _known_swh_object("snapshots")


def new_snapshots(nb_snapshots=None):
    min_size = nb_snapshots if nb_snapshots else 2
    max_size = nb_snapshots if nb_snapshots else 8
    return lists(
        new_snapshot(min_size=2, max_size=10, only_objects=True),
        min_size=min_size,
        max_size=max_size,
    )


def unknown_snapshot():
    """
    Hypothesis strategy returning a random revision not ingested
    into the test archive.
    """
    return sha1().filter(
        lambda s: get_tests_data()["storage"].snapshot_get_branches(hash_to_bytes(s))
        is None
    )


def _get_origin_dfs_revisions_walker():
    tests_data = get_tests_data()
    storage = tests_data["storage"]
    origin = random.choice(tests_data["origins"][:-1])
    snapshot = snapshot_get_latest(storage, origin["url"])
    if snapshot.branches[b"HEAD"].target_type.value == "alias":
        target = snapshot.branches[b"HEAD"].target
        head = snapshot.branches[target].target
    else:
        head = snapshot.branches[b"HEAD"].target
    return get_revisions_walker("dfs", storage, head)


def ancestor_revisions():
    """
    Hypothesis strategy returning a pair of revisions ingested into the
    test archive with an ancestor relation.
    """
    # get a dfs revisions walker for one of the origins
    # loaded into the test archive
    revisions_walker = _get_origin_dfs_revisions_walker()
    master_revisions = []
    children = defaultdict(list)
    init_rev_found = False
    # get revisions only authored in the master branch
    for rev in revisions_walker:
        for rev_p in rev["parents"]:
            children[rev_p].append(rev["id"])
        if not init_rev_found:
            master_revisions.append(rev)
        if not rev["parents"]:
            init_rev_found = True

    # head revision
    root_rev = master_revisions[0]
    # pick a random revision, different from head, only authored
    # in the master branch
    ancestor_rev_idx = random.choice(list(range(1, len(master_revisions) - 1)))
    ancestor_rev = master_revisions[ancestor_rev_idx]
    ancestor_child_revs = children[ancestor_rev["id"]]

    return just(
        {
            "sha1_git_root": hash_to_hex(root_rev["id"]),
            "sha1_git": hash_to_hex(ancestor_rev["id"]),
            "children": [hash_to_hex(r) for r in ancestor_child_revs],
        }
    )


def non_ancestor_revisions():
    """
    Hypothesis strategy returning a pair of revisions ingested into the
    test archive with no ancestor relation.
    """
    # get a dfs revisions walker for one of the origins
    # loaded into the test archive
    revisions_walker = _get_origin_dfs_revisions_walker()
    merge_revs = []
    children = defaultdict(list)
    # get all merge revisions
    for rev in revisions_walker:
        if len(rev["parents"]) > 1:
            merge_revs.append(rev)
        for rev_p in rev["parents"]:
            children[rev_p].append(rev["id"])
    # find a merge revisions whose parents have a unique child revision
    random.shuffle(merge_revs)
    selected_revs = None
    for merge_rev in merge_revs:
        if all(len(children[rev_p]) == 1 for rev_p in merge_rev["parents"]):
            selected_revs = merge_rev["parents"]

    return just(
        {
            "sha1_git_root": hash_to_hex(selected_revs[0]),
            "sha1_git": hash_to_hex(selected_revs[1]),
        }
    )


# The following strategies returns data specific to some tests
# that can not be generated and thus are hardcoded.


def revision_with_submodules():
    """
    Hypothesis strategy returning a revision that is known to
    point to a directory with revision entries (aka git submodule)
    """
    return just(
        {
            "rev_sha1_git": "ffcb69001f3f6745dfd5b48f72ab6addb560e234",
            "rev_dir_sha1_git": "d92a21446387fa28410e5a74379c934298f39ae2",
            "rev_dir_rev_path": "libtess2",
        }
    )


def swhid():
    """
    Hypothesis strategy returning a qualified SWHID for any object
    ingested into the test archive.
    """
    return _known_swh_object("swhids")


def directory_swhid():
    """
    Hypothesis strategy returning a qualified SWHID for a directory object
    ingested into the test archive.
    """
    return swhid().filter(lambda swhid: swhid.object_type == ObjectType.DIRECTORY)


def release_swhid():
    """
    Hypothesis strategy returning a qualified SWHID for a release object
    ingested into the test archive.
    """
    return swhid().filter(lambda swhid: swhid.object_type == ObjectType.RELEASE)


def revision_swhid():
    """
    Hypothesis strategy returning a qualified SWHID for a revision object
    ingested into the test archive.
    """
    return swhid().filter(lambda swhid: swhid.object_type == ObjectType.REVISION)


def snapshot_swhid():
    """
    Hypothesis strategy returning a qualified SWHID for a snapshot object
    ingested into the test archive.
    """
    return swhid().filter(lambda swhid: swhid.object_type == ObjectType.SNAPSHOT)
