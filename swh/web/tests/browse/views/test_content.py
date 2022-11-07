# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random
import re

import pytest

from django.utils.html import escape

from swh.model.hashutil import hash_to_bytes
from swh.model.model import ObjectType as ModelObjectType
from swh.model.model import Release, Snapshot, SnapshotBranch, TargetType
from swh.model.swhids import ObjectType
from swh.web.browse.snapshot_context import process_snapshot_branches
from swh.web.browse.utils import (
    get_mimetype_and_encoding_for_content,
    prepare_content_for_display,
    re_encode_content,
)
from swh.web.tests.data import get_content
from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.helpers import check_html_get_response, check_http_get_response
from swh.web.utils import (
    format_utc_iso_date,
    gen_path_info,
    parse_iso8601_date_to_utc,
    reverse,
)
from swh.web.utils.exc import NotFoundExc
from swh.web.utils.identifiers import gen_swhid


def test_content_view_text(client, archive_data, content_text):
    sha1_git = content_text["sha1_git"]

    url = reverse(
        "browse-content",
        url_args={"query_string": content_text["sha1"]},
        query_params={"path": content_text["path"]},
    )

    url_raw = reverse(
        "browse-content-raw", url_args={"query_string": content_text["sha1"]}
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-content.html"
    )

    content_display = _process_content_for_display(archive_data, content_text)
    mimetype = content_display["mimetype"]

    if mimetype.startswith("text/"):
        assert_contains(resp, '<code class="%s">' % content_display["language"])
        assert_contains(resp, escape(content_display["content_data"]))
    assert_contains(resp, url_raw)

    swh_cnt_id = gen_swhid(ObjectType.CONTENT, sha1_git)
    swh_cnt_id_url = reverse("browse-swhid", url_args={"swhid": swh_cnt_id})
    assert_contains(resp, swh_cnt_id)
    assert_contains(resp, swh_cnt_id_url)
    assert_not_contains(resp, "swh-metadata-popover")


def test_content_view_no_highlight(
    client, archive_data, content_application_no_highlight, content_text_no_highlight
):
    for content_ in (content_application_no_highlight, content_text_no_highlight):
        content = content_
        sha1_git = content["sha1_git"]

        url = reverse("browse-content", url_args={"query_string": content["sha1"]})

        url_raw = reverse(
            "browse-content-raw", url_args={"query_string": content["sha1"]}
        )

        resp = check_html_get_response(
            client, url, status_code=200, template_used="browse-content.html"
        )

        content_display = _process_content_for_display(archive_data, content)

        if content["encoding"] != "binary":
            assert_contains(resp, '<code class="plaintext">')
            assert_contains(resp, escape(content_display["content_data"]))

        assert_contains(resp, url_raw)

        swh_cnt_id = gen_swhid(ObjectType.CONTENT, sha1_git)
        swh_cnt_id_url = reverse("browse-swhid", url_args={"swhid": swh_cnt_id})

        assert_contains(resp, swh_cnt_id)
        assert_contains(resp, swh_cnt_id_url)


def test_content_view_no_utf8_text(client, archive_data, content_text_non_utf8):
    sha1_git = content_text_non_utf8["sha1_git"]

    url = reverse(
        "browse-content", url_args={"query_string": content_text_non_utf8["sha1"]}
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-content.html"
    )

    content_display = _process_content_for_display(archive_data, content_text_non_utf8)

    swh_cnt_id = gen_swhid(ObjectType.CONTENT, sha1_git)
    swh_cnt_id_url = reverse("browse-swhid", url_args={"swhid": swh_cnt_id})
    assert_contains(resp, swh_cnt_id_url)
    assert_contains(resp, escape(content_display["content_data"]))


def test_content_view_image(client, archive_data, content_image_type):
    url = reverse(
        "browse-content", url_args={"query_string": content_image_type["sha1"]}
    )

    url_raw = reverse(
        "browse-content-raw", url_args={"query_string": content_image_type["sha1"]}
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-content.html"
    )

    content_display = _process_content_for_display(archive_data, content_image_type)
    mimetype = content_display["mimetype"]
    content_data = content_display["content_data"]
    assert_contains(resp, '<img src="data:%s;base64,%s"/>' % (mimetype, content_data))
    assert_contains(resp, url_raw)


