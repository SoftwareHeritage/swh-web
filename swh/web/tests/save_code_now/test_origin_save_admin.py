# Copyright (C) 2015-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from urllib.parse import unquote

import pytest

from django.conf import settings

from swh.web.save_code_now.models import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_REQUEST_PENDING,
    SAVE_REQUEST_REJECTED,
    SAVE_TASK_NOT_YET_SCHEDULED,
    SaveAuthorizedOrigin,
    SaveOriginRequest,
    SaveUnauthorizedOrigin,
)
from swh.web.save_code_now.origin_save import can_save_origin
from swh.web.tests.helpers import check_http_get_response, check_http_post_response
from swh.web.utils import reverse

_authorized_origin_url = "https://scm.ourproject.org/anonscm/"
_unauthorized_origin_url = "https://www.softwareheritage.org/"


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def populated_db():
    SaveAuthorizedOrigin.objects.create(url=_authorized_origin_url)
    SaveUnauthorizedOrigin.objects.create(url=_unauthorized_origin_url)


def check_not_login(client, url):
    login_url = reverse(settings.LOGIN_URL, query_params={"next": url})

    resp = check_http_post_response(client, url, status_code=302)
    assert unquote(resp.url) == login_url


def test_add_authorized_origin_url(client, staff_user):
    authorized_url = "https://scm.adullact.net/anonscm/"
    assert can_save_origin(authorized_url) == SAVE_REQUEST_PENDING

    url = reverse(
        "admin-origin-save-add-authorized-url", url_args={"origin_url": authorized_url}
    )

    check_not_login(client, url)

    assert can_save_origin(authorized_url) == SAVE_REQUEST_PENDING

    client.force_login(staff_user)

    check_http_post_response(client, url, status_code=200)
    assert can_save_origin(authorized_url) == SAVE_REQUEST_ACCEPTED


def test_remove_authorized_origin_url(client, staff_user):
    assert can_save_origin(_authorized_origin_url) == SAVE_REQUEST_ACCEPTED

    url = reverse(
        "admin-origin-save-remove-authorized-url",
        url_args={"origin_url": _authorized_origin_url},
    )

    check_not_login(client, url)

    assert can_save_origin(_authorized_origin_url) == SAVE_REQUEST_ACCEPTED

    client.force_login(staff_user)
    check_http_post_response(client, url, status_code=200)
    assert can_save_origin(_authorized_origin_url) == SAVE_REQUEST_PENDING


def test_add_unauthorized_origin_url(client, staff_user):
    unauthorized_url = "https://www.yahoo./"
    assert can_save_origin(unauthorized_url) == SAVE_REQUEST_PENDING

    url = reverse(
        "admin-origin-save-add-unauthorized-url",
        url_args={"origin_url": unauthorized_url},
    )

    check_not_login(client, url)

    assert can_save_origin(unauthorized_url) == SAVE_REQUEST_PENDING

    client.force_login(staff_user)
    check_http_post_response(client, url, status_code=200)
    assert can_save_origin(unauthorized_url) == SAVE_REQUEST_REJECTED


def test_remove_unauthorized_origin_url(client, staff_user):
    assert can_save_origin(_unauthorized_origin_url) == SAVE_REQUEST_REJECTED

    url = reverse(
        "admin-origin-save-remove-unauthorized-url",
        url_args={"origin_url": _unauthorized_origin_url},
    )

    check_not_login(client, url)

    assert can_save_origin(_unauthorized_origin_url) == SAVE_REQUEST_REJECTED

    client.force_login(staff_user)
    check_http_post_response(client, url, status_code=200)
    assert can_save_origin(_unauthorized_origin_url) == SAVE_REQUEST_PENDING


def test_accept_pending_save_request(client, staff_user, swh_scheduler):

    visit_type = "git"
    origin_url = "https://v2.pikacode.com/bthate/botlib.git"
    save_request_url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": visit_type, "origin_url": origin_url},
    )
    response = check_http_post_response(client, save_request_url, status_code=200)
    assert response.data["save_request_status"] == SAVE_REQUEST_PENDING

    accept_request_url = reverse(
        "admin-origin-save-request-accept",
        url_args={"visit_type": visit_type, "origin_url": origin_url},
    )

    check_not_login(client, accept_request_url)

    client.force_login(staff_user)
    response = check_http_post_response(client, accept_request_url, status_code=200)

    response = check_http_get_response(client, save_request_url, status_code=200)
    assert response.data[0]["save_request_status"] == SAVE_REQUEST_ACCEPTED
    assert response.data[0]["save_task_status"] == SAVE_TASK_NOT_YET_SCHEDULED


def test_reject_pending_save_request(client, staff_user, swh_scheduler):

    visit_type = "git"
    origin_url = "https://wikipedia.com"

    save_request_url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": visit_type, "origin_url": origin_url},
    )

    response = check_http_post_response(client, save_request_url, status_code=200)
    assert response.data["save_request_status"] == SAVE_REQUEST_PENDING

    reject_request_url = reverse(
        "admin-origin-save-request-reject",
        url_args={"visit_type": visit_type, "origin_url": origin_url},
    )

    check_not_login(client, reject_request_url)

    client.force_login(staff_user)
    response = check_http_post_response(client, reject_request_url, status_code=200)

    response = check_http_get_response(client, save_request_url, status_code=200)
    assert response.data[0]["save_request_status"] == SAVE_REQUEST_REJECTED
    assert response.data[0]["note"] is None


def test_reject_pending_save_request_not_found(client, staff_user, swh_scheduler):

    visit_type = "git"
    origin_url = "https://example.org"

    reject_request_url = reverse(
        "admin-origin-save-request-reject",
        url_args={"visit_type": visit_type, "origin_url": origin_url},
    )

    client.force_login(staff_user)
    check_http_post_response(client, reject_request_url, status_code=404)


def test_reject_pending_save_request_with_note(client, staff_user, swh_scheduler):

    visit_type = "git"
    origin_url = "https://wikipedia.com"

    save_request_url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": visit_type, "origin_url": origin_url},
    )

    response = check_http_post_response(client, save_request_url, status_code=200)
    assert response.data["save_request_status"] == SAVE_REQUEST_PENDING

    reject_request_url = reverse(
        "admin-origin-save-request-reject",
        url_args={"visit_type": visit_type, "origin_url": origin_url},
    )

    data = {"note": "The URL does not target a git repository"}

    client.force_login(staff_user)
    response = check_http_post_response(
        client, reject_request_url, status_code=200, data=data
    )

    response = check_http_get_response(client, save_request_url, status_code=200)
    assert response.data[0]["save_request_status"] == SAVE_REQUEST_REJECTED
    assert response.data[0]["note"] == data["note"]


def test_remove_save_request(client, staff_user):
    sor = SaveOriginRequest.objects.create(
        visit_type="git",
        origin_url="https://wikipedia.com",
        status=SAVE_REQUEST_PENDING,
    )
    assert SaveOriginRequest.objects.count() == 1

    remove_request_url = reverse(
        "admin-origin-save-request-remove", url_args={"sor_id": sor.id}
    )

    check_not_login(client, remove_request_url)

    client.force_login(staff_user)
    check_http_post_response(client, remove_request_url, status_code=200)
    assert SaveOriginRequest.objects.count() == 0
