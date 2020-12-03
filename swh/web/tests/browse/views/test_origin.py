# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random
import re
import string

from hypothesis import given

from django.utils.html import escape

from swh.model.hashutil import hash_to_bytes
from swh.model.identifiers import CONTENT, DIRECTORY, RELEASE, REVISION, SNAPSHOT
from swh.model.model import (
    OriginVisit,
    OriginVisitStatus,
    Snapshot,
    SnapshotBranch,
    TargetType,
)
from swh.storage.utils import now
from swh.web.browse.snapshot_context import process_snapshot_branches
from swh.web.common.exc import NotFoundExc
from swh.web.common.identifiers import gen_swhid
from swh.web.common.utils import (
    format_utc_iso_date,
    gen_path_info,
    parse_iso8601_date_to_utc,
    reverse,
)
from swh.web.tests.data import get_content, random_sha1
from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.strategies import (
    new_origin,
    new_snapshot,
    origin,
    origin_with_multiple_visits,
    origin_with_releases,
)
from swh.web.tests.strategies import release as existing_release
from swh.web.tests.strategies import revisions, unknown_revision, visit_dates
from swh.web.tests.utils import check_html_get_response


@given(origin_with_multiple_visits())
def test_origin_visits_browse(client, archive_data, origin):
    url = reverse("browse-origin-visits", query_params={"origin_url": origin["url"]})

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse/origin-visits.html"
    )

    visits = archive_data.origin_visit_get(origin["url"])

    for v in visits:
        vdate = format_utc_iso_date(v["date"], "%Y-%m-%dT%H:%M:%SZ")
        browse_dir_url = reverse(
            "browse-origin-directory",
            query_params={"origin_url": origin["url"], "timestamp": vdate},
        )
        assert_contains(resp, browse_dir_url)

    _check_origin_link(resp, origin["url"])


@given(origin_with_multiple_visits())
def test_origin_content_view(client, archive_data, origin):
    origin_visits = archive_data.origin_visit_get(origin["url"])

    def _get_archive_data(visit_idx):
        snapshot = archive_data.snapshot_get(origin_visits[visit_idx]["snapshot"])
        head_rev_id = archive_data.snapshot_get_head(snapshot)
        head_rev = archive_data.revision_get(head_rev_id)
        dir_content = archive_data.directory_ls(head_rev["directory"])
        dir_files = [e for e in dir_content if e["type"] == "file"]
        dir_file = random.choice(dir_files)
        branches, releases, _ = process_snapshot_branches(snapshot)
        return {
            "branches": branches,
            "releases": releases,
            "root_dir_sha1": head_rev["directory"],
            "content": get_content(dir_file["checksums"]["sha1"]),
            "visit": origin_visits[visit_idx],
            "snapshot_sizes": archive_data.snapshot_count_branches(snapshot["id"]),
        }

    tdata = _get_archive_data(-1)

    _origin_content_view_test_helper(
        client,
        archive_data,
        origin,
        origin_visits[-1],
        tdata["snapshot_sizes"],
        tdata["branches"],
        tdata["releases"],
        tdata["root_dir_sha1"],
        tdata["content"],
    )

    _origin_content_view_test_helper(
        client,
        archive_data,
        origin,
        origin_visits[-1],
        tdata["snapshot_sizes"],
        tdata["branches"],
        tdata["releases"],
        tdata["root_dir_sha1"],
        tdata["content"],
        timestamp=tdata["visit"]["date"],
    )

    _origin_content_view_test_helper(
        client,
        archive_data,
        origin,
        origin_visits[-1],
        tdata["snapshot_sizes"],
        tdata["branches"],
        tdata["releases"],
        tdata["root_dir_sha1"],
        tdata["content"],
        snapshot_id=tdata["visit"]["snapshot"],
    )

    tdata = _get_archive_data(0)

    _origin_content_view_test_helper(
        client,
        archive_data,
        origin,
        origin_visits[0],
        tdata["snapshot_sizes"],
        tdata["branches"],
        tdata["releases"],
        tdata["root_dir_sha1"],
        tdata["content"],
        visit_id=tdata["visit"]["visit"],
    )

    _origin_content_view_test_helper(
        client,
        archive_data,
        origin,
        origin_visits[0],
        tdata["snapshot_sizes"],
        tdata["branches"],
        tdata["releases"],
        tdata["root_dir_sha1"],
        tdata["content"],
        snapshot_id=tdata["visit"]["snapshot"],
    )


