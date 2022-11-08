# Copyright (C) 2021-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import hashlib
import re
import textwrap
from urllib.parse import unquote, urlparse

import pytest

from django.http.response import StreamingHttpResponse

from swh.model.hashutil import hash_to_bytes
from swh.model.swhids import ExtendedObjectType, ExtendedSWHID
from swh.web.api.views.graph import API_GRAPH_PERM
from swh.web.config import SWH_WEB_INTERNAL_SERVER_NAME, get_config
from swh.web.tests.helpers import check_http_get_response
from swh.web.utils import reverse


def test_graph_endpoint_no_authentication_for_vpn_users(api_client, requests_mock):
    graph_query = "stats"
    url = reverse("api-1-graph", url_args={"graph_query": graph_query})
    requests_mock.get(
        get_config()["graph"]["server_url"] + graph_query,
        json={},
        headers={"Content-Type": "application/json"},
    )
    check_http_get_response(
        api_client, url, status_code=200, server_name=SWH_WEB_INTERNAL_SERVER_NAME
    )


def test_graph_endpoint_needs_authentication(api_client):
    url = reverse("api-1-graph", url_args={"graph_query": "stats"})
    check_http_get_response(api_client, url, status_code=401)


def _authenticate_graph_user(api_client, keycloak_oidc, is_staff=False):
    keycloak_oidc.client_permissions = [API_GRAPH_PERM]
    if is_staff:
        keycloak_oidc.user_groups = ["/staff"]
    oidc_profile = keycloak_oidc.login()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {oidc_profile['refresh_token']}")


def test_graph_endpoint_needs_permission(api_client, keycloak_oidc, requests_mock):
    graph_query = "stats"
    url = reverse("api-1-graph", url_args={"graph_query": graph_query})
    oidc_profile = keycloak_oidc.login()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {oidc_profile['refresh_token']}")

    check_http_get_response(api_client, url, status_code=403)

    _authenticate_graph_user(api_client, keycloak_oidc)
    requests_mock.get(
        get_config()["graph"]["server_url"] + graph_query,
        json={},
        headers={"Content-Type": "application/json"},
    )
    check_http_get_response(api_client, url, status_code=200)


def test_graph_text_plain_response(api_client, keycloak_oidc, requests_mock):
    _authenticate_graph_user(api_client, keycloak_oidc)

    graph_query = "leaves/swh:1:dir:432d1b21c1256f7408a07c577b6974bbdbcc1323"

    response_text = textwrap.dedent(
        """\
        swh:1:cnt:1d3dace0a825b0535c37c53ed669ef817e9c1b47
        swh:1:cnt:6d5b280f4e33589ae967a7912a587dd5cb8dedaa
        swh:1:cnt:91bef238bf01356a550d416d14bb464c576ac6f4
        swh:1:cnt:58a8b925a463b87d49639fda282b8f836546e396
        swh:1:cnt:fd32ee0a87e16ccc853dfbeb7018674f9ce008c0
        swh:1:cnt:ab7c39871872589a4fc9e249ebc927fb1042c90d
        swh:1:cnt:93073c02bf3869845977527de16af4d54765838d
        swh:1:cnt:4251f795b52c54c447a97c9fe904d8b1f993b1e0
        swh:1:cnt:c6e7055424332006d07876ffeba684e7e284b383
        swh:1:cnt:8459d8867dc3b15ef7ae9683e21cccc9ab2ec887
        swh:1:cnt:5f9981d52202815aa947f85b9dfa191b66f51138
        swh:1:cnt:00a685ec51bcdf398c15d588ecdedb611dbbab4b
        swh:1:cnt:e1cf1ea335106a0197a2f92f7804046425a7d3eb
        swh:1:cnt:07069b38087f88ec192d2c9aff75a502476fd17d
        swh:1:cnt:f045ee845c7f14d903a2c035b2691a7c400c01f0
        """
    )

    requests_mock.get(
        get_config()["graph"]["server_url"] + graph_query,
        text=response_text,
        headers={"Content-Type": "text/plain", "Transfer-Encoding": "chunked"},
    )

    url = reverse("api-1-graph", url_args={"graph_query": graph_query})

    resp = check_http_get_response(
        api_client, url, status_code=200, content_type="text/plain"
    )
    assert isinstance(resp, StreamingHttpResponse)
    assert b"".join(resp.streaming_content) == response_text.encode()


_response_json = {
    "counts": {"nodes": 17075708289, "edges": 196236587976},
    "ratios": {
        "compression": 0.16,
        "bits_per_node": 58.828,
        "bits_per_edge": 5.119,
        "avg_locality": 2184278529.729,
    },
    "indegree": {"min": 0, "max": 263180117, "avg": 11.4921492364925},
    "outdegree": {"min": 0, "max": 1033207, "avg": 11.4921492364925},
}


def test_graph_json_response(api_client, keycloak_oidc, requests_mock):
    _authenticate_graph_user(api_client, keycloak_oidc)

    graph_query = "stats"

    requests_mock.get(
        get_config()["graph"]["server_url"] + graph_query,
        json=_response_json,
        headers={"Content-Type": "application/json"},
    )

    url = reverse("api-1-graph", url_args={"graph_query": graph_query})

    resp = check_http_get_response(api_client, url, status_code=200)
    assert resp.content_type == "application/json"
    assert resp.data == _response_json


