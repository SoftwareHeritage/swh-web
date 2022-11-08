# Copyright (C) 2015-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from collections import defaultdict
import datetime
import hashlib
import itertools
import random

from hypothesis import given, settings
import pytest

from swh.model.from_disk import DentryPerms
from swh.model.hashutil import hash_to_bytes, hash_to_hex
from swh.model.model import (
    Directory,
    DirectoryEntry,
    Origin,
    OriginVisit,
    OriginVisitStatus,
    Revision,
    Snapshot,
    SnapshotBranch,
    TargetType,
)
from swh.model.swhids import ObjectType
from swh.storage.utils import now
from swh.web.tests.data import random_content, random_sha1
from swh.web.tests.helpers import fossology_missing
from swh.web.tests.strategies import new_origin, new_revision, visit_dates
from swh.web.utils import archive
from swh.web.utils.exc import BadInputExc, NotFoundExc
from swh.web.utils.typing import OriginInfo, PagedResult


def test_lookup_multiple_hashes_all_present(contents):
    input_data = []
    expected_output = []
    for cnt in contents:
        input_data.append({"sha1": cnt["sha1"]})
        expected_output.append({"sha1": cnt["sha1"], "found": True})

    assert archive.lookup_multiple_hashes(input_data) == expected_output


def test_lookup_multiple_hashes_some_missing(contents, unknown_contents):
    input_contents = list(itertools.chain(contents, unknown_contents))
    random.shuffle(input_contents)

    input_data = []
    expected_output = []
    for cnt in input_contents:
        input_data.append({"sha1": cnt["sha1"]})
        expected_output.append({"sha1": cnt["sha1"], "found": cnt in contents})

    assert archive.lookup_multiple_hashes(input_data) == expected_output


def test_lookup_hash_does_not_exist():
    unknown_content_ = random_content()

    actual_lookup = archive.lookup_hash("sha1_git:%s" % unknown_content_["sha1_git"])

    assert actual_lookup == {"found": None, "algo": "sha1_git"}


def test_lookup_hash_exist(archive_data, content):
    actual_lookup = archive.lookup_hash("sha1:%s" % content["sha1"])

    content_metadata = archive_data.content_get(content["sha1"])

    assert {"found": content_metadata, "algo": "sha1"} == actual_lookup


def test_search_hash_does_not_exist():
    unknown_content_ = random_content()

    actual_lookup = archive.search_hash("sha1_git:%s" % unknown_content_["sha1_git"])

    assert {"found": False} == actual_lookup


def test_search_hash_exist(content):
    actual_lookup = archive.search_hash("sha1:%s" % content["sha1"])

    assert {"found": True} == actual_lookup


def test_lookup_content_filetype(indexer_data, content):
    indexer_data.content_add_mimetype(content["sha1"])
    actual_filetype = archive.lookup_content_filetype(content["sha1"])

    expected_filetype = indexer_data.content_get_mimetype(content["sha1"])
    assert actual_filetype == expected_filetype


@pytest.mark.skipif(fossology_missing, reason="requires fossology-nomossa installed")
def test_lookup_content_license(indexer_data, content):
    indexer_data.content_add_license(content["sha1"])
    actual_license = archive.lookup_content_license(content["sha1"])

    expected_license = indexer_data.content_get_license(content["sha1"])
    assert actual_license == expected_license


def test_stat_counters(archive_data):
    actual_stats = archive.stat_counters()
    assert actual_stats == archive_data.stat_counters()


@given(new_origin(), visit_dates())
def test_lookup_origin_visits(subtest, new_origin, visit_dates):
    # ensure archive_data fixture will be reset between each hypothesis
    # example test run
    @subtest
    def test_inner(archive_data):
        archive_data.origin_add([new_origin])

        archive_data.origin_visit_add(
            [
                OriginVisit(
                    origin=new_origin.url,
                    date=ts,
                    type="git",
                )
                for ts in visit_dates
            ]
        )

        actual_origin_visits = list(
            archive.lookup_origin_visits(new_origin.url, per_page=100)
        )

        expected_visits = archive_data.origin_visit_get(new_origin.url)
        for expected_visit in expected_visits:
            expected_visit["origin"] = new_origin.url

        assert actual_origin_visits == expected_visits


@given(new_origin(), visit_dates())
def test_lookup_origin_visit(archive_data, new_origin, visit_dates):
    archive_data.origin_add([new_origin])
    visits = archive_data.origin_visit_add(
        [
            OriginVisit(
                origin=new_origin.url,
                date=ts,
                type="git",
            )
            for ts in visit_dates
        ]
    )

    visit = random.choice(visits).visit
    actual_origin_visit = archive.lookup_origin_visit(new_origin.url, visit)

    expected_visit = dict(archive_data.origin_visit_get_by(new_origin.url, visit))

    assert actual_origin_visit == expected_visit