@given(origin())
def test_origin_root_directory_view(client, archive_data, origin):
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
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        dir_content,
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        dir_content,
        visit_id=visit["visit"],
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        dir_content,
        timestamp=visit["date"],
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        dir_content,
        snapshot_id=visit["snapshot"],
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        dir_content,
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        dir_content,
        visit_id=visit["visit"],
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        dir_content,
        timestamp=visit["date"],
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        dir_content,
        snapshot_id=visit["snapshot"],
    )


@given(origin())
def test_origin_sub_directory_view(client, archive_data, origin):
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
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir_content,
        path=subdir_path,
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir_content,
        path=subdir_path,
        visit_id=visit["visit"],
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir_content,
        path=subdir_path,
        timestamp=visit["date"],
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir_content,
        path=subdir_path,
        snapshot_id=visit["snapshot"],
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir_content,
        path=subdir_path,
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir_content,
        path=subdir_path,
        visit_id=visit["visit"],
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir_content,
        path=subdir_path,
        timestamp=visit["date"],
    )

    _origin_directory_view_test_helper(
        client,
        archive_data,
        origin,
        visit,
        snapshot_sizes,
        branches,
        releases,
        root_dir_sha1,
        subdir_content,
        path=subdir_path,
        snapshot_id=visit["snapshot"],
    )


@given(origin())
def test_origin_branches(client, archive_data, origin):
    origin_visits = archive_data.origin_visit_get(origin["url"])

    visit = origin_visits[-1]
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    snapshot_sizes = archive_data.snapshot_count_branches(snapshot["id"])
    snapshot_content = process_snapshot_branches(snapshot)

    _origin_branches_test_helper(client, origin, snapshot_content, snapshot_sizes)

    _origin_branches_test_helper(
        client, origin, snapshot_content, snapshot_sizes, snapshot_id=visit["snapshot"]
    )


@given(origin())
def test_origin_releases(client, archive_data, origin):
    origin_visits = archive_data.origin_visit_get(origin["url"])

    visit = origin_visits[-1]
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    snapshot_sizes = archive_data.snapshot_count_branches(snapshot["id"])
    snapshot_content = process_snapshot_branches(snapshot)

    _origin_releases_test_helper(client, origin, snapshot_content, snapshot_sizes)

    _origin_releases_test_helper(
        client, origin, snapshot_content, snapshot_sizes, snapshot_id=visit["snapshot"]
    )


@given(
    new_origin(),
    new_snapshot(min_size=4, max_size=4),
    visit_dates(),
    revisions(min_size=3, max_size=3),
)
def test_origin_snapshot_null_branch(
    client, archive_data, new_origin, new_snapshot, visit_dates, revisions
):
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
        [OriginVisit(origin=new_origin.url, date=visit_dates[0], type="git",)]
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
        client, url, status_code=200, template_used="browse/directory.html"
    )


@given(
    new_origin(),
    new_snapshot(min_size=4, max_size=4),
    visit_dates(),
    revisions(min_size=4, max_size=4),
)
def test_origin_snapshot_invalid_branch(
    client, archive_data, new_origin, new_snapshot, visit_dates, revisions
):
    snp_dict = new_snapshot.to_dict()
    archive_data.origin_add([new_origin])
    for i, branch in enumerate(snp_dict["branches"].keys()):
        snp_dict["branches"][branch] = {
            "target_type": "revision",
            "target": hash_to_bytes(revisions[i]),
        }

    archive_data.snapshot_add([Snapshot.from_dict(snp_dict)])
    visit = archive_data.origin_visit_add(
        [OriginVisit(origin=new_origin.url, date=visit_dates[0], type="git",)]
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


@given(origin())
def test_browse_origin_directory_no_visit(client, mocker, origin):
    mock_get_origin_visits = mocker.patch(
        "swh.web.common.origin_visits.get_origin_visits"
    )
    mock_get_origin_visits.return_value = []
    mock_archive = mocker.patch("swh.web.common.origin_visits.archive")
    mock_archive.lookup_origin_visit_latest.return_value = None
    url = reverse("browse-origin-directory", query_params={"origin_url": origin["url"]})

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert_contains(resp, "No valid visit", status_code=404)
    assert not mock_get_origin_visits.called


@given(origin())
def test_browse_origin_directory_unknown_visit(client, mocker, origin):
    mock_get_origin_visits = mocker.patch(
        "swh.web.common.origin_visits.get_origin_visits"
    )
    mock_get_origin_visits.return_value = [{"visit": 1}]

    url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": origin["url"], "visit_id": 2},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert re.search("Visit.*not found", resp.content.decode("utf-8"))
    assert mock_get_origin_visits.called


@given(origin())
def test_browse_origin_directory_not_found(client, origin):
    url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": origin["url"], "path": "/invalid/dir/path/"},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="browse/directory.html"
    )
    assert re.search("Directory.*not found", resp.content.decode("utf-8"))