def test_graph_ndjson_response(api_client, keycloak_oidc, requests_mock):
    _authenticate_graph_user(api_client, keycloak_oidc)

    graph_query = "visit/paths/swh:1:dir:644dd466d8ad527ea3a609bfd588a3244e6dafcb"

    response_ndjson = textwrap.dedent(
        """\
        ["swh:1:dir:644dd466d8ad527ea3a609bfd588a3244e6dafcb",\
         "swh:1:cnt:acfb7cabd63b368a03a9df87670ece1488c8bce0"]
        ["swh:1:dir:644dd466d8ad527ea3a609bfd588a3244e6dafcb",\
         "swh:1:cnt:2a0837708151d76edf28fdbb90dc3eabc676cff3"]
        ["swh:1:dir:644dd466d8ad527ea3a609bfd588a3244e6dafcb",\
         "swh:1:cnt:eaf025ad54b94b2fdda26af75594cfae3491ec75"]
        """
    )

    requests_mock.get(
        get_config()["graph"]["server_url"] + graph_query,
        text=response_ndjson,
        headers={
            "Content-Type": "application/x-ndjson",
            "Transfer-Encoding": "chunked",
        },
    )

    url = reverse("api-1-graph", url_args={"graph_query": graph_query})

    resp = check_http_get_response(api_client, url, status_code=200)
    assert isinstance(resp, StreamingHttpResponse)
    assert resp["Content-Type"] == "application/x-ndjson"
    assert b"".join(resp.streaming_content) == response_ndjson.encode()


def test_graph_response_resolve_origins(
    archive_data, api_client, keycloak_oidc, requests_mock, origin
):
    hasher = hashlib.sha1()
    hasher.update(origin["url"].encode())
    origin_sha1 = hasher.digest()
    origin_swhid = str(
        ExtendedSWHID(object_type=ExtendedObjectType.ORIGIN, object_id=origin_sha1)
    )
    snapshot = archive_data.snapshot_get_latest(origin["url"])["id"]
    snapshot_swhid = str(
        ExtendedSWHID(
            object_type=ExtendedObjectType.SNAPSHOT, object_id=hash_to_bytes(snapshot)
        )
    )

    _authenticate_graph_user(api_client, keycloak_oidc)

    for graph_query, response_text, strip_empty_lines, content_type in (
        (
            f"visit/nodes/{snapshot_swhid}",
            f"{snapshot_swhid}\n{origin_swhid}\n",
            False,
            "text/plain",
        ),
        (
            f"visit/nodes/{snapshot_swhid}",
            f"{snapshot_swhid}\n{origin_swhid}\n\n",  # empty line at the end
            True,
            "text/plain",
        ),
        (
            f"visit/edges/{snapshot_swhid}",
            f"{snapshot_swhid} {origin_swhid}\n",
            False,
            "text/plain",
        ),
        (
            f"visit/paths/{snapshot_swhid}",
            f'["{snapshot_swhid}", "{origin_swhid}"]\n',
            False,
            "application/x-ndjson",
        ),
    ):

        # set two lines response to check resolved origins cache
        response_text = response_text + response_text

        requests_mock.get(
            get_config()["graph"]["server_url"] + graph_query,
            text=response_text,
            headers={"Content-Type": content_type, "Transfer-Encoding": "chunked"},
        )

        url = reverse(
            "api-1-graph",
            url_args={"graph_query": graph_query},
            query_params={"direction": "backward"},
        )

        resp = check_http_get_response(api_client, url, status_code=200)
        assert isinstance(resp, StreamingHttpResponse)
        assert resp["Content-Type"] == content_type
        assert b"".join(resp.streaming_content) == response_text.encode()

        url = reverse(
            "api-1-graph",
            url_args={"graph_query": graph_query},
            query_params={"direction": "backward", "resolve_origins": "true"},
        )

        resp = check_http_get_response(api_client, url, status_code=200)
        assert isinstance(resp, StreamingHttpResponse)
        assert resp["Content-Type"] == content_type

        expected_response = response_text.replace(origin_swhid, origin["url"])

        if strip_empty_lines:
            expected_response = expected_response.replace("\n\n", "\n")

        assert b"".join(resp.streaming_content) == expected_response.encode()


def test_graph_response_resolve_origins_nothing_to_do(
    api_client, keycloak_oidc, requests_mock
):
    _authenticate_graph_user(api_client, keycloak_oidc)

    graph_query = "stats"

    requests_mock.get(
        get_config()["graph"]["server_url"] + graph_query,
        json=_response_json,
        headers={"Content-Type": "application/json"},
    )

    url = reverse(
        "api-1-graph",
        url_args={"graph_query": graph_query},
        query_params={"resolve_origins": "true"},
    )

    resp = check_http_get_response(api_client, url, status_code=200)
    assert resp.content_type == "application/json"
    assert resp.data == _response_json


