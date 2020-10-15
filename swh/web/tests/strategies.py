# Copyright (C) 2018-2020  The Software Heritage developers
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

from swh.model.hashutil import DEFAULT_ALGORITHMS, hash_to_bytes, hash_to_hex
from swh.model.hypothesis_strategies import origins as new_origin_strategy
from swh.model.hypothesis_strategies import snapshots as new_snapshot
from swh.model.model import (
    Content,
    Directory,
    Person,
    Revision,
    RevisionType,
    TimestampWithTimezone,
)
from swh.storage.algos.revisions_walker import get_revisions_walker
from swh.storage.algos.snapshot import snapshot_get_latest
from swh.web.common.utils import browsers_supported_image_mimes
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


def _filter_checksum(cs):
    generated_checksums = get_tests_data()["generated_checksums"]
    if not int.from_bytes(cs, byteorder="little") or cs in generated_checksums:
        return False
    generated_checksums.add(cs)
    return True


def _known_swh_object(object_type):
    return sampled_from(get_tests_data()[object_type])


def sha1():
    """
    Hypothesis strategy returning a valid hexadecimal sha1 value.
    """
    return binary(min_size=20, max_size=20).filter(_filter_checksum).map(hash_to_hex)


def invalid_sha1():
    """
    Hypothesis strategy returning an invalid sha1 representation.
    """
    return binary(min_size=50, max_size=50).filter(_filter_checksum).map(hash_to_hex)


def sha256():
    """
    Hypothesis strategy returning a valid hexadecimal sha256 value.
    """
    return binary(min_size=32, max_size=32).filter(_filter_checksum).map(hash_to_hex)


def content():
    """
    Hypothesis strategy returning a random content ingested
    into the test archive.
    """
    return _known_swh_object("contents")


def contents():
    """
    Hypothesis strategy returning random contents ingested
    into the test archive.
    """
    return lists(content(), min_size=2, max_size=8)


def empty_content():
    """
    Hypothesis strategy returning the empty content ingested
    into the test archive.
    """
    empty_content = Content.from_data(data=b"").to_dict()
    for algo in DEFAULT_ALGORITHMS:
        empty_content[algo] = hash_to_hex(empty_content[algo])
    return just(empty_content)


def content_text():
    """
    Hypothesis strategy returning random textual contents ingested
    into the test archive.
    """
    return content().filter(lambda c: c["mimetype"].startswith("text/"))


def content_text_non_utf8():
    """
    Hypothesis strategy returning random textual contents not encoded
    to UTF-8 ingested into the test archive.
    """
    return content().filter(
        lambda c: c["mimetype"].startswith("text/")
        and c["encoding"] not in ("utf-8", "us-ascii")
    )


def content_text_no_highlight():
    """
    Hypothesis strategy returning random textual contents with no detected
    programming language to highlight ingested into the test archive.
    """
    return content().filter(
        lambda c: c["mimetype"].startswith("text/")
        and c["hljs_language"] == "nohighlight"
    )


def content_image_type():
    """
    Hypothesis strategy returning random image contents ingested
    into the test archive.
    """
    return content().filter(lambda c: c["mimetype"] in browsers_supported_image_mimes)


def content_unsupported_image_type_rendering():
    """
    Hypothesis strategy returning random image contents ingested
    into the test archive that can not be rendered by browsers.
    """
    return content().filter(
        lambda c: c["mimetype"].startswith("image/")
        and c["mimetype"] not in browsers_supported_image_mimes
    )


def content_utf8_detected_as_binary():
    """
    Hypothesis strategy returning random textual contents detected as binary
    by libmagic while they are valid UTF-8 encoded files.
    """

    def utf8_binary_detected(content):
        if content["encoding"] != "binary":
            return False
        try:
            content["data"].decode("utf-8")
        except Exception:
            return False
        else:
            return True

    return content().filter(utf8_binary_detected)


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


def directory_with_subdirs():
    """
    Hypothesis strategy returning a random directory containing
    sub directories ingested into the test archive.
    """
    return directory().filter(
        lambda d: any(
            [
                e["type"] == "dir"
                for e in list(
                    get_tests_data()["storage"].directory_ls(hash_to_bytes(d))
                )
            ]
        )
    )


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


def new_origin():
    """
    Hypothesis strategy returning a random origin not ingested
    into the test archive.
    """
    return new_origin_strategy().filter(
        lambda origin: get_tests_data()["storage"].origin_get([origin.url])[0] is None
    )


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


def contents_with_ctags():
    """
    Hypothesis strategy returning contents ingested into the test
    archive. Those contents are ctags compatible, that is running
    ctags on those lay results.
    """
    return just(
        {
            "sha1s": [
                "0ab37c02043ebff946c1937523f60aadd0844351",
                "15554cf7608dde6bfefac7e3d525596343a85b6f",
                "2ce837f1489bdfb8faf3ebcc7e72421b5bea83bd",
                "30acd0b47fc25e159e27a980102ddb1c4bea0b95",
                "4f81f05aaea3efb981f9d90144f746d6b682285b",
                "5153aa4b6e4455a62525bc4de38ed0ff6e7dd682",
                "59d08bafa6a749110dfb65ba43a61963d5a5bf9f",
                "7568285b2d7f31ae483ae71617bd3db873deaa2c",
                "7ed3ee8e94ac52ba983dd7690bdc9ab7618247b4",
                "8ed7ef2e7ff9ed845e10259d08e4145f1b3b5b03",
                "9b3557f1ab4111c8607a4f2ea3c1e53c6992916c",
                "9c20da07ed14dc4fcd3ca2b055af99b2598d8bdd",
                "c20ceebd6ec6f7a19b5c3aebc512a12fbdc9234b",
                "e89e55a12def4cd54d5bff58378a3b5119878eb7",
                "e8c0654fe2d75ecd7e0b01bee8a8fc60a130097e",
                "eb6595e559a1d34a2b41e8d4835e0e4f98a5d2b5",
            ],
            "symbol_name": "ABS",
        }
    )


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
