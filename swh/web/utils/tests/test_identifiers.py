# Copyright (C) 2020-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random
from urllib.parse import quote, unquote, urlparse

import pytest

from swh.model.hashutil import hash_to_bytes
from swh.model.model import Origin
from swh.model.swhids import ObjectType, QualifiedSWHID
from swh.web.browse.snapshot_context import get_snapshot_context
from swh.web.tests.data import random_sha1
from swh.web.utils import reverse
from swh.web.utils.exc import BadInputExc
from swh.web.utils.identifiers import (
    gen_swhid,
    get_swhid,
    get_swhids_info,
    group_swhids,
    parse_object_type,
    resolve_swhid,
)
from swh.web.utils.typing import SWHObjectInfo


def test_gen_swhid(content):
    swh_object_type = ObjectType.CONTENT
    sha1_git = content["sha1_git"]

    expected_swhid = "swh:1:cnt:" + sha1_git

    assert gen_swhid(swh_object_type, sha1_git) == expected_swhid

    assert (
        gen_swhid(swh_object_type, sha1_git, metadata={"origin": "test"})
        == expected_swhid + ";origin=test"
    )

    assert (
        gen_swhid(swh_object_type, sha1_git, metadata={"origin": None})
        == expected_swhid
    )

    with pytest.raises(BadInputExc) as e:
        gen_swhid(swh_object_type, "not a valid id")
    assert e.match("Invalid object")


def test_parse_object_type():
    assert parse_object_type("content") == ObjectType.CONTENT
    assert parse_object_type("directory") == ObjectType.DIRECTORY
    assert parse_object_type("revision") == ObjectType.REVISION
    assert parse_object_type("release") == ObjectType.RELEASE
    assert parse_object_type("snapshot") == ObjectType.SNAPSHOT

    with pytest.raises(BadInputExc) as e:
        parse_object_type("foo")
    assert e.match("Invalid swh object type")


def test_resolve_swhid_legacy(content, directory, release, revision, snapshot):
    for obj_type, obj_id in (
        (ObjectType.CONTENT, content["sha1_git"]),
        (ObjectType.DIRECTORY, directory),
        (ObjectType.RELEASE, release),
        (ObjectType.REVISION, revision),
        (ObjectType.SNAPSHOT, snapshot),
    ):

        swhid = gen_swhid(obj_type, obj_id)

        url_args = {}
        if obj_type == ObjectType.CONTENT:
            url_args["query_string"] = f"sha1_git:{obj_id}"
        elif obj_type == ObjectType.SNAPSHOT:
            url_args["snapshot_id"] = obj_id
        else:
            url_args["sha1_git"] = obj_id
        query_params = {"origin_url": "some-origin"}
        browse_url = reverse(
            f"browse-{obj_type.name.lower()}",
            url_args=url_args,
            query_params=query_params,
        )

        for swhid_ in (swhid, swhid.upper()):
            resolved_swhid = resolve_swhid(swhid_, query_params)

            assert isinstance(resolved_swhid["swhid_parsed"], QualifiedSWHID)
            assert str(resolved_swhid["swhid_parsed"]) == swhid
            assert resolved_swhid["browse_url"] == browse_url

    with pytest.raises(BadInputExc, match="'ori' is not a valid ObjectType"):
        resolve_swhid(f"swh:1:ori:{random_sha1()}")


def test_get_swhid(content, directory, release, revision, snapshot):
    for obj_type, obj_id in (
        (ObjectType.CONTENT, content["sha1_git"]),
        (ObjectType.DIRECTORY, directory),
        (ObjectType.RELEASE, release),
        (ObjectType.REVISION, revision),
        (ObjectType.SNAPSHOT, snapshot),
    ):
        swhid = gen_swhid(obj_type, obj_id)
        for swhid_ in (swhid, swhid.upper()):
            swh_parsed_swhid = get_swhid(swhid_)
            assert isinstance(swh_parsed_swhid, QualifiedSWHID)
            assert str(swh_parsed_swhid) == swhid.lower()

    with pytest.raises(BadInputExc, match="Error when parsing identifier"):
        get_swhid("foo")


