# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict, Optional, cast

from django.http import HttpResponse, StreamingHttpResponse
from django.test.client import Client
from rest_framework.response import Response
from rest_framework.test import APIClient

from swh.web.tests.django_asserts import assert_template_used


def _assert_http_response(
    response: HttpResponse, status_code: int, content_type: str
) -> HttpResponse:

    if isinstance(response, Response):
        drf_response = cast(Response, response)
        error_context = (
            drf_response.data.pop("traceback")
            if isinstance(drf_response.data, dict) and "traceback" in drf_response.data
            else drf_response.data
        )
    elif isinstance(response, StreamingHttpResponse):
        error_context = getattr(response, "traceback", response.streaming_content)
    else:
        error_context = getattr(response, "traceback", response.content)

    assert response.status_code == status_code, error_context
    if content_type != "*/*":
        assert response["Content-Type"].startswith(content_type)
    return response


def check_http_get_response(
    client: Client,
    url: str,
    status_code: int,
    content_type: str = "*/*",
    http_origin: Optional[str] = None,
    server_name: Optional[str] = None,
) -> HttpResponse:
    """Helper function to check HTTP response for a GET request.

    Args:
        client: Django test client
        url: URL to check response
        status_code: expected HTTP status code
        content_type: expected response content type
        http_origin: optional HTTP_ORIGIN header value

    Returns:
        The HTTP response
    """
    return _assert_http_response(
        response=client.get(
            url,
            HTTP_ACCEPT=content_type,
            HTTP_ORIGIN=http_origin,
            SERVER_NAME=server_name if server_name else "testserver",
        ),
        status_code=status_code,
        content_type=content_type,
    )


def check_http_post_response(
    client: Client,
    url: str,
    status_code: int,
    content_type: str = "*/*",
    data: Optional[Dict[str, Any]] = None,
    http_origin: Optional[str] = None,
) -> HttpResponse:
    """Helper function to check HTTP response for a POST request.

    Args:
        client: Django test client
        url: URL to check response
        status_code: expected HTTP status code
        content_type: expected response content type
        data: optional POST data

    Returns:
        The HTTP response
    """
    return _assert_http_response(
        response=client.post(
            url,
            data=data,
            content_type="application/json",
            HTTP_ACCEPT=content_type,
            HTTP_ORIGIN=http_origin,
        ),
        status_code=status_code,
        content_type=content_type,
    )


def check_api_get_responses(
    api_client: APIClient, url: str, status_code: int
) -> Response:
    """Helper function to check Web API responses for GET requests
    for all accepted content types (JSON, YAML, HTML).

    Args:
        api_client: DRF test client
        url: Web API URL to check responses
        status_code: expected HTTP status code

    Returns:
        The Web API JSON response
    """
    # check JSON response
    response_json = check_http_get_response(
        api_client, url, status_code, content_type="application/json"
    )

    # check HTML response (API Web UI)
    check_http_get_response(api_client, url, status_code, content_type="text/html")

    # check YAML response
    check_http_get_response(
        api_client, url, status_code, content_type="application/yaml"
    )

    return cast(Response, response_json)


def check_api_post_response(
    api_client: APIClient,
    url: str,
    status_code: int,
    content_type: str = "*/*",
    data: Optional[Dict[str, Any]] = None,
) -> HttpResponse:
    """Helper function to check Web API response for a POST request
    for all accepted content types.

    Args:
        api_client: DRF test client
        url: Web API URL to check response
        status_code: expected HTTP status code

    Returns:
        The HTTP response
    """
    return _assert_http_response(
        response=api_client.post(
            url, data=data, format="json", HTTP_ACCEPT=content_type,
        ),
        status_code=status_code,
        content_type=content_type,
    )


def check_api_post_responses(
    api_client: APIClient,
    url: str,
    status_code: int,
    data: Optional[Dict[str, Any]] = None,
) -> Response:
    """Helper function to check Web API responses for POST requests
    for all accepted content types (JSON, YAML).

    Args:
        api_client: DRF test client
        url: Web API URL to check responses
        status_code: expected HTTP status code

    Returns:
        The Web API JSON response
    """
    # check JSON response
    response_json = check_api_post_response(
        api_client, url, status_code, content_type="application/json", data=data
    )

    # check YAML response
    check_api_post_response(
        api_client, url, status_code, content_type="application/yaml", data=data
    )

    return cast(Response, response_json)


def check_html_get_response(
    client: Client, url: str, status_code: int, template_used: Optional[str] = None
) -> HttpResponse:
    """Helper function to check HTML responses for a GET request.

    Args:
        client: Django test client
        url: URL to check responses
        status_code: expected HTTP status code
        template_used: optional used Django template to check

    Returns:
        The HTML response
    """
    response = check_http_get_response(
        client, url, status_code, content_type="text/html"
    )
    if template_used is not None:
        assert_template_used(response, template_used)
    return response
