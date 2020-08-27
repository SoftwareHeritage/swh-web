# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict, Optional

from rest_framework.test import APIClient
from rest_framework.response import Response


def check_api_get_responses(
    api_client: APIClient, url: str, status_code: int
) -> Response:
    """Helper function to check Web API responses to GET requests
    for all accepted content types.

    Args:
        api_client: DRF test client
        url: Web API URL to check responses
        status_code: expected HTTP status code

    Returns:
        The Web API JSON response
    """
    # check API Web UI
    html_content_type = "text/html"
    resp = api_client.get(url, HTTP_ACCEPT=html_content_type)
    assert resp.status_code == status_code, resp.content
    assert resp["Content-Type"] == html_content_type

    # check YAML response
    yaml_content_type = "application/yaml"
    resp = api_client.get(url, HTTP_ACCEPT=yaml_content_type)
    assert resp.status_code == status_code, resp.data
    assert resp["Content-Type"] == yaml_content_type

    # check JSON response
    resp = api_client.get(url)
    assert resp.status_code == status_code, resp.data
    assert resp["Content-Type"] == "application/json"

    return resp


def check_api_post_responses(
    api_client: APIClient, url: str, data: Optional[Dict[str, Any]], status_code: int
) -> Response:
    """Helper function to check Web API responses to POST requests
    for all accepted content types.

    Args:
        api_client: DRF test client
        url: Web API URL to check responses
        status_code: expected HTTP status code

    Returns:
        The Web API JSON response
    """
    # check YAML response
    yaml_content_type = "application/yaml"
    resp = api_client.post(url, data=data, format="json", HTTP_ACCEPT=yaml_content_type)
    assert resp.status_code == status_code, resp.data
    assert resp["Content-Type"] == yaml_content_type

    # check JSON response
    resp = api_client.post(url, data=data, format="json")
    assert resp.status_code == status_code, resp.data
    assert resp["Content-Type"] == "application/json"

    return resp
