# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta, timezone
import json

import pytest

from django.test import Client

from swh.web.common.models import SaveOriginRequest
from swh.web.common.origin_save import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_TASK_NOT_YET_SCHEDULED,
    SAVE_TASK_SUCCEEDED,
)
from swh.web.common.utils import reverse
from swh.web.settings.tests import save_origin_rate_post
from swh.web.tests.utils import (
    check_api_post_response,
    check_http_get_response,
    check_http_post_response,
)

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

    check_http_post_response(client, url, status_code=403)

    data = _get_csrf_token(client, reverse("origin-save"))
    check_api_post_response(client, url, data=data, status_code=200)


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
        check_api_post_response(client, url, data=data, status_code=200)

    check_api_post_response(client, url, data=data, status_code=429)


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
    check_api_post_response(client, url, data=data, status_code=500)


def test_old_save_url_redirection(client):
    url = reverse("browse-origin-save")
    redirect_url = reverse("origin-save")

    resp = check_http_get_response(client, url, status_code=302)
    assert resp["location"] == redirect_url


@pytest.mark.django_db
def test_save_origin_requests_list(client, mocker):
    visit_types = ("git", "svn", "hg")
    nb_origins_per_type = 10
    for visit_type in visit_types:
        for i in range(nb_origins_per_type):
            SaveOriginRequest.objects.create(
                request_date=datetime.now(tz=timezone.utc),
                visit_type=visit_type,
                origin_url=f"https://{visit_type}.example.org/project{i}",
                status=SAVE_REQUEST_ACCEPTED,
                visit_date=datetime.now(tz=timezone.utc) + timedelta(hours=1),
                loading_task_id=i,
                loading_task_status=SAVE_TASK_SUCCEEDED,
            )

    mock_scheduler = mocker.patch("swh.web.common.origin_save.scheduler")
    mock_scheduler.get_tasks.return_value = []
    mock_scheduler.get_task_runs.return_value = []

    # retrieve all save requests in 3 pages, sorted in descending order
    # of request creation
    for i, visit_type in enumerate(reversed(visit_types)):
        url = reverse(
            "origin-save-requests-list",
            url_args={"status": "all"},
            query_params={
                "draw": i + 1,
                "search[value]": "",
                "order[0][column]": "0",
                "columns[0][name]": "request_date",
                "order[0][dir]": "desc",
                "length": nb_origins_per_type,
                "start": i * nb_origins_per_type,
            },
        )

        resp = check_http_get_response(
            client, url, status_code=200, content_type="application/json"
        )
        sors = json.loads(resp.content.decode("utf-8"))
        assert sors["draw"] == i + 1
        assert sors["recordsFiltered"] == len(visit_types) * nb_origins_per_type
        assert sors["recordsTotal"] == len(visit_types) * nb_origins_per_type
        assert len(sors["data"]) == nb_origins_per_type
        assert all(d["visit_type"] == visit_type for d in sors["data"])

    # retrieve save requests filtered by visit type in a single page
    for i, visit_type in enumerate(reversed(visit_types)):
        url = reverse(
            "origin-save-requests-list",
            url_args={"status": "all"},
            query_params={
                "draw": i + 1,
                "search[value]": visit_type,
                "order[0][column]": "0",
                "columns[0][name]": "request_date",
                "order[0][dir]": "desc",
                "length": nb_origins_per_type,
                "start": 0,
            },
        )

        resp = check_http_get_response(
            client, url, status_code=200, content_type="application/json"
        )
        sors = json.loads(resp.content.decode("utf-8"))
        assert sors["draw"] == i + 1
        assert sors["recordsFiltered"] == nb_origins_per_type
        assert sors["recordsTotal"] == len(visit_types) * nb_origins_per_type
        assert len(sors["data"]) == nb_origins_per_type
        assert all(d["visit_type"] == visit_type for d in sors["data"])


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
