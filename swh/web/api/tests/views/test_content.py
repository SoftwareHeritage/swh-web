# Copyright (C) 2015-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.tests.data import random_content
from swh.web.tests.helpers import (
    check_api_get_responses,
    check_api_post_responses,
    check_http_get_response,
    fossology_missing,
)
from swh.web.utils import reverse


def test_api_content_filetype(api_client, indexer_data, content):
    indexer_data.content_add_mimetype(content["sha1"])
    url = reverse(
        "api-1-content-filetype", url_args={"q": "sha1_git:%s" % content["sha1_git"]}
    )
    rv = check_api_get_responses(api_client, url, status_code=200)

    content_url = reverse(
        "api-1-content",
        url_args={"q": "sha1:%s" % content["sha1"]},
        request=rv.wsgi_request,
    )
    expected_data = indexer_data.content_get_mimetype(content["sha1"])
    expected_data["content_url"] = content_url
    assert rv.data == expected_data


def test_api_content_filetype_sha_not_found(api_client):
    unknown_content_ = random_content()

    url = reverse(
        "api-1-content-filetype", url_args={"q": "sha1:%s" % unknown_content_["sha1"]}
    )
    rv = check_api_get_responses(api_client, url, status_code=404)

    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "No filetype information found for content "
        "sha1:%s." % unknown_content_["sha1"],
    }


def test_api_content_language_sha_not_found(api_client):
    unknown_content_ = random_content()

    url = reverse(
        "api-1-content-language", url_args={"q": "sha1:%s" % unknown_content_["sha1"]}
    )
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "No language information found for content "
        "sha1:%s." % unknown_content_["sha1"],
    }


@pytest.mark.skipif(fossology_missing, reason="requires fossology-nomossa installed")
def test_api_content_license(api_client, indexer_data, content):
    indexer_data.content_add_license(content["sha1"])
    url = reverse(
        "api-1-content-license", url_args={"q": "sha1_git:%s" % content["sha1_git"]}
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    content_url = reverse(
        "api-1-content",
        url_args={"q": "sha1:%s" % content["sha1"]},
        request=rv.wsgi_request,
    )
    expected_data = list(indexer_data.content_get_license(content["sha1"]))
    for license in expected_data:
        del license["id"]
    assert rv.data == {
        "content_url": content_url,
        "id": content["sha1"],
        "facts": expected_data,
    }


def test_api_content_license_sha_not_found(api_client):
    unknown_content_ = random_content()

    url = reverse(
        "api-1-content-license", url_args={"q": "sha1:%s" % unknown_content_["sha1"]}
    )
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "No license information found for content "
        "sha1:%s." % unknown_content_["sha1"],
    }


def test_api_content_metadata(api_client, archive_data, content):
    url = reverse("api-1-content", {"q": "sha1:%s" % content["sha1"]})
    rv = check_api_get_responses(api_client, url, status_code=200)
    expected_data = archive_data.content_get(content["sha1"])
    for key, view_name in (
        ("data_url", "api-1-content-raw"),
        ("license_url", "api-1-content-license"),
        ("language_url", "api-1-content-language"),
        ("filetype_url", "api-1-content-filetype"),
    ):
        expected_data[key] = reverse(
            view_name,
            url_args={"q": "sha1:%s" % content["sha1"]},
            request=rv.wsgi_request,
        )
    assert rv.data == expected_data


def test_api_content_not_found(api_client):
    unknown_content_ = random_content()

    url = reverse("api-1-content", url_args={"q": "sha1:%s" % unknown_content_["sha1"]})
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "Content with sha1 checksum equals to %s not found!"
        % unknown_content_["sha1"],
    }


def test_api_content_raw_ko_not_found(api_client):
    unknown_content_ = random_content()

    url = reverse(
        "api-1-content-raw", url_args={"q": "sha1:%s" % unknown_content_["sha1"]}
    )
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "Content with sha1 checksum equals to %s not found!"
        % unknown_content_["sha1"],
    }