@given(origin())
def test_browse_origin_content_no_visit(client, mocker, origin):
    mock_get_origin_visits = mocker.patch(
        "swh.web.common.origin_visits.get_origin_visits"
    )
    mock_get_origin_visits.return_value = []
    mock_archive = mocker.patch("swh.web.common.origin_visits.archive")
    mock_archive.lookup_origin_visit_latest.return_value = None
    url = reverse(
        "browse-origin-content",
        query_params={"origin_url": origin["url"], "path": "foo"},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert_contains(resp, "No valid visit", status_code=404)
    assert not mock_get_origin_visits.called


@given(origin())
def test_browse_origin_content_unknown_visit(client, mocker, origin):
    mock_get_origin_visits = mocker.patch(
        "swh.web.common.origin_visits.get_origin_visits"
    )
    mock_get_origin_visits.return_value = [{"visit": 1}]

    url = reverse(
        "browse-origin-content",
        query_params={"origin_url": origin["url"], "path": "foo", "visit_id": 2},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert re.search("Visit.*not found", resp.content.decode("utf-8"))
    assert mock_get_origin_visits.called


@given(origin())
def test_browse_origin_content_directory_empty_snapshot(client, mocker, origin):
    mock_snapshot_archive = mocker.patch("swh.web.browse.snapshot_context.archive")
    mock_get_origin_visit_snapshot = mocker.patch(
        "swh.web.browse.snapshot_context.get_origin_visit_snapshot"
    )
    mock_get_origin_visit_snapshot.return_value = ([], [], {})
    mock_snapshot_archive.lookup_origin.return_value = origin
    mock_snapshot_archive.lookup_snapshot_sizes.return_value = {
        "alias": 0,
        "revision": 0,
        "release": 0,
    }

    for browse_context in ("content", "directory"):
        url = reverse(
            f"browse-origin-{browse_context}",
            query_params={"origin_url": origin["url"], "path": "baz"},
        )

        resp = check_html_get_response(
            client, url, status_code=200, template_used=f"browse/{browse_context}.html"
        )
        assert re.search("snapshot.*is empty", resp.content.decode("utf-8"))
        assert mock_get_origin_visit_snapshot.called
        assert mock_snapshot_archive.lookup_origin.called
        assert mock_snapshot_archive.lookup_snapshot_sizes.called


@given(origin())
def test_browse_origin_content_not_found(client, origin):
    url = reverse(
        "browse-origin-content",
        query_params={"origin_url": origin["url"], "path": "/invalid/file/path"},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="browse/content.html"
    )
    assert re.search("Directory entry.*not found", resp.content.decode("utf-8"))


@given(origin())
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


@given(origin())
def test_origin_empty_snapshot(client, mocker, origin):
    mock_archive = mocker.patch("swh.web.browse.snapshot_context.archive")
    mock_get_origin_visit_snapshot = mocker.patch(
        "swh.web.browse.snapshot_context.get_origin_visit_snapshot"
    )
    mock_get_origin_visit_snapshot.return_value = ([], [], {})
    mock_archive.lookup_snapshot_sizes.return_value = {
        "alias": 0,
        "revision": 0,
        "release": 0,
    }
    mock_archive.lookup_origin.return_value = origin
    url = reverse("browse-origin-directory", query_params={"origin_url": origin["url"]})

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse/directory.html"
    )
    resp_content = resp.content.decode("utf-8")
    assert re.search("snapshot.*is empty", resp_content)
    assert not re.search("swh-tr-link", resp_content)
    assert mock_get_origin_visit_snapshot.called
    assert mock_archive.lookup_snapshot_sizes.called


@given(new_origin())
def test_origin_empty_snapshot_null_revision(client, archive_data, new_origin):
    snapshot = Snapshot(
        branches={
            b"HEAD": SnapshotBranch(
                target="refs/head/master".encode(), target_type=TargetType.ALIAS,
            ),
            b"refs/head/master": None,
        }
    )
    archive_data.origin_add([new_origin])
    archive_data.snapshot_add([snapshot])
    visit = archive_data.origin_visit_add(
        [OriginVisit(origin=new_origin.url, date=now(), type="git",)]
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
        "browse-origin-directory", query_params={"origin_url": new_origin.url},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse/directory.html"
    )
    resp_content = resp.content.decode("utf-8")
    assert re.search("snapshot.*is empty", resp_content)
    assert not re.search("swh-tr-link", resp_content)


@given(origin_with_releases())
def test_origin_release_browse(client, archive_data, origin):
    snapshot = archive_data.snapshot_get_latest(origin["url"])
    release = [
        b for b in snapshot["branches"].values() if b["target_type"] == "release"
    ][-1]
    release_data = archive_data.release_get(release["target"])
    revision_data = archive_data.revision_get(release_data["target"])
    url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": origin["url"], "release": release_data["name"]},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse/directory.html"
    )
    assert_contains(resp, release_data["name"])
    assert_contains(resp, release["target"])

    swhid_context = {
        "origin": origin["url"],
        "visit": gen_swhid(SNAPSHOT, snapshot["id"]),
        "anchor": gen_swhid(RELEASE, release_data["id"]),
    }

    swh_dir_id = gen_swhid(
        DIRECTORY, revision_data["directory"], metadata=swhid_context
    )
    swh_dir_id_url = reverse("browse-swhid", url_args={"swhid": swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)


@given(origin_with_releases())
def test_origin_release_browse_not_found(client, origin):

    invalid_release_name = "swh-foo-bar"
    url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": origin["url"], "release": invalid_release_name},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert re.search(
        f"Release {invalid_release_name}.*not found", resp.content.decode("utf-8")
    )