@given(new_origin(), visit_dates())
@settings(max_examples=1)
def test_origin_visit_find_by_date_no_result(archive_data, new_origin, visit_dates):
    """No visit registered in storage for an origin should return no visit"""
    archive_data.origin_add([new_origin])

    for visit_date in visit_dates:
        # No visit yet, so nothing will get returned
        actual_origin_visit_status = archive.origin_visit_find_by_date(
            new_origin.url, visit_date
        )
        assert actual_origin_visit_status is None


@settings(max_examples=1)
@given(new_origin())
def test_origin_visit_find_by_date(archive_data, new_origin):
    # Add origin and two visits
    archive_data.origin_add([new_origin])

    pivot_date = now()
    # First visit one hour before pivot date
    first_visit_date = pivot_date - datetime.timedelta(hours=1)
    # Second visit two hours after pivot date
    second_visit_date = pivot_date + datetime.timedelta(hours=2)
    visits = archive_data.origin_visit_add(
        [
            OriginVisit(
                origin=new_origin.url,
                date=visit_date,
                type="git",
            )
            for visit_date in [first_visit_date, second_visit_date]
        ]
    )

    # Finalize visits
    visit_statuses = []
    for visit in visits:
        visit_statuses.append(
            OriginVisitStatus(
                origin=new_origin.url,
                visit=visit.visit,
                date=visit.date + datetime.timedelta(hours=1),
                type=visit.type,
                status="full",
                snapshot=None,
            )
        )
    archive_data.origin_visit_status_add(visit_statuses)

    # Check correct visit is returned when searching by date
    for search_date, greater_or_equal, expected_visit in [
        (first_visit_date, True, 1),
        (pivot_date, True, 2),
        (pivot_date, False, 1),
        (second_visit_date, True, 2),
    ]:
        origin_visit = archive.origin_visit_find_by_date(
            new_origin.url, search_date, greater_or_equal
        )
        assert origin_visit["visit"] == expected_visit


@given(new_origin())
def test_lookup_origin(archive_data, new_origin):
    archive_data.origin_add([new_origin])

    actual_origin = archive.lookup_origin({"url": new_origin.url})
    expected_origin = archive_data.origin_get([new_origin.url])[0]
    assert actual_origin == expected_origin


def test_lookup_origin_snapshots(archive_data, origin_with_multiple_visits):
    origin_url = origin_with_multiple_visits["url"]
    visits = archive_data.origin_visit_get(origin_url)

    origin_snapshots = archive.lookup_origin_snapshots(origin_with_multiple_visits)
    assert set(origin_snapshots) == {v["snapshot"] for v in visits}


def test_lookup_release_ko_id_checksum_not_a_sha1(invalid_sha1):
    with pytest.raises(BadInputExc) as e:
        archive.lookup_release(invalid_sha1)
    assert e.match("Invalid checksum")


def test_lookup_release_ko_id_checksum_too_long(sha256):
    with pytest.raises(BadInputExc) as e:
        archive.lookup_release(sha256)
    assert e.match("Only sha1_git is supported.")


def test_lookup_release_multiple(archive_data, releases):
    actual_releases = list(archive.lookup_release_multiple(releases))

    expected_releases = []
    for release_id in releases:
        release_info = archive_data.release_get(release_id)
        expected_releases.append(release_info)

    assert actual_releases == expected_releases


def test_lookup_release_multiple_none_found():
    unknown_releases_ = [random_sha1(), random_sha1(), random_sha1()]

    actual_releases = list(archive.lookup_release_multiple(unknown_releases_))

    assert actual_releases == [None] * len(unknown_releases_)


def test_lookup_directory_with_path_not_found(directory):
    path = "some/invalid/path/here"
    with pytest.raises(NotFoundExc) as e:
        archive.lookup_directory_with_path(directory, path)
    assert e.match(
        f"Directory entry with path {path} from root directory {directory} not found"
    )


def test_lookup_directory_with_path_found(archive_data, directory):
    directory_content = archive_data.directory_ls(directory)
    directory_entry = random.choice(directory_content)
    path = directory_entry["name"]
    actual_result = archive.lookup_directory_with_path(directory, path)
    assert actual_result == directory_entry


def test_lookup_release(archive_data, release):
    actual_release = archive.lookup_release(release)

    assert actual_release == archive_data.release_get(release)


def test_lookup_revision_with_context_ko_not_a_sha1(revision, invalid_sha1, sha256):
    sha1_git_root = revision
    sha1_git = invalid_sha1

    with pytest.raises(BadInputExc) as e:
        archive.lookup_revision_with_context(sha1_git_root, sha1_git)
    assert e.match("Invalid checksum query string")

    sha1_git = sha256

    with pytest.raises(BadInputExc) as e:
        archive.lookup_revision_with_context(sha1_git_root, sha1_git)
    assert e.match("Only sha1_git is supported")


def test_lookup_revision_with_context_ko_sha1_git_does_not_exist(
    revision, unknown_revision
):
    sha1_git_root = revision
    sha1_git = unknown_revision

    with pytest.raises(NotFoundExc) as e:
        archive.lookup_revision_with_context(sha1_git_root, sha1_git)
    assert e.match("Revision %s not found" % sha1_git)


