# Copyright (C) 2015-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from corsheaders.middleware import (
    ACCESS_CONTROL_ALLOW_HEADERS,
    ACCESS_CONTROL_ALLOW_METHODS,
    ACCESS_CONTROL_ALLOW_ORIGIN,
)

from django.test.utils import override_settings

from swh.model.swhids import ObjectType
from swh.web.api.apiresponse import (
    compute_link_header,
    filter_by_fields,
    make_api_response,
    transform,
)
from swh.web.browse.tests.views.conftest import (  # noqa: F401
    make_masked_object_exception,
)
from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.helpers import check_http_get_response, check_http_post_response
from swh.web.utils import reverse
from swh.web.utils.identifiers import gen_swhid


def test_compute_link_header():
    next_link = "/api/endpoint/next"
    prev_link = "/api/endpoint/prev"
    rv = {
        "headers": {"link-next": next_link, "link-prev": prev_link},
        "results": [1, 2, 3],
    }
    options = {}

    headers = compute_link_header(rv, options)

    assert headers == {
        "Link": (f'<{next_link}>; rel="next",' f'<{prev_link}>; rel="previous"')
    }


def test_compute_link_header_nothing_changed():
    rv = {}
    options = {}

    headers = compute_link_header(rv, options)

    assert headers == {}


def test_compute_link_header_nothing_changed_2():
    rv = {"headers": {}}
    options = {}

    headers = compute_link_header(rv, options)

    assert headers == {}


def test_transform_only_return_results_1():
    rv = {"results": {"some-key": "some-value"}}
    assert transform(rv) == {"some-key": "some-value"}


def test_transform_only_return_results_2():
    rv = {"headers": {"something": "do changes"}, "results": {"some-key": "some-value"}}
    assert transform(rv) == {"some-key": "some-value"}


def test_transform_do_remove_headers():
    rv = {"headers": {"something": "do changes"}, "some-key": "some-value"}
    assert transform(rv) == {"some-key": "some-value"}


def test_transform_do_nothing():
    rv = {"some-key": "some-value"}
    assert transform(rv) == {"some-key": "some-value"}


def test_swh_multi_response_mimetype(mocker, api_request_factory):
    mock_shorten_path = mocker.patch("swh.web.api.apiresponse.shorten_path")
    mock_filter = mocker.patch("swh.web.api.apiresponse.filter_by_fields")
    mock_json = mocker.patch("swh.web.api.apiresponse.json")

    data = {"data": [12, 34], "id": "adc83b19e793491b1c6ea0fd8b46cd9f32e592fc"}

    mock_filter.return_value = data
    mock_shorten_path.return_value = "my_short_path"
    mock_json.dumps.return_value = json.dumps(data)

    accepted_response_formats = {
        "html": "text/html",
        "yaml": "application/yaml",
        "json": "application/json",
    }

    for resp_format in accepted_response_formats:
        request = api_request_factory.get("/api/test/path/")

        content_type = accepted_response_formats[resp_format]
        setattr(request, "accepted_media_type", content_type)

        rv = make_api_response(request, data)

        mock_filter.assert_called_with(request, data)

        if resp_format != "html":
            assert rv.status_code == 200, rv.data
            assert rv.data == data
        else:
            assert rv.status_code == 200, rv.content
            assert_contains(rv, json.dumps(data))


def test_swh_filter_renderer_do_nothing(api_request_factory):
    input_data = {"a": "some-data"}

    request = api_request_factory.get("/api/test/path/", data={})
    setattr(request, "query_params", request.GET)

    actual_data = filter_by_fields(request, input_data)

    assert actual_data == input_data


def test_swh_filter_renderer_do_filter(mocker, api_request_factory):
    mock_ffk = mocker.patch("swh.web.api.apiresponse.utils.filter_field_keys")
    mock_ffk.return_value = {"a": "some-data"}

    request = api_request_factory.get("/api/test/path/", data={"fields": "a,c"})
    setattr(request, "query_params", request.GET)

    input_data = {"a": "some-data", "b": "some-other-data"}

    actual_data = filter_by_fields(request, input_data)

    assert actual_data == {"a": "some-data"}

    mock_ffk.assert_called_once_with(input_data, {"a", "c"})


