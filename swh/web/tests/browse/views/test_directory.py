# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from hypothesis import given
import pytest

from django.utils.html import escape

from swh.model.from_disk import DentryPerms
from swh.model.hashutil import hash_to_bytes, hash_to_hex
from swh.model.model import (
    Origin,
    OriginVisit,
    OriginVisitStatus,
    Release,
    Revision,
    RevisionType,
    Snapshot,
    SnapshotBranch,
    TargetType,
    TimestampWithTimezone,
)
from swh.model.model import Directory, DirectoryEntry
from swh.model.model import ObjectType as ModelObjectType
from swh.model.swhids import ObjectType
from swh.storage.utils import now
from swh.web.browse.snapshot_context import process_snapshot_branches
from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.helpers import check_html_get_response
from swh.web.tests.strategies import new_person, new_swh_date
from swh.web.utils import gen_path_info, reverse
from swh.web.utils.identifiers import gen_swhid


def test_root_directory_view(client, archive_data, directory):
    _directory_view_checks(client, directory, archive_data.directory_ls(directory))


def test_sub_directory_view(client, archive_data, directory_with_subdirs):
    dir_content = archive_data.directory_ls(directory_with_subdirs)
    subdir = random.choice([e for e in dir_content if e["type"] == "dir"])
    subdir_content = archive_data.directory_ls(subdir["target"])
    _directory_view_checks(
        client, directory_with_subdirs, subdir_content, subdir["name"]
    )


@given(new_person(), new_swh_date())
def test_sub_directory_view_origin_context(
    client, archive_data, empty_directory, person, date
):
    origin_url = "test_sub_directory_view_origin_context"
    subdir = Directory(
        entries=(
            DirectoryEntry(
                name=b"foo",
                type="dir",
                target=hash_to_bytes(empty_directory),
                perms=DentryPerms.directory,
            ),
            DirectoryEntry(
                name=b"bar",
                type="dir",
                target=hash_to_bytes(empty_directory),
                perms=DentryPerms.directory,
            ),
        )
    )

    parentdir = Directory(
        entries=(
            DirectoryEntry(
                name=b"baz",
                type="dir",
                target=subdir.id,
                perms=DentryPerms.directory,
            ),
        )
    )
    archive_data.directory_add([subdir, parentdir])

    revision = Revision(
        directory=parentdir.id,
        author=person,
        committer=person,
        message=b"commit message",
        date=TimestampWithTimezone.from_datetime(date),
        committer_date=TimestampWithTimezone.from_datetime(date),
        synthetic=False,
        type=RevisionType.GIT,
    )
    archive_data.revision_add([revision])

    snapshot = Snapshot(
        branches={
            b"HEAD": SnapshotBranch(
                target="refs/head/master".encode(),
                target_type=TargetType.ALIAS,
            ),
            b"refs/head/master": SnapshotBranch(
                target=revision.id,
                target_type=TargetType.REVISION,
            ),
        }
    )
    archive_data.snapshot_add([snapshot])

    archive_data.origin_add([Origin(url=origin_url)])
    date = now()
    visit = OriginVisit(origin=origin_url, date=date, type="git")
    visit = archive_data.origin_visit_add([visit])[0]
    visit_status = OriginVisitStatus(
        origin=origin_url,
        visit=visit.visit,
        date=date,
        status="full",
        snapshot=snapshot.id,
    )
    archive_data.origin_visit_status_add([visit_status])

    dir_content = archive_data.directory_ls(hash_to_hex(parentdir.id))
    subdir = dir_content[0]
    subdir_content = archive_data.directory_ls(subdir["target"])
    _directory_view_checks(
        client,
        hash_to_hex(parentdir.id),
        subdir_content,
        subdir["name"],
        origin_url,
        hash_to_hex(snapshot.id),
        hash_to_hex(revision.id),
    )


def test_directory_request_errors(client, invalid_sha1, unknown_directory):
    dir_url = reverse("browse-directory", url_args={"sha1_git": invalid_sha1})

    check_html_get_response(
        client, dir_url, status_code=400, template_used="error.html"
    )

    dir_url = reverse("browse-directory", url_args={"sha1_git": unknown_directory})

    check_html_get_response(
        client, dir_url, status_code=404, template_used="error.html"
    )


