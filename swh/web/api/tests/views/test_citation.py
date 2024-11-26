# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from yaml import YAMLError

from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.helpers import (
    check_api_get_responses,
    check_html_get_response,
    check_http_get_response,
)
from swh.web.utils import reverse


def check_api_citation_response(api_client, client, url, title):
    rv = check_api_get_responses(api_client, url, status_code=200)
    bibtex = rv.data["content"]
    assert "@software" in bibtex
    assert f'title = "{title}"' in bibtex

    # check citation metadata can be fecthed
    resp = check_http_get_response(api_client, rv.data["source_url"], status_code=200)
    citation_metadata = (b"".join(resp.streaming_content)).decode()
    assert title in citation_metadata

    # check source SWHID can be resolved and browsed
    browse_source_swhid_url = reverse(
        "browse-swhid", url_args={"swhid": rv.data["source_swhid"]}
    )
    resp = check_html_get_response(client, browse_source_swhid_url, status_code=302)
    resp = check_html_get_response(
        client, resp["location"], status_code=200, template_used="browse-content.html"
    )
    assert_contains(resp, title)


def test_api_citation_bibtex_origin_get(api_client, client, origin_with_metadata_file):
    url = reverse(
        "api-1-raw-intrinsic-citation-origin-get",
        query_params={
            "origin_url": origin_with_metadata_file["url"],
            "citation_format": "bibtex",
        },
    )
    check_api_citation_response(api_client, client, url, "Test Software")


def test_api_citation_bibtex_cff_origin_get(api_client, client, origin_with_cff_file):
    url = reverse(
        "api-1-raw-intrinsic-citation-origin-get",
        query_params={
            "origin_url": origin_with_cff_file["url"],
            "citation_format": "bibtex",
        },
    )
    check_api_citation_response(api_client, client, url, "My Research Software")


def test_api_citation_bibtex_unknown_origin_get(api_client):
    fake_origin_url = "https://foo.bar"
    url = reverse(
        "api-1-raw-intrinsic-citation-origin-get",
        query_params={"origin_url": fake_origin_url, "citation_format": "bibtex"},
    )
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert "NotFoundExc" in rv.data["exception"]
    assert f"No origin with url {fake_origin_url} found." in rv.data["reason"]


def test_api_citation_bibtex_swhid_get(api_client, client, objects_with_metadata_file):
    url = reverse(
        "api-1-raw-intrinsic-citation-swhid-get",
        query_params={
            "target_swhid": str(objects_with_metadata_file[0]),
            "citation_format": "bibtex",
        },
    )
    check_api_citation_response(api_client, client, url, "Test Software")


def test_api_citation_bibtex_parsing_error(api_client, origin_with_cff_file, mocker):

    error_message = "Error parsing YAML file"
    mocker.patch("yaml.safe_load").side_effect = YAMLError(error_message)
    url = reverse(
        "api-1-raw-intrinsic-citation-origin-get",
        query_params={
            "origin_url": origin_with_cff_file["url"],
            "citation_format": "bibtex",
        },
    )
    rv = check_api_get_responses(api_client, url, status_code=400)
    assert "BadInputExc" in rv.data["exception"]
    assert error_message in rv.data["reason"]
    assert "source_swhid" in rv.data
    assert "source_url" in rv.data