def test_error_response_handler(mocker, api_client):
    mock_archive = mocker.patch("swh.web.api.views.stat.archive")
    mock_archive.stat_counters.side_effect = Exception("Something went wrong")
    url = reverse("api-1-stat-counters")
    resp = api_client.get(url)
    assert resp.status_code == 500
    assert "traceback" in resp.data
    assert "Traceback" in resp.data["traceback"]


def test_error_response_handler_for_masked(
    mocker, api_client, content, make_masked_object_exception  # noqa: F811
):
    swhid = f"swh:1:cnt:{content['sha1_git']}"
    masked_object_exception = make_masked_object_exception(swhid)

    mock_archive = mocker.patch("swh.web.api.views.stat.archive")
    mock_archive.stat_counters.side_effect = masked_object_exception
    url = reverse("api-1-stat-counters")
    resp = api_client.get(url)
    assert resp.status_code == 403
    assert swhid in resp.data["masked"]


def test_api_endpoints_have_cors_headers(client, content, directory, revision):
    url = reverse("api-1-stat-counters")

    resp = check_http_get_response(
        client, url, status_code=200, http_origin="https://example.org"
    )
    assert ACCESS_CONTROL_ALLOW_ORIGIN in resp

    swhids = [
        gen_swhid(ObjectType.CONTENT, content["sha1_git"]),
        gen_swhid(ObjectType.DIRECTORY, directory),
        gen_swhid(ObjectType.REVISION, revision),
    ]
    url = reverse("api-1-known")
    ac_request_method = "POST"
    ac_request_headers = "Content-Type"
    resp = client.options(
        url,
        HTTP_ORIGIN="https://example.org",
        HTTP_ACCESS_CONTROL_REQUEST_METHOD=ac_request_method,
        HTTP_ACCESS_CONTROL_REQUEST_HEADERS=ac_request_headers,
    )

    assert resp.status_code == 200
    assert ACCESS_CONTROL_ALLOW_ORIGIN in resp
    assert ACCESS_CONTROL_ALLOW_METHODS in resp
    assert ac_request_method in resp[ACCESS_CONTROL_ALLOW_METHODS]
    assert ACCESS_CONTROL_ALLOW_HEADERS in resp
    assert ac_request_headers.lower() in resp[ACCESS_CONTROL_ALLOW_HEADERS]

    resp = resp = check_http_post_response(
        client, url, data=swhids, status_code=200, http_origin="https://example.org"
    )
    assert ACCESS_CONTROL_ALLOW_ORIGIN in resp


@override_settings(DEBUG=False)
def test_api_response_invalid_url(client):
    json_reponse = (
        b'{"error":"Resource not found",'
        b'"reason":"The resource /api/1/foo/bar/ could not be found on the server."}'
    )
    yaml_reponse = (
        b"error: Resource not found\n"
        b"reason: The resource /api/1/foo/bar/ could not be found on the server.\n"
    )

    response = client.get("/api/1/foo/bar/", HTTP_ACCEPT="*/*")
    assert response.status_code == 404
    assert response["content-type"] == "application/json"
    assert response.content == json_reponse

    response = client.get("/api/1/foo/bar/", HTTP_ACCEPT="application/json")
    assert response.status_code == 404
    assert response["content-type"] == "application/json"
    assert response.content == json_reponse

    response = client.get("/api/1/foo/bar/", HTTP_ACCEPT="application/yaml")
    assert response.status_code == 404
    assert response["content-type"] == "application/yaml"
    assert response.content == yaml_reponse

    response = client.get("/api/1/foo/bar/", HTTP_ACCEPT="text/html")
    assert response.status_code == 404
    assert response["content-type"].startswith("text/html")
    assert b"<!DOCTYPE html>" in response.content