def test_directory_with_invalid_path(client, directory):
    path = "foo/bar"
    dir_url = reverse(
        "browse-directory",
        url_args={"sha1_git": directory},
        query_params={"path": path},
    )

    resp = check_html_get_response(
        client, dir_url, status_code=404, template_used="browse-directory.html"
    )
    error_message = (
        f"Directory entry with path {path} from root directory {directory} not found"
    )
    assert_contains(resp, error_message, status_code=404)


def test_directory_uppercase(client, directory):
    url = reverse(
        "browse-directory-uppercase-checksum", url_args={"sha1_git": directory.upper()}
    )

    resp = check_html_get_response(client, url, status_code=302)

    redirect_url = reverse("browse-directory", url_args={"sha1_git": directory})

    assert resp["location"] == redirect_url


def test_permalink_box_context(client, tests_data, directory):
    origin_url = random.choice(tests_data["origins"])["url"]
    url = reverse(
        "browse-directory",
        url_args={"sha1_git": directory},
        query_params={"origin_url": origin_url},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )
    assert_contains(resp, 'id="swhid-context-option-directory"')


def test_directory_origin_snapshot_branch_browse(
    client, archive_data, origin_with_multiple_visits
):
    origin_url = origin_with_multiple_visits["url"]
    visits = archive_data.origin_visit_get(origin_url)
    visit = random.choice(visits)
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    snapshot_sizes = archive_data.snapshot_count_branches(visit["snapshot"])
    branches, releases, _ = process_snapshot_branches(snapshot)
    branch_info = next(
        branch for branch in branches if branch["name"] == "refs/heads/master"
    )

    directory = archive_data.revision_get(branch_info["target"])["directory"]
    directory_content = archive_data.directory_ls(directory)
    directory_subdir = random.choice(
        [e for e in directory_content if e["type"] == "dir"]
    )

    url = reverse(
        "browse-directory",
        url_args={"sha1_git": directory},
        query_params={
            "origin_url": origin_url,
            "snapshot": snapshot["id"],
            "branch": branch_info["name"],
            "path": directory_subdir["name"],
        },
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )

    _check_origin_snapshot_related_html(
        resp, origin_with_multiple_visits, snapshot, snapshot_sizes, branches, releases
    )
    assert_contains(resp, directory_subdir["name"])
    assert_contains(resp, f"Branch: <strong>{branch_info['name']}</strong>")

    dir_swhid = gen_swhid(
        ObjectType.DIRECTORY,
        directory_subdir["target"],
        metadata={
            "origin": origin_url,
            "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
            "anchor": gen_swhid(ObjectType.REVISION, branch_info["target"]),
            "path": "/",
        },
    )
    assert_contains(resp, dir_swhid)

    rev_swhid = gen_swhid(
        ObjectType.REVISION,
        branch_info["target"],
        metadata={
            "origin": origin_url,
            "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
        },
    )
    assert_contains(resp, rev_swhid)

    snp_swhid = gen_swhid(
        ObjectType.SNAPSHOT,
        snapshot["id"],
        metadata={
            "origin": origin_url,
        },
    )
    assert_contains(resp, snp_swhid)