def test_lookup_revision_with_context_ko_root_sha1_git_does_not_exist(
    revision, unknown_revision
):
    sha1_git_root = unknown_revision
    sha1_git = revision
    with pytest.raises(NotFoundExc) as e:
        archive.lookup_revision_with_context(sha1_git_root, sha1_git)
    assert e.match("Revision root %s not found" % sha1_git_root)


def test_lookup_revision_with_context(archive_data, ancestor_revisions):
    sha1_git = ancestor_revisions["sha1_git"]
    root_sha1_git = ancestor_revisions["sha1_git_root"]
    for sha1_git_root in (root_sha1_git, {"id": hash_to_bytes(root_sha1_git)}):
        actual_revision = archive.lookup_revision_with_context(sha1_git_root, sha1_git)

        children = []
        for rev in archive_data.revision_log(root_sha1_git):
            for p_rev in rev["parents"]:
                p_rev_hex = hash_to_hex(p_rev)
                if p_rev_hex == sha1_git:
                    children.append(rev["id"])

        expected_revision = archive_data.revision_get(sha1_git)
        expected_revision["children"] = children
        assert actual_revision == expected_revision


def test_lookup_revision_with_context_ko(non_ancestor_revisions):
    sha1_git = non_ancestor_revisions["sha1_git"]
    root_sha1_git = non_ancestor_revisions["sha1_git_root"]

    with pytest.raises(NotFoundExc) as e:
        archive.lookup_revision_with_context(root_sha1_git, sha1_git)
    assert e.match("Revision %s is not an ancestor of %s" % (sha1_git, root_sha1_git))


def test_lookup_directory_with_revision_not_found():
    unknown_revision_ = random_sha1()

    with pytest.raises(NotFoundExc) as e:
        archive.lookup_directory_with_revision(unknown_revision_)
    assert e.match("Revision %s not found" % unknown_revision_)


@given(new_revision())
def test_lookup_directory_with_revision_unknown_content(archive_data, new_revision):
    unknown_content_ = random_content()

    dir_path = "README.md"

    # A directory that points to unknown content
    dir = Directory(
        entries=(
            DirectoryEntry(
                name=bytes(dir_path.encode("utf-8")),
                type="file",
                target=hash_to_bytes(unknown_content_["sha1_git"]),
                perms=DentryPerms.content,
            ),
        )
    )

    # Create a revision that points to a directory
    # Which points to unknown content
    new_revision = new_revision.to_dict()
    new_revision["directory"] = dir.id
    del new_revision["id"]
    new_revision = Revision.from_dict(new_revision)

    # Add the directory and revision in mem
    archive_data.directory_add([dir])
    archive_data.revision_add([new_revision])
    new_revision_id = hash_to_hex(new_revision.id)
    with pytest.raises(NotFoundExc) as e:
        archive.lookup_directory_with_revision(new_revision_id, dir_path)
    assert e.match("Content not found for revision %s" % new_revision_id)


def test_lookup_directory_with_revision_ko_path_to_nowhere(revision):
    invalid_path = "path/to/something/unknown"
    with pytest.raises(NotFoundExc) as e:
        archive.lookup_directory_with_revision(revision, invalid_path)
    assert e.match("Directory or File")
    assert e.match(invalid_path)
    assert e.match("revision %s" % revision)
    assert e.match("not found")


def test_lookup_directory_with_revision_submodules(
    archive_data, revision_with_submodules
):
    rev_sha1_git = revision_with_submodules["rev_sha1_git"]
    rev_dir_path = revision_with_submodules["rev_dir_rev_path"]

    actual_data = archive.lookup_directory_with_revision(rev_sha1_git, rev_dir_path)

    revision = archive_data.revision_get(revision_with_submodules["rev_sha1_git"])
    directory = archive_data.directory_ls(revision["directory"])
    rev_entry = next(e for e in directory if e["name"] == rev_dir_path)

    expected_data = {
        "content": archive_data.revision_get(rev_entry["target"]),
        "path": rev_dir_path,
        "revision": rev_sha1_git,
        "type": "rev",
    }

    assert actual_data == expected_data


def test_lookup_directory_with_revision_without_path(archive_data, revision):
    actual_directory_entries = archive.lookup_directory_with_revision(revision)

    revision_data = archive_data.revision_get(revision)
    expected_directory_entries = archive_data.directory_ls(revision_data["directory"])

    assert actual_directory_entries["type"] == "dir"
    assert actual_directory_entries["content"] == expected_directory_entries


