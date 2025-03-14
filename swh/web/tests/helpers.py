# Copyright (C) 2020-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from html import unescape
import shutil
from typing import Any, Optional, cast

from bs4 import BeautifulSoup

from django.http.response import HttpResponse, HttpResponseBase, StreamingHttpResponse
from django.test.client import MULTIPART_CONTENT, Client
from rest_framework.response import Response
from rest_framework.test import APIClient

from swh.web.tests.django_asserts import assert_template_used


def _assert_http_response(
    response: HttpResponseBase, status_code: int, content_type: str
) -> HttpResponseBase:
    if isinstance(response, Response):
        drf_response = cast(Response, response)
        error_context = (
            drf_response.data.pop("traceback")
            if isinstance(drf_response.data, dict) and "traceback" in drf_response.data
            else drf_response.data
        )
    elif isinstance(response, StreamingHttpResponse):
        error_context = getattr(response, "traceback", response.streaming_content)
    elif isinstance(response, HttpResponse):
        error_context = (
            # traceback was escaped for HTML views as they are displayed in error page
            # when debug mode is activated
            unescape(response.traceback)
            if hasattr(response, "traceback")
            else response.content
        )

    assert (
        response.status_code == status_code
    ), f"Expected status code {status_code} but actual is {response.status_code}" + (
        f"\n{error_context}" if error_context else ""
    )
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
    **headers,
) -> HttpResponseBase:
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
            **headers,
        ),
        status_code=status_code,
        content_type=content_type,
    )


def check_http_post_response(
    client: Client,
    url: str,
    status_code: int,
    content_type: str = "*/*",
    request_content_type="application/json",
    data: dict[str, Any] | Optional[str] = None,
    http_origin: Optional[str] = None,
    **headers,
) -> HttpResponseBase:
    """Helper function to check HTTP response for a POST request.

    Args:
        client: Django test client
        url: URL to check response
        status_code: expected HTTP status code
        content_type: expected response content type
        request_content_type: content type of request body
        data: optional POST data

    Returns:
        The HTTP response
    """
    return _assert_http_response(
        response=client.post(
            url,
            data=data,
            content_type=request_content_type,
            HTTP_ACCEPT=content_type,
            HTTP_ORIGIN=http_origin,
            **headers,
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
    data: Optional[Any] = None,
    **headers,
) -> Response:
    """Helper function to check Web API response for a POST request
    for all accepted content types.

    Args:
        api_client: DRF test client
        url: Web API URL to check response
        status_code: expected HTTP status code

    Returns:
        The HTTP response
    """
    return cast(
        Response,
        _assert_http_response(
            response=api_client.post(
                url,
                data=data,
                content_type=headers.get("HTTP_CONTENT_TYPE"),
                format="json" if not headers.get("HTTP_CONTENT_TYPE") else None,
                HTTP_ACCEPT=content_type,
                **headers,
            ),
            status_code=status_code,
            content_type=content_type,
        ),
    )


def check_api_post_responses(
    api_client: APIClient,
    url: str,
    status_code: int,
    data: Optional[dict[str, Any]] = None,
    **headers,
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
        api_client,
        url,
        status_code,
        content_type="application/json",
        data=data,
        **headers,
    )

    # check YAML response
    check_api_post_response(
        api_client,
        url,
        status_code,
        content_type="application/yaml",
        data=data,
        **headers,
    )

    return cast(Response, response_json)


def check_html_get_response(
    client: Client,
    url: str,
    status_code: int,
    template_used: Optional[str] = None,
    http_origin: Optional[str] = None,
    server_name: Optional[str] = None,
) -> HttpResponseBase:
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
        client,
        url,
        status_code,
        content_type="text/html",
        http_origin=http_origin,
        server_name=server_name,
    )
    if template_used is not None:
        assert_template_used(response, template_used)
    return response


def check_html_post_response(
    client: Client,
    url: str,
    status_code: int,
    data: dict[str, Any],
    template_used: Optional[str] = None,
    http_origin: Optional[str] = None,
    server_name: Optional[str] = None,
    **headers,
) -> HttpResponseBase:
    """Helper function to check HTML responses for a POST request.

    Args:
        client: Django test client
        url: URL to check responses
        status_code: expected HTTP status code
        data: POST data
        template_used: optional used Django template to check

    Keyword Args:
        headers: extra kwargs passed to ``client.post``, for example follow=True

    Returns:
        The HTML response
    """
    response = check_http_post_response(
        client,
        url,
        status_code,
        data=data,
        content_type="text/html",
        request_content_type=MULTIPART_CONTENT,
        http_origin=http_origin,
        server_name=server_name,
        **headers,
    )
    if template_used is not None:
        assert_template_used(response, template_used)
    return response


def prettify_html(html: str) -> str:
    """
    Prettify an HTML document.

    Since it adds whitespace (in the form of newlines), this method changes
    the meaning of the HTML document and should not be used for reformatting
    purpose. The goal is to help visually understanding the structure of the
    document.

    Args:
        html: Input HTML document

    Returns:
        The prettified HTML document
    """
    return BeautifulSoup(html, "lxml").prettify()


fossology_missing = shutil.which("nomossa") is None
