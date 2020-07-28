# Copyright (C) 2015-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import itertools
import pytest
import random

from collections import defaultdict
from hypothesis import given

from swh.model.hashutil import hash_to_bytes, hash_to_hex
from swh.model.from_disk import DentryPerms
from swh.model.identifiers import CONTENT, DIRECTORY, RELEASE, REVISION, SNAPSHOT
from swh.model.model import Directory, DirectoryEntry, Origin, OriginVisit, Revision

from swh.web.common import service
from swh.web.common.exc import BadInputExc, NotFoundExc
from swh.web.tests.data import random_sha1, random_content
from swh.web.tests.strategies import (
    content,
    unknown_content,
    contents,
    unknown_contents,
    contents_with_ctags,
    origin,
    new_origin,
    visit_dates,
    directory,
    unknown_directory,
    release,
    unknown_release,
    revision,
    unknown_revision,
    revisions,
    ancestor_revisions,
    non_ancestor_revisions,
    invalid_sha1,
    sha256,
    revision_with_submodules,
    empty_directory,
    new_revision,
    snapshot,
    unknown_snapshot,
)
from swh.web.tests.conftest import ctags_json_missing, fossology_missing


@given(contents())
def test_lookup_multiple_hashes_all_present(contents):
    input_data = []
    expected_output = []
    for cnt in contents:
        input_data.append({"sha1": cnt["sha1"]})
        expected_output.append({"sha1": cnt["sha1"], "found": True})

    assert service.lookup_multiple_hashes(input_data) == expected_output


@given(contents(), unknown_contents())
def test_lookup_multiple_hashes_some_missing(contents, unknown_contents):
    input_contents = list(itertools.chain(contents, unknown_contents))
    random.shuffle(input_contents)

    input_data = []
    expected_output = []
    for cnt in input_contents:
        input_data.append({"sha1": cnt["sha1"]})
        expected_output.append({"sha1": cnt["sha1"], "found": cnt in contents})

    assert service.lookup_multiple_hashes(input_data) == expected_output


def test_lookup_hash_does_not_exist():
    unknown_content_ = random_content()

    actual_lookup = service.lookup_hash("sha1_git:%s" % unknown_content_["sha1_git"])

    assert actual_lookup == {"found": None, "algo": "sha1_git"}


@given(content())
def test_lookup_hash_exist(archive_data, content):
    actual_lookup = service.lookup_hash("sha1:%s" % content["sha1"])

    content_metadata = archive_data.content_get_metadata(content["sha1"])

    assert {"found": content_metadata, "algo": "sha1"} == actual_lookup


def test_search_hash_does_not_exist():
    unknown_content_ = random_content()

    actual_lookup = service.search_hash("sha1_git:%s" % unknown_content_["sha1_git"])

    assert {"found": False} == actual_lookup


@given(content())
def test_search_hash_exist(content):
    actual_lookup = service.search_hash("sha1:%s" % content["sha1"])

    assert {"found": True} == actual_lookup


@pytest.mark.skipif(
    ctags_json_missing, reason="requires ctags with json output support"
)
@given(contents_with_ctags())
def test_lookup_content_ctags(indexer_data, contents_with_ctags):
    content_sha1 = random.choice(contents_with_ctags["sha1s"])
    indexer_data.content_add_ctags(content_sha1)
    actual_ctags = list(service.lookup_content_ctags("sha1:%s" % content_sha1))

    expected_data = list(indexer_data.content_get_ctags(content_sha1))
    for ctag in expected_data:
        ctag["id"] = content_sha1

    assert actual_ctags == expected_data


def test_lookup_content_ctags_no_hash():
    unknown_content_ = random_content()

    actual_ctags = list(
        service.lookup_content_ctags("sha1:%s" % unknown_content_["sha1"])
    )

    assert actual_ctags == []


@given(content())
def test_lookup_content_filetype(indexer_data, content):
    indexer_data.content_add_mimetype(content["sha1"])
    actual_filetype = service.lookup_content_filetype(content["sha1"])

    expected_filetype = indexer_data.content_get_mimetype(content["sha1"])
    assert actual_filetype == expected_filetype