def test_lookup_directory_with_revision_with_path(archive_data, revision):
    rev_data = archive_data.revision_get(revision)
    dir_entries = [
        e
        for e in archive_data.directory_ls(rev_data["directory"])
        if e["type"] in ("file", "dir")
    ]
    expected_dir_entry = random.choice(dir_entries)

    actual_dir_entry = archive.lookup_directory_with_revision(
        revision, expected_dir_entry["name"]
    )

    assert actual_dir_entry["type"] == expected_dir_entry["type"]
    assert actual_dir_entry["revision"] == revision
    assert actual_dir_entry["path"] == expected_dir_entry["name"]
    if actual_dir_entry["type"] == "file":
        del actual_dir_entry["content"]["checksums"]["blake2s256"]
        for key in ("checksums", "status", "length"):
            assert actual_dir_entry["content"][key] == expected_dir_entry[key]
    else:
        sub_dir_entries = archive_data.directory_ls(expected_dir_entry["target"])
        assert actual_dir_entry["content"] == sub_dir_entries


def test_lookup_directory_with_revision_with_path_to_file_and_data(
    archive_data, revision
):
    rev_data = archive_data.revision_get(revision)
    dir_entries = [
        e
        for e in archive_data.directory_ls(rev_data["directory"])
        if e["type"] == "file"
    ]
    expected_dir_entry = random.choice(dir_entries)
    expected_data = archive_data.content_get_data(
        expected_dir_entry["checksums"]["sha1"]
    )

    actual_dir_entry = archive.lookup_directory_with_revision(
        revision, expected_dir_entry["name"], with_data=True
    )

    assert actual_dir_entry["type"] == expected_dir_entry["type"]
    assert actual_dir_entry["revision"] == revision
    assert actual_dir_entry["path"] == expected_dir_entry["name"]
    del actual_dir_entry["content"]["checksums"]["blake2s256"]
    for key in ("checksums", "status", "length"):
        assert actual_dir_entry["content"][key] == expected_dir_entry[key]
    assert actual_dir_entry["content"]["data"] == expected_data["data"]


def test_lookup_revision(archive_data, revision):
    actual_revision = archive.lookup_revision(revision)
    assert actual_revision == archive_data.revision_get(revision)


@given(new_revision())
def test_lookup_revision_invalid_msg(archive_data, new_revision):
    new_revision = new_revision.to_dict()
    new_revision["message"] = b"elegant fix for bug \xff"
    archive_data.revision_add([Revision.from_dict(new_revision)])

    revision = archive.lookup_revision(hash_to_hex(new_revision["id"]))
    assert revision["message"] == "elegant fix for bug \\xff"
    assert "message" in revision["decoding_failures"]


@given(new_revision())
def test_lookup_revision_msg_ok(archive_data, new_revision):
    archive_data.revision_add([new_revision])

    revision_message = archive.lookup_revision_message(hash_to_hex(new_revision.id))

    assert revision_message == {"message": new_revision.message}


def test_lookup_revision_msg_no_rev():
    unknown_revision_ = random_sha1()

    with pytest.raises(NotFoundExc) as e:
        archive.lookup_revision_message(unknown_revision_)

    assert e.match("Revision with sha1_git %s not found." % unknown_revision_)


def test_lookup_revision_multiple(archive_data, revisions):
    actual_revisions = list(archive.lookup_revision_multiple(revisions))

    expected_revisions = []
    for rev in revisions:
        expected_revisions.append(archive_data.revision_get(rev))

    assert actual_revisions == expected_revisions


def test_lookup_revision_multiple_none_found():
    unknown_revisions_ = [random_sha1(), random_sha1(), random_sha1()]

    actual_revisions = list(archive.lookup_revision_multiple(unknown_revisions_))

    assert actual_revisions == [None] * len(unknown_revisions_)


def test_lookup_revision_log(archive_data, revision):
    actual_revision_log = list(archive.lookup_revision_log(revision, limit=25))
    expected_revision_log = archive_data.revision_log(revision, limit=25)

    assert actual_revision_log == expected_revision_log


def _get_origin_branches(archive_data, origin):
    origin_visit = archive_data.origin_visit_get(origin["url"])[-1]
    snapshot = archive_data.snapshot_get(origin_visit["snapshot"])
    branches = {
        k: v
        for (k, v) in snapshot["branches"].items()
        if v["target_type"] == "revision"
    }
    return branches


def test_lookup_revision_log_by(archive_data, origin):
    branches = _get_origin_branches(archive_data, origin)
    branch_name = random.choice(list(branches.keys()))

    actual_log = list(
        archive.lookup_revision_log_by(origin["url"], branch_name, None, limit=25)
    )

    expected_log = archive_data.revision_log(branches[branch_name]["target"], limit=25)

    assert actual_log == expected_log


def test_lookup_revision_log_by_notfound(origin):
    with pytest.raises(NotFoundExc):
        archive.lookup_revision_log_by(
            origin["url"], "unknown_branch_name", None, limit=100
        )


def test_lookup_content_raw_not_found():
    unknown_content_ = random_content()

    with pytest.raises(NotFoundExc) as e:
        archive.lookup_content_raw("sha1:" + unknown_content_["sha1"])

    assert e.match(
        "Content with %s checksum equals to %s not found!"
        % ("sha1", unknown_content_["sha1"])
    )


def test_lookup_content_raw(archive_data, content):
    actual_content = archive.lookup_content_raw("sha256:%s" % content["sha256"])

    expected_content = archive_data.content_get_data(content["sha1"])

    assert actual_content == expected_content


