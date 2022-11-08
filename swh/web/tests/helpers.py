# Copyright (C) 2020-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import shutil
from typing import Any, Dict, Optional, cast

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.http.response import HttpResponse, HttpResponseBase, StreamingHttpResponse
from django.test.client import Client
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
    data: Optional[Dict[str, Any]] = None,
    http_origin: Optional[str] = None,
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
    **headers,
) -> HttpResponseBase:
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
            url,
            data=data,
            format="json",
            HTTP_ACCEPT=content_type,
            **headers,
        ),
        status_code=status_code,
        content_type=content_type,
    )


def check_api_post_responses(
    api_client: APIClient,
    url: str,
    status_code: int,
    data: Optional[Dict[str, Any]] = None,
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


def create_django_permission(perm_name: str) -> Permission:
    """Create permission out of a permission name string

    Args:
        perm_name: Permission name (e.g. swh.web.api.throttling_exempted,
          swh.ambassador, ...)

    Returns:
        The persisted permission

    """
    perm_splitted = perm_name.split(".")
    app_label = ".".join(perm_splitted[:-1])
    perm_name = perm_splitted[-1]
    content_type = ContentType.objects.create(
        id=1000 + ContentType.objects.count(),
        app_label=app_label,
        model=perm_splitted[-1],
    )

    return Permission.objects.create(
        codename=perm_name,
        name=perm_name,
        content_type=content_type,
        id=1000 + Permission.objects.count(),
    )


fossology_missing = shutil.which("nomossa") is None