@given(new_origin(), unknown_revision())
def test_origin_browse_directory_branch_with_non_resolvable_revision(
    client, archive_data, new_origin, unknown_revision
):
    branch_name = "master"
    snapshot = Snapshot(
        branches={
            branch_name.encode(): SnapshotBranch(
                target=hash_to_bytes(unknown_revision), target_type=TargetType.REVISION,
            )
        }
    )
    archive_data.origin_add([new_origin])
    archive_data.snapshot_add([snapshot])
    visit = archive_data.origin_visit_add(
        [OriginVisit(origin=new_origin.url, date=now(), type="git",)]
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
        client, url, status_code=200, template_used="browse/directory.html"
    )
    assert_contains(
        resp, f"Revision {unknown_revision } could not be found in the archive."
    )


@given(origin())
def test_origin_content_no_path(client, origin):
    url = reverse("browse-origin-content", query_params={"origin_url": origin["url"]})

    resp = check_html_get_response(
        client, url, status_code=400, template_used="error.html"
    )
    assert_contains(
        resp, "The path of a content must be given as query parameter.", status_code=400
    )


def test_origin_views_no_url_query_parameter(client):
    for browse_context in (
        "content",
        "directory",
        "log",
        "branches",
        "releases",
        "visits",
    ):
        url = reverse(f"browse-origin-{browse_context}")

        resp = check_html_get_response(
            client, url, status_code=400, template_used="error.html"
        )
        assert_contains(
            resp, "An origin URL must be provided as query parameter.", status_code=400
        )