def test_lookup_empty_content_raw(empty_content):
    content_raw = archive.lookup_content_raw(f"sha1_git:{empty_content['sha1_git']}")
    assert content_raw["data"] == b""


def test_lookup_content_not_found():
    unknown_content_ = random_content()

    with pytest.raises(NotFoundExc) as e:
        archive.lookup_content("sha1:%s" % unknown_content_["sha1"])

    assert e.match(
        "Content with %s checksum equals to %s not found!"
        % ("sha1", unknown_content_["sha1"])
    )


def test_lookup_content_with_sha1(archive_data, content):
    actual_content = archive.lookup_content(f"sha1:{content['sha1']}")

    expected_content = archive_data.content_get(content["sha1"])

    assert actual_content == expected_content


def test_lookup_content_with_sha256(archive_data, content):
    actual_content = archive.lookup_content(f"sha256:{content['sha256']}")

    expected_content = archive_data.content_get(content["sha1"])

    assert actual_content == expected_content


def test_lookup_directory_bad_checksum():
    with pytest.raises(BadInputExc):
        archive.lookup_directory("directory_id")


def test_lookup_directory_not_found():
    unknown_directory_ = random_sha1()

    with pytest.raises(NotFoundExc) as e:
        archive.lookup_directory(unknown_directory_)

    assert e.match("Directory with sha1_git %s not found" % unknown_directory_)


def test_lookup_directory(archive_data, directory):
    actual_directory_ls = list(archive.lookup_directory(directory))

    expected_directory_ls = archive_data.directory_ls(directory)

    assert actual_directory_ls == expected_directory_ls


def test_lookup_directory_empty(empty_directory):
    actual_directory_ls = list(archive.lookup_directory(empty_directory))

    assert actual_directory_ls == []


def test_lookup_revision_by_nothing_found(origin):
    with pytest.raises(NotFoundExc):
        archive.lookup_revision_by(origin["url"], "invalid-branch-name")


def test_lookup_revision_by(archive_data, origin):
    branches = _get_origin_branches(archive_data, origin)
    branch_name = random.choice(list(branches.keys()))

    actual_revision = archive.lookup_revision_by(origin["url"], branch_name)

    expected_revision = archive_data.revision_get(branches[branch_name]["target"])

    assert actual_revision == expected_revision


def test_lookup_revision_with_context_by_ko(origin, revision):
    with pytest.raises(NotFoundExc):
        archive.lookup_revision_with_context_by(
            origin["url"], "invalid-branch-name", None, revision
        )


def test_lookup_revision_with_context_by(archive_data, origin):
    branches = _get_origin_branches(archive_data, origin)
    branch_name = random.choice(list(branches.keys()))

    root_rev = branches[branch_name]["target"]
    root_rev_log = archive_data.revision_log(root_rev)

    children = defaultdict(list)

    for rev in root_rev_log:
        for rev_p in rev["parents"]:
            children[rev_p].append(rev["id"])

    rev = root_rev_log[-1]["id"]

    actual_root_rev, actual_rev = archive.lookup_revision_with_context_by(
        origin["url"], branch_name, None, rev
    )

    expected_root_rev = archive_data.revision_get(root_rev)
    expected_rev = archive_data.revision_get(rev)
    expected_rev["children"] = children[rev]

    assert actual_root_rev == expected_root_rev
    assert actual_rev == expected_rev


def test_lookup_revision_through_ko_not_implemented():
    with pytest.raises(NotImplementedError):
        archive.lookup_revision_through({"something-unknown": 10})


def test_lookup_revision_through_with_context_by(archive_data, origin):
    branches = _get_origin_branches(archive_data, origin)
    branch_name = random.choice(list(branches.keys()))

    root_rev = branches[branch_name]["target"]
    root_rev_log = archive_data.revision_log(root_rev)
    rev = root_rev_log[-1]["id"]

    assert archive.lookup_revision_through(
        {
            "origin_url": origin["url"],
            "branch_name": branch_name,
            "ts": None,
            "sha1_git": rev,
        }
    ) == archive.lookup_revision_with_context_by(origin["url"], branch_name, None, rev)


def test_lookup_revision_through_with_revision_by(archive_data, origin):
    branches = _get_origin_branches(archive_data, origin)
    branch_name = random.choice(list(branches.keys()))

    assert archive.lookup_revision_through(
        {
            "origin_url": origin["url"],
            "branch_name": branch_name,
            "ts": None,
        }
    ) == archive.lookup_revision_by(origin["url"], branch_name, None)


def test_lookup_revision_through_with_context(ancestor_revisions):
    sha1_git = ancestor_revisions["sha1_git"]
    sha1_git_root = ancestor_revisions["sha1_git_root"]

    assert archive.lookup_revision_through(
        {
            "sha1_git_root": sha1_git_root,
            "sha1_git": sha1_git,
        }
    ) == archive.lookup_revision_with_context(sha1_git_root, sha1_git)