def test_content_view_image_no_rendering(
    client, archive_data, content_unsupported_image_type_rendering
):
    url = reverse(
        "browse-content",
        url_args={"query_string": content_unsupported_image_type_rendering["sha1"]},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-content.html"
    )

    mimetype = content_unsupported_image_type_rendering["mimetype"]
    encoding = content_unsupported_image_type_rendering["encoding"]
    assert_contains(
        resp,
        (
            f"Content with mime type {mimetype} and encoding {encoding} "
            "cannot be displayed."
        ),
    )


def test_content_view_text_with_path(client, archive_data, content_text):
    path = content_text["path"]

    url = reverse(
        "browse-content",
        url_args={"query_string": content_text["sha1"]},
        query_params={"path": path},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-content.html"
    )

    assert_contains(resp, '<nav class="bread-crumbs')

    content_display = _process_content_for_display(archive_data, content_text)
    mimetype = content_display["mimetype"]

    if mimetype.startswith("text/"):
        hljs_language = content_text["hljs_language"]
        assert_contains(resp, '<code class="%s">' % hljs_language)
        assert_contains(resp, escape(content_display["content_data"]))

    split_path = path.split("/")

    root_dir_sha1 = split_path[0]
    filename = split_path[-1]
    path = path.replace(root_dir_sha1 + "/", "").replace(filename, "")

    swhid_context = {
        "anchor": gen_swhid(ObjectType.DIRECTORY, root_dir_sha1),
        "path": f"/{path}{filename}",
    }

    swh_cnt_id = gen_swhid(
        ObjectType.CONTENT, content_text["sha1_git"], metadata=swhid_context
    )
    swh_cnt_id_url = reverse("browse-swhid", url_args={"swhid": swh_cnt_id})
    assert_contains(resp, swh_cnt_id)
    assert_contains(resp, swh_cnt_id_url)

    path_info = gen_path_info(path)

    root_dir_url = reverse("browse-directory", url_args={"sha1_git": root_dir_sha1})

    assert_contains(resp, '<li class="swh-path">', count=len(path_info) + 1)

    assert_contains(
        resp, '<a href="' + root_dir_url + '">' + root_dir_sha1[:7] + "</a>"
    )

    for p in path_info:
        dir_url = reverse(
            "browse-directory",
            url_args={"sha1_git": root_dir_sha1},
            query_params={"path": p["path"]},
        )
        assert_contains(resp, '<a href="' + dir_url + '">' + p["name"] + "</a>")

    assert_contains(resp, "<li>" + filename + "</li>")

    url_raw = reverse(
        "browse-content-raw",
        url_args={"query_string": content_text["sha1"]},
        query_params={"filename": filename},
    )
    assert_contains(resp, url_raw)

    url = reverse(
        "browse-content",
        url_args={"query_string": content_text["sha1"]},
        query_params={"path": filename},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-content.html"
    )

    assert_not_contains(resp, '<nav class="bread-crumbs')

    invalid_path = "%s/foo/bar/baz" % root_dir_sha1
    url = reverse(
        "browse-content",
        url_args={"query_string": content_text["sha1"]},
        query_params={"path": invalid_path},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )


def test_content_raw_text(client, archive_data, content_text):
    url = reverse("browse-content-raw", url_args={"query_string": content_text["sha1"]})

    resp = check_http_get_response(
        client, url, status_code=200, content_type="text/plain"
    )

    content_data = archive_data.content_get_data(content_text["sha1"])["data"]

    assert resp["Content-Type"] == "text/plain"
    assert resp["Content-disposition"] == (
        "filename=%s_%s" % ("sha1", content_text["sha1"])
    )
    assert resp.content == content_data

    filename = content_text["path"].split("/")[-1]

    url = reverse(
        "browse-content-raw",
        url_args={"query_string": content_text["sha1"]},
        query_params={"filename": filename},
    )

    resp = check_http_get_response(
        client, url, status_code=200, content_type="text/plain"
    )

    assert resp["Content-Type"] == "text/plain"
    assert resp["Content-disposition"] == "filename=%s" % filename
    assert resp.content == content_data