def test_api_content_raw_text(api_client, archive_data, content):
    url = reverse("api-1-content-raw", url_args={"q": "sha1:%s" % content["sha1"]})

    rv = check_http_get_response(api_client, url, status_code=200)
    assert rv["Content-Type"] == "application/octet-stream"
    assert (
        rv["Content-disposition"]
        == 'attachment; filename="content_sha1_%s_raw"' % content["sha1"]
    )
    expected_data = archive_data.content_get_data(content["sha1"])
    assert b"".join(rv.streaming_content) == expected_data["data"]
    assert int(rv["Content-Length"]) == len(expected_data["data"])


def test_api_content_raw_text_with_filename(api_client, archive_data, content):
    url = reverse(
        "api-1-content-raw",
        url_args={"q": "sha1:%s" % content["sha1"]},
        query_params={"filename": "filename.txt"},
    )
    rv = check_http_get_response(api_client, url, status_code=200)
    assert rv["Content-disposition"] == 'attachment; filename="filename.txt"'
    assert rv["Content-Type"] == "application/octet-stream"
    expected_data = archive_data.content_get_data(content["sha1"])
    assert b"".join(rv.streaming_content) == expected_data["data"]
    assert int(rv["Content-Length"]) == len(expected_data["data"])


@pytest.mark.parametrize(
    "encoded,expected",
    [
        # From https://datatracker.ietf.org/doc/html/rfc5987#section-3.2.2
        (
            "%c2%a3%20and%20%e2%82%ac%20rates.txt",
            "%C2%A3%20and%20%E2%82%AC%20rates.txt",
        ),
        ("%A3%20rates.txt", "%EF%BF%BD%20rates.txt"),
        # found in the wild
        (
            "Th%C3%A9orie%20de%20sant%C3%A9-aide-justice.pdf",
            "Th%C3%A9orie%20de%20sant%C3%A9-aide-justice.pdf",
        ),
    ],
)
def test_api_content_raw_text_with_nonascii_filename(
    api_client, archive_data, content, encoded, expected
):
    url = reverse(
        "api-1-content-raw",
        url_args={"q": "sha1:%s" % content["sha1"]},
    )
    rv = check_http_get_response(
        api_client, f"{url}?filename={encoded}", status_code=200
    )

    # technically, ISO8859-1 is allowed too
    assert rv["Content-disposition"].isascii(), rv["Content-disposition"]

    assert rv["Content-disposition"] == (
        f"attachment; filename*=utf-8''{expected}"
    ), rv["Content-disposition"]

    assert rv["Content-Type"] == "application/octet-stream"
    expected_data = archive_data.content_get_data(content["sha1"])
    assert b"".join(rv.streaming_content) == expected_data["data"]
    assert int(rv["Content-Length"]) == len(expected_data["data"])


def test_api_check_content_known(api_client, content):
    url = reverse("api-1-content-known", url_args={"q": content["sha1"]})
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert rv.data == {
        "search_res": [{"found": True, "sha1": content["sha1"]}],
        "search_stats": {"nbfiles": 1, "pct": 100.0},
    }


def test_api_check_content_known_post(api_client, content):
    url = reverse("api-1-content-known")
    rv = check_api_post_responses(
        api_client, url, data={"q": content["sha1"]}, status_code=200
    )

    assert rv.data == {
        "search_res": [{"found": True, "sha1": content["sha1"]}],
        "search_stats": {"nbfiles": 1, "pct": 100.0},
    }


def test_api_check_content_known_not_found(api_client):
    unknown_content_ = random_content()

    url = reverse("api-1-content-known", url_args={"q": unknown_content_["sha1"]})
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert rv.data == {
        "search_res": [{"found": False, "sha1": unknown_content_["sha1"]}],
        "search_stats": {"nbfiles": 1, "pct": 0.0},
    }


def test_api_content_uppercase(api_client, content):
    url = reverse(
        "api-1-content-uppercase-checksum", url_args={"q": content["sha1"].upper()}
    )

    rv = check_http_get_response(api_client, url, status_code=302)
    redirect_url = reverse("api-1-content", url_args={"q": content["sha1"]})
    assert rv["location"] == redirect_url