def test_get_swhid_with_unquoted_white_spaces(content):
    swhid = gen_swhid(
        ObjectType.CONTENT, content["sha1_git"], metadata={"path": "/test/foo bar/baz"}
    )

    swhid_parsed = get_swhid(swhid)

    assert swhid_parsed.path == b"/test/foo bar/baz"
    assert "path=/test/foo%20bar/baz" in str(swhid_parsed)


def test_group_swhids(content, directory, release, revision, snapshot):
    swhids = []
    expected = {}
    for obj_type, obj_id in (
        (ObjectType.CONTENT, content["sha1_git"]),
        (ObjectType.DIRECTORY, directory),
        (ObjectType.RELEASE, release),
        (ObjectType.REVISION, revision),
        (ObjectType.SNAPSHOT, snapshot),
    ):
        swhid = gen_swhid(obj_type, obj_id)
        swhid = get_swhid(swhid)
        swhids.append(swhid)
        expected[obj_type] = [hash_to_bytes(obj_id)]

    swhid_groups = group_swhids(swhids)

    assert swhid_groups == expected


def test_get_swhids_info_directory_context(archive_data, directory_with_subdirs):
    swhid = get_swhids_info(
        [
            SWHObjectInfo(
                object_type=ObjectType.DIRECTORY, object_id=directory_with_subdirs
            )
        ],
        snapshot_context=None,
    )[0]
    assert swhid["swhid_with_context"] is None

    # path qualifier should be discarded for a root directory
    swhid = get_swhids_info(
        [
            SWHObjectInfo(
                object_type=ObjectType.DIRECTORY, object_id=directory_with_subdirs
            )
        ],
        snapshot_context=None,
        extra_context={"path": "/"},
    )[0]
    assert swhid["swhid_with_context"] is None

    dir_content = archive_data.directory_ls(directory_with_subdirs)
    dir_subdirs = [e for e in dir_content if e["type"] == "dir"]
    dir_subdir = random.choice(dir_subdirs)
    dir_subdir_path = f'/{dir_subdir["name"]}/'

    dir_subdir_content = archive_data.directory_ls(dir_subdir["target"])
    dir_subdir_files = [e for e in dir_subdir_content if e["type"] == "file"]

    swh_objects_info = [
        SWHObjectInfo(object_type=ObjectType.DIRECTORY, object_id=dir_subdir["target"])
    ]

    extra_context = {
        "root_directory": directory_with_subdirs,
        "path": dir_subdir_path,
    }

    if dir_subdir_files:
        dir_subdir_file = random.choice(dir_subdir_files)
        extra_context["filename"] = dir_subdir_file["name"]
        swh_objects_info.append(
            SWHObjectInfo(
                object_type=ObjectType.CONTENT,
                object_id=dir_subdir_file["checksums"]["sha1_git"],
            )
        )

    swhids = get_swhids_info(
        swh_objects_info,
        snapshot_context=None,
        extra_context=extra_context,
    )

    swhid_lower = swhids[0]["swhid_with_context"]
    swhid_upper = swhid_lower.replace(swhids[0]["swhid"], swhids[0]["swhid"].upper())

    for swhid in (swhid_lower, swhid_upper):
        swhid_dir_parsed = get_swhid(swhid)

        anchor = gen_swhid(ObjectType.DIRECTORY, directory_with_subdirs)

        assert swhid_dir_parsed.qualifiers() == {
            "anchor": anchor,
            "path": dir_subdir_path,
        }

    if dir_subdir_files:
        swhid_cnt_parsed = get_swhid(swhids[1]["swhid_with_context"])

        assert swhid_cnt_parsed.qualifiers() == {
            "anchor": anchor,
            "path": f'{dir_subdir_path}{dir_subdir_file["name"]}',
        }


