# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

import pytest

from swh.web.tests.helpers import check_http_get_response
from swh.web.utils import reverse

from .test_api_views import create_add_forge_request

NB_FORGE_TYPE = 2
NB_FORGES_PER_TYPE = 20


def create_add_forge_requests(client, regular_user, regular_user2):
    requests = []
    for i in range(NB_FORGES_PER_TYPE):
        request = {
            "forge_type": "gitlab",
            "forge_url": f"https://gitlab.example{i:02d}.org",
            "forge_contact_email": f"admin@gitlab.example{i:02d}.org",
            "forge_contact_name": f"gitlab.example{i:02d}.org admin",
            "forge_contact_comment": "user marked as owner in forge members",
        }

        requests.append(
            json.loads(
                create_add_forge_request(
                    client,
                    regular_user,
                    data=request,
                ).content
            )
        )

        request = {
            "forge_type": "gitea",
            "forge_url": f"https://gitea.example{i:02d}.org",
            "forge_contact_email": f"admin@gitea.example{i:02d}.org",
            "forge_contact_name": f"gitea.example{i:02d}.org admin",
            "forge_contact_comment": "user marked as owner in forge members",
        }

        requests.append(
            json.loads(
                create_add_forge_request(
                    client,
                    regular_user2,
                    data=request,
                ).content
            )
        )
    return requests


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_list_datatables_no_parameters(
    client, regular_user, regular_user2
):
    create_add_forge_requests(client, regular_user, regular_user2)

    url = reverse("add-forge-request-list-datatables")
    resp = check_http_get_response(client, url, status_code=200)
    data = json.loads(resp.content)

    length = 10
    assert data["draw"] == 0
    assert data["recordsFiltered"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert data["recordsTotal"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert len(data["data"]) == length
    # default ordering is by descending id
    assert data["data"][0]["id"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert data["data"][-1]["id"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE - length + 1
    assert "submitter_name" not in data["data"][0]


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_list_datatables(
    client, regular_user, regular_user2, add_forge_moderator
):
    create_add_forge_requests(client, regular_user, regular_user2)

    length = 10

    url = reverse(
        "add-forge-request-list-datatables",
        query_params={"draw": 1, "length": length, "start": 0},
    )

    client.force_login(regular_user)
    resp = check_http_get_response(client, url, status_code=200)
    data = json.loads(resp.content)

    assert data["draw"] == 1
    assert data["recordsFiltered"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert data["recordsTotal"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert len(data["data"]) == length
    # default ordering is by descending id
    assert data["data"][0]["id"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert data["data"][-1]["id"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE - length + 1
    assert "submitter_name" not in data["data"][0]

    client.force_login(add_forge_moderator)
    resp = check_http_get_response(client, url, status_code=200)
    data = json.loads(resp.content)

    assert data["draw"] == 1
    assert data["recordsFiltered"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert data["recordsTotal"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert len(data["data"]) == length
    # default ordering is by descending id
    assert data["data"][0]["id"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert data["data"][-1]["id"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE - length + 1
    assert "submitter_name" in data["data"][0]
    assert "last_moderator" in data["data"][0]
    assert "last_modified_date" in data["data"][0]

    return data


@pytest.mark.django_db(transaction=True, reset_sequences=True)
@pytest.mark.parametrize("order_field", ["forge_url", "last_modified_date"])
def test_add_forge_request_list_datatables_ordering(
    client, add_forge_moderator, admin_user, order_field
):
    requests = create_add_forge_requests(client, add_forge_moderator, admin_user)
    requests_sorted = list(sorted(requests, key=lambda d: d[order_field]))
    forge_urls_asc = [request[order_field] for request in requests_sorted]
    forge_urls_desc = list(reversed(forge_urls_asc))

    length = 10

    client.force_login(admin_user)

    for direction in ("asc", "desc"):
        for i in range(4):
            url = reverse(
                "add-forge-request-list-datatables",
                query_params={
                    "draw": 1,
                    "length": length,
                    "start": i * length,
                    "order[0][column]": 2,
                    "order[0][dir]": direction,
                    "columns[2][name]": order_field,
                },
            )

            resp = check_http_get_response(client, url, status_code=200)
            data = json.loads(resp.content)

            assert data["draw"] == 1
            assert data["recordsFiltered"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
            assert data["recordsTotal"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
            assert len(data["data"]) == length

            page_forge_urls = [request[order_field] for request in data["data"]]
            if direction == "asc":
                expected_forge_urls = forge_urls_asc[i * length : (i + 1) * length]
            else:
                expected_forge_urls = forge_urls_desc[i * length : (i + 1) * length]
            assert page_forge_urls == expected_forge_urls


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_list_datatables_search(client, regular_user, regular_user2):
    create_add_forge_requests(client, regular_user, regular_user2)

    url = reverse(
        "add-forge-request-list-datatables",
        query_params={
            "draw": 1,
            "length": NB_FORGES_PER_TYPE,
            "start": 0,
            "search[value]": "gitlab",
        },
    )

    client.force_login(regular_user)
    resp = check_http_get_response(client, url, status_code=200)
    data = json.loads(resp.content)

    assert data["draw"] == 1
    assert data["recordsFiltered"] == NB_FORGES_PER_TYPE
    assert data["recordsTotal"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert len(data["data"]) == NB_FORGES_PER_TYPE

    page_forge_type = [request["forge_type"] for request in data["data"]]
    assert page_forge_type == ["gitlab"] * NB_FORGES_PER_TYPE


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_list_datatables_user_requests(
    client, regular_user, regular_user2
):
    create_add_forge_requests(client, regular_user, regular_user2)

    url = reverse(
        "add-forge-request-list-datatables",
        query_params={
            "draw": 1,
            "length": NB_FORGES_PER_TYPE * NB_FORGE_TYPE,
            "start": 0,
            "user_requests_only": 1,
        },
    )

    client.force_login(regular_user2)
    resp = check_http_get_response(client, url, status_code=200)
    data = json.loads(resp.content)

    assert data["draw"] == 1
    assert data["recordsFiltered"] == NB_FORGES_PER_TYPE
    assert data["recordsTotal"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert len(data["data"]) == NB_FORGES_PER_TYPE

    page_forge_type = [request["forge_type"] for request in data["data"]]
    assert page_forge_type == ["gitea"] * NB_FORGES_PER_TYPE
