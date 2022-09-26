# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random
import re

from hypothesis import given
import pytest

from django.utils.html import escape

from swh.model.hashutil import hash_to_bytes
from swh.model.model import (
    OriginVisit,
    OriginVisitStatus,
    Snapshot,
    SnapshotBranch,
    TargetType,
)
from swh.model.swhids import ObjectType
from swh.storage.utils import now
from swh.web.browse.snapshot_context import process_snapshot_branches
from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.helpers import check_html_get_response
from swh.web.tests.strategies import new_origin, new_snapshot, visit_dates
from swh.web.utils import format_utc_iso_date, parse_iso8601_date_to_utc, reverse
from swh.web.utils.exc import NotFoundExc
from swh.web.utils.identifiers import gen_swhid


def test_origin_visits_browse(client, archive_data, origin_with_multiple_visits):
    origin_url = origin_with_multiple_visits["url"]
    url = reverse("browse-origin-visits", query_params={"origin_url": origin_url})

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-origin-visits.html"
    )

    visits = archive_data.origin_visit_get(origin_url)

    for v in visits:
        vdate = format_utc_iso_date(v["date"], "%Y-%m-%dT%H:%M:%SZ")
        browse_dir_url = reverse(
            "browse-origin-directory",
            query_params={"origin_url": origin_url, "timestamp": vdate},
        )
        assert_contains(resp, browse_dir_url)

    _check_origin_link(resp, origin_url)

    assert_contains(resp, "swh-take-new-snashot")


@pytest.mark.django_db
def test_origin_root_directory_view(
    client, staff_user, archive_data, swh_scheduler, origin
):
    origin_visits = archive_data.origin_visit_get(origin["url"])

    visit = origin_visits[-1]
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    snapshot_sizes = archive_data.snapshot_count_branches(snapshot["id"])
    head_rev_id = archive_data.snapshot_get_head(snapshot)
    head_rev = archive_data.revision_get(head_rev_id)
    root_dir_sha1 = head_rev["directory"]
    dir_content = archive_data.directory_ls(root_dir_sha1)
    branches, releases, _ = process_snapshot_branches(snapshot)

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        root_dir_sha1,
        dir_content,
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        root_dir_sha1,
        dir_content,
        visit_id=visit["visit"],
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        root_dir_sha1,
        dir_content,
        timestamp=visit["date"],
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        root_dir_sha1,
        dir_content,
        snapshot_id=visit["snapshot"],
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        root_dir_sha1,
        dir_content,
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        root_dir_sha1,
        dir_content,
        visit_id=visit["visit"],
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        root_dir_sha1,
        dir_content,
        timestamp=visit["date"],
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        root_dir_sha1,
        dir_content,
        snapshot_id=visit["snapshot"],
    )


@pytest.mark.django_db
def test_origin_sub_directory_view(
    client, staff_user, archive_data, swh_scheduler, origin
):
    origin_visits = archive_data.origin_visit_get(origin["url"])

    visit = origin_visits[-1]
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    snapshot_sizes = archive_data.snapshot_count_branches(snapshot["id"])
    head_rev_id = archive_data.snapshot_get_head(snapshot)
    head_rev = archive_data.revision_get(head_rev_id)
    root_dir_sha1 = head_rev["directory"]
    subdirs = [
        e for e in archive_data.directory_ls(root_dir_sha1) if e["type"] == "dir"
    ]
    branches, releases, _ = process_snapshot_branches(snapshot)

    if len(subdirs) == 0:
        return

    subdir = random.choice(subdirs)
    subdir_content = archive_data.directory_ls(subdir["target"])
    subdir_path = subdir["name"]

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir["target"],
        subdir_content,
        path=subdir_path,
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir["target"],
        subdir_content,
        path=subdir_path,
        visit_id=visit["visit"],
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir["target"],
        subdir_content,
        path=subdir_path,
        timestamp=visit["date"],
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir["target"],
        subdir_content,
        path=subdir_path,
        snapshot_id=visit["snapshot"],
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir["target"],
        subdir_content,
        path=subdir_path,
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir["target"],
        subdir_content,
        path=subdir_path,
        visit_id=visit["visit"],
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir["target"],
        subdir_content,
        path=subdir_path,
        timestamp=visit["date"],
    )

    _origin_directory_view_test_helper(
        client,
        staff_user,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir["target"],
        subdir_content,
        path=subdir_path,
        snapshot_id=visit["snapshot"],
    )


