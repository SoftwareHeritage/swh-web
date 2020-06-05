# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from hypothesis import given

import pytest

from swh.model.hashutil import hash_to_bytes
from swh.model.identifiers import (
    CONTENT,
    DIRECTORY,
    RELEASE,
    REVISION,
    SNAPSHOT,
    PersistentId,
)

from swh.web.common.exc import BadInputExc
from swh.web.common.identifiers import (
    get_swh_persistent_id,
    resolve_swh_persistent_id,
    get_persistent_identifier,
    group_swh_persistent_identifiers,
    get_swhids_info,
)
from swh.web.browse.snapshot_context import get_snapshot_context
from swh.web.common.utils import reverse
from swh.web.common.typing import SWHObjectInfo
from swh.web.tests.data import random_sha1
from swh.web.tests.strategies import (
    content,
    directory,
    release,
    revision,
    snapshot,
    origin,
    origin_with_multiple_visits,
    directory_with_subdirs,
)


@given(content())
def test_get_swh_persistent_id(content):
    swh_object_type = CONTENT
    sha1_git = content["sha1_git"]

    expected_swh_id = "swh:1:cnt:" + sha1_git

    assert get_swh_persistent_id(swh_object_type, sha1_git) == expected_swh_id

    with pytest.raises(BadInputExc) as e:
        get_swh_persistent_id("foo", sha1_git)
    assert e.match("Invalid object")

    with pytest.raises(BadInputExc) as e:
        get_swh_persistent_id(swh_object_type, "not a valid id")
    assert e.match("Invalid object")


@given(content(), directory(), release(), revision(), snapshot())
def test_resolve_swh_persistent_id_legacy(
    content, directory, release, revision, snapshot
):
    for obj_type, obj_id in (
        (CONTENT, content["sha1_git"]),
        (DIRECTORY, directory),
        (RELEASE, release),
        (REVISION, revision),
        (SNAPSHOT, snapshot),
    ):

        swh_pid = get_swh_persistent_id(obj_type, obj_id)

        url_args = {}
        if obj_type == CONTENT:
            url_args["query_string"] = f"sha1_git:{obj_id}"
        elif obj_type == SNAPSHOT:
            url_args["snapshot_id"] = obj_id
        else:
            url_args["sha1_git"] = obj_id
        query_params = {"origin_url": "some-origin"}
        browse_url = reverse(
            f"browse-{obj_type}", url_args=url_args, query_params=query_params
        )

        resolved_pid = resolve_swh_persistent_id(swh_pid, query_params)

        assert isinstance(resolved_pid["swh_id_parsed"], PersistentId)
        assert str(resolved_pid["swh_id_parsed"]) == swh_pid
        assert resolved_pid["browse_url"] == browse_url

    with pytest.raises(BadInputExc, match="Origin PIDs"):
        resolve_swh_persistent_id(f"swh:1:ori:{random_sha1()}")


@given(content(), directory(), release(), revision(), snapshot())
def test_get_persistent_identifier(content, directory, release, revision, snapshot):
    for obj_type, obj_id in (
        (CONTENT, content["sha1_git"]),
        (DIRECTORY, directory),
        (RELEASE, release),
        (REVISION, revision),
        (SNAPSHOT, snapshot),
    ):
        swh_pid = get_swh_persistent_id(obj_type, obj_id)
        swh_parsed_pid = get_persistent_identifier(swh_pid)

        assert isinstance(swh_parsed_pid, PersistentId)
        assert str(swh_parsed_pid) == swh_pid

    with pytest.raises(BadInputExc, match="Error when parsing identifier"):
        get_persistent_identifier("foo")


@given(content(), directory(), release(), revision(), snapshot())
def test_group_persistent_identifiers(content, directory, release, revision, snapshot):
    swh_pids = []
    expected = {}
    for obj_type, obj_id in (
        (CONTENT, content["sha1_git"]),
        (DIRECTORY, directory),
        (RELEASE, release),
        (REVISION, revision),
        (SNAPSHOT, snapshot),
    ):
        swh_pid = get_swh_persistent_id(obj_type, obj_id)
        swh_pid = get_persistent_identifier(swh_pid)
        swh_pids.append(swh_pid)
        expected[obj_type] = [hash_to_bytes(obj_id)]

    pid_groups = group_swh_persistent_identifiers(swh_pids)

    assert pid_groups == expected