def test_get_swhids_info_revision_context(archive_data, revision):
    revision_data = archive_data.revision_get(revision)
    directory = revision_data["directory"]
    dir_content = archive_data.directory_ls(directory)
    dir_entry = random.choice(dir_content)

    swh_objects = [
        SWHObjectInfo(object_type=ObjectType.REVISION, object_id=revision),
        SWHObjectInfo(object_type=ObjectType.DIRECTORY, object_id=directory),
    ]

    extra_context = {"revision": revision, "path": "/"}
    if dir_entry["type"] == "file":
        swh_objects.append(
            SWHObjectInfo(
                object_type=ObjectType.CONTENT,
                object_id=dir_entry["checksums"]["sha1_git"],
            )
        )
        extra_context["filename"] = dir_entry["name"]

    swhids = get_swhids_info(
        swh_objects,
        snapshot_context=None,
        extra_context=extra_context,
    )

    assert swhids[0]["context"] == {}

    swhid_lower = swhids[1]["swhid_with_context"]
    swhid_upper = swhid_lower.replace(swhids[1]["swhid"], swhids[1]["swhid"].upper())

    for swhid in (swhid_lower, swhid_upper):
        swhid_dir_parsed = get_swhid(swhid)

        anchor = gen_swhid(ObjectType.REVISION, revision)

        assert swhid_dir_parsed.qualifiers() == {
            "anchor": anchor,
        }

    if dir_entry["type"] == "file":
        swhid_cnt_parsed = get_swhid(swhids[2]["swhid_with_context"])
        assert swhid_cnt_parsed.qualifiers() == {
            "anchor": anchor,
            "path": f'/{dir_entry["name"]}',
        }