def test_lookup_revision_through_with_revision(revision):
    assert archive.lookup_revision_through(
        {"sha1_git": revision}
    ) == archive.lookup_revision(revision)


def test_lookup_directory_through_revision_ko_not_found(revision):
    with pytest.raises(NotFoundExc):
        archive.lookup_directory_through_revision(
            {"sha1_git": revision}, "some/invalid/path"
        )


def test_lookup_directory_through_revision_ok(archive_data, revision):
    rev_data = archive_data.revision_get(revision)
    dir_entries = [
        e
        for e in archive_data.directory_ls(rev_data["directory"])
        if e["type"] == "file"
    ]
    dir_entry = random.choice(dir_entries)

    assert archive.lookup_directory_through_revision(
        {"sha1_git": revision}, dir_entry["name"]
    ) == (revision, archive.lookup_directory_with_revision(revision, dir_entry["name"]))


def test_lookup_directory_through_revision_ok_with_data(archive_data, revision):
    rev_data = archive_data.revision_get(revision)
    dir_entries = [
        e
        for e in archive_data.directory_ls(rev_data["directory"])
        if e["type"] == "file"
    ]
    dir_entry = random.choice(dir_entries)

    assert archive.lookup_directory_through_revision(
        {"sha1_git": revision}, dir_entry["name"], with_data=True
    ) == (
        revision,
        archive.lookup_directory_with_revision(
            revision, dir_entry["name"], with_data=True
        ),
    )


def test_lookup_known_objects(
    archive_data, content, directory, release, revision, snapshot
):
    expected = archive_data.content_find(content)
    assert archive.lookup_object(ObjectType.CONTENT, content["sha1_git"]) == expected

    expected = archive_data.directory_get(directory)
    assert archive.lookup_object(ObjectType.DIRECTORY, directory) == expected

    expected = archive_data.release_get(release)
    assert archive.lookup_object(ObjectType.RELEASE, release) == expected

    expected = archive_data.revision_get(revision)
    assert archive.lookup_object(ObjectType.REVISION, revision) == expected

    expected = {**archive_data.snapshot_get(snapshot), "next_branch": None}
    assert archive.lookup_object(ObjectType.SNAPSHOT, snapshot) == expected


def test_lookup_unknown_objects(
    unknown_content,
    unknown_directory,
    unknown_release,
    unknown_revision,
    unknown_snapshot,
):
    with pytest.raises(NotFoundExc) as e:
        archive.lookup_object(ObjectType.CONTENT, unknown_content["sha1_git"])
    assert e.match(r"Content.*not found")

    with pytest.raises(NotFoundExc) as e:
        archive.lookup_object(ObjectType.DIRECTORY, unknown_directory)
    assert e.match(r"Directory.*not found")

    with pytest.raises(NotFoundExc) as e:
        archive.lookup_object(ObjectType.RELEASE, unknown_release)
    assert e.match(r"Release.*not found")

    with pytest.raises(NotFoundExc) as e:
        archive.lookup_object(ObjectType.REVISION, unknown_revision)
    assert e.match(r"Revision.*not found")

    with pytest.raises(NotFoundExc) as e:
        archive.lookup_object(ObjectType.SNAPSHOT, unknown_snapshot)
    assert e.match(r"Snapshot.*not found")


def test_lookup_invalid_objects(invalid_sha1):

    with pytest.raises(BadInputExc) as e:
        archive.lookup_object(ObjectType.CONTENT, invalid_sha1)
    assert e.match("Invalid hash")

    with pytest.raises(BadInputExc) as e:
        archive.lookup_object(ObjectType.DIRECTORY, invalid_sha1)
    assert e.match("Invalid checksum")

    with pytest.raises(BadInputExc) as e:
        archive.lookup_object(ObjectType.RELEASE, invalid_sha1)
    assert e.match("Invalid checksum")

    with pytest.raises(BadInputExc) as e:
        archive.lookup_object(ObjectType.REVISION, invalid_sha1)
    assert e.match("Invalid checksum")

    with pytest.raises(BadInputExc) as e:
        archive.lookup_object(ObjectType.SNAPSHOT, invalid_sha1)
    assert e.match("Invalid checksum")


def test_lookup_missing_hashes_non_present():
    missing_cnt = random_sha1()
    missing_dir = random_sha1()
    missing_rev = random_sha1()
    missing_rel = random_sha1()
    missing_snp = random_sha1()

    grouped_swhids = {
        ObjectType.CONTENT: [hash_to_bytes(missing_cnt)],
        ObjectType.DIRECTORY: [hash_to_bytes(missing_dir)],
        ObjectType.REVISION: [hash_to_bytes(missing_rev)],
        ObjectType.RELEASE: [hash_to_bytes(missing_rel)],
        ObjectType.SNAPSHOT: [hash_to_bytes(missing_snp)],
    }

    actual_result = archive.lookup_missing_hashes(grouped_swhids)

    assert actual_result == {
        missing_cnt,
        missing_dir,
        missing_rev,
        missing_rel,
        missing_snp,
    }


