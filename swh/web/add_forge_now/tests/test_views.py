# Copyright (C) 2022-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from urllib.parse import urlencode

import pytest

from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.helpers import (
    check_html_get_response,
    check_http_get_response,
    check_http_post_response,
)
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
            create_add_forge_request(
                client,
                regular_user,
                data=request,
                HTTP_CONTENT_TYPE="application/json",
            ).data
        )

        request = {
            "forge_type": "gitea",
            "forge_url": f"https://gitea.example{i:02d}.org",
            "forge_contact_email": f"admin@gitea.example{i:02d}.org",
            "forge_contact_name": f"gitea.example{i:02d}.org admin",
            "forge_contact_comment": "user marked as owner in forge members",
        }

        requests.append(
            create_add_forge_request(
                client,
                regular_user2,
                data=request,
                HTTP_CONTENT_TYPE="application/json",
            ).data
        )
    return requests


@pytest.mark.django_db(transaction=True)
def test_add_forge_request_list_datatables_no_parameters(
    client, regular_user, regular_user2
):
    requests = create_add_forge_requests(client, regular_user, regular_user2)

    url = reverse("add-forge-request-list-datatables")
    resp = check_http_get_response(client, url, status_code=200)
    data = json.loads(resp.content)

    length = 10
    assert data["draw"] == 0
    assert data["recordsFiltered"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert data["recordsTotal"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert len(data["data"]) == length
    # default ordering is by descending id
    assert data["data"][0]["id"] == requests[-1]["id"]
    assert data["data"][-1]["id"] == requests[-1]["id"] - length + 1
    assert "submitter_name" not in data["data"][0]


@pytest.mark.django_db(transaction=True)
def test_add_forge_request_list_datatables(
    client, regular_user, regular_user2, add_forge_moderator
):
    requests = create_add_forge_requests(client, regular_user, regular_user2)

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
    assert data["data"][0]["id"] == requests[-1]["id"]
    assert data["data"][-1]["id"] == requests[-1]["id"] - length + 1
    assert "submitter_name" not in data["data"][0]

    client.force_login(add_forge_moderator)
    resp = check_http_get_response(client, url, status_code=200)
    data = json.loads(resp.content)

    assert data["draw"] == 1
    assert data["recordsFiltered"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert data["recordsTotal"] == NB_FORGE_TYPE * NB_FORGES_PER_TYPE
    assert len(data["data"]) == length
    # default ordering is by descending id
    assert data["data"][0]["id"] == requests[-1]["id"]
    assert data["data"][-1]["id"] == requests[-1]["id"] - length + 1
    assert "submitter_name" in data["data"][0]
    assert "last_moderator" in data["data"][0]
    assert "last_modified_date" in data["data"][0]


@pytest.mark.django_db(transaction=True)
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
                    "order[0][name]": order_field,
                    "columns[2][name]": order_field,
                    "order[0][dir]": direction,
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


@pytest.mark.django_db(transaction=True)
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


@pytest.mark.django_db(transaction=True)
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


@pytest.mark.django_db(transaction=True)
def test_create_add_forge_now_request_anonymous_user(client):
    url = reverse("forge-add-create")
    check_http_post_response(client, url, status_code=403)


@pytest.mark.django_db(transaction=True)
def test_create_add_forge_now_request_missing_form_data(client, regular_user):
    client.force_login(regular_user)
    url = reverse("forge-add-create")
    resp = check_http_post_response(
        client,
        url,
        request_content_type="application/x-www-form-urlencoded",
        data=urlencode({"forge_type": "foo"}),
        status_code=400,
    )
    assert_contains(resp, "This field is required", count=3, status_code=400)


@pytest.mark.django_db(transaction=True)
def test_create_add_forge_now_request_invalid_form_data(client, regular_user):
    client.force_login(regular_user)
    url = reverse("forge-add-create")
    resp = check_http_post_response(
        client,
        url,
        request_content_type="application/x-www-form-urlencoded",
        data=urlencode(
            {
                "forge_type": "gitlab",
                "forge_url": "bar",
                "forge_contact_email": "baz",
                "forge_contact_name": "foo",
            }
        ),
        status_code=400,
    )
    assert_contains(resp, "Enter a valid URL", status_code=400)
    assert_contains(resp, "Enter a valid email", status_code=400)


@pytest.mark.django_db(transaction=True)
def test_create_add_forge_now_request_valid(client, regular_user):
    client.force_login(regular_user)
    url = reverse("forge-add-create")
    resp = check_http_post_response(
        client,
        url,
        request_content_type="application/x-www-form-urlencoded",
        data=urlencode(
            {
                "forge_type": "gitlab",
                "forge_url": "https://gitlab.example.org",
                "forge_contact_email": "jonhdoe@example.org",
                "forge_contact_name": "John Doe",
            }
        ),
        status_code=200,
    )
    assert_contains(resp, "Your request has been submitted")


@pytest.mark.django_db(transaction=True)
def test_add_forge_request_admin_dashboard(
    client, admin_user, regular_user, regular_user2
):
    requests = create_add_forge_requests(client, regular_user, regular_user2)

    request_id = requests[0]["id"]
    url = reverse(
        "add-forge-now-request-dashboard", url_args={"request_id": request_id}
    )

    client.force_login(admin_user)
    resp = check_html_get_response(client, url, status_code=200)
    request_edit_url = request_edit_url = reverse(
        "admin:swh_web_add_forge_now_request_change",
        url_args={"object_id": request_id},
    )
    assert_contains(resp, request_edit_url)
    check_html_get_response(client, request_edit_url, status_code=200)
