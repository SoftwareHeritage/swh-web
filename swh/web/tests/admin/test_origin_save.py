# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from urllib.parse import unquote

import pytest

from django.contrib.auth import get_user_model

from swh.web.common.models import (
    SaveAuthorizedOrigin,
    SaveUnauthorizedOrigin,
    SaveOriginRequest,
)
from swh.web.common.origin_save import can_save_origin
from swh.web.common.models import (
    SAVE_REQUEST_PENDING,
    SAVE_REQUEST_ACCEPTED,
    SAVE_REQUEST_REJECTED,
    SAVE_TASK_NOT_YET_SCHEDULED,
)
from swh.web.common.utils import reverse

_user_name = "swh-web-admin"
_user_mail = "admin@swh-web.org"
_user_password = "..34~pounds~BEAUTY~march~63.."

_authorized_origin_url = "https://scm.ourproject.org/anonscm/"
_unauthorized_origin_url = "https://www.softwareheritage.org/"


pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def populated_db():
    User = get_user_model()
    user = User.objects.create_user(_user_name, _user_mail, _user_password)
    user.is_staff = True
    user.save()
    SaveAuthorizedOrigin.objects.create(url=_authorized_origin_url)
    SaveUnauthorizedOrigin.objects.create(url=_unauthorized_origin_url)


def check_not_login(client, url):
    login_url = reverse("login", query_params={"next": url})
    response = client.post(url)
    assert response.status_code == 302
    assert unquote(response.url) == login_url


def test_add_authorized_origin_url(client):
    authorized_url = "https://scm.adullact.net/anonscm/"
    assert can_save_origin(authorized_url) == SAVE_REQUEST_PENDING

    url = reverse(
        "admin-origin-save-add-authorized-url", url_args={"origin_url": authorized_url}
    )

    check_not_login(client, url)

    assert can_save_origin(authorized_url) == SAVE_REQUEST_PENDING

    client.login(username=_user_name, password=_user_password)
    response = client.post(url)
    assert response.status_code == 200
    assert can_save_origin(authorized_url) == SAVE_REQUEST_ACCEPTED


def test_remove_authorized_origin_url(client):
    assert can_save_origin(_authorized_origin_url) == SAVE_REQUEST_ACCEPTED

    url = reverse(
        "admin-origin-save-remove-authorized-url",
        url_args={"origin_url": _authorized_origin_url},
    )

    check_not_login(client, url)

    assert can_save_origin(_authorized_origin_url) == SAVE_REQUEST_ACCEPTED

    client.login(username=_user_name, password=_user_password)
    response = client.post(url)
    assert response.status_code == 200
    assert can_save_origin(_authorized_origin_url) == SAVE_REQUEST_PENDING


def test_add_unauthorized_origin_url(client):
    unauthorized_url = "https://www.yahoo./"
    assert can_save_origin(unauthorized_url) == SAVE_REQUEST_PENDING

    url = reverse(
        "admin-origin-save-add-unauthorized-url",
        url_args={"origin_url": unauthorized_url},
    )

    check_not_login(client, url)

    assert can_save_origin(unauthorized_url) == SAVE_REQUEST_PENDING

    client.login(username=_user_name, password=_user_password)
    response = client.post(url)
    assert response.status_code == 200
    assert can_save_origin(unauthorized_url) == SAVE_REQUEST_REJECTED


def test_remove_unauthorized_origin_url(client):
    assert can_save_origin(_unauthorized_origin_url) == SAVE_REQUEST_REJECTED

    url = reverse(
        "admin-origin-save-remove-unauthorized-url",
        url_args={"origin_url": _unauthorized_origin_url},
    )

    check_not_login(client, url)

    assert can_save_origin(_unauthorized_origin_url) == SAVE_REQUEST_REJECTED

    client.login(username=_user_name, password=_user_password)
    response = client.post(url)
    assert response.status_code == 200
    assert can_save_origin(_unauthorized_origin_url) == SAVE_REQUEST_PENDING


def test_accept_pending_save_request(client, mocker):
    mock_scheduler = mocker.patch("swh.web.common.origin_save.scheduler")
    visit_type = "git"
    origin_url = "https://v2.pikacode.com/bthate/botlib.git"
    save_request_url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": visit_type, "origin_url": origin_url},
    )
    response = client.post(
        save_request_url, data={}, content_type="application/x-www-form-urlencoded"
    )
    assert response.status_code == 200
    assert response.data["save_request_status"] == SAVE_REQUEST_PENDING

    accept_request_url = reverse(
        "admin-origin-save-request-accept",
        url_args={"visit_type": visit_type, "origin_url": origin_url},
    )

    check_not_login(client, accept_request_url)

    tasks_data = [
        {
            "priority": "high",
            "policy": "oneshot",
            "type": "load-git",
            "arguments": {"kwargs": {"repo_url": origin_url}, "args": []},
            "status": "next_run_not_scheduled",
            "id": 1,
        }
    ]

    mock_scheduler.create_tasks.return_value = tasks_data
    mock_scheduler.get_tasks.return_value = tasks_data

    client.login(username=_user_name, password=_user_password)
    response = client.post(accept_request_url)
    assert response.status_code == 200

    response = client.get(save_request_url)
    assert response.status_code == 200
    assert response.data[0]["save_request_status"] == SAVE_REQUEST_ACCEPTED
    assert response.data[0]["save_task_status"] == SAVE_TASK_NOT_YET_SCHEDULED


def test_reject_pending_save_request(client, mocker):
    mock_scheduler = mocker.patch("swh.web.common.origin_save.scheduler")
    visit_type = "git"
    origin_url = "https://wikipedia.com"
    save_request_url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": visit_type, "origin_url": origin_url},
    )
    response = client.post(
        save_request_url, data={}, content_type="application/x-www-form-urlencoded"
    )
    assert response.status_code == 200
    assert response.data["save_request_status"] == SAVE_REQUEST_PENDING

    reject_request_url = reverse(
        "admin-origin-save-request-reject",
        url_args={"visit_type": visit_type, "origin_url": origin_url},
    )

    check_not_login(client, reject_request_url)

    client.login(username=_user_name, password=_user_password)
    response = client.post(reject_request_url)
    assert response.status_code == 200

    tasks_data = [
        {
            "priority": "high",
            "policy": "oneshot",
            "type": "load-git",
            "arguments": {"kwargs": {"repo_url": origin_url}, "args": []},
            "status": "next_run_not_scheduled",
            "id": 1,
        }
    ]

    mock_scheduler.create_tasks.return_value = tasks_data
    mock_scheduler.get_tasks.return_value = tasks_data

    response = client.get(save_request_url)
    assert response.status_code == 200
    assert response.data[0]["save_request_status"] == SAVE_REQUEST_REJECTED


def test_remove_save_request(client):
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

    client.login(username=_user_name, password=_user_password)
    response = client.post(remove_request_url)
    assert response.status_code == 200
    assert SaveOriginRequest.objects.count() == 0