def test_lookup_missing_hashes_some_present(content, directory):
    missing_rev = random_sha1()
    missing_rel = random_sha1()
    missing_snp = random_sha1()

    grouped_swhids = {
        ObjectType.CONTENT: [hash_to_bytes(content["sha1_git"])],
        ObjectType.DIRECTORY: [hash_to_bytes(directory)],
        ObjectType.REVISION: [hash_to_bytes(missing_rev)],
        ObjectType.RELEASE: [hash_to_bytes(missing_rel)],
        ObjectType.SNAPSHOT: [hash_to_bytes(missing_snp)],
    }

    actual_result = archive.lookup_missing_hashes(grouped_swhids)

    assert actual_result == {missing_rev, missing_rel, missing_snp}


def test_lookup_origin_extra_trailing_slash(origin):
    origin_info = archive.lookup_origin({"url": f"{origin['url']}/"})
    assert origin_info["url"] == origin["url"]


def test_lookup_origin_missing_trailing_slash(archive_data):
    deb_origin = Origin(url="http://snapshot.debian.org/package/r-base/")
    archive_data.origin_add([deb_origin])
    origin_info = archive.lookup_origin({"url": deb_origin.url[:-1]})
    assert origin_info["url"] == deb_origin.url


def test_lookup_origin_single_slash_after_protocol(archive_data):
    origin_url = "http://snapshot.debian.org/package/r-base/"
    malformed_origin_url = "http:/snapshot.debian.org/package/r-base/"
    archive_data.origin_add([Origin(url=origin_url)])
    origin_info = archive.lookup_origin({"url": malformed_origin_url})
    assert origin_info["url"] == origin_url


@given(new_origin())
def test_lookup_origins_get_by_sha1s(origin, unknown_origin):
    hasher = hashlib.sha1()
    hasher.update(origin["url"].encode("utf-8"))
    origin_info = OriginInfo(url=origin["url"])
    origin_sha1 = hasher.hexdigest()

    hasher = hashlib.sha1()
    hasher.update(unknown_origin.url.encode("utf-8"))
    unknown_origin_sha1 = hasher.hexdigest()

    origins = list(archive.lookup_origins_by_sha1s([origin_sha1]))
    assert origins == [origin_info]

    origins = list(archive.lookup_origins_by_sha1s([origin_sha1, origin_sha1]))
    assert origins == [origin_info, origin_info]

    origins = list(archive.lookup_origins_by_sha1s([origin_sha1, unknown_origin_sha1]))
    assert origins == [origin_info, None]


def test_search_origin(origin):
    results = archive.search_origin(url_pattern=origin["url"])[0]
    assert results == [{"url": origin["url"]}]


def test_search_origin_use_ql(mocker, origin):

    ORIGIN = [{"url": origin["url"]}]

    mock_archive_search = mocker.patch("swh.web.utils.archive.search")
    mock_archive_search.origin_search.return_value = PagedResult(
        results=ORIGIN,
        next_page_token=None,
    )

    query = f"origin = '{origin['url']}'"

    results = archive.search_origin(url_pattern=query, use_ql=True)[0]
    assert results == ORIGIN

    mock_archive_search.origin_search.assert_called_with(
        query=query, page_token=None, with_visit=False, visit_types=None, limit=50
    )


def test_lookup_snapshot_sizes(archive_data, snapshot):
    branches = archive_data.snapshot_get(snapshot)["branches"]

    expected_sizes = {
        "alias": 0,
        "branch": 0,
        "release": 0,
        "revision": 0,
    }

    for _, branch_info in branches.items():
        if branch_info is not None:
            expected_sizes[branch_info["target_type"]] += 1
            if branch_info["target_type"] in ("content", "directory", "revision"):
                expected_sizes["branch"] += 1

    assert archive.lookup_snapshot_sizes(snapshot) == expected_sizes


def test_lookup_snapshot_sizes_with_filtering(archive_data, revision):
    rev_id = hash_to_bytes(revision)
    snapshot = Snapshot(
        branches={
            b"refs/heads/master": SnapshotBranch(
                target=rev_id,
                target_type=TargetType.REVISION,
            ),
            b"refs/heads/incoming": SnapshotBranch(
                target=rev_id,
                target_type=TargetType.REVISION,
            ),
            b"refs/pull/1": SnapshotBranch(
                target=rev_id,
                target_type=TargetType.REVISION,
            ),
            b"refs/pull/2": SnapshotBranch(
                target=rev_id,
                target_type=TargetType.REVISION,
            ),
        },
    )
    archive_data.snapshot_add([snapshot])

    expected_sizes = {"alias": 0, "branch": 2, "release": 0, "revision": 2}

    assert (
        archive.lookup_snapshot_sizes(
            snapshot.id.hex(), branch_name_exclude_prefix="refs/pull/"
        )
        == expected_sizes
    )