def _origin_content_view_test_helper(
    client,
    archive_data,
    origin_info,
    origin_visit,
    snapshot_sizes,
    origin_branches,
    origin_releases,
    root_dir_sha1,
    content,
    visit_id=None,
    timestamp=None,
    snapshot_id=None,
):
    content_path = "/".join(content["path"].split("/")[1:])

    if not visit_id and not snapshot_id:
        visit_id = origin_visit["visit"]

    query_params = {"origin_url": origin_info["url"], "path": content_path}

    if timestamp:
        query_params["timestamp"] = timestamp

    if visit_id:
        query_params["visit_id"] = visit_id
    elif snapshot_id:
        query_params["snapshot"] = snapshot_id

    url = reverse("browse-origin-content", query_params=query_params)

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse/content.html"
    )

    assert type(content["data"]) == str

    assert_contains(resp, '<code class="%s">' % content["hljs_language"])
    assert_contains(resp, escape(content["data"]))

    split_path = content_path.split("/")

    filename = split_path[-1]
    path = content_path.replace(filename, "")[:-1]

    path_info = gen_path_info(path)

    del query_params["path"]

    if timestamp:
        query_params["timestamp"] = format_utc_iso_date(
            parse_iso8601_date_to_utc(timestamp).isoformat(), "%Y-%m-%dT%H:%M:%SZ"
        )

    root_dir_url = reverse("browse-origin-directory", query_params=query_params)

    assert_contains(resp, '<li class="swh-path">', count=len(path_info) + 1)

    assert_contains(resp, '<a href="%s">%s</a>' % (root_dir_url, root_dir_sha1[:7]))

    for p in path_info:
        query_params["path"] = p["path"]
        dir_url = reverse("browse-origin-directory", query_params=query_params)
        assert_contains(resp, '<a href="%s">%s</a>' % (dir_url, p["name"]))

    assert_contains(resp, "<li>%s</li>" % filename)

    query_string = "sha1_git:" + content["sha1_git"]

    url_raw = reverse(
        "browse-content-raw",
        url_args={"query_string": query_string},
        query_params={"filename": filename},
    )
    assert_contains(resp, url_raw)

    if "path" in query_params:
        del query_params["path"]

    origin_branches_url = reverse("browse-origin-branches", query_params=query_params)

    assert_contains(resp, f'href="{escape(origin_branches_url)}"')
    assert_contains(resp, f"Branches ({snapshot_sizes['revision']})")

    origin_releases_url = reverse("browse-origin-releases", query_params=query_params)

    assert_contains(resp, f'href="{escape(origin_releases_url)}">')
    assert_contains(resp, f"Releases ({snapshot_sizes['release']})")

    assert_contains(resp, '<li class="swh-branch">', count=len(origin_branches))

    query_params["path"] = content_path

    for branch in origin_branches:
        root_dir_branch_url = reverse(
            "browse-origin-content",
            query_params={"branch": branch["name"], **query_params},
        )

        assert_contains(resp, '<a href="%s">' % root_dir_branch_url)

    assert_contains(resp, '<li class="swh-release">', count=len(origin_releases))

    query_params["branch"] = None
    for release in origin_releases:
        root_dir_release_url = reverse(
            "browse-origin-content",
            query_params={"release": release["name"], **query_params},
        )

        assert_contains(resp, '<a href="%s">' % root_dir_release_url)

    url = reverse("browse-origin-content", query_params=query_params)

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse/content.html"
    )

    snapshot = archive_data.snapshot_get(origin_visit["snapshot"])
    head_rev_id = archive_data.snapshot_get_head(snapshot)

    swhid_context = {
        "origin": origin_info["url"],
        "visit": gen_swhid(SNAPSHOT, snapshot["id"]),
        "anchor": gen_swhid(REVISION, head_rev_id),
        "path": f"/{content_path}",
    }

    swh_cnt_id = gen_swhid(CONTENT, content["sha1_git"], metadata=swhid_context)
    swh_cnt_id_url = reverse("browse-swhid", url_args={"swhid": swh_cnt_id})
    assert_contains(resp, swh_cnt_id)
    assert_contains(resp, swh_cnt_id_url)

    assert_contains(resp, "swh-take-new-snapshot")

    _check_origin_link(resp, origin_info["url"])

    assert_not_contains(resp, "swh-metadata-popover")


def _origin_directory_view_test_helper(
    client,
    archive_data,
    origin_info,
    origin_visit,
    snapshot_sizes,
    origin_branches,
    origin_releases,
    root_directory_sha1,
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
        client, url, status_code=200, template_used="browse/directory.html"
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
            dir_url = reverse("browse-origin-directory", query_params=query_params,)
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
        "visit": gen_swhid(SNAPSHOT, snapshot["id"]),
        "anchor": gen_swhid(REVISION, head_rev_id),
        "path": f"/{path}" if path else None,
    }

    swh_dir_id = gen_swhid(
        DIRECTORY, directory_entries[0]["dir_id"], metadata=swhid_context
    )
    swh_dir_id_url = reverse("browse-swhid", url_args={"swhid": swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)

    assert_contains(resp, "swh-take-new-snapshot")

    _check_origin_link(resp, origin_info["url"])

    assert_not_contains(resp, "swh-metadata-popover")


def _origin_branches_test_helper(
    client, origin_info, origin_snapshot, snapshot_sizes, snapshot_id=None
):
    query_params = {"origin_url": origin_info["url"], "snapshot": snapshot_id}

    url = reverse("browse-origin-branches", query_params=query_params)

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse/branches.html"
    )

    origin_branches = origin_snapshot[0]
    origin_releases = origin_snapshot[1]

    origin_branches_url = reverse("browse-origin-branches", query_params=query_params)

    assert_contains(resp, f'href="{escape(origin_branches_url)}"')
    assert_contains(resp, f"Branches ({snapshot_sizes['revision']})")

    origin_releases_url = reverse("browse-origin-releases", query_params=query_params)

    nb_releases = len(origin_releases)
    if nb_releases > 0:
        assert_contains(resp, f'href="{escape(origin_releases_url)}">')
        assert_contains(resp, f"Releases ({snapshot_sizes['release']})")

    assert_contains(resp, '<tr class="swh-branch-entry', count=len(origin_branches))

    for branch in origin_branches:
        browse_branch_url = reverse(
            "browse-origin-directory",
            query_params={"branch": branch["name"], **query_params},
        )
        assert_contains(resp, '<a href="%s">' % escape(browse_branch_url))

        browse_revision_url = reverse(
            "browse-revision",
            url_args={"sha1_git": branch["revision"]},
            query_params=query_params,
        )
        assert_contains(resp, '<a href="%s">' % escape(browse_revision_url))

    _check_origin_link(resp, origin_info["url"])