@given(directory_with_subdirs())
def test_get_swhids_info_directory_context(archive_data, directory):
    extra_context = {"path": "/"}
    swhid = get_swhids_info(
        [SWHObjectInfo(object_type=DIRECTORY, object_id=directory)],
        snapshot_context=None,
        extra_context=extra_context,
    )[0]
    swhid_dir_parsed = get_persistent_identifier(swhid["swhid_with_context"])

    assert swhid_dir_parsed.metadata == extra_context

    dir_content = archive_data.directory_ls(directory)
    dir_subdirs = [e for e in dir_content if e["type"] == "dir"]
    dir_subdir = random.choice(dir_subdirs)
    dir_subdir_path = f'/{dir_subdir["name"]}/'

    dir_subdir_content = archive_data.directory_ls(dir_subdir["target"])
    dir_subdir_files = [e for e in dir_subdir_content if e["type"] == "file"]
    dir_subdir_file = random.choice(dir_subdir_files)

    extra_context = {
        "root_directory": directory,
        "path": dir_subdir_path,
        "filename": dir_subdir_file["name"],
    }
    swhids = get_swhids_info(
        [
            SWHObjectInfo(object_type=DIRECTORY, object_id=dir_subdir["target"]),
            SWHObjectInfo(
                object_type=CONTENT, object_id=dir_subdir_file["checksums"]["sha1_git"]
            ),
        ],
        snapshot_context=None,
        extra_context=extra_context,
    )
    swhid_dir_parsed = get_persistent_identifier(swhids[0]["swhid_with_context"])
    swhid_cnt_parsed = get_persistent_identifier(swhids[1]["swhid_with_context"])

    anchor = get_swh_persistent_id(DIRECTORY, directory)

    assert swhid_dir_parsed.metadata == {
        "anchor": anchor,
        "path": dir_subdir_path,
    }

    assert swhid_cnt_parsed.metadata == {
        "anchor": anchor,
        "path": f'{dir_subdir_path}{dir_subdir_file["name"]}',
    }


@given(revision())
def test_get_swhids_info_revision_context(archive_data, revision):
    revision_data = archive_data.revision_get(revision)
    directory = revision_data["directory"]
    dir_content = archive_data.directory_ls(directory)
    dir_entry = random.choice(dir_content)

    swh_objects = [
        SWHObjectInfo(object_type=REVISION, object_id=revision),
        SWHObjectInfo(object_type=DIRECTORY, object_id=directory),
    ]

    extra_context = {"revision": revision, "path": "/"}
    if dir_entry["type"] == "file":
        swh_objects.append(
            SWHObjectInfo(
                object_type=CONTENT, object_id=dir_entry["checksums"]["sha1_git"]
            )
        )
        extra_context["filename"] = dir_entry["name"]

    swhids = get_swhids_info(
        swh_objects, snapshot_context=None, extra_context=extra_context,
    )

    assert swhids[0]["context"] == {}
    swhid_dir_parsed = get_persistent_identifier(swhids[1]["swhid_with_context"])

    anchor = get_swh_persistent_id(REVISION, revision)

    assert swhid_dir_parsed.metadata == {
        "anchor": anchor,
        "path": "/",
    }

    if dir_entry["type"] == "file":
        swhid_cnt_parsed = get_persistent_identifier(swhids[2]["swhid_with_context"])
        assert swhid_cnt_parsed.metadata == {
            "anchor": anchor,
            "path": f'/{dir_entry["name"]}',
        }