@given(
    new_origin(),
    new_snapshot(min_size=4, max_size=4),
    visit_dates(),
)
def test_origin_snapshot_null_branch(
    client,
    archive_data,
    revisions_list,
    new_origin,
    new_snapshot,
    visit_dates,
):
    revisions = revisions_list(size=4)
    snp_dict = new_snapshot.to_dict()
    archive_data.origin_add([new_origin])
    for i, branch in enumerate(snp_dict["branches"].keys()):
        if i == 0:
            snp_dict["branches"][branch] = None
        else:
            snp_dict["branches"][branch] = {
                "target_type": "revision",
                "target": hash_to_bytes(revisions[i - 1]),
            }

    archive_data.snapshot_add([Snapshot.from_dict(snp_dict)])
    visit = archive_data.origin_visit_add(
        [
            OriginVisit(
                origin=new_origin.url,
                date=visit_dates[0],
                type="git",
            )
        ]
    )[0]
    visit_status = OriginVisitStatus(
        origin=new_origin.url,
        visit=visit.visit,
        date=now(),
        status="partial",
        snapshot=snp_dict["id"],
    )
    archive_data.origin_visit_status_add([visit_status])

    url = reverse(
        "browse-origin-directory", query_params={"origin_url": new_origin.url}
    )

    check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )


@given(
    new_origin(),
    new_snapshot(min_size=4, max_size=4),
    visit_dates(),
)
def test_origin_snapshot_invalid_branch(
    client,
    archive_data,
    revisions_list,
    new_origin,
    new_snapshot,
    visit_dates,
):
    revisions = revisions_list(size=4)
    snp_dict = new_snapshot.to_dict()
    archive_data.origin_add([new_origin])
    for i, branch in enumerate(snp_dict["branches"].keys()):
        snp_dict["branches"][branch] = {
            "target_type": "revision",
            "target": hash_to_bytes(revisions[i]),
        }

    archive_data.snapshot_add([Snapshot.from_dict(snp_dict)])
    visit = archive_data.origin_visit_add(
        [
            OriginVisit(
                origin=new_origin.url,
                date=visit_dates[0],
                type="git",
            )
        ]
    )[0]
    visit_status = OriginVisitStatus(
        origin=new_origin.url,
        visit=visit.visit,
        date=now(),
        status="full",
        snapshot=snp_dict["id"],
    )
    archive_data.origin_visit_status_add([visit_status])

    url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": new_origin.url, "branch": "invalid_branch"},
    )

    check_html_get_response(client, url, status_code=404, template_used="error.html")


@given(new_origin())
def test_browse_visits_origin_not_found(client, new_origin):
    url = reverse("browse-origin-visits", query_params={"origin_url": new_origin.url})

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert_contains(
        resp, f"Origin with url {new_origin.url} not found", status_code=404
    )


def test_browse_origin_directory_no_visit(client, mocker, origin):
    mock_get_origin_visits = mocker.patch(
        "swh.web.utils.origin_visits.get_origin_visits"
    )
    mock_get_origin_visits.return_value = []
    mock_archive = mocker.patch("swh.web.utils.origin_visits.archive")
    mock_archive.lookup_origin_visit_latest.return_value = None
    url = reverse("browse-origin-directory", query_params={"origin_url": origin["url"]})

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert_contains(resp, "No valid visit", status_code=404)
    assert not mock_get_origin_visits.called


