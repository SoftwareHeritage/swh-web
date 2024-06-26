# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.tests.helpers import check_http_get_response
from swh.web.utils import reverse


def test_api_citation_bibtex_origin_get(api_client, origin_with_metadata_file):
    url = reverse(
        "api-1-raw-intrinsic-citation-origin-get",
        query_params={
            "origin_url": origin_with_metadata_file["url"],
            "citation_format": "bibtex",
        },
    )
    rv = check_http_get_response(api_client, url, status_code=200)
    assert "@software" in rv.data
    assert 'title = "Test Software"' in rv.data


def test_api_citation_bibtex_cff_origin_get(api_client, origin_with_cff_file):
    url = reverse(
        "api-1-raw-intrinsic-citation-origin-get",
        query_params={
            "origin_url": origin_with_cff_file["url"],
            "citation_format": "bibtex",
        },
    )
    rv = check_http_get_response(api_client, url, status_code=200)
    assert "@software" in rv.data
    assert 'title = "My Research Software"' in rv.data


def test_api_citation_bibtex_unknown_origin_get(api_client):
    fake_origin_url = "https://foo.bar"
    url = reverse(
        "api-1-raw-intrinsic-citation-origin-get",
        query_params={"origin_url": fake_origin_url, "citation_format": "bibtex"},
    )
    rv = check_http_get_response(api_client, url, status_code=404)
    assert "NotFoundExc" in rv.data["exception"]
    assert f"No origin with url {fake_origin_url} found." in rv.data["reason"]


def test_api_citation_bibtex_swhid_get(api_client, objects_with_metadata_file):
    url = reverse(
        "api-1-raw-intrinsic-citation-swhid-get",
        query_params={
            "target_swhid": str(objects_with_metadata_file[0]),
            "citation_format": "bibtex",
        },
    )
    rv = check_http_get_response(api_client, url, status_code=200)
    assert "@software" in rv.data
    assert 'title = "Test Software"' in rv.data