@given(origin_with_multiple_visits())
def test_get_swhids_info_origin_snapshot_context(archive_data, origin):
    """
    Test SWHIDs with contextual info computation under a variety of origin / snapshot
    browsing contexts.
    """

    visits = archive_data.origin_visit_get(origin["url"])

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
                {"anchor_type": REVISION, "anchor_id": head_rev_id},
            ),
            (
                {"snapshot_id": snapshot_id, "branch_name": branch_name},
                {"anchor_type": REVISION, "anchor_id": branches[branch_name]},
            ),
            (
                {"snapshot_id": snapshot_id, "release_name": release_name},
                {"anchor_type": RELEASE, "anchor_id": releases[release]},
            ),
            (
                {"snapshot_id": snapshot_id, "revision_id": revision_id},
                {"anchor_type": REVISION, "anchor_id": revision_id},
            ),
            (
                {"origin_url": origin["url"], "snapshot_id": snapshot_id},
                {"anchor_type": REVISION, "anchor_id": head_rev_id},
            ),
            (
                {
                    "origin_url": origin["url"],
                    "snapshot_id": snapshot_id,
                    "branch_name": branch_name,
                },
                {"anchor_type": REVISION, "anchor_id": branches[branch_name]},
            ),
            (
                {
                    "origin_url": origin["url"],
                    "snapshot_id": snapshot_id,
                    "release_name": release_name,
                },
                {"anchor_type": RELEASE, "anchor_id": releases[release]},
            ),
            (
                {
                    "origin_url": origin["url"],
                    "snapshot_id": snapshot_id,
                    "revision_id": revision_id,
                },
                {"anchor_type": REVISION, "anchor_id": revision_id},
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
                    object_type=CONTENT, object_id=dir_file["checksums"]["sha1_git"]
                ),
                SWHObjectInfo(object_type=DIRECTORY, object_id=root_dir),
                SWHObjectInfo(object_type=REVISION, object_id=rev_id),
                SWHObjectInfo(object_type=SNAPSHOT, object_id=snapshot_id),
            ]

            if "release_name" in snp_ctx_params:
                swh_objects.append(
                    SWHObjectInfo(object_type=RELEASE, object_id=release_data["id"])
                )

            swhids = get_swhids_info(
                swh_objects,
                snapshot_context,
                extra_context={"path": "/", "filename": dir_file["name"]},
            )

            swhid_cnt_parsed = get_persistent_identifier(
                swhids[0]["swhid_with_context"]
            )
            swhid_dir_parsed = get_persistent_identifier(
                swhids[1]["swhid_with_context"]
            )
            swhid_rev_parsed = get_persistent_identifier(
                swhids[2]["swhid_with_context"]
            )

            swhid_snp_parsed = get_persistent_identifier(
                swhids[3]["swhid_with_context"] or swhids[3]["swhid"]
            )

            swhid_rel_parsed = None
            if "release_name" in snp_ctx_params:
                swhid_rel_parsed = get_persistent_identifier(
                    swhids[4]["swhid_with_context"]
                )

            anchor = get_swh_persistent_id(
                object_type=anchor_info["anchor_type"],
                object_id=anchor_info["anchor_id"],
            )

            snapshot_swhid = get_swh_persistent_id(
                object_type=SNAPSHOT, object_id=snapshot_id
            )

            expected_cnt_context = {
                "visit": snapshot_swhid,
                "anchor": anchor,
                "path": f'/{dir_file["name"]}',
            }

            expected_dir_context = {
                "visit": snapshot_swhid,
                "anchor": anchor,
                "path": "/",
            }

            expected_rev_context = {"visit": snapshot_swhid}

            expected_snp_context = {}

            if "origin_url" in snp_ctx_params:
                expected_cnt_context["origin"] = origin["url"]
                expected_dir_context["origin"] = origin["url"]
                expected_rev_context["origin"] = origin["url"]
                expected_snp_context["origin"] = origin["url"]

            assert swhid_cnt_parsed.metadata == expected_cnt_context
            assert swhid_dir_parsed.metadata == expected_dir_context
            assert swhid_rev_parsed.metadata == expected_rev_context
            assert swhid_snp_parsed.metadata == expected_snp_context

            if "release_name" in snp_ctx_params:
                assert swhid_rel_parsed.metadata == expected_rev_context


@given(origin(), directory())
def test_get_swhids_info_path_encoding(archive_data, origin, directory):
    snapshot_context = get_snapshot_context(origin_url=origin["url"])
    snapshot_context["origin_info"]["url"] = "http://example.org/?project=abc;def%"
    path = "/foo;/bar%"

    swhid = get_swhids_info(
        [SWHObjectInfo(object_type=DIRECTORY, object_id=directory)],
        snapshot_context=snapshot_context,
        extra_context={"path": path},
    )[0]

    assert swhid["context"]["origin"] == "http://example.org/?project%3Dabc%3Bdef%25"
    assert swhid["context"]["path"] == "/foo%3B/bar%25"