def test_content_raw_no_utf8_text(client, content_text_non_utf8):
    url = reverse(
        "browse-content-raw", url_args={"query_string": content_text_non_utf8["sha1"]}
    )

    resp = check_http_get_response(
        client, url, status_code=200, content_type="text/plain"
    )
    _, encoding = get_mimetype_and_encoding_for_content(resp.content)
    assert encoding == content_text_non_utf8["encoding"]


def test_content_raw_bin(client, archive_data, content_image_type):
    url = reverse(
        "browse-content-raw", url_args={"query_string": content_image_type["sha1"]}
    )

    resp = check_http_get_response(
        client, url, status_code=200, content_type="application/octet-stream"
    )

    filename = content_image_type["path"].split("/")[-1]
    content_data = archive_data.content_get_data(content_image_type["sha1"])["data"]

    assert resp["Content-Type"] == "application/octet-stream"
    assert resp["Content-disposition"] == "attachment; filename=%s_%s" % (
        "sha1",
        content_image_type["sha1"],
    )
    assert resp.content == content_data

    url = reverse(
        "browse-content-raw",
        url_args={"query_string": content_image_type["sha1"]},
        query_params={"filename": filename},
    )

    resp = check_http_get_response(
        client, url, status_code=200, content_type="application/octet-stream"
    )

    assert resp["Content-Type"] == "application/octet-stream"
    assert resp["Content-disposition"] == "attachment; filename=%s" % filename
    assert resp.content == content_data


@pytest.mark.django_db
@pytest.mark.parametrize("staff_user_logged_in", [False, True])
def test_content_request_errors(
    client, staff_user, invalid_sha1, unknown_content, staff_user_logged_in
):

    if staff_user_logged_in:
        client.force_login(staff_user)

    url = reverse("browse-content", url_args={"query_string": invalid_sha1})
    check_html_get_response(client, url, status_code=400, template_used="error.html")

    url = reverse("browse-content", url_args={"query_string": unknown_content["sha1"]})
    check_html_get_response(
        client, url, status_code=404, template_used="browse-content.html"
    )


def test_content_bytes_missing(client, archive_data, mocker, content):
    mock_archive = mocker.patch("swh.web.browse.utils.archive")
    content_data = archive_data.content_get(content["sha1"])

    mock_archive.lookup_content.return_value = content_data
    mock_archive.lookup_content_filetype.side_effect = Exception()
    mock_archive.lookup_content_raw.side_effect = NotFoundExc(
        "Content bytes not available!"
    )

    url = reverse("browse-content", url_args={"query_string": content["sha1"]})

    check_html_get_response(
        client, url, status_code=404, template_used="browse-content.html"
    )


def test_content_too_large(client, mocker):
    mock_request_content = mocker.patch("swh.web.browse.views.content.request_content")
    stub_content_too_large_data = {
        "checksums": {
            "sha1": "8624bcdae55baeef00cd11d5dfcfa60f68710a02",
            "sha1_git": "94a9ed024d3859793618152ea559a168bbcbb5e2",
            "sha256": (
                "8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b16" "5a1dcd80c7c545eb65b903"
            ),
            "blake2s256": (
                "38702b7168c7785bfe748b51b45d9856070ba90" "f9dc6d90f2ea75d4356411ffe"
            ),
        },
        "length": 30000000,
        "raw_data": None,
        "mimetype": "text/plain",
        "encoding": "us-ascii",
        "language": "not detected",
        "licenses": "GPL",
        "error_code": 200,
        "error_message": "",
        "error_description": "",
    }

    content_sha1 = stub_content_too_large_data["checksums"]["sha1"]

    mock_request_content.return_value = stub_content_too_large_data

    url = reverse("browse-content", url_args={"query_string": content_sha1})

    url_raw = reverse("browse-content-raw", url_args={"query_string": content_sha1})

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-content.html"
    )

    assert_contains(resp, "Content is too large to be displayed")
    assert_contains(resp, url_raw)