def _origin_releases_test_helper(
    client, origin_info, origin_snapshot, snapshot_sizes, snapshot_id=None
):
    query_params = {"origin_url": origin_info["url"], "snapshot": snapshot_id}

    url = reverse("browse-origin-releases", query_params=query_params)

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse/releases.html"
    )

    origin_releases = origin_snapshot[1]

    origin_branches_url = reverse("browse-origin-branches", query_params=query_params)

    assert_contains(resp, f'href="{escape(origin_branches_url)}"')
    assert_contains(resp, f"Branches ({snapshot_sizes['revision']})")

    origin_releases_url = reverse("browse-origin-releases", query_params=query_params)

    nb_releases = len(origin_releases)
    if nb_releases > 0:
        assert_contains(resp, f'href="{escape(origin_releases_url)}"')
        assert_contains(resp, f"Releases ({snapshot_sizes['release']}")

    assert_contains(resp, '<tr class="swh-release-entry', count=nb_releases)

    for release in origin_releases:
        browse_release_url = reverse(
            "browse-release",
            url_args={"sha1_git": release["id"]},
            query_params=query_params,
        )
        browse_revision_url = reverse(
            "browse-revision",
            url_args={"sha1_git": release["target"]},
            query_params=query_params,
        )

        assert_contains(resp, '<a href="%s">' % escape(browse_release_url))
        assert_contains(resp, '<a href="%s">' % escape(browse_revision_url))

    _check_origin_link(resp, origin_info["url"])


@given(
    new_origin(), visit_dates(), revisions(min_size=10, max_size=10), existing_release()
)
def test_origin_branches_pagination_with_alias(
    client, archive_data, mocker, new_origin, visit_dates, revisions, existing_release
):
    """
    When a snapshot contains a branch or a release alias, pagination links
    in the branches / releases view should be displayed.
    """
    mocker.patch("swh.web.browse.snapshot_context.PER_PAGE", len(revisions) / 2)
    snp_dict = {"branches": {}, "id": hash_to_bytes(random_sha1())}
    for i in range(len(revisions)):
        branch = "".join(random.choices(string.ascii_lowercase, k=8))
        snp_dict["branches"][branch.encode()] = {
            "target_type": "revision",
            "target": hash_to_bytes(revisions[i]),
        }
    release = "".join(random.choices(string.ascii_lowercase, k=8))
    snp_dict["branches"][b"RELEASE_ALIAS"] = {
        "target_type": "alias",
        "target": release.encode(),
    }
    snp_dict["branches"][release.encode()] = {
        "target_type": "release",
        "target": hash_to_bytes(existing_release),
    }
    archive_data.origin_add([new_origin])
    archive_data.snapshot_add([Snapshot.from_dict(snp_dict)])
    visit = archive_data.origin_visit_add(
        [OriginVisit(origin=new_origin.url, date=visit_dates[0], type="git",)]
    )[0]
    visit_status = OriginVisitStatus(
        origin=new_origin.url,
        visit=visit.visit,
        date=now(),
        status="full",
        snapshot=snp_dict["id"],
    )
    archive_data.origin_visit_status_add([visit_status])

    url = reverse("browse-origin-branches", query_params={"origin_url": new_origin.url})

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse/branches.html"
    )
    assert_contains(resp, '<ul class="pagination')


def _check_origin_link(resp, origin_url):
    browse_origin_url = reverse(
        "browse-origin", query_params={"origin_url": origin_url}
    )
    assert_contains(resp, f'href="{browse_origin_url}"')