def test_get_swhids_info_origin_snapshot_context(
    archive_data, origin_with_multiple_visits
):
    """
    Test SWHIDs with contextual info computation under a variety of origin / snapshot
    browsing contexts.
    """
    origin_url = origin_with_multiple_visits["url"]
    visits = archive_data.origin_visit_get(origin_url)

    for visit in visits:
        snapshot = archive_data.snapshot_get(visit["snapshot"])
        snapshot_id = snapshot["id"]
        branches = {
            k: v["target"]
            for k, v in snapshot["branches"].items()
            if v["target_type"] == "revision"
        }
        releases = {
            k: v["target"]
            for k, v in snapshot["branches"].items()
            if v["target_type"] == "release"
        }
        head_rev_id = archive_data.snapshot_get_head(snapshot)
        head_rev = archive_data.revision_get(head_rev_id)
        root_dir = head_rev["directory"]
        dir_content = archive_data.directory_ls(root_dir)
        dir_files = [e for e in dir_content if e["type"] == "file"]
        dir_file = random.choice(dir_files)
        revision_log = [r["id"] for r in archive_data.revision_log(head_rev_id)]

        branch_name = random.choice(list(branches))
        release = random.choice(list(releases))
        release_data = archive_data.release_get(releases[release])
        release_name = release_data["name"]
        revision_id = random.choice(revision_log)

        for snp_ctx_params, anchor_info in (
            (
                {"snapshot_id": snapshot_id},
                {"anchor_type": ObjectType.REVISION, "anchor_id": head_rev_id},
            ),
            (
                {"snapshot_id": snapshot_id, "branch_name": branch_name},
                {
                    "anchor_type": ObjectType.REVISION,
                    "anchor_id": branches[branch_name],
                },
            ),
            (
                {"snapshot_id": snapshot_id, "release_name": release_name},
                {"anchor_type": ObjectType.RELEASE, "anchor_id": releases[release]},
            ),
            (
                {"snapshot_id": snapshot_id, "revision_id": revision_id},
                {"anchor_type": ObjectType.REVISION, "anchor_id": revision_id},
            ),
            (
                {"origin_url": origin_url, "snapshot_id": snapshot_id},
                {"anchor_type": ObjectType.REVISION, "anchor_id": head_rev_id},
            ),
            (
                {
                    "origin_url": origin_url,
                    "snapshot_id": snapshot_id,
                    "branch_name": branch_name,
                },
                {
                    "anchor_type": ObjectType.REVISION,
                    "anchor_id": branches[branch_name],
                },
            ),
            (
                {
                    "origin_url": origin_url,
                    "snapshot_id": snapshot_id,
                    "release_name": release_name,
                },
                {"anchor_type": ObjectType.RELEASE, "anchor_id": releases[release]},
            ),
            (
                {
                    "origin_url": origin_url,
                    "snapshot_id": snapshot_id,
                    "revision_id": revision_id,
                },
                {"anchor_type": ObjectType.REVISION, "anchor_id": revision_id},
            ),
        ):

            snapshot_context = get_snapshot_context(**snp_ctx_params)

            rev_id = head_rev_id
            if "branch_name" in snp_ctx_params:
                rev_id = branches[branch_name]
            elif "release_name" in snp_ctx_params:
                rev_id = release_data["target"]
            elif "revision_id" in snp_ctx_params:
                rev_id = revision_id

            swh_objects = [
                SWHObjectInfo(
                    object_type=ObjectType.CONTENT,
                    object_id=dir_file["checksums"]["sha1_git"],
                ),
                SWHObjectInfo(object_type=ObjectType.DIRECTORY, object_id=root_dir),
                SWHObjectInfo(object_type=ObjectType.REVISION, object_id=rev_id),
                SWHObjectInfo(object_type=ObjectType.SNAPSHOT, object_id=snapshot_id),
            ]

            if "release_name" in snp_ctx_params:
                swh_objects.append(
                    SWHObjectInfo(
                        object_type=ObjectType.RELEASE, object_id=release_data["id"]
                    )
                )

            swhids = get_swhids_info(
                swh_objects,
                snapshot_context,
                extra_context={"path": "/", "filename": dir_file["name"]},
            )

            swhid_cnt_parsed = get_swhid(swhids[0]["swhid_with_context"])
            swhid_dir_parsed = get_swhid(swhids[1]["swhid_with_context"])
            swhid_rev_parsed = get_swhid(swhids[2]["swhid_with_context"])

            swhid_snp_parsed = get_swhid(
                swhids[3]["swhid_with_context"] or swhids[3]["swhid"]
            )

            swhid_rel_parsed = None
            if "release_name" in snp_ctx_params:
                swhid_rel_parsed = get_swhid(swhids[4]["swhid_with_context"])

            anchor = gen_swhid(
                object_type=anchor_info["anchor_type"],
                object_id=anchor_info["anchor_id"],
            )

            snapshot_swhid = gen_swhid(
                object_type=ObjectType.SNAPSHOT, object_id=snapshot_id
            )

            expected_cnt_context = {
                "visit": snapshot_swhid,
                "anchor": anchor,
                "path": f'/{dir_file["name"]}',
            }

            expected_dir_context = {
                "visit": snapshot_swhid,
                "anchor": anchor,
            }

            expected_rev_context = {"visit": snapshot_swhid}

            expected_snp_context = {}

            if "origin_url" in snp_ctx_params:
                expected_cnt_context["origin"] = origin_url
                expected_dir_context["origin"] = origin_url
                expected_rev_context["origin"] = origin_url
                expected_snp_context["origin"] = origin_url

            assert swhid_cnt_parsed.qualifiers() == expected_cnt_context
            assert swhid_dir_parsed.qualifiers() == expected_dir_context
            assert swhid_rev_parsed.qualifiers() == expected_rev_context
            assert swhid_snp_parsed.qualifiers() == expected_snp_context

            if "release_name" in snp_ctx_params:
                assert swhid_rel_parsed.qualifiers() == expected_rev_context


