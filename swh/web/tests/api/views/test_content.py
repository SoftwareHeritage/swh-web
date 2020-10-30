# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given
import pytest

from swh.web.common.utils import reverse
from swh.web.tests.conftest import ctags_json_missing, fossology_missing
from swh.web.tests.data import random_content
from swh.web.tests.strategies import content, contents_with_ctags
from swh.web.tests.utils import (
    check_api_get_responses,
    check_api_post_responses,
    check_http_get_response,
)


@given(content())
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


@pytest.mark.skip  # Language indexer is disabled
@pytest.mark.skipif(
    ctags_json_missing, reason="requires ctags with json output support"
)
@given(contents_with_ctags())
def test_api_content_symbol(api_client, indexer_data, contents_with_ctags):
    expected_data = {}
    for content_sha1 in contents_with_ctags["sha1s"]:
        indexer_data.content_add_ctags(content_sha1)
        for ctag in indexer_data.content_get_ctags(content_sha1):
            if ctag["name"] == contents_with_ctags["symbol_name"]:
                expected_data[content_sha1] = ctag
                break
    url = reverse(
        "api-1-content-symbol",
        url_args={"q": contents_with_ctags["symbol_name"]},
        query_params={"per_page": 100},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)

    for entry in rv.data:
        content_sha1 = entry["sha1"]
        expected_entry = expected_data[content_sha1]
        for key, view_name in (
            ("content_url", "api-1-content"),
            ("data_url", "api-1-content-raw"),
            ("license_url", "api-1-content-license"),
            ("language_url", "api-1-content-language"),
            ("filetype_url", "api-1-content-filetype"),
        ):
            expected_entry[key] = reverse(
                view_name,
                url_args={"q": "sha1:%s" % content_sha1},
                request=rv.wsgi_request,
            )
        expected_entry["sha1"] = content_sha1
        del expected_entry["id"]
        assert entry == expected_entry
    assert "Link" not in rv

    url = reverse(
        "api-1-content-symbol",
        url_args={"q": contents_with_ctags["symbol_name"]},
        query_params={"per_page": 2},
    )

    rv = check_api_get_responses(api_client, url, status_code=200)

    next_url = (
        reverse(
            "api-1-content-symbol",
            url_args={"q": contents_with_ctags["symbol_name"]},
            query_params={"last_sha1": rv.data[1]["sha1"], "per_page": 2},
            request=rv.wsgi_request,
        ),
    )
    assert rv["Link"] == '<%s>; rel="next"' % next_url


def test_api_content_symbol_not_found(api_client):
    url = reverse("api-1-content-symbol", url_args={"q": "bar"})
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "No indexed raw content match expression 'bar'.",
    }
    assert "Link" not in rv


@pytest.mark.skipif(
    ctags_json_missing, reason="requires ctags with json output support"
)
@given(content())
def test_api_content_ctags(api_client, indexer_data, content):
    indexer_data.content_add_ctags(content["sha1"])
    url = reverse(
        "api-1-content-ctags", url_args={"q": "sha1_git:%s" % content["sha1_git"]}
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    content_url = reverse(
        "api-1-content",
        url_args={"q": "sha1:%s" % content["sha1"]},
        request=rv.wsgi_request,
    )
    expected_data = list(indexer_data.content_get_ctags(content["sha1"]))
    for e in expected_data:
        e["content_url"] = content_url
    assert rv.data == expected_data


@pytest.mark.skipif(fossology_missing, reason="requires fossology-nomossa installed")
@given(content())
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


@given(content())
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


@given(content())
def test_api_content_raw_text(api_client, archive_data, content):
    url = reverse("api-1-content-raw", url_args={"q": "sha1:%s" % content["sha1"]})

    rv = check_http_get_response(api_client, url, status_code=200)
    assert rv["Content-Type"] == "application/octet-stream"
    assert (
        rv["Content-disposition"]
        == "attachment; filename=content_sha1_%s_raw" % content["sha1"]
    )
    expected_data = archive_data.content_get_data(content["sha1"])
    assert rv.content == expected_data["data"]


@given(content())
def test_api_content_raw_text_with_filename(api_client, archive_data, content):
    url = reverse(
        "api-1-content-raw",
        url_args={"q": "sha1:%s" % content["sha1"]},
        query_params={"filename": "filename.txt"},
    )
    rv = check_http_get_response(api_client, url, status_code=200)
    assert rv["Content-disposition"] == "attachment; filename=filename.txt"
    assert rv["Content-Type"] == "application/octet-stream"
    expected_data = archive_data.content_get_data(content["sha1"])
    assert rv.content == expected_data["data"]


@given(content())
def test_api_check_content_known(api_client, content):
    url = reverse("api-1-content-known", url_args={"q": content["sha1"]})
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert rv.data == {
        "search_res": [{"found": True, "sha1": content["sha1"]}],
        "search_stats": {"nbfiles": 1, "pct": 100.0},
    }


@given(content())
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


@given(content())
def test_api_content_uppercase(api_client, content):
    url = reverse(
        "api-1-content-uppercase-checksum", url_args={"q": content["sha1"].upper()}
    )

    rv = check_http_get_response(api_client, url, status_code=302)
    redirect_url = reverse("api-1-content", url_args={"q": content["sha1"]})
    assert rv["location"] == redirect_url
