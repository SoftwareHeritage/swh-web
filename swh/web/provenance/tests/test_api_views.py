# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.tests.helpers import check_api_get_responses, check_api_post_responses
from swh.web.utils import reverse

pytest_plugins = ["swh.graph.pytest_plugin", "swh.provenance.pytest_plugin"]

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="session")
def graph_grpc_backend_implementation():
    return "rust"


@pytest.fixture
def swh_provenance_config(graph_grpc_server):
    return {
        "cls": "graph",
        "url": graph_grpc_server,
    }


@pytest.fixture(autouse=True)
def swh_provenance(swh_provenance, mocker):
    mocker.patch("swh.web.provenance.api_views._provenance").return_value = (
        swh_provenance
    )
    return swh_provenance


def test_api_provenance_whereis_anonymous(api_client):
    url = reverse(
        "api-1-provenance-whereis",
        url_args={"target": "swh:1:cnt:0000000000000000000000000000000000000001"},
    )
    resp = check_api_get_responses(api_client, url, status_code=401)
    assert resp.data == {
        "exception": "UnauthorizedExc",
        "reason": "This API endpoint requires authentication.",
    }


def test_api_provenance_whereis_missing_user_permission(api_client, regular_user):
    api_client.force_login(regular_user)
    url = reverse(
        "api-1-provenance-whereis",
        url_args={"target": "swh:1:cnt:0000000000000000000000000000000000000001"},
    )
    resp = check_api_get_responses(api_client, url, status_code=403)
    assert resp.data == {
        "exception": "ForbiddenExc",
        "reason": "This API endpoint requires a special user permission.",
    }


def test_api_provenance_whereis_invalid_swhid(api_client, provenance_user):
    api_client.force_login(provenance_user)
    content_swhid = "swh:1:abc:0000000000000000000000000000000000000001"
    url = reverse("api-1-provenance-whereis", url_args={"target": content_swhid})
    resp = check_api_get_responses(api_client, url, status_code=400)
    assert resp.data["exception"] == "BadInputExc"
    assert resp.data["reason"].startswith(
        "Error when parsing identifier: Invalid SWHID"
    )


def test_api_provenance_whereis(api_client, provenance_user):
    api_client.force_login(provenance_user)

    # see swh.graph.example_dataset module
    content_swhid = "swh:1:cnt:0000000000000000000000000000000000000001"
    expected_provenance_swhid = (
        "swh:1:cnt:0000000000000000000000000000000000000001;"
        "origin=https://example.com/swh/graph2;"
        "anchor=swh:1:rel:0000000000000000000000000000000000000010"
    )

    url = reverse("api-1-provenance-whereis", url_args={"target": content_swhid})
    resp = check_api_get_responses(api_client, url, status_code=200)
    assert resp.data == expected_provenance_swhid


def test_api_provenance_whereare_anonymous(api_client):
    url = reverse("api-1-provenance-whereare")
    resp = check_api_post_responses(api_client, url, status_code=401)
    assert resp.data == {
        "exception": "UnauthorizedExc",
        "reason": "This API endpoint requires authentication.",
    }


def test_api_provenance_whereare_missing_user_permission(api_client, regular_user):
    api_client.force_login(regular_user)
    url = reverse("api-1-provenance-whereare")
    resp = check_api_post_responses(api_client, url, status_code=403)
    assert resp.data == {
        "exception": "ForbiddenExc",
        "reason": "This API endpoint requires a special user permission.",
    }


def test_api_provenance_whereare_invalid_swhid(api_client, provenance_user):
    api_client.force_login(provenance_user)
    content_swhids = ["swh:1:abc:0000000000000000000000000000000000000001"]
    url = reverse("api-1-provenance-whereare")
    resp = check_api_post_responses(
        api_client, url, data=content_swhids, status_code=400
    )
    assert resp.data["exception"] == "BadInputExc"
    assert resp.data["reason"].startswith(
        "Error when parsing identifier: Invalid SWHID"
    )


def test_api_provenance_whereare(api_client, provenance_user):
    api_client.force_login(provenance_user)

    # see swh.graph.example_dataset module
    content_swhids = [
        "swh:1:cnt:0000000000000000000000000000000000000001",
        "swh:1:cnt:0000000000000000000000000000000000000014",
    ]
    expected_provenance_swhids = [
        (
            "swh:1:cnt:0000000000000000000000000000000000000001;"
            "origin=https://example.com/swh/graph2;"
            "anchor=swh:1:rel:0000000000000000000000000000000000000010"
        ),
        (
            "swh:1:cnt:0000000000000000000000000000000000000014;"
            "origin=https://example.com/swh/graph2;"
            "anchor=swh:1:rel:0000000000000000000000000000000000000021"
        ),
    ]

    url = reverse("api-1-provenance-whereare")
    resp = check_api_post_responses(
        api_client, url, data=content_swhids, status_code=200
    )
    assert resp.data == expected_provenance_swhids