def test_get_swhids_info_characters_and_url_escaping(archive_data, directory, origin):
    snapshot_context = get_snapshot_context(origin_url=origin["url"])
    snapshot_context["origin_info"]["url"] = "http://example.org/?project=abc;def%"
    path = "/foo;/bar%"

    swhid_info = get_swhids_info(
        [SWHObjectInfo(object_type=ObjectType.DIRECTORY, object_id=directory)],
        snapshot_context=snapshot_context,
        extra_context={"path": path},
    )[0]

    # check special characters in SWHID have been percent escaped
    assert (
        swhid_info["context"]["origin"] == "http://example.org/?project%3Dabc%3Bdef%25"
    )
    assert swhid_info["context"]["path"] == "/foo%3B/bar%25"

    # check special characters in SWHID URL have been escaped
    parsed_swhid_url = urlparse(swhid_info["swhid_with_context_url"])
    assert (
        "origin=http://example.org/%253Fproject%25253Dabc%25253Bdef%252525;"
        in parsed_swhid_url.path
    )
    assert "path=/foo%25253B/bar%252525" in parsed_swhid_url.path

    # check that by double unquoting SWHID URL path, we get back on the SWHID value
    # first unquoting is done by HTTP server, second unquoting by the SWHID parser
    # when processing origin and path qualifiers
    assert (
        unquote(unquote(parsed_swhid_url.path[1:])) == swhid_info["swhid_with_context"]
    )


def test_resolve_swhids_snapshot_context(
    client, archive_data, origin_with_multiple_visits
):
    origin_url = origin_with_multiple_visits["url"]
    visits = archive_data.origin_visit_get(origin_url)
    visit = random.choice(visits)
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    head_rev_id = archive_data.snapshot_get_head(snapshot)

    branch_info = None
    release_info = None
    for branch_name in sorted(snapshot["branches"]):
        target_type = snapshot["branches"][branch_name]["target_type"]
        target = snapshot["branches"][branch_name]["target"]
        if target_type == "revision" and branch_info is None:
            branch_info = {"name": branch_name, "revision": target}
        elif target_type == "release" and release_info is None:
            release_info = {"name": branch_name, "release": target}
        if branch_info and release_info:
            break

    release_info["name"] = archive_data.release_get(release_info["release"])["name"]

    directory = archive_data.revision_get(branch_info["revision"])["directory"]
    directory_content = archive_data.directory_ls(directory)
    directory_subdirs = [e for e in directory_content if e["type"] == "dir"]
    directory_subdir = None
    if directory_subdirs:
        directory_subdir = random.choice(directory_subdirs)
    directory_files = [e for e in directory_content if e["type"] == "file"]
    directory_file = None
    if directory_files:
        directory_file = random.choice(directory_files)
    random_rev_id = random.choice(archive_data.revision_log(head_rev_id))["id"]

    for snp_ctx_params in (
        {},
        {"branch_name": branch_info["name"]},
        {"release_name": release_info["name"]},
        {"revision_id": random_rev_id},
    ):
        snapshot_context = get_snapshot_context(
            snapshot["id"], origin_url, **snp_ctx_params
        )

        _check_resolved_swhid_browse_url(
            ObjectType.SNAPSHOT, snapshot["id"], snapshot_context
        )

        rev = head_rev_id
        if "branch_name" in snp_ctx_params:
            rev = branch_info["revision"]
        if "revision_id" in snp_ctx_params:
            rev = random_rev_id

        _check_resolved_swhid_browse_url(ObjectType.REVISION, rev, snapshot_context)

        _check_resolved_swhid_browse_url(
            ObjectType.DIRECTORY, directory, snapshot_context, path="/"
        )

        if directory_subdir:
            _check_resolved_swhid_browse_url(
                ObjectType.DIRECTORY,
                directory_subdir["target"],
                snapshot_context,
                path=f"/{directory_subdir['name']}/",
            )

        if directory_file:
            _check_resolved_swhid_browse_url(
                ObjectType.CONTENT,
                directory_file["target"],
                snapshot_context,
                path=f"/{directory_file['name']}",
            )

            _check_resolved_swhid_browse_url(
                ObjectType.CONTENT,
                directory_file["target"],
                snapshot_context,
                path=f"/{directory_file['name']}",
                lines="10",
            )

            _check_resolved_swhid_browse_url(
                ObjectType.CONTENT,
                directory_file["target"],
                snapshot_context,
                path=f"/{directory_file['name']}",
                lines="10-20",
            )