def test_browse_origin_directory_unknown_visit(client, origin):

    url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": origin["url"], "visit_id": 200},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert re.search("visit.*not found", resp.content.decode("utf-8"))


def test_browse_origin_directory_not_found(client, origin):
    url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": origin["url"], "path": "/invalid/dir/path/"},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="browse-directory.html"
    )
    assert re.search("Directory.*not found", resp.content.decode("utf-8"))


def _add_empty_snapshot_origin(new_origin, archive_data):
    snapshot = Snapshot(branches={})
    archive_data.origin_add([new_origin])
    archive_data.snapshot_add([snapshot])
    visit = archive_data.origin_visit_add(
        [
            OriginVisit(
                origin=new_origin.url,
                date=now(),
                type="git",
            )
        ]
    )[0]
    visit_status = OriginVisitStatus(
        origin=new_origin.url,
        visit=visit.visit,
        date=now(),
        status="full",
        snapshot=snapshot.id,
    )
    archive_data.origin_visit_status_add([visit_status])


@pytest.mark.django_db
@pytest.mark.parametrize("object_type", ["directory"])
@given(new_origin())
def test_browse_origin_content_directory_empty_snapshot(
    client, staff_user, archive_data, object_type, new_origin
):

    _add_empty_snapshot_origin(new_origin, archive_data)

    # to check proper generation of raw extrinsic metadata api links
    client.force_login(staff_user)

    url = reverse(
        f"browse-origin-{object_type}",
        query_params={"origin_url": new_origin.url, "path": "baz"},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used=f"browse-{object_type}.html"
    )
    assert re.search("snapshot.*is empty", resp.content.decode("utf-8"))


def test_browse_directory_snapshot_not_found(client, mocker, origin):
    mock_get_snapshot_context = mocker.patch(
        "swh.web.browse.snapshot_context.get_snapshot_context"
    )
    mock_get_snapshot_context.side_effect = NotFoundExc("Snapshot not found")
    url = reverse("browse-origin-directory", query_params={"origin_url": origin["url"]})

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert_contains(resp, "Snapshot not found", status_code=404)
    assert mock_get_snapshot_context.called


@given(new_origin())
def test_origin_empty_snapshot(client, archive_data, new_origin):

    _add_empty_snapshot_origin(new_origin, archive_data)

    url = reverse(
        "browse-origin-directory", query_params={"origin_url": new_origin.url}
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )
    resp_content = resp.content.decode("utf-8")
    assert re.search("snapshot.*is empty", resp_content)
    assert not re.search("swh-tr-link", resp_content)


@given(new_origin())
def test_origin_empty_snapshot_null_revision(client, archive_data, new_origin):
    snapshot = Snapshot(
        branches={
            b"HEAD": SnapshotBranch(
                target="refs/head/master".encode(),
                target_type=TargetType.ALIAS,
            ),
            b"refs/head/master": None,
        }
    )
    archive_data.origin_add([new_origin])
    archive_data.snapshot_add([snapshot])
    visit = archive_data.origin_visit_add(
        [
            OriginVisit(
                origin=new_origin.url,
                date=now(),
                type="git",
            )
        ]
    )[0]
    visit_status = OriginVisitStatus(
        origin=new_origin.url,
        visit=visit.visit,
        date=now(),
        status="partial",
        snapshot=snapshot.id,
    )
    archive_data.origin_visit_status_add([visit_status])

    url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": new_origin.url},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )
    resp_content = resp.content.decode("utf-8")
    assert re.search("snapshot.*is empty", resp_content)
    assert not re.search("swh-tr-link", resp_content)


