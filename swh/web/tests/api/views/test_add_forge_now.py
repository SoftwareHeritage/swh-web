# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime
from urllib.parse import urlencode

import iso8601
import pytest

from swh.web.add_forge_now.models import Request
from swh.web.common.utils import reverse
from swh.web.tests.utils import check_api_post_response, check_http_post_response


def test_add_forge_request_create_anonymous_user(api_client):
    url = reverse("api-1-add-forge-request-create")
    check_api_post_response(api_client, url, status_code=403)


@pytest.mark.django_db
def test_add_forge_request_create_empty(api_client, regular_user):
    api_client.force_login(regular_user)
    url = reverse("api-1-add-forge-request-create")
    resp = check_api_post_response(api_client, url, status_code=400)
    assert '"forge_type"' in resp.data["reason"]


ADD_FORGE_DATA = {
    "forge_type": "gitlab",
    "forge_url": "https://gitlab.example.org",
    "forge_contact_email": "admin@gitlab.example.org",
    "forge_contact_name": "gitlab.example.org admin",
    "forge_contact_comment": "user marked as owner in forge members",
}


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_create_success(api_client, regular_user):
    api_client.force_login(regular_user)
    url = reverse("api-1-add-forge-request-create")

    date_before = datetime.datetime.now(tz=datetime.timezone.utc)

    resp = check_api_post_response(
        api_client, url, data=ADD_FORGE_DATA, status_code=201,
    )

    date_after = datetime.datetime.now(tz=datetime.timezone.utc)

    assert resp.data == {
        **ADD_FORGE_DATA,
        "id": 1,
        "status": "PENDING",
        "submission_date": resp.data["submission_date"],
        "submitter_name": regular_user.username,
        "submitter_email": regular_user.email,
    }

    assert date_before < iso8601.parse_date(resp.data["submission_date"]) < date_after

    request = Request.objects.all()[0]

    assert request.forge_url == ADD_FORGE_DATA["forge_url"]
    assert request.submitter_name == regular_user.username


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_create_success_form_encoded(client, regular_user):
    client.force_login(regular_user)
    url = reverse("api-1-add-forge-request-create")

    date_before = datetime.datetime.now(tz=datetime.timezone.utc)

    resp = check_http_post_response(
        client,
        url,
        request_content_type="application/x-www-form-urlencoded",
        data=urlencode(ADD_FORGE_DATA),
        status_code=201,
    )

    date_after = datetime.datetime.now(tz=datetime.timezone.utc)

    assert resp.data == {
        **ADD_FORGE_DATA,
        "id": 1,
        "status": "PENDING",
        "submission_date": resp.data["submission_date"],
        "submitter_name": regular_user.username,
        "submitter_email": regular_user.email,
    }

    assert date_before < iso8601.parse_date(resp.data["submission_date"]) < date_after

    request = Request.objects.all()[0]

    assert request.forge_url == ADD_FORGE_DATA["forge_url"]
    assert request.submitter_name == regular_user.username


@pytest.mark.django_db(transaction=True, reset_sequences=True)
def test_add_forge_request_create_duplicate(api_client, regular_user):
    api_client.force_login(regular_user)
    url = reverse("api-1-add-forge-request-create")

    check_api_post_response(
        api_client, url, data=ADD_FORGE_DATA, status_code=201,
    )

    check_api_post_response(
        api_client, url, data=ADD_FORGE_DATA, status_code=409,
    )

    requests = Request.objects.all()
    assert len(requests) == 1