def _check_resolved_swhid_browse_url(
    object_type, object_id, snapshot_context, path=None, lines=None
):
    snapshot_id = snapshot_context["snapshot_id"]
    origin_url = None
    if snapshot_context["origin_info"]:
        origin_url = snapshot_context["origin_info"]["url"]

    obj_context = {}
    query_params = {}

    if origin_url:
        obj_context["origin"] = origin_url
        query_params["origin_url"] = origin_url

    obj_context["visit"] = gen_swhid(ObjectType.SNAPSHOT, snapshot_id)
    query_params["snapshot"] = snapshot_id

    if object_type in (ObjectType.CONTENT, ObjectType.DIRECTORY, ObjectType.REVISION):
        if snapshot_context["release"]:
            obj_context["anchor"] = gen_swhid(
                ObjectType.RELEASE, snapshot_context["release_id"]
            )
            query_params["release"] = snapshot_context["release"]
        else:
            obj_context["anchor"] = gen_swhid(
                ObjectType.REVISION, snapshot_context["revision_id"]
            )
            if object_type != ObjectType.REVISION:
                query_params["revision"] = snapshot_context["revision_id"]

    if path:
        obj_context["path"] = path
        if path != "/":
            if object_type == ObjectType.CONTENT:
                query_params["path"] = path[1:]
            else:
                query_params["path"] = path[1:-1]

    if object_type == ObjectType.DIRECTORY:
        object_id = snapshot_context["root_directory"]

    if lines:
        obj_context["lines"] = lines

    obj_core_swhid = gen_swhid(object_type, object_id)
    obj_swhid_lower = gen_swhid(object_type, object_id, metadata=obj_context)
    obj_swhid_upper = obj_swhid_lower.replace(obj_core_swhid, obj_core_swhid.upper(), 1)

    for obj_swhid in (obj_swhid_lower, obj_swhid_upper):
        obj_swhid_resolved = resolve_swhid(obj_swhid)

        url_args = {"sha1_git": object_id}
        if object_type == ObjectType.CONTENT:
            url_args = {"query_string": f"sha1_git:{object_id}"}
        elif object_type == ObjectType.SNAPSHOT:
            url_args = {"snapshot_id": object_id}

        expected_url = reverse(
            f"browse-{object_type.name.lower()}",
            url_args=url_args,
            query_params=query_params,
        )
        if lines:
            lines_number = lines.split("-")
            expected_url += f"#L{lines_number[0]}"
            if len(lines_number) > 1:
                expected_url += f"-L{lines_number[1]}"

        assert obj_swhid_resolved["browse_url"] == expected_url


def test_resolve_swhid_with_escaped_chars(archive_data, directory):
    origin_url = "http://example.org/?project=abc;"
    archive_data.origin_add([Origin(url=origin_url)])
    origin_swhid_escaped = quote(origin_url, safe="/?:@&")
    origin_swhid_url_escaped = quote(origin_url, safe="/:@;")
    swhid = gen_swhid(
        ObjectType.DIRECTORY, directory, metadata={"origin": origin_swhid_escaped}
    )
    resolved_swhid = resolve_swhid(swhid)
    assert resolved_swhid["swhid_parsed"].origin == origin_swhid_escaped
    assert origin_swhid_url_escaped in resolved_swhid["browse_url"]