@given(origin_with_multiple_visits())
def test_resolve_swhids_snapshot_context(client, archive_data, origin):
    visits = archive_data.origin_visit_get(origin["url"])
    visit = random.choice(visits)
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    head_rev_id = archive_data.snapshot_get_head(snapshot)
    branch_info = random.choice(
        [
            {"name": k, "revision": v["target"]}
            for k, v in snapshot["branches"].items()
            if v["target_type"] == "revision"
        ]
    )
    release_info = random.choice(
        [
            {"name": k, "release": v["target"]}
            for k, v in snapshot["branches"].items()
            if v["target_type"] == "release"
        ]
    )
    release_info["name"] = archive_data.release_get(release_info["release"])["name"]

    directory = archive_data.revision_get(branch_info["revision"])["directory"]
    directory_content = archive_data.directory_ls(directory)
    directory_subdir = random.choice(
        [e for e in directory_content if e["type"] == "dir"]
    )
    directory_file = random.choice(
        [e for e in directory_content if e["type"] == "file"]
    )
    random_rev_id = random.choice(archive_data.revision_log(head_rev_id))["id"]

    for snp_ctx_params in (
        {},
        {"branch_name": branch_info["name"]},
        {"release_name": release_info["name"]},
        {"revision_id": random_rev_id},
    ):
        snapshot_context = get_snapshot_context(
            snapshot["id"], origin["url"], **snp_ctx_params
        )

        _check_resolved_swhid_browse_url(SNAPSHOT, snapshot["id"], snapshot_context)

        rev = head_rev_id
        if "branch_name" in snp_ctx_params:
            rev = branch_info["revision"]
        if "revision_id" in snp_ctx_params:
            rev = random_rev_id

        _check_resolved_swhid_browse_url(REVISION, rev, snapshot_context)

        _check_resolved_swhid_browse_url(
            DIRECTORY, directory, snapshot_context, path="/"
        )

        _check_resolved_swhid_browse_url(
            DIRECTORY,
            directory_subdir["target"],
            snapshot_context,
            path=f"/{directory_subdir['name']}/",
        )

        _check_resolved_swhid_browse_url(
            CONTENT,
            directory_file["target"],
            snapshot_context,
            path=f"/{directory_file['name']}",
        )


def _check_resolved_swhid_browse_url(
    object_type, object_id, snapshot_context, path=None
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

    obj_context["visit"] = get_swh_persistent_id(SNAPSHOT, snapshot_id)
    query_params["snapshot"] = snapshot_id

    if object_type in (CONTENT, DIRECTORY, REVISION):
        if snapshot_context["release"]:
            obj_context["anchor"] = get_swh_persistent_id(
                RELEASE, snapshot_context["release_id"]
            )
            query_params["release"] = snapshot_context["release"]
        else:
            obj_context["anchor"] = get_swh_persistent_id(
                REVISION, snapshot_context["revision_id"]
            )
            if (
                snapshot_context["branch"]
                and snapshot_context["branch"] != snapshot_context["revision_id"]
            ):
                branch = snapshot_context["branch"]
                if branch == "HEAD":
                    for b in snapshot_context["branches"]:
                        if (
                            b["revision"] == snapshot_context["revision_id"]
                            and b["name"] != "HEAD"
                        ):
                            branch = b["name"]
                            break

                query_params["branch"] = branch
            elif object_type != REVISION:
                query_params["revision"] = snapshot_context["revision_id"]

    if path:
        obj_context["path"] = path
        if path != "/":
            if object_type == CONTENT:
                query_params["path"] = path[1:]
            else:
                query_params["path"] = path[1:-1]

    if object_type == DIRECTORY:
        object_id = snapshot_context["root_directory"]

    obj_swhid = get_swh_persistent_id(object_type, object_id, metadata=obj_context)

    obj_swhid_resolved = resolve_swh_persistent_id(obj_swhid)

    url_args = {"sha1_git": object_id}
    if object_type == CONTENT:
        url_args = {"query_string": f"sha1_git:{object_id}"}
    elif object_type == SNAPSHOT:
        url_args = {"snapshot_id": object_id}

    expected_url = reverse(
        f"browse-{object_type}", url_args=url_args, query_params=query_params,
    )

    assert obj_swhid_resolved["browse_url"] == expected_url