@pytest.mark.skip  # Language indexer is disabled.
@given(content())
def test_lookup_content_language(indexer_data, content):
    indexer_data.content_add_language(content["sha1"])
    actual_language = service.lookup_content_language(content["sha1"])

    expected_language = indexer_data.content_get_language(content["sha1"])
    assert actual_language == expected_language


@given(contents_with_ctags())
def test_lookup_expression(indexer_data, contents_with_ctags):
    per_page = 10
    expected_ctags = []

    for content_sha1 in contents_with_ctags["sha1s"]:
        if len(expected_ctags) == per_page:
            break
        indexer_data.content_add_ctags(content_sha1)
        for ctag in indexer_data.content_get_ctags(content_sha1):
            if len(expected_ctags) == per_page:
                break
            if ctag["name"] == contents_with_ctags["symbol_name"]:
                del ctag["id"]
                ctag["sha1"] = content_sha1
                expected_ctags.append(ctag)

    actual_ctags = list(
        service.lookup_expression(
            contents_with_ctags["symbol_name"], last_sha1=None, per_page=10
        )
    )

    assert actual_ctags == expected_ctags


def test_lookup_expression_no_result():
    expected_ctags = []

    actual_ctags = list(
        service.lookup_expression("barfoo", last_sha1=None, per_page=10)
    )
    assert actual_ctags == expected_ctags


@pytest.mark.skipif(fossology_missing, reason="requires fossology-nomossa installed")
@given(content())
def test_lookup_content_license(indexer_data, content):
    indexer_data.content_add_license(content["sha1"])
    actual_license = service.lookup_content_license(content["sha1"])

    expected_license = indexer_data.content_get_license(content["sha1"])
    assert actual_license == expected_license


def test_stat_counters(archive_data):
    actual_stats = service.stat_counters()
    assert actual_stats == archive_data.stat_counters()


@given(new_origin(), visit_dates())
def test_lookup_origin_visits(archive_data, new_origin, visit_dates):
    archive_data.origin_add([new_origin])

    archive_data.origin_visit_add(
        [OriginVisit(origin=new_origin.url, date=ts, type="git",) for ts in visit_dates]
    )

    actual_origin_visits = list(
        service.lookup_origin_visits(new_origin.url, per_page=100)
    )

    expected_visits = archive_data.origin_visit_get(new_origin.url)
    for expected_visit in expected_visits:
        expected_visit["origin"] = new_origin.url

    assert actual_origin_visits == expected_visits


@given(new_origin(), visit_dates())
def test_lookup_origin_visit(archive_data, new_origin, visit_dates):
    archive_data.origin_add([new_origin])
    visits = archive_data.origin_visit_add(
        [OriginVisit(origin=new_origin.url, date=ts, type="git",) for ts in visit_dates]
    )

    visit = random.choice(visits).visit
    actual_origin_visit = service.lookup_origin_visit(new_origin.url, visit)

    expected_visit = dict(archive_data.origin_visit_get_by(new_origin.url, visit))

    assert actual_origin_visit == expected_visit


@given(new_origin())
def test_lookup_origin(archive_data, new_origin):
    archive_data.origin_add([new_origin])

    actual_origin = service.lookup_origin({"url": new_origin.url})
    expected_origin = archive_data.origin_get([new_origin.url])[0]
    assert actual_origin == expected_origin


@given(invalid_sha1())
def test_lookup_release_ko_id_checksum_not_a_sha1(invalid_sha1):
    with pytest.raises(BadInputExc) as e:
        service.lookup_release(invalid_sha1)
    assert e.match("Invalid checksum")


@given(sha256())
def test_lookup_release_ko_id_checksum_too_long(sha256):
    with pytest.raises(BadInputExc) as e:
        service.lookup_release(sha256)
    assert e.match("Only sha1_git is supported.")


@given(directory())
def test_lookup_directory_with_path_not_found(directory):
    path = "some/invalid/path/here"
    with pytest.raises(NotFoundExc) as e:
        service.lookup_directory_with_path(directory, path)
    assert e.match("Directory entry with path %s from %s not found" % (path, directory))


