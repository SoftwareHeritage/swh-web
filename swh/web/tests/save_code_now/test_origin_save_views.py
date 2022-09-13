# Copyright (C) 2019-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta, timezone
import json

import pytest

from swh.auth.django.utils import oidc_user_from_profile
from swh.web.save_code_now.models import SaveOriginRequest
from swh.web.save_code_now.origin_save import SAVE_REQUEST_ACCEPTED, SAVE_TASK_SUCCEEDED
from swh.web.tests.helpers import check_http_get_response
from swh.web.utils import reverse

VISIT_TYPES = ("git", "svn", "hg", "cvs", "bzr")
PRIVILEGED_VISIT_TYPES = tuple(list(VISIT_TYPES) + ["archives"])


def test_old_save_url_redirection(client):
    url = reverse("browse-origin-save")
    redirect_url = reverse("origin-save")

    resp = check_http_get_response(client, url, status_code=302)
    assert resp["location"] == redirect_url


@pytest.mark.django_db
def test_save_origin_requests_list(client, mocker):
    nb_origins_per_type = 10
    for visit_type in VISIT_TYPES:
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

    mock_scheduler = mocker.patch("swh.web.save_code_now.origin_save.scheduler")
    mock_scheduler.get_tasks.return_value = []
    mock_scheduler.get_task_runs.return_value = []

    # retrieve all save requests in 3 pages, sorted in descending order
    # of request creation
    for i, visit_type in enumerate(reversed(VISIT_TYPES)):
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
        assert sors["recordsFiltered"] == len(VISIT_TYPES) * nb_origins_per_type
        assert sors["recordsTotal"] == len(VISIT_TYPES) * nb_origins_per_type
        assert len(sors["data"]) == nb_origins_per_type
        assert all(d["visit_type"] == visit_type for d in sors["data"])

    # retrieve save requests filtered by visit type in a single page
    for i, visit_type in enumerate(reversed(VISIT_TYPES)):
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
        assert sors["recordsTotal"] == len(VISIT_TYPES) * nb_origins_per_type
        assert len(sors["data"]) == nb_origins_per_type
        assert all(d["visit_type"] == visit_type for d in sors["data"])


@pytest.mark.django_db
def test_save_origin_requests_list_user_filter(client, mocker, keycloak_oidc):

    # anonymous user created a save request
    sor = SaveOriginRequest.objects.create(
        request_date=datetime.now(tz=timezone.utc),
        visit_type="svn",
        origin_url="https://svn.example.org/user/project",
        status=SAVE_REQUEST_ACCEPTED,
        visit_date=datetime.now(tz=timezone.utc) + timedelta(hours=1),
        loading_task_id=1,
        loading_task_status=SAVE_TASK_SUCCEEDED,
    )

    # authenticated user created a save request
    user = oidc_user_from_profile(keycloak_oidc, keycloak_oidc.login())
    client.login(code="", code_verifier="", redirect_uri="")

    sor = SaveOriginRequest.objects.create(
        request_date=datetime.now(tz=timezone.utc),
        visit_type="git",
        origin_url="https://git.example.org/user/project",
        status=SAVE_REQUEST_ACCEPTED,
        visit_date=datetime.now(tz=timezone.utc) + timedelta(hours=1),
        loading_task_id=2,
        loading_task_status=SAVE_TASK_SUCCEEDED,
        user_ids=f'"{user.id}"',
    )

    # filter save requests according to user id
    url = reverse(
        "origin-save-requests-list",
        url_args={"status": "all"},
        query_params={
            "draw": 1,
            "search[value]": "",
            "order[0][column]": "0",
            "columns[0][name]": "request_date",
            "order[0][dir]": "desc",
            "length": 10,
            "start": "0",
            "user_requests_only": "1",
        },
    )

    resp = check_http_get_response(
        client, url, status_code=200, content_type="application/json"
    )
    sors = json.loads(resp.content.decode("utf-8"))
    assert sors["recordsFiltered"] == 1
    assert sors["recordsTotal"] == 2
    assert sors["data"][0] == sor.to_dict()