def test_lookup_snapshot_alias(snapshot):
    resolved_alias = archive.lookup_snapshot_alias(snapshot, "HEAD")
    assert resolved_alias is not None
    assert resolved_alias["target_type"] == "revision"
    assert resolved_alias["target"] is not None


def test_lookup_snapshot_missing(revision):
    with pytest.raises(NotFoundExc):
        archive.lookup_snapshot(revision)


def test_lookup_snapshot_empty_branch_list(archive_data, revision):
    rev_id = hash_to_bytes(revision)
    snapshot = Snapshot(
        branches={
            b"refs/heads/master": SnapshotBranch(
                target=rev_id,
                target_type=TargetType.REVISION,
            ),
        },
    )
    archive_data.snapshot_add([snapshot])

    # FIXME; This test will change once the inconsistency in storage is fixed
    # postgres backend returns None in case of a missing branch whereas the
    # in-memory implementation (used in tests) returns a data structure;
    # hence the inconsistency
    branches = archive.lookup_snapshot(
        hash_to_hex(snapshot.id),
        branch_name_include_substring="non-existing",
    )["branches"]
    assert not branches


def test_lookup_snapshot_branch_names_filtering(archive_data, revision):
    rev_id = hash_to_bytes(revision)
    snapshot = Snapshot(
        branches={
            b"refs/heads/master": SnapshotBranch(
                target=rev_id,
                target_type=TargetType.REVISION,
            ),
            b"refs/heads/incoming": SnapshotBranch(
                target=rev_id,
                target_type=TargetType.REVISION,
            ),
            b"refs/pull/1": SnapshotBranch(
                target=rev_id,
                target_type=TargetType.REVISION,
            ),
            b"refs/pull/2": SnapshotBranch(
                target=rev_id,
                target_type=TargetType.REVISION,
            ),
            "non_ascii_name_é".encode(): SnapshotBranch(
                target=rev_id,
                target_type=TargetType.REVISION,
            ),
        },
    )
    archive_data.snapshot_add([snapshot])

    for include_pattern, exclude_prefix, nb_results in (
        ("pull", None, 2),
        ("incoming", None, 1),
        ("é", None, 1),
        (None, "refs/heads/", 3),
        ("refs", "refs/heads/master", 3),
    ):

        branches = archive.lookup_snapshot(
            hash_to_hex(snapshot.id),
            branch_name_include_substring=include_pattern,
            branch_name_exclude_prefix=exclude_prefix,
        )["branches"]
        assert len(branches) == nb_results
        for branch_name in branches:
            if include_pattern:
                assert include_pattern in branch_name
            if exclude_prefix:
                assert not branch_name.startswith(exclude_prefix)


def test_lookup_snapshot_branch_names_filtering_paginated(
    archive_data, directory, revision
):
    pattern = "foo"
    nb_branches_by_target_type = 10
    branches = {}
    for i in range(nb_branches_by_target_type):
        branches[f"branch/directory/bar{i}".encode()] = SnapshotBranch(
            target=hash_to_bytes(directory),
            target_type=TargetType.DIRECTORY,
        )
        branches[f"branch/revision/bar{i}".encode()] = SnapshotBranch(
            target=hash_to_bytes(revision),
            target_type=TargetType.REVISION,
        )
        branches[f"branch/directory/{pattern}{i}".encode()] = SnapshotBranch(
            target=hash_to_bytes(directory),
            target_type=TargetType.DIRECTORY,
        )
        branches[f"branch/revision/{pattern}{i}".encode()] = SnapshotBranch(
            target=hash_to_bytes(revision),
            target_type=TargetType.REVISION,
        )

    snapshot = Snapshot(branches=branches)
    archive_data.snapshot_add([snapshot])

    branches_count = nb_branches_by_target_type // 2

    for target_type in (
        ObjectType.DIRECTORY.name.lower(),
        ObjectType.REVISION.name.lower(),
    ):
        partial_branches = archive.lookup_snapshot(
            hash_to_hex(snapshot.id),
            target_types=[target_type],
            branches_count=branches_count,
            branch_name_include_substring=pattern,
        )
        branches = partial_branches["branches"]

        assert len(branches) == branches_count
        for branch_name, branch_data in branches.items():
            assert pattern in branch_name
            assert branch_data["target_type"] == target_type
        for i in range(branches_count):
            assert f"branch/{target_type}/{pattern}{i}" in branches
        assert (
            partial_branches["next_branch"]
            == f"branch/{target_type}/{pattern}{branches_count}"
        )

        partial_branches = archive.lookup_snapshot(
            hash_to_hex(snapshot.id),
            target_types=[target_type],
            branches_from=partial_branches["next_branch"],
            branch_name_include_substring=pattern,
        )
        branches = partial_branches["branches"]

        assert len(branches) == branches_count
        for branch_name, branch_data in branches.items():
            assert pattern in branch_name
            assert branch_data["target_type"] == target_type
        for i in range(branches_count, 2 * branches_count):
            assert f"branch/{target_type}/{pattern}{i}" in branches
        assert partial_branches["next_branch"] is None