def test_origin_release_browse(client, archive_data, origin_with_releases):
    origin_url = origin_with_releases["url"]
    snapshot = archive_data.snapshot_get_latest(origin_url)
    release = [
        b for b in snapshot["branches"].values() if b["target_type"] == "release"
    ][-1]
    release_data = archive_data.release_get(release["target"])
    revision_data = archive_data.revision_get(release_data["target"])
    url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": origin_url, "release": release_data["name"]},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )
    assert_contains(resp, release_data["name"])
    assert_contains(resp, release["target"])

    swhid_context = {
        "origin": origin_url,
        "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
        "anchor": gen_swhid(ObjectType.RELEASE, release_data["id"]),
    }

    swh_dir_id = gen_swhid(
        ObjectType.DIRECTORY, revision_data["directory"], metadata=swhid_context
    )
    swh_dir_id_url = reverse("browse-swhid", url_args={"swhid": swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)


def test_origin_release_browse_not_found(client, origin_with_releases):

    invalid_release_name = "swh-foo-bar"
    url = reverse(
        "browse-origin-directory",
        query_params={
            "origin_url": origin_with_releases["url"],
            "release": invalid_release_name,
        },
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert re.search(
        f"Release {invalid_release_name}.*not found", resp.content.decode("utf-8")
    )


@given(new_origin())
def test_origin_browse_directory_branch_with_non_resolvable_revision(
    client,
    archive_data,
    unknown_revision,
    new_origin,
):
    branch_name = "master"
    snapshot = Snapshot(
        branches={
            branch_name.encode(): SnapshotBranch(
                target=hash_to_bytes(unknown_revision),
                target_type=TargetType.REVISION,
            )
        }
    )
    archive_data.origin_add([new_origin])
    archive_data.snapshot_add([snapshot])
    visit = archive_data.origin_visit_add(
        [
            OriginVisit(
                origin=new_origin.url,
                date=now(),
                type="git",
            )
        ]
    )[0]
    visit_status = OriginVisitStatus(
        origin=new_origin.url,
        visit=visit.visit,
        date=now(),
        status="partial",
        snapshot=snapshot.id,
    )
    archive_data.origin_visit_status_add([visit_status])

    url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": new_origin.url, "branch": branch_name},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )
    assert_contains(
        resp, f"Revision {unknown_revision } could not be found in the archive."
    )

    # no revision card
    assert_not_contains(resp, "swh-tip-revision")
    # no Download dropdown
    assert_not_contains(resp, "swh-vault-download")
    # no History link
    assert_not_contains(resp, "swh-tr-link")
    # no SWHIDs for directory and revision
    assert_not_contains(resp, "swh:1:dir:")
    assert_not_contains(resp, "swh:1:rev:")


def test_origin_views_no_url_query_parameter(client):
    for browse_context in (
        "directory",
        "visits",
    ):
        url = reverse(f"browse-origin-{browse_context}")
        resp = check_html_get_response(
            client, url, status_code=400, template_used="error.html"
        )
        assert_contains(
            resp,
            "An origin URL must be provided as query parameter.",
            status_code=400,
        )


@given(new_origin())
@pytest.mark.parametrize("browse_context", ["log", "branches", "releases"])
def test_origin_view_redirects(client, browse_context, new_origin):
    query_params = {"origin_url": new_origin.url}
    url = reverse(f"browse-origin-{browse_context}", query_params=query_params)

    resp = check_html_get_response(client, url, status_code=301)
    assert resp["location"] == reverse(
        f"browse-snapshot-{browse_context}", query_params=query_params
    )


@given(new_origin())
@pytest.mark.parametrize("browse_context", ["content"])
def test_origin_content_view_redirects(client, browse_context, new_origin):
    query_params = {"origin_url": new_origin.url, "path": "test.txt"}
    url = reverse(f"browse-origin-{browse_context}", query_params=query_params)

    resp = check_html_get_response(client, url, status_code=301)
    assert resp["location"] == reverse(
        f"browse-{browse_context}", query_params=query_params
    )


@given(new_origin())
@pytest.mark.parametrize("browse_context", ["log", "branches", "releases"])
def test_origin_view_legacy_redirects(client, browse_context, new_origin):
    # Each legacy route corresponds to two URL patterns, testing both
    url_args = [
        {"origin_url": new_origin.url},
        {"origin_url": new_origin.url, "timestamp": "2021-01-23T22:24:10Z"},
    ]
    params = {"extra-param1": "extra-param1", "extra-param2": "extra-param2"}
    for each_arg in url_args:
        url = reverse(
            f"browse-origin-{browse_context}-legacy",
            url_args=each_arg,
            query_params=params,
        )

        resp = check_html_get_response(client, url, status_code=301)
        assert resp["location"] == reverse(
            f"browse-snapshot-{browse_context}", query_params={**each_arg, **params}
        )


@given(new_origin())
def test_origin_content_view_legacy_redirects(client, new_origin):
    url_args = [
        {"origin_url": new_origin.url},
        {
            "origin_url": new_origin.url,
            "path": "test.txt",
            "timestamp": "2021-01-23T22:24:10Z",
        },
        {"origin_url": new_origin.url, "path": "test.txt"},
    ]
    params = {"extra-param1": "extra-param1", "extra-param2": "extra-param2"}
    for each_arg in url_args:
        url = reverse(
            "browse-origin-content-legacy",
            url_args=each_arg,
            query_params=params,
        )

        resp = check_html_get_response(client, url, status_code=301)
        assert resp["location"] == reverse(
            "browse-content", query_params={**each_arg, **params}
        )


def _origin_directory_view_test_helper(
    client,
    staff_user,
    archive_data,
    origin_info,
    origin_visit,
    snapshot_sizes,
    origin_branches,
    origin_releases,
    root_directory_sha1,
    target_directory_sha1,
    directory_entries,
    visit_id=None,
    timestamp=None,
    snapshot_id=None,
    path=None,
):
    dirs = [e for e in directory_entries if e["type"] in ("dir", "rev")]
    files = [e for e in directory_entries if e["type"] == "file"]

    if not visit_id and not snapshot_id:
        visit_id = origin_visit["visit"]

    query_params = {"origin_url": origin_info["url"]}

    if timestamp:
        query_params["timestamp"] = timestamp
    elif visit_id:
        query_params["visit_id"] = visit_id
    else:
        query_params["snapshot"] = snapshot_id

    if path:
        query_params["path"] = path

    url = reverse("browse-origin-directory", query_params=query_params)

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )
    assert_contains(resp, '<td class="swh-directory">', count=len(dirs))
    assert_contains(resp, '<td class="swh-content">', count=len(files))

    if timestamp:
        query_params["timestamp"] = format_utc_iso_date(
            parse_iso8601_date_to_utc(timestamp).isoformat(), "%Y-%m-%dT%H:%M:%SZ"
        )

    for d in dirs:
        if d["type"] == "rev":
            dir_url = reverse("browse-revision", url_args={"sha1_git": d["target"]})
        else:
            dir_path = d["name"]
            if path:
                dir_path = "%s/%s" % (path, d["name"])
            query_params["path"] = dir_path
            dir_url = reverse(
                "browse-origin-directory",
                query_params=query_params,
            )
        assert_contains(resp, dir_url)

    for f in files:
        file_path = f["name"]
        if path:
            file_path = "%s/%s" % (path, f["name"])
        query_params["path"] = file_path
        file_url = reverse("browse-origin-content", query_params=query_params)
        assert_contains(resp, file_url)

    if "path" in query_params:
        del query_params["path"]

    root_dir_branch_url = reverse("browse-origin-directory", query_params=query_params)

    nb_bc_paths = 1
    if path:
        nb_bc_paths = len(path.split("/")) + 1

    assert_contains(resp, '<li class="swh-path">', count=nb_bc_paths)
    assert_contains(
        resp, '<a href="%s">%s</a>' % (root_dir_branch_url, root_directory_sha1[:7])
    )

    origin_branches_url = reverse("browse-origin-branches", query_params=query_params)

    assert_contains(resp, f'href="{escape(origin_branches_url)}"')
    assert_contains(resp, f"Branches ({snapshot_sizes['revision']})")

    origin_releases_url = reverse("browse-origin-releases", query_params=query_params)

    nb_releases = len(origin_releases)
    if nb_releases > 0:
        assert_contains(resp, f'href="{escape(origin_releases_url)}"')
        assert_contains(resp, f"Releases ({snapshot_sizes['release']})")

    if path:
        query_params["path"] = path

    assert_contains(resp, '<li class="swh-branch">', count=len(origin_branches))

    for branch in origin_branches:
        query_params["branch"] = branch["name"]
        root_dir_branch_url = reverse(
            "browse-origin-directory", query_params=query_params
        )

        assert_contains(resp, '<a href="%s">' % root_dir_branch_url)

    assert_contains(resp, '<li class="swh-release">', count=len(origin_releases))

    query_params["branch"] = None
    for release in origin_releases:
        query_params["release"] = release["name"]
        root_dir_release_url = reverse(
            "browse-origin-directory", query_params=query_params
        )

        assert_contains(resp, 'href="%s"' % root_dir_release_url)

    assert_contains(resp, "vault-cook-directory")
    assert_contains(resp, "vault-cook-revision")

    snapshot = archive_data.snapshot_get(origin_visit["snapshot"])
    head_rev_id = archive_data.snapshot_get_head(snapshot)

    swhid_context = {
        "origin": origin_info["url"],
        "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
        "anchor": gen_swhid(ObjectType.REVISION, head_rev_id),
        "path": f"/{path}" if path else None,
    }

    swh_dir_id = gen_swhid(
        ObjectType.DIRECTORY, directory_entries[0]["dir_id"], metadata=swhid_context
    )
    swh_dir_id_url = reverse("browse-swhid", url_args={"swhid": swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)

    assert_contains(resp, "swh-take-new-snapshot")

    _check_origin_link(resp, origin_info["url"])

    assert_not_contains(resp, "swh-metadata-popover")

    # Finally, check "Extrinsic metadata" dropdown:

    origin_metadata_api_url = reverse(
        "api-1-raw-extrinsic-metadata-origin-authorities",
        url_args={"origin_url": origin_info["url"]},
    )
    directory_metadata_api_url = reverse(
        "api-1-raw-extrinsic-metadata-swhid-authorities",
        url_args={"target": f"swh:1:dir:{target_directory_sha1}"},
    )
    extrinsic_metadata_snippets = [
        "Extrinsic metadata",
        f'<a href="{origin_metadata_api_url}" class="dropdown-item" role="button">',
        f'<a href="{directory_metadata_api_url}" class="dropdown-item" role="button">',
    ]

    client.logout()

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )
    # None of the above should be present for logged-out users
    for snippet in extrinsic_metadata_snippets:
        assert_not_contains(resp, snippet)

    client.force_login(staff_user)

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )

    # But they should for staff users
    for snippet in extrinsic_metadata_snippets:
        assert_contains(resp, snippet)

    client.logout()


def _check_origin_link(resp, origin_url):
    browse_origin_url = reverse(
        "browse-origin", query_params={"origin_url": origin_url}
    )
    assert_contains(resp, f'href="{browse_origin_url}"')


def test_browse_pull_request_branch(
    client, archive_data, origin_with_pull_request_branches
):
    origin_url = origin_with_pull_request_branches.url
    snapshot = archive_data.snapshot_get_latest(origin_url)
    pr_branch = random.choice(
        [
            branch
            for branch in snapshot["branches"].keys()
            if branch.startswith("refs/pull/")
        ]
    )
    url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": origin_url, "branch": pr_branch},
    )
    check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )
