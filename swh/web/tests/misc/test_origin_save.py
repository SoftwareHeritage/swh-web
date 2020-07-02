# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from datetime import datetime

from django.test import Client

from swh.web.common.origin_save import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_TASK_NOT_YET_SCHEDULED,
)
from swh.web.common.utils import reverse
from swh.web.settings.tests import save_origin_rate_post


visit_type = "git"
origin = {"url": "https://github.com/python/cpython"}


@pytest.fixture
def client():
    return Client(enforce_csrf_checks=True)


def test_save_request_form_csrf_token(client, mocker):
    mock_create_save_origin_request = mocker.patch(
        "swh.web.misc.origin_save.create_save_origin_request"
    )
    _mock_create_save_origin_request(mock_create_save_origin_request)

    url = reverse(
        "origin-save-request",
        url_args={"visit_type": visit_type, "origin_url": origin["url"]},
    )

    resp = client.post(url)
    assert resp.status_code == 403

    data = _get_csrf_token(client, reverse("origin-save"))
    resp = client.post(url, data=data)
    assert resp.status_code == 200


def test_save_request_form_rate_limit(client, mocker):
    mock_create_save_origin_request = mocker.patch(
        "swh.web.misc.origin_save.create_save_origin_request"
    )
    _mock_create_save_origin_request(mock_create_save_origin_request)

    url = reverse(
        "origin-save-request",
        url_args={"visit_type": visit_type, "origin_url": origin["url"]},
    )

    data = _get_csrf_token(client, reverse("origin-save"))
    for _ in range(save_origin_rate_post):
        resp = client.post(url, data=data)
        assert resp.status_code == 200

    resp = client.post(url, data=data)
    assert resp.status_code == 429


def test_save_request_form_server_error(client, mocker):
    mock_create_save_origin_request = mocker.patch(
        "swh.web.misc.origin_save.create_save_origin_request"
    )
    mock_create_save_origin_request.side_effect = Exception("Server error")

    url = reverse(
        "origin-save-request",
        url_args={"visit_type": visit_type, "origin_url": origin["url"]},
    )

    data = _get_csrf_token(client, reverse("origin-save"))

    resp = client.post(url, data=data)
    assert resp.status_code == 500


def test_old_save_url_redirection(client):
    url = reverse("browse-origin-save")
    resp = client.get(url)
    assert resp.status_code == 302
    redirect_url = reverse("origin-save")
    assert resp["location"] == redirect_url


def _get_csrf_token(client, url):
    resp = client.get(url)
    return {"csrfmiddlewaretoken": resp.cookies["csrftoken"].value}


def _mock_create_save_origin_request(mock):
    expected_data = {
        "visit_type": visit_type,
        "origin_url": origin["url"],
        "save_request_date": datetime.now().isoformat(),
        "save_request_status": SAVE_REQUEST_ACCEPTED,
        "save_task_status": SAVE_TASK_NOT_YET_SCHEDULED,
        "visit_date": None,
    }
    mock.return_value = expected_data