@given(directory())
def test_lookup_directory_with_path_found(archive_data, directory):
    directory_content = archive_data.directory_ls(directory)
    directory_entry = random.choice(directory_content)
    path = directory_entry["name"]
    actual_result = service.lookup_directory_with_path(directory, path)
    assert actual_result == directory_entry


@given(release())
def test_lookup_release(archive_data, release):
    actual_release = service.lookup_release(release)

    assert actual_release == archive_data.release_get(release)


@given(revision(), invalid_sha1(), sha256())
def test_lookup_revision_with_context_ko_not_a_sha1(revision, invalid_sha1, sha256):
    sha1_git_root = revision
    sha1_git = invalid_sha1

    with pytest.raises(BadInputExc) as e:
        service.lookup_revision_with_context(sha1_git_root, sha1_git)
    assert e.match("Invalid checksum query string")

    sha1_git = sha256

    with pytest.raises(BadInputExc) as e:
        service.lookup_revision_with_context(sha1_git_root, sha1_git)
    assert e.match("Only sha1_git is supported")


@given(revision(), unknown_revision())
def test_lookup_revision_with_context_ko_sha1_git_does_not_exist(
    revision, unknown_revision
):
    sha1_git_root = revision
    sha1_git = unknown_revision

    with pytest.raises(NotFoundExc) as e:
        service.lookup_revision_with_context(sha1_git_root, sha1_git)
    assert e.match("Revision %s not found" % sha1_git)


@given(revision(), unknown_revision())
def test_lookup_revision_with_context_ko_root_sha1_git_does_not_exist(
    revision, unknown_revision
):
    sha1_git_root = unknown_revision
    sha1_git = revision
    with pytest.raises(NotFoundExc) as e:
        service.lookup_revision_with_context(sha1_git_root, sha1_git)
    assert e.match("Revision root %s not found" % sha1_git_root)


@given(ancestor_revisions())
def test_lookup_revision_with_context(archive_data, ancestor_revisions):
    sha1_git = ancestor_revisions["sha1_git"]
    root_sha1_git = ancestor_revisions["sha1_git_root"]
    for sha1_git_root in (root_sha1_git, {"id": hash_to_bytes(root_sha1_git)}):
        actual_revision = service.lookup_revision_with_context(sha1_git_root, sha1_git)

        children = []
        for rev in archive_data.revision_log(root_sha1_git):
            for p_rev in rev["parents"]:
                p_rev_hex = hash_to_hex(p_rev)
                if p_rev_hex == sha1_git:
                    children.append(rev["id"])

        expected_revision = archive_data.revision_get(sha1_git)
        expected_revision["children"] = children
        assert actual_revision == expected_revision


@given(non_ancestor_revisions())
def test_lookup_revision_with_context_ko(non_ancestor_revisions):
    sha1_git = non_ancestor_revisions["sha1_git"]
    root_sha1_git = non_ancestor_revisions["sha1_git_root"]

    with pytest.raises(NotFoundExc) as e:
        service.lookup_revision_with_context(root_sha1_git, sha1_git)
    assert e.match("Revision %s is not an ancestor of %s" % (sha1_git, root_sha1_git))


def test_lookup_directory_with_revision_not_found():
    unknown_revision_ = random_sha1()

    with pytest.raises(NotFoundExc) as e:
        service.lookup_directory_with_revision(unknown_revision_)
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
        service.lookup_directory_with_revision(new_revision_id, dir_path)
    assert e.match("Content not found for revision %s" % new_revision_id)


@given(revision())
def test_lookup_directory_with_revision_ko_path_to_nowhere(revision):
    invalid_path = "path/to/something/unknown"
    with pytest.raises(NotFoundExc) as e:
        service.lookup_directory_with_revision(revision, invalid_path)
    assert e.match("Directory or File")
    assert e.match(invalid_path)
    assert e.match("revision %s" % revision)
    assert e.match("not found")


