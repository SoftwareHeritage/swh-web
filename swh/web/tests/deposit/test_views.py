# Copyright (C) 2021-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from base64 import b64encode

import pytest

from django.conf import settings

from swh.web.auth.utils import ADMIN_LIST_DEPOSIT_PERMISSION
from swh.web.config import get_config
from swh.web.tests.helpers import (
    check_html_get_response,
    check_http_get_response,
    create_django_permission,
)
from swh.web.utils import reverse


def test_deposit_admin_view_not_available_for_anonymous_user(client):
    url = reverse("admin-deposit")
    resp = check_html_get_response(client, url, status_code=302)
    assert resp["location"] == reverse(settings.LOGIN_URL, query_params={"next": url})


@pytest.mark.django_db
def test_deposit_admin_view_available_for_staff_user(client, staff_user):
    client.force_login(staff_user)
    url = reverse("admin-deposit")
    check_html_get_response(
        client, url, status_code=200, template_used="deposit-admin.html"
    )


@pytest.mark.django_db
def test_deposit_admin_view_available_for_user_with_permission(client, regular_user):
    regular_user.user_permissions.add(
        create_django_permission(ADMIN_LIST_DEPOSIT_PERMISSION)
    )
    client.force_login(regular_user)
    url = reverse("admin-deposit")
    check_html_get_response(
        client, url, status_code=200, template_used="deposit-admin.html"
    )


@pytest.mark.django_db
def test_deposit_admin_view_list_deposits(client, staff_user, requests_mock):
    deposits_data = {
        "data": [
            {
                "external_id": "hal-02527986",
                "id": 1066,
                "raw_metadata": None,
                "reception_date": "2022-04-08T14:12:34.143000Z",
                "status": "rejected",
                "status_detail": None,
                "swhid": None,
                "swhid_context": None,
                "type": "code",
                "uri": "https://inria.halpreprod.archives-ouvertes.fr/hal-02527986",
            },
            {
                "external_id": "hal-01243573",
                "id": 1065,
                "raw_metadata": None,
                "reception_date": "2022-04-08T12:53:50.940000Z",
                "status": "rejected",
                "status_detail": None,
                "swhid": None,
                "swhid_context": None,
                "type": "code",
                "uri": "https://inria.halpreprod.archives-ouvertes.fr/hal-01243573",
            },
        ],
        "draw": 2,
        "recordsFiltered": 645,
        "recordsTotal": 1066,
    }

    config = get_config()["deposit"]
    private_api_url = config["private_api_url"].rstrip("/") + "/"
    deposits_list_url = private_api_url + "deposits/datatables/"

    basic_auth_payload = (
        config["private_api_user"] + ":" + config["private_api_password"]
    ).encode()

    requests_mock.get(
        deposits_list_url,
        json=deposits_data,
        request_headers={
            "Authorization": f"Basic {b64encode(basic_auth_payload).decode('ascii')}"
        },
    )

    client.force_login(staff_user)
    url = reverse("admin-deposit-list")
    check_http_get_response(
        client, url, status_code=200, content_type="application/json"
    )
