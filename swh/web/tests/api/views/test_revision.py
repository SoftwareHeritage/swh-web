# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given

from swh.web.api.utils import enrich_revision
from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import reverse
from swh.web.tests.data import random_sha1
from swh.web.tests.strategies import revision


@given(revision())
def test_api_revision(api_client, archive_data, revision):
    url = reverse("api-1-revision", url_args={"sha1_git": revision})
    rv = api_client.get(url)

    expected_revision = archive_data.revision_get(revision)

    enrich_revision(expected_revision, rv.wsgi_request)

    assert rv.status_code == 200, rv.data
    assert rv["Content-Type"] == "application/json"
    assert rv.data == expected_revision


def test_api_revision_not_found(api_client):
    unknown_revision_ = random_sha1()

    url = reverse("api-1-revision", url_args={"sha1_git": unknown_revision_})
    rv = api_client.get(url)

    assert rv.status_code == 404, rv.data
    assert rv["Content-Type"] == "application/json"
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "Revision with sha1_git %s not found." % unknown_revision_,
    }


@given(revision())
def test_api_revision_raw_ok(api_client, archive_data, revision):
    url = reverse("api-1-revision-raw-message", url_args={"sha1_git": revision})
    rv = api_client.get(url)

    expected_message = archive_data.revision_get(revision)["message"]

    assert rv.status_code == 200
    assert rv["Content-Type"] == "application/octet-stream"
    assert rv.content == expected_message.encode()


def test_api_revision_raw_ko_no_rev(api_client):
    unknown_revision_ = random_sha1()

    url = reverse(
        "api-1-revision-raw-message", url_args={"sha1_git": unknown_revision_}
    )
    rv = api_client.get(url)

    assert rv.status_code == 404, rv.data
    assert rv["Content-Type"] == "application/json"
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "Revision with sha1_git %s not found." % unknown_revision_,
    }


@given(revision())
def test_api_revision_log(api_client, archive_data, revision):
    limit = 10

    url = reverse(
        "api-1-revision-log",
        url_args={"sha1_git": revision},
        query_params={"limit": limit},
    )

    rv = api_client.get(url)

    expected_log = archive_data.revision_log(revision, limit=limit)
    expected_log = list(
        map(enrich_revision, expected_log, [rv.wsgi_request] * len(expected_log))
    )

    assert rv.status_code == 200, rv.data
    assert rv["Content-Type"] == "application/json"
    assert rv.data == expected_log


def test_api_revision_log_not_found(api_client):
    unknown_revision_ = random_sha1()

    url = reverse("api-1-revision-log", url_args={"sha1_git": unknown_revision_})

    rv = api_client.get(url)

    assert rv.status_code == 404, rv.data
    assert rv["Content-Type"] == "application/json"
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "Revision with sha1_git %s not found." % unknown_revision_,
    }
    assert not rv.has_header("Link")


def test_api_revision_directory_ko_not_found(api_client, mocker):
    mock_rev_dir = mocker.patch("swh.web.api.views.revision._revision_directory_by")
    mock_rev_dir.side_effect = NotFoundExc("Not found")

    rv = api_client.get("/api/1/revision/999/directory/some/path/to/dir/")

    assert rv.status_code == 404, rv.data
    assert rv["Content-Type"] == "application/json"
    assert rv.data == {"exception": "NotFoundExc", "reason": "Not found"}

    mock_rev_dir.assert_called_once_with(
        {"sha1_git": "999"},
        "some/path/to/dir",
        "/api/1/revision/999/directory/some/path/to/dir/",
        with_data=False,
    )


def test_api_revision_directory_ok_returns_dir_entries(api_client, mocker):
    mock_rev_dir = mocker.patch("swh.web.api.views.revision._revision_directory_by")
    stub_dir = {
        "type": "dir",
        "revision": "999",
        "content": [
            {
                "sha1_git": "789",
                "type": "file",
                "target": "101",
                "target_url": "/api/1/content/sha1_git:101/",
                "name": "somefile",
                "file_url": "/api/1/revision/999/directory/some/path/" "somefile/",
            },
            {
                "sha1_git": "123",
                "type": "dir",
                "target": "456",
                "target_url": "/api/1/directory/456/",
                "name": "to-subdir",
                "dir_url": "/api/1/revision/999/directory/some/path/" "to-subdir/",
            },
        ],
    }

    mock_rev_dir.return_value = stub_dir

    rv = api_client.get("/api/1/revision/999/directory/some/path/")

    stub_dir["content"][0]["target_url"] = rv.wsgi_request.build_absolute_uri(
        stub_dir["content"][0]["target_url"]
    )
    stub_dir["content"][0]["file_url"] = rv.wsgi_request.build_absolute_uri(
        stub_dir["content"][0]["file_url"]
    )
    stub_dir["content"][1]["target_url"] = rv.wsgi_request.build_absolute_uri(
        stub_dir["content"][1]["target_url"]
    )
    stub_dir["content"][1]["dir_url"] = rv.wsgi_request.build_absolute_uri(
        stub_dir["content"][1]["dir_url"]
    )

    assert rv.status_code == 200, rv.data
    assert rv["Content-Type"] == "application/json"
    assert rv.data == stub_dir

    mock_rev_dir.assert_called_once_with(
        {"sha1_git": "999"},
        "some/path",
        "/api/1/revision/999/directory/some/path/",
        with_data=False,
    )


def test_api_revision_directory_ok_returns_content(api_client, mocker):
    mock_rev_dir = mocker.patch("swh.web.api.views.revision._revision_directory_by")
    stub_content = {
        "type": "file",
        "revision": "999",
        "content": {
            "sha1_git": "789",
            "sha1": "101",
            "data_url": "/api/1/content/101/raw/",
        },
    }

    mock_rev_dir.return_value = stub_content

    url = "/api/1/revision/666/directory/some/other/path/"
    rv = api_client.get(url)

    stub_content["content"]["data_url"] = rv.wsgi_request.build_absolute_uri(
        stub_content["content"]["data_url"]
    )

    assert rv.status_code == 200, rv.data
    assert rv["Content-Type"] == "application/json"
    assert rv.data == stub_content

    mock_rev_dir.assert_called_once_with(
        {"sha1_git": "666"}, "some/other/path", url, with_data=False
    )


@given(revision())
def test_api_revision_uppercase(api_client, revision):
    url = reverse(
        "api-1-revision-uppercase-checksum", url_args={"sha1_git": revision.upper()}
    )

    resp = api_client.get(url)
    assert resp.status_code == 302

    redirect_url = reverse("api-1-revision", url_args={"sha1_git": revision})

    assert resp["location"] == redirect_url