def test_resolve_directory_swhid_path_without_trailing_slash(
    archive_data, directory_with_subdirs
):
    dir_content = archive_data.directory_ls(directory_with_subdirs)
    dir_subdirs = [e for e in dir_content if e["type"] == "dir"]
    dir_subdir = random.choice(dir_subdirs)
    dir_subdir_path = dir_subdir["name"]
    anchor = gen_swhid(ObjectType.DIRECTORY, directory_with_subdirs)
    swhid = gen_swhid(
        ObjectType.DIRECTORY,
        dir_subdir["target"],
        metadata={"anchor": anchor, "path": "/" + dir_subdir_path},
    )
    resolved_swhid = resolve_swhid(swhid)
    browse_url = reverse(
        "browse-directory",
        url_args={"sha1_git": directory_with_subdirs},
        query_params={"path": dir_subdir_path},
    )
    assert resolved_swhid["browse_url"] == browse_url


def test_resolve_swhid_with_malformed_origin_url(archive_data, directory):
    origin_url = "http://example.org/project/abc"
    malformed_origin_url = "http:/example.org/project/abc"
    archive_data.origin_add([Origin(url=origin_url)])
    swhid = gen_swhid(
        ObjectType.DIRECTORY, directory, metadata={"origin": malformed_origin_url}
    )
    resolved_swhid = resolve_swhid(swhid)
    assert origin_url in resolved_swhid["browse_url"]


def test_resolve_dir_entry_swhid_with_anchor_revision(archive_data, revision):
    revision_data = archive_data.revision_get(revision)
    directory = revision_data["directory"]
    dir_content = archive_data.directory_ls(directory)
    dir_entry = random.choice(dir_content)

    rev_swhid = gen_swhid(ObjectType.REVISION, revision)

    if dir_entry["type"] == "rev":
        return

    if dir_entry["type"] == "file":
        swhid = gen_swhid(
            ObjectType.CONTENT,
            dir_entry["checksums"]["sha1_git"],
            metadata={"anchor": rev_swhid, "path": f"/{dir_entry['name']}"},
        )

    else:
        swhid = gen_swhid(
            ObjectType.DIRECTORY,
            dir_entry["target"],
            metadata={"anchor": rev_swhid, "path": f"/{dir_entry['name']}/"},
        )

    browse_url = reverse(
        "browse-revision",
        url_args={"sha1_git": revision},
        query_params={"path": dir_entry["name"]},
    )

    resolved_swhid = resolve_swhid(swhid)

    assert resolved_swhid["browse_url"] == browse_url


def test_resolve_dir_entry_swhid_with_anchor_directory(
    archive_data, directory_with_subdirs
):
    dir_content = archive_data.directory_ls(directory_with_subdirs)
    dir_entry = random.choice(
        [entry for entry in dir_content if entry["type"] == "dir"]
    )

    dir_swhid = gen_swhid(ObjectType.DIRECTORY, directory_with_subdirs)

    swhid = gen_swhid(
        ObjectType.DIRECTORY,
        dir_entry["target"],
        metadata={"anchor": dir_swhid, "path": f"/{dir_entry['name']}/"},
    )
    browse_url = reverse(
        "browse-directory",
        url_args={"sha1_git": directory_with_subdirs},
        query_params={"path": f"{dir_entry['name']}"},
    )

    resolved_swhid = resolve_swhid(swhid)

    assert resolved_swhid["browse_url"] == browse_url


def test_resolve_file_entry_swhid_with_anchor_directory(
    archive_data, directory_with_files
):
    dir_content = archive_data.directory_ls(directory_with_files)
    file_entry = random.choice(
        [entry for entry in dir_content if entry["type"] == "file"]
    )

    dir_swhid = gen_swhid(ObjectType.DIRECTORY, directory_with_files)

    sha1_git = file_entry["checksums"]["sha1_git"]
    swhid = gen_swhid(
        ObjectType.CONTENT,
        sha1_git,
        metadata={"anchor": dir_swhid, "path": f"/{file_entry['name']}"},
    )
    browse_url = reverse(
        "browse-content",
        url_args={"query_string": f"sha1_git:{sha1_git}"},
        query_params={"path": f"{directory_with_files}/{file_entry['name']}"},
    )

    resolved_swhid = resolve_swhid(swhid)

    assert resolved_swhid["browse_url"] == browse_url