def test_drectory_origin_snapshot_release_browse(
    client, archive_data, origin_with_multiple_visits
):
    origin_url = origin_with_multiple_visits["url"]
    visits = archive_data.origin_visit_get(origin_url)
    visit = random.choice(visits)
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    snapshot_sizes = archive_data.snapshot_count_branches(visit["snapshot"])
    branches, releases, _ = process_snapshot_branches(snapshot)
    release_info = random.choice(releases)

    directory = release_info["directory"]
    directory_content = archive_data.directory_ls(directory)
    directory_subdir = random.choice(
        [e for e in directory_content if e["type"] == "dir"]
    )

    url = reverse(
        "browse-directory",
        url_args={"sha1_git": directory},
        query_params={
            "origin_url": origin_url,
            "snapshot": snapshot["id"],
            "release": release_info["name"],
            "path": directory_subdir["name"],
        },
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )

    _check_origin_snapshot_related_html(
        resp, origin_with_multiple_visits, snapshot, snapshot_sizes, branches, releases
    )
    assert_contains(resp, directory_subdir["name"])
    assert_contains(resp, f"Release: <strong>{release_info['name']}</strong>")

    dir_swhid = gen_swhid(
        ObjectType.DIRECTORY,
        directory_subdir["target"],
        metadata={
            "origin": origin_url,
            "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
            "anchor": gen_swhid(ObjectType.RELEASE, release_info["id"]),
            "path": "/",
        },
    )
    assert_contains(resp, dir_swhid)

    rev_swhid = gen_swhid(
        ObjectType.REVISION,
        release_info["target"],
        metadata={
            "origin": origin_url,
            "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
        },
    )
    assert_contains(resp, rev_swhid)

    rel_swhid = gen_swhid(
        ObjectType.RELEASE,
        release_info["id"],
        metadata={
            "origin": origin_url,
            "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
        },
    )
    assert_contains(resp, rel_swhid)

    snp_swhid = gen_swhid(
        ObjectType.SNAPSHOT,
        snapshot["id"],
        metadata={
            "origin": origin_url,
        },
    )
    assert_contains(resp, snp_swhid)


def test_directory_origin_snapshot_revision_browse(
    client, archive_data, origin_with_multiple_visits
):
    origin_url = origin_with_multiple_visits["url"]
    visits = archive_data.origin_visit_get(origin_url)
    visit = random.choice(visits)
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    branches, releases, _ = process_snapshot_branches(snapshot)
    branch_info = next(
        branch for branch in branches if branch["name"] == "refs/heads/master"
    )

    directory = archive_data.revision_get(branch_info["target"])["directory"]
    directory_content = archive_data.directory_ls(directory)
    directory_subdir = random.choice(
        [e for e in directory_content if e["type"] == "dir"]
    )

    url = reverse(
        "browse-directory",
        url_args={"sha1_git": directory},
        query_params={
            "origin_url": origin_url,
            "snapshot": snapshot["id"],
            "revision": branch_info["target"],
            "path": directory_subdir["name"],
        },
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )

    assert_contains(resp, f"Revision: <strong>{branch_info['target']}</strong>")


def _check_origin_snapshot_related_html(
    resp, origin, snapshot, snapshot_sizes, branches, releases
):
    browse_origin_url = reverse(
        "browse-origin", query_params={"origin_url": origin["url"]}
    )

    assert_contains(resp, f'href="{browse_origin_url}"')

    origin_branches_url = reverse(
        "browse-origin-branches",
        query_params={"origin_url": origin["url"], "snapshot": snapshot["id"]},
    )

    assert_contains(resp, f'href="{escape(origin_branches_url)}"')
    assert_contains(resp, f"Branches ({snapshot_sizes['revision']})")

    origin_releases_url = reverse(
        "browse-origin-releases",
        query_params={"origin_url": origin["url"], "snapshot": snapshot["id"]},
    )

    assert_contains(resp, f'href="{escape(origin_releases_url)}"')
    assert_contains(resp, f"Releases ({snapshot_sizes['release']})")

    assert_contains(resp, '<li class="swh-branch">', count=len(branches))
    assert_contains(resp, '<li class="swh-release">', count=len(releases))