def test_content_uppercase(client, content):
    url = reverse(
        "browse-content-uppercase-checksum",
        url_args={"query_string": content["sha1"].upper()},
    )

    resp = check_html_get_response(client, url, status_code=302)

    redirect_url = reverse("browse-content", url_args={"query_string": content["sha1"]})

    assert resp["location"] == redirect_url


def test_content_utf8_detected_as_binary_display(
    client, archive_data, content_utf8_detected_as_binary
):
    url = reverse(
        "browse-content",
        url_args={"query_string": content_utf8_detected_as_binary["sha1"]},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-content.html"
    )

    content_display = _process_content_for_display(
        archive_data, content_utf8_detected_as_binary
    )

    assert_contains(resp, escape(content_display["content_data"]))


def test_content_origin_snapshot_branch_browse(
    client, archive_data, origin_with_multiple_visits
):
    origin_url = origin_with_multiple_visits["url"]
    visits = archive_data.origin_visit_get(origin_url)
    visit = random.choice(visits)
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    snapshot_sizes = archive_data.snapshot_count_branches(visit["snapshot"])
    branches, releases, _ = process_snapshot_branches(snapshot)
    branch_info = random.choice(branches)

    directory = archive_data.revision_get(branch_info["target"])["directory"]
    directory_content = archive_data.directory_ls(directory)
    directory_file = random.choice(
        [e for e in directory_content if e["type"] == "file"]
    )

    url = reverse(
        "browse-content",
        url_args={"query_string": directory_file["checksums"]["sha1"]},
        query_params={
            "origin_url": origin_with_multiple_visits["url"],
            "snapshot": snapshot["id"],
            "branch": branch_info["name"],
            "path": directory_file["name"],
        },
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-content.html"
    )

    _check_origin_snapshot_related_html(
        resp, origin_with_multiple_visits, snapshot, snapshot_sizes, branches, releases
    )
    assert_contains(resp, directory_file["name"])
    assert_contains(resp, f"Branch: <strong>{branch_info['name']}</strong>")

    cnt_swhid = gen_swhid(
        ObjectType.CONTENT,
        directory_file["checksums"]["sha1_git"],
        metadata={
            "origin": origin_url,
            "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
            "anchor": gen_swhid(ObjectType.REVISION, branch_info["target"]),
            "path": f"/{directory_file['name']}",
        },
    )
    assert_contains(resp, cnt_swhid)

    dir_swhid = gen_swhid(
        ObjectType.DIRECTORY,
        directory,
        metadata={
            "origin": origin_url,
            "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
            "anchor": gen_swhid(ObjectType.REVISION, branch_info["target"]),
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


def test_content_origin_snapshot_release_browse(
    client, archive_data, origin_with_multiple_visits
):
    origin_url = origin_with_multiple_visits["url"]
    visits = archive_data.origin_visit_get(origin_url)
    visit = random.choice(visits)
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    snapshot_sizes = archive_data.snapshot_count_branches(visit["snapshot"])
    branches, releases, _ = process_snapshot_branches(snapshot)
    release_info = random.choice(releases)

    directory_content = archive_data.directory_ls(release_info["directory"])
    directory_file = random.choice(
        [e for e in directory_content if e["type"] == "file"]
    )

    url = reverse(
        "browse-content",
        url_args={"query_string": directory_file["checksums"]["sha1"]},
        query_params={
            "origin_url": origin_url,
            "snapshot": snapshot["id"],
            "release": release_info["name"],
            "path": directory_file["name"],
        },
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-content.html"
    )

    _check_origin_snapshot_related_html(
        resp, origin_with_multiple_visits, snapshot, snapshot_sizes, branches, releases
    )
    assert_contains(resp, directory_file["name"])
    assert_contains(resp, f"Release: <strong>{release_info['name']}</strong>")

    cnt_swhid = gen_swhid(
        ObjectType.CONTENT,
        directory_file["checksums"]["sha1_git"],
        metadata={
            "origin": origin_url,
            "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
            "anchor": gen_swhid(ObjectType.RELEASE, release_info["id"]),
            "path": f"/{directory_file['name']}",
        },
    )
    assert_contains(resp, cnt_swhid)

    dir_swhid = gen_swhid(
        ObjectType.DIRECTORY,
        release_info["directory"],
        metadata={
            "origin": origin_url,
            "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
            "anchor": gen_swhid(ObjectType.RELEASE, release_info["id"]),
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


def _process_content_for_display(archive_data, content):
    content_data = archive_data.content_get_data(content["sha1"])

    mime_type, encoding = get_mimetype_and_encoding_for_content(content_data["data"])

    mime_type, encoding, content_data = re_encode_content(
        mime_type, encoding, content_data["data"]
    )

    content_display = prepare_content_for_display(
        content_data, mime_type, content["path"]
    )

    assert type(content_display["content_data"]) == str

    return content_display


def test_content_dispaly_empty_query_string_missing_path(client):
    url = reverse(
        "browse-content",
        query_params={"origin_url": "http://example.com"},
    )
    resp = check_html_get_response(
        client, url, status_code=400, template_used="error.html"
    )
    assert_contains(resp, "The path query parameter must be provided.", status_code=400)


def test_content_dispaly_empty_query_string_and_snapshot_origin(client):
    url = reverse(
        "browse-content",
        query_params={"path": "test.txt"},
    )
    resp = check_html_get_response(
        client,
        url,
        status_code=400,
    )
    assert_contains(
        resp,
        "The origin_url or snapshot query parameters must be provided.",
        status_code=400,
    )


def test_content_dispaly_empty_query_string_with_origin(
    client, archive_data, origin_with_multiple_visits
):
    origin_url = origin_with_multiple_visits["url"]
    snapshot = archive_data.snapshot_get_latest(origin_url)
    head_rev_id = archive_data.snapshot_get_head(snapshot)
    head_rev = archive_data.revision_get(head_rev_id)
    dir_content = archive_data.directory_ls(head_rev["directory"])
    dir_files = [e for e in dir_content if e["type"] == "file"]
    dir_file = random.choice(dir_files)

    url = reverse(
        "browse-content",
        query_params={
            "origin_url": origin_url,
            "path": dir_file["name"],
        },
    )

    resp = check_html_get_response(
        client,
        url,
        status_code=302,
    )
    redict_url = reverse(
        "browse-content",
        url_args={"query_string": f"sha1_git:{dir_file['checksums']['sha1_git']}"},
        query_params={
            "origin_url": origin_url,
            "path": dir_file["name"],
        },
    )
    assert resp.url == redict_url


def test_content_dispaly_empty_query_string_with_snapshot(
    client, archive_data, origin_with_multiple_visits
):
    origin_url = origin_with_multiple_visits["url"]
    snapshot = archive_data.snapshot_get_latest(origin_url)
    head_rev_id = archive_data.snapshot_get_head(snapshot)
    head_rev = archive_data.revision_get(head_rev_id)
    dir_content = archive_data.directory_ls(head_rev["directory"])
    dir_files = [e for e in dir_content if e["type"] == "file"]
    dir_file = random.choice(dir_files)
    url = reverse(
        "browse-content",
        query_params={
            "snapshot": snapshot["id"],
            "path": dir_file["name"],
        },
    )

    resp = check_html_get_response(
        client,
        url,
        status_code=302,
    )
    redict_url = reverse(
        "browse-content",
        url_args={"query_string": f"sha1_git:{dir_file['checksums']['sha1_git']}"},
        query_params={
            "snapshot": snapshot["id"],
            "path": dir_file["name"],
        },
    )
    assert resp.url == redict_url


def test_browse_origin_content_no_visit(client, mocker, origin):
    mock_get_origin_visits = mocker.patch(
        "swh.web.utils.origin_visits.get_origin_visits"
    )
    mock_get_origin_visits.return_value = []
    mock_archive = mocker.patch("swh.web.utils.origin_visits.archive")
    mock_archive.lookup_origin_visit_latest.return_value = None
    url = reverse(
        "browse-content",
        query_params={"origin_url": origin["url"], "path": "foo"},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert_contains(resp, "No valid visit", status_code=404)
    assert not mock_get_origin_visits.called


def test_browse_origin_content_unknown_visit(client, mocker, origin):
    mock_get_origin_visits = mocker.patch(
        "swh.web.utils.origin_visits.get_origin_visits"
    )
    mock_get_origin_visits.return_value = [{"visit": 1}]

    url = reverse(
        "browse-content",
        query_params={"origin_url": origin["url"], "path": "foo", "visit_id": 2},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert re.search("Resource not found", resp.content.decode("utf-8"))


def test_browse_origin_content_not_found(client, origin):
    url = reverse(
        "browse-content",
        query_params={"origin_url": origin["url"], "path": "/invalid/file/path"},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert re.search("Resource not found", resp.content.decode("utf-8"))


def test_browse_content_invalid_origin(client):
    url = reverse(
        "browse-content",
        query_params={
            "origin_url": "http://invalid-origin",
            "path": "/invalid/file/path",
        },
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert re.search("Resource not found", resp.content.decode("utf-8"))


def test_origin_content_view(
    client, archive_data, swh_scheduler, origin_with_multiple_visits
):
    origin_visits = archive_data.origin_visit_get(origin_with_multiple_visits["url"])

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
        origin_with_multiple_visits,
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
        origin_with_multiple_visits,
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
        origin_with_multiple_visits,
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
        origin_with_multiple_visits,
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
        origin_with_multiple_visits,
        origin_visits[0],
        tdata["snapshot_sizes"],
        tdata["branches"],
        tdata["releases"],
        tdata["root_dir_sha1"],
        tdata["content"],
        snapshot_id=tdata["visit"]["snapshot"],
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

    url = reverse(
        "browse-content",
        url_args={"query_string": f"sha1_git:{content['sha1_git']}"},
        query_params=query_params,
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-content.html"
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

    root_dir_url = reverse(
        "browse-directory",
        url_args={"sha1_git": root_dir_sha1},
        query_params=query_params,
    )

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

    url = reverse(
        "browse-content",
        url_args={"query_string": query_string},
        query_params=query_params,
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-content.html"
    )

    snapshot = archive_data.snapshot_get(origin_visit["snapshot"])
    head_rev_id = archive_data.snapshot_get_head(snapshot)

    swhid_context = {
        "origin": origin_info["url"],
        "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
        "anchor": gen_swhid(ObjectType.REVISION, head_rev_id),
        "path": f"/{content_path}",
    }

    swh_cnt_id = gen_swhid(
        ObjectType.CONTENT, content["sha1_git"], metadata=swhid_context
    )
    swh_cnt_id_url = reverse("browse-swhid", url_args={"swhid": swh_cnt_id})
    assert_contains(resp, swh_cnt_id)
    assert_contains(resp, swh_cnt_id_url)

    assert_contains(resp, "swh-take-new-snapshot")

    _check_origin_link(resp, origin_info["url"])

    assert_not_contains(resp, "swh-metadata-popover")


def _check_origin_link(resp, origin_url):
    browse_origin_url = reverse(
        "browse-origin", query_params={"origin_url": origin_url}
    )
    assert_contains(resp, f'href="{browse_origin_url}"')


@pytest.mark.django_db
@pytest.mark.parametrize("staff_user_logged_in", [False, True])
def test_browse_content_snapshot_context_release_directory_target(
    client, staff_user, archive_data, directory_with_files, staff_user_logged_in
):

    if staff_user_logged_in:
        client.force_login(staff_user)

    release_name = "v1.0.0"
    release = Release(
        name=release_name.encode(),
        message=f"release {release_name}".encode(),
        target=hash_to_bytes(directory_with_files),
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

    dir_content = archive_data.directory_ls(directory_with_files)
    file_entry = random.choice(
        [entry for entry in dir_content if entry["type"] == "file"]
    )

    sha1_git = file_entry["checksums"]["sha1_git"]

    browse_url = reverse(
        "browse-content",
        url_args={"query_string": f"sha1_git:{sha1_git}"},
        query_params={
            "path": file_entry["name"],
            "release": release_name,
            "snapshot": snapshot.id.hex(),
        },
    )

    check_html_get_response(
        client, browse_url, status_code=200, template_used="browse-content.html"
    )