def test_graph_response_invalid_accept_header(api_client):
    url = reverse(
        "api-1-graph",
        url_args={"graph_query": "stats"},
        query_params={"resolve_origins": "true"},
    )

    resp = api_client.get(url, HTTP_ACCEPT="text/html")
    assert resp.status_code == 406
    assert resp.content_type == "application/json"
    assert resp.data["exception"] == "NotAcceptable"
    assert resp.data["reason"] == "Could not satisfy the request Accept header."


def test_graph_error_response(api_client, keycloak_oidc, requests_mock):
    _authenticate_graph_user(api_client, keycloak_oidc)

    graph_query = "foo"

    error_message = "Not found"
    content_type = "text/plain"

    requests_mock.get(
        get_config()["graph"]["server_url"] + graph_query,
        text=error_message,
        headers={"Content-Type": content_type},
        status_code=404,
    )

    url = reverse("api-1-graph", url_args={"graph_query": graph_query})

    resp = check_http_get_response(api_client, url, status_code=404)
    assert resp.content_type == content_type
    assert resp.content == f'"{error_message}"'.encode()


@pytest.mark.parametrize(
    "graph_query, query_params, expected_graph_query_params",
    [
        ("stats", {}, ""),
        ("stats", {"resolve_origins": "true"}, "resolve_origins=true"),
        ("stats?a=1", {}, "a=1"),
        ("stats%3Fb=2", {}, "b=2"),
        ("stats?a=1", {"resolve_origins": "true"}, "a=1&resolve_origins=true"),
        ("stats%3Fb=2", {"resolve_origins": "true"}, "b=2&resolve_origins=true"),
        ("stats/?a=1", {"a": "2"}, "a=1&a=2"),
        ("stats/%3Fa=1", {"a": "2"}, "a=1&a=2"),
    ],
)
def test_graph_query_params(
    api_client,
    keycloak_oidc,
    requests_mock,
    graph_query,
    query_params,
    expected_graph_query_params,
):
    _authenticate_graph_user(api_client, keycloak_oidc)

    requests_mock.get(
        re.compile(get_config()["graph"]["server_url"]),
        json=_response_json,
        headers={"Content-Type": "application/json"},
    )

    url = reverse(
        "api-1-graph",
        url_args={"graph_query": graph_query},
        query_params=query_params,
    )

    check_http_get_response(api_client, url, status_code=200)

    url = requests_mock.request_history[0].url
    parsed_url = urlparse(url)
    assert parsed_url.path == f"/graph/{unquote(graph_query).split('?')[0]}"
    assert expected_graph_query_params in parsed_url.query


@pytest.mark.django_db  # for authentication
def test_graph_endpoint_max_edges_settings(api_client, keycloak_oidc, requests_mock):
    graph_config = get_config()["graph"]
    graph_query = "stats"
    url = reverse("api-1-graph", url_args={"graph_query": graph_query})
    requests_mock.get(
        get_config()["graph"]["server_url"] + graph_query,
        json={},
        headers={"Content-Type": "application/json"},
    )

    # currently unauthenticated user can only use the graph endpoint from
    # Software Heritage VPN
    check_http_get_response(
        api_client, url, status_code=200, server_name=SWH_WEB_INTERNAL_SERVER_NAME
    )
    assert (
        f"max_edges={graph_config['max_edges']['anonymous']}"
        in requests_mock.request_history[0].url
    )

    # standard user
    _authenticate_graph_user(api_client, keycloak_oidc)
    check_http_get_response(
        api_client,
        url,
        status_code=200,
    )
    assert (
        f"max_edges={graph_config['max_edges']['user']}"
        in requests_mock.request_history[1].url
    )

    # staff user
    _authenticate_graph_user(api_client, keycloak_oidc, is_staff=True)
    check_http_get_response(
        api_client,
        url,
        status_code=200,
    )
    assert (
        f"max_edges={graph_config['max_edges']['staff']}"
        in requests_mock.request_history[2].url
    )


def test_graph_endpoint_max_edges_query_parameter_value(
    api_client, keycloak_oidc, requests_mock
):
    graph_config = get_config()["graph"]
    graph_query = "stats"

    requests_mock.get(
        get_config()["graph"]["server_url"] + graph_query,
        json={},
        headers={"Content-Type": "application/json"},
    )
    _authenticate_graph_user(api_client, keycloak_oidc)

    max_edges_max_value = graph_config["max_edges"]["user"]

    max_edges = max_edges_max_value // 2
    url = reverse(
        "api-1-graph",
        url_args={"graph_query": graph_query},
        query_params={"max_edges": max_edges},
    )
    check_http_get_response(
        api_client,
        url,
        status_code=200,
    )
    assert f"max_edges={max_edges}" in requests_mock.request_history[0].url

    max_edges = max_edges_max_value * 2
    url = reverse(
        "api-1-graph",
        url_args={"graph_query": graph_query},
        query_params={"max_edges": max_edges},
    )
    check_http_get_response(
        api_client,
        url,
        status_code=200,
    )
    assert f"max_edges={max_edges_max_value}" in requests_mock.request_history[1].url