@given(revision_with_submodules())
def test_lookup_directory_with_revision_submodules(
    archive_data, revision_with_submodules
):
    rev_sha1_git = revision_with_submodules["rev_sha1_git"]
    rev_dir_path = revision_with_submodules["rev_dir_rev_path"]

    actual_data = service.lookup_directory_with_revision(rev_sha1_git, rev_dir_path)

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


@given(revision())
def test_lookup_directory_with_revision_without_path(archive_data, revision):
    actual_directory_entries = service.lookup_directory_with_revision(revision)

    revision_data = archive_data.revision_get(revision)
    expected_directory_entries = archive_data.directory_ls(revision_data["directory"])

    assert actual_directory_entries["type"] == "dir"
    assert actual_directory_entries["content"] == expected_directory_entries


@given(revision())
def test_lookup_directory_with_revision_with_path(archive_data, revision):
    rev_data = archive_data.revision_get(revision)
    dir_entries = [
        e
        for e in archive_data.directory_ls(rev_data["directory"])
        if e["type"] in ("file", "dir")
    ]
    expected_dir_entry = random.choice(dir_entries)

    actual_dir_entry = service.lookup_directory_with_revision(
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


@given(revision())
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
    expected_data = archive_data.content_get(expected_dir_entry["checksums"]["sha1"])

    actual_dir_entry = service.lookup_directory_with_revision(
        revision, expected_dir_entry["name"], with_data=True
    )

    assert actual_dir_entry["type"] == expected_dir_entry["type"]
    assert actual_dir_entry["revision"] == revision
    assert actual_dir_entry["path"] == expected_dir_entry["name"]
    del actual_dir_entry["content"]["checksums"]["blake2s256"]
    for key in ("checksums", "status", "length"):
        assert actual_dir_entry["content"][key] == expected_dir_entry[key]
    assert actual_dir_entry["content"]["data"] == expected_data["data"]


@given(revision())
def test_lookup_revision(archive_data, revision):
    actual_revision = service.lookup_revision(revision)
    assert actual_revision == archive_data.revision_get(revision)


@given(new_revision())
def test_lookup_revision_invalid_msg(archive_data, new_revision):
    new_revision = new_revision.to_dict()
    new_revision["message"] = b"elegant fix for bug \xff"
    archive_data.revision_add([Revision.from_dict(new_revision)])

    revision = service.lookup_revision(hash_to_hex(new_revision["id"]))
    assert revision["message"] is None
    assert revision["message_decoding_failed"] is True


@given(new_revision())
def test_lookup_revision_msg_ok(archive_data, new_revision):
    archive_data.revision_add([new_revision])

    revision_message = service.lookup_revision_message(hash_to_hex(new_revision.id))

    assert revision_message == {"message": new_revision.message}


def test_lookup_revision_msg_no_rev():
    unknown_revision_ = random_sha1()

    with pytest.raises(NotFoundExc) as e:
        service.lookup_revision_message(unknown_revision_)

    assert e.match("Revision with sha1_git %s not found." % unknown_revision_)


@given(revisions())
def test_lookup_revision_multiple(archive_data, revisions):
    actual_revisions = list(service.lookup_revision_multiple(revisions))

    expected_revisions = []
    for rev in revisions:
        expected_revisions.append(archive_data.revision_get(rev))

    assert actual_revisions == expected_revisions


def test_lookup_revision_multiple_none_found():
    unknown_revisions_ = [random_sha1(), random_sha1(), random_sha1()]

    actual_revisions = list(service.lookup_revision_multiple(unknown_revisions_))

    assert actual_revisions == [None] * len(unknown_revisions_)


@given(revision())
def test_lookup_revision_log(archive_data, revision):
    actual_revision_log = list(service.lookup_revision_log(revision, limit=25))
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


@given(origin())
def test_lookup_revision_log_by(archive_data, origin):
    branches = _get_origin_branches(archive_data, origin)
    branch_name = random.choice(list(branches.keys()))

    actual_log = list(
        service.lookup_revision_log_by(origin["url"], branch_name, None, limit=25)
    )

    expected_log = archive_data.revision_log(branches[branch_name]["target"], limit=25)

    assert actual_log == expected_log


@given(origin())
def test_lookup_revision_log_by_notfound(origin):
    with pytest.raises(NotFoundExc):
        service.lookup_revision_log_by(
            origin["url"], "unknown_branch_name", None, limit=100
        )


def test_lookup_content_raw_not_found():
    unknown_content_ = random_content()

    with pytest.raises(NotFoundExc) as e:
        service.lookup_content_raw("sha1:" + unknown_content_["sha1"])

    assert e.match(
        "Content with %s checksum equals to %s not found!"
        % ("sha1", unknown_content_["sha1"])
    )


@given(content())
def test_lookup_content_raw(archive_data, content):
    actual_content = service.lookup_content_raw("sha256:%s" % content["sha256"])

    expected_content = archive_data.content_get(content["sha1"])

    assert actual_content == expected_content


def test_lookup_content_not_found():
    unknown_content_ = random_content()

    with pytest.raises(NotFoundExc) as e:
        service.lookup_content("sha1:%s" % unknown_content_["sha1"])

    assert e.match(
        "Content with %s checksum equals to %s not found!"
        % ("sha1", unknown_content_["sha1"])
    )


@given(content())
def test_lookup_content_with_sha1(archive_data, content):
    actual_content = service.lookup_content("sha1:%s" % content["sha1"])

    expected_content = archive_data.content_get_metadata(content["sha1"])

    assert actual_content == expected_content


@given(content())
def test_lookup_content_with_sha256(archive_data, content):
    actual_content = service.lookup_content("sha256:%s" % content["sha256"])

    expected_content = archive_data.content_get_metadata(content["sha1"])

    assert actual_content == expected_content


def test_lookup_directory_bad_checksum():
    with pytest.raises(BadInputExc):
        service.lookup_directory("directory_id")


def test_lookup_directory_not_found():
    unknown_directory_ = random_sha1()

    with pytest.raises(NotFoundExc) as e:
        service.lookup_directory(unknown_directory_)

    assert e.match("Directory with sha1_git %s not found" % unknown_directory_)


@given(directory())
def test_lookup_directory(archive_data, directory):
    actual_directory_ls = list(service.lookup_directory(directory))

    expected_directory_ls = archive_data.directory_ls(directory)

    assert actual_directory_ls == expected_directory_ls


@given(empty_directory())
def test_lookup_directory_empty(empty_directory):
    actual_directory_ls = list(service.lookup_directory(empty_directory))

    assert actual_directory_ls == []


@given(origin())
def test_lookup_revision_by_nothing_found(origin):
    with pytest.raises(NotFoundExc):
        service.lookup_revision_by(origin["url"], "invalid-branch-name")


@given(origin())
def test_lookup_revision_by(archive_data, origin):
    branches = _get_origin_branches(archive_data, origin)
    branch_name = random.choice(list(branches.keys()))

    actual_revision = service.lookup_revision_by(origin["url"], branch_name)

    expected_revision = archive_data.revision_get(branches[branch_name]["target"])

    assert actual_revision == expected_revision


@given(origin(), revision())
def test_lookup_revision_with_context_by_ko(origin, revision):
    with pytest.raises(NotFoundExc):
        service.lookup_revision_with_context_by(
            origin["url"], "invalid-branch-name", None, revision
        )


@given(origin())
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

    actual_root_rev, actual_rev = service.lookup_revision_with_context_by(
        origin["url"], branch_name, None, rev
    )

    expected_root_rev = archive_data.revision_get(root_rev)
    expected_rev = archive_data.revision_get(rev)
    expected_rev["children"] = children[rev]

    assert actual_root_rev == expected_root_rev
    assert actual_rev == expected_rev


def test_lookup_revision_through_ko_not_implemented():
    with pytest.raises(NotImplementedError):
        service.lookup_revision_through({"something-unknown": 10})


@given(origin())
def test_lookup_revision_through_with_context_by(archive_data, origin):
    branches = _get_origin_branches(archive_data, origin)
    branch_name = random.choice(list(branches.keys()))

    root_rev = branches[branch_name]["target"]
    root_rev_log = archive_data.revision_log(root_rev)
    rev = root_rev_log[-1]["id"]

    assert service.lookup_revision_through(
        {
            "origin_url": origin["url"],
            "branch_name": branch_name,
            "ts": None,
            "sha1_git": rev,
        }
    ) == service.lookup_revision_with_context_by(origin["url"], branch_name, None, rev)


@given(origin())
def test_lookup_revision_through_with_revision_by(archive_data, origin):
    branches = _get_origin_branches(archive_data, origin)
    branch_name = random.choice(list(branches.keys()))

    assert service.lookup_revision_through(
        {"origin_url": origin["url"], "branch_name": branch_name, "ts": None,}
    ) == service.lookup_revision_by(origin["url"], branch_name, None)


@given(ancestor_revisions())
def test_lookup_revision_through_with_context(ancestor_revisions):
    sha1_git = ancestor_revisions["sha1_git"]
    sha1_git_root = ancestor_revisions["sha1_git_root"]

    assert service.lookup_revision_through(
        {"sha1_git_root": sha1_git_root, "sha1_git": sha1_git,}
    ) == service.lookup_revision_with_context(sha1_git_root, sha1_git)


@given(revision())
def test_lookup_revision_through_with_revision(revision):
    assert service.lookup_revision_through(
        {"sha1_git": revision}
    ) == service.lookup_revision(revision)


@given(revision())
def test_lookup_directory_through_revision_ko_not_found(revision):
    with pytest.raises(NotFoundExc):
        service.lookup_directory_through_revision(
            {"sha1_git": revision}, "some/invalid/path"
        )


@given(revision())
def test_lookup_directory_through_revision_ok(archive_data, revision):
    rev_data = archive_data.revision_get(revision)
    dir_entries = [
        e
        for e in archive_data.directory_ls(rev_data["directory"])
        if e["type"] == "file"
    ]
    dir_entry = random.choice(dir_entries)

    assert service.lookup_directory_through_revision(
        {"sha1_git": revision}, dir_entry["name"]
    ) == (revision, service.lookup_directory_with_revision(revision, dir_entry["name"]))


@given(revision())
def test_lookup_directory_through_revision_ok_with_data(archive_data, revision):
    rev_data = archive_data.revision_get(revision)
    dir_entries = [
        e
        for e in archive_data.directory_ls(rev_data["directory"])
        if e["type"] == "file"
    ]
    dir_entry = random.choice(dir_entries)

    assert service.lookup_directory_through_revision(
        {"sha1_git": revision}, dir_entry["name"], with_data=True
    ) == (
        revision,
        service.lookup_directory_with_revision(
            revision, dir_entry["name"], with_data=True
        ),
    )


@given(content(), directory(), release(), revision(), snapshot())
def test_lookup_known_objects(
    archive_data, content, directory, release, revision, snapshot
):
    expected = archive_data.content_find(content)
    assert service.lookup_object(CONTENT, content["sha1_git"]) == expected

    expected = archive_data.directory_get(directory)
    assert service.lookup_object(DIRECTORY, directory) == expected

    expected = archive_data.release_get(release)
    assert service.lookup_object(RELEASE, release) == expected

    expected = archive_data.revision_get(revision)
    assert service.lookup_object(REVISION, revision) == expected

    expected = archive_data.snapshot_get(snapshot)
    assert service.lookup_object(SNAPSHOT, snapshot) == expected


@given(
    unknown_content(),
    unknown_directory(),
    unknown_release(),
    unknown_revision(),
    unknown_snapshot(),
)
def test_lookup_unknown_objects(
    unknown_content,
    unknown_directory,
    unknown_release,
    unknown_revision,
    unknown_snapshot,
):
    with pytest.raises(NotFoundExc) as e:
        service.lookup_object(CONTENT, unknown_content["sha1_git"])
    assert e.match(r"Content.*not found")

    with pytest.raises(NotFoundExc) as e:
        service.lookup_object(DIRECTORY, unknown_directory)
    assert e.match(r"Directory.*not found")

    with pytest.raises(NotFoundExc) as e:
        service.lookup_object(RELEASE, unknown_release)
    assert e.match(r"Release.*not found")

    with pytest.raises(NotFoundExc) as e:
        service.lookup_object(REVISION, unknown_revision)
    assert e.match(r"Revision.*not found")

    with pytest.raises(NotFoundExc) as e:
        service.lookup_object(SNAPSHOT, unknown_snapshot)
    assert e.match(r"Snapshot.*not found")


@given(invalid_sha1())
def test_lookup_invalid_objects(invalid_sha1):

    with pytest.raises(BadInputExc) as e:
        service.lookup_object("foo", invalid_sha1)
    assert e.match("Invalid swh object type")

    with pytest.raises(BadInputExc) as e:
        service.lookup_object(CONTENT, invalid_sha1)
    assert e.match("Invalid hash")

    with pytest.raises(BadInputExc) as e:
        service.lookup_object(DIRECTORY, invalid_sha1)
    assert e.match("Invalid checksum")

    with pytest.raises(BadInputExc) as e:
        service.lookup_object(RELEASE, invalid_sha1)
    assert e.match("Invalid checksum")

    with pytest.raises(BadInputExc) as e:
        service.lookup_object(REVISION, invalid_sha1)
    assert e.match("Invalid checksum")

    with pytest.raises(BadInputExc) as e:
        service.lookup_object(SNAPSHOT, invalid_sha1)
    assert e.match("Invalid checksum")


def test_lookup_missing_hashes_non_present():
    missing_cnt = random_sha1()
    missing_dir = random_sha1()
    missing_rev = random_sha1()
    missing_rel = random_sha1()
    missing_snp = random_sha1()

    grouped_swhids = {
        CONTENT: [hash_to_bytes(missing_cnt)],
        DIRECTORY: [hash_to_bytes(missing_dir)],
        REVISION: [hash_to_bytes(missing_rev)],
        RELEASE: [hash_to_bytes(missing_rel)],
        SNAPSHOT: [hash_to_bytes(missing_snp)],
    }

    actual_result = service.lookup_missing_hashes(grouped_swhids)

    assert actual_result == {
        missing_cnt,
        missing_dir,
        missing_rev,
        missing_rel,
        missing_snp,
    }


@given(content(), directory())
def test_lookup_missing_hashes_some_present(archive_data, content, directory):
    missing_rev = random_sha1()
    missing_rel = random_sha1()
    missing_snp = random_sha1()

    grouped_swhids = {
        CONTENT: [hash_to_bytes(content["sha1_git"])],
        DIRECTORY: [hash_to_bytes(directory)],
        REVISION: [hash_to_bytes(missing_rev)],
        RELEASE: [hash_to_bytes(missing_rel)],
        SNAPSHOT: [hash_to_bytes(missing_snp)],
    }

    actual_result = service.lookup_missing_hashes(grouped_swhids)

    assert actual_result == {missing_rev, missing_rel, missing_snp}


@given(origin())
def test_lookup_origin_extra_trailing_slash(origin):
    origin_info = service.lookup_origin({"url": f"{origin['url']}/"})
    assert origin_info["url"] == origin["url"]


def test_lookup_origin_missing_trailing_slash(archive_data):
    deb_origin = Origin(url="http://snapshot.debian.org/package/r-base/")
    archive_data.origin_add([deb_origin])
    origin_info = service.lookup_origin({"url": deb_origin.url[:-1]})
    assert origin_info["url"] == deb_origin.url


@given(snapshot())
def test_lookup_snapshot_branch_name_from_tip_revision(archive_data, snapshot_id):
    snapshot = archive_data.snapshot_get(snapshot_id)
    branches = [
        {"name": k, "revision": v["target"]}
        for k, v in snapshot["branches"].items()
        if v["target_type"] == "revision"
    ]
    branch_info = random.choice(branches)
    possible_results = [
        b["name"] for b in branches if b["revision"] == branch_info["revision"]
    ]

    assert (
        service.lookup_snapshot_branch_name_from_tip_revision(
            snapshot_id, branch_info["revision"]
        )
        in possible_results
    )
