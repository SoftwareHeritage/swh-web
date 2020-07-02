# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from swh.web.api.apiresponse import (
    compute_link_header,
    transform,
    make_api_response,
    filter_by_fields,
)


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

    accepted_response_formats = {
        "html": "text/html",
        "yaml": "application/yaml",
        "json": "application/json",
    }

    for format in accepted_response_formats:

        request = api_request_factory.get("/api/test/path/")

        mime_type = accepted_response_formats[format]
        setattr(request, "accepted_media_type", mime_type)

        if mime_type == "text/html":

            expected_data = {
                "response_data": json.dumps(data),
                "headers_data": {},
                "heading": "my_short_path",
                "status_code": 200,
            }

            mock_json.dumps.return_value = json.dumps(data)
        else:
            expected_data = data

        rv = make_api_response(request, data)

        mock_filter.assert_called_with(request, data)

        assert rv.status_code == 200, rv.data
        assert rv.data == expected_data
        if mime_type == "text/html":
            assert rv.template_name == "api/apidoc.html"


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