def _directory_view_checks(
    client,
    root_directory_sha1,
    directory_entries,
    path=None,
    origin_url=None,
    snapshot_id=None,
    revision_id=None,
):
    dirs = [e for e in directory_entries if e["type"] in ("dir", "rev")]
    files = [e for e in directory_entries if e["type"] == "file"]

    url_args = {"sha1_git": root_directory_sha1}
    query_params = {"origin_url": origin_url, "snapshot": snapshot_id}

    url = reverse(
        "browse-directory",
        url_args=url_args,
        query_params={**query_params, "path": path},
    )

    root_dir_url = reverse(
        "browse-directory",
        url_args=url_args,
        query_params=query_params,
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )

    assert_contains(
        resp,
        '<a href="' + root_dir_url + '">' + root_directory_sha1[:7] + "</a>",
    )
    assert_contains(resp, '<td class="swh-directory">', count=len(dirs))
    assert_contains(resp, '<td class="swh-content">', count=len(files))

    for d in dirs:
        if d["type"] == "rev":
            dir_url = reverse("browse-revision", url_args={"sha1_git": d["target"]})
        else:
            dir_path = d["name"]
            if path:
                dir_path = "%s/%s" % (path, d["name"])
            dir_url = reverse(
                "browse-directory",
                url_args={"sha1_git": root_directory_sha1},
                query_params={**query_params, "path": dir_path},
            )
        assert_contains(resp, dir_url)

    for f in files:
        file_path = "%s/%s" % (root_directory_sha1, f["name"])
        if path:
            file_path = "%s/%s/%s" % (root_directory_sha1, path, f["name"])
        query_string = "sha1_git:" + f["target"]
        file_url = reverse(
            "browse-content",
            url_args={"query_string": query_string},
            query_params={**query_params, "path": file_path},
        )
        assert_contains(resp, file_url)

    path_info = gen_path_info(path)

    assert_contains(resp, '<li class="swh-path">', count=len(path_info) + 1)
    assert_contains(
        resp, '<a href="%s">%s</a>' % (root_dir_url, root_directory_sha1[:7])
    )

    for p in path_info:
        dir_url = reverse(
            "browse-directory",
            url_args={"sha1_git": root_directory_sha1},
            query_params={**query_params, "path": p["path"]},
        )
        assert_contains(resp, '<a href="%s">%s</a>' % (dir_url, p["name"]))

    assert_contains(resp, "vault-cook-directory")

    swh_dir_id = gen_swhid(ObjectType.DIRECTORY, directory_entries[0]["dir_id"])
    swh_dir_id_url = reverse("browse-swhid", url_args={"swhid": swh_dir_id})

    swhid_context = {}
    if origin_url:
        swhid_context["origin"] = origin_url
    if snapshot_id:
        swhid_context["visit"] = gen_swhid(ObjectType.SNAPSHOT, snapshot_id)
    if root_directory_sha1 != directory_entries[0]["dir_id"]:
        swhid_context["anchor"] = gen_swhid(ObjectType.DIRECTORY, root_directory_sha1)
    if root_directory_sha1 != directory_entries[0]["dir_id"]:
        swhid_context["anchor"] = gen_swhid(ObjectType.DIRECTORY, root_directory_sha1)
    if revision_id:
        swhid_context["anchor"] = gen_swhid(ObjectType.REVISION, revision_id)
    swhid_context["path"] = f"/{path}/" if path else None

    swh_dir_id = gen_swhid(
        ObjectType.DIRECTORY, directory_entries[0]["dir_id"], metadata=swhid_context
    )
    swh_dir_id_url = reverse("browse-swhid", url_args={"swhid": swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)

    assert_not_contains(resp, "swh-metadata-popover")


@pytest.mark.django_db
@pytest.mark.parametrize("staff_user_logged_in", [False, True])
def test_browse_directory_snapshot_context_release_directory_target(
    client, staff_user, archive_data, directory_with_subdirs, staff_user_logged_in
):

    if staff_user_logged_in:
        client.force_login(staff_user)

    release_name = "v1.0.0"
    release = Release(
        name=release_name.encode(),
        message=f"release {release_name}".encode(),
        target=hash_to_bytes(directory_with_subdirs),
        target_type=ModelObjectType.DIRECTORY,
        synthetic=True,
    )
    archive_data.release_add([release])

    snapshot = Snapshot(
        branches={
            release_name.encode(): SnapshotBranch(
                target=release.id, target_type=TargetType.RELEASE
            ),
        },
    )
    archive_data.snapshot_add([snapshot])

    dir_content = archive_data.directory_ls(directory_with_subdirs)
    dir_entry = random.choice(
        [entry for entry in dir_content if entry["type"] == "dir"]
    )

    browse_url = reverse(
        "browse-directory",
        url_args={"sha1_git": directory_with_subdirs},
        query_params={
            "path": dir_entry["name"],
            "release": release_name,
            "snapshot": snapshot.id.hex(),
        },
    )

    check_html_get_response(
        client, browse_url, status_code=200, template_used="browse-directory.html"
    )
