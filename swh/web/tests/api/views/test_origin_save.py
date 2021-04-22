# Copyright (C) 2018-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta

import pytest

from django.utils import timezone

from swh.web.common.models import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_REQUEST_PENDING,
    SAVE_REQUEST_REJECTED,
    SAVE_TASK_FAILED,
    SAVE_TASK_NOT_CREATED,
    SAVE_TASK_NOT_YET_SCHEDULED,
    SAVE_TASK_SCHEDULED,
    SAVE_TASK_SUCCEEDED,
    VISIT_STATUS_FAILED,
    VISIT_STATUS_FULL,
    SaveOriginRequest,
    SaveUnauthorizedOrigin,
)
from swh.web.common.utils import reverse
from swh.web.tests.utils import check_api_get_responses, check_api_post_responses

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def populated_db():
    SaveUnauthorizedOrigin.objects.create(url="https://github.com/user/illegal_repo")
    SaveUnauthorizedOrigin.objects.create(url="https://gitlab.com/user_to_exclude")


def test_invalid_visit_type(api_client):
    url = reverse(
        "api-1-save-origin",
        url_args={
            "visit_type": "foo",
            "origin_url": "https://github.com/torvalds/linux",
        },
    )
    check_api_get_responses(api_client, url, status_code=400)


def test_invalid_origin_url(api_client):
    url = reverse(
        "api-1-save-origin", url_args={"visit_type": "git", "origin_url": "bar"}
    )
    check_api_get_responses(api_client, url, status_code=400)


def check_created_save_request_status(
    api_client,
    mocker,
    origin_url,
    expected_request_status,
    scheduler_task_status=None,
    scheduler_task_run_status=None,
    expected_task_status=None,
    visit_date=None,
):

    mock_scheduler = mocker.patch("swh.web.common.origin_save.scheduler")
    if scheduler_task_status is None:
        mock_scheduler.get_tasks.return_value = []
    else:
        mock_scheduler.get_tasks.return_value = [
            {
                "priority": "high",
                "policy": "oneshot",
                "type": "load-git",
                "arguments": {"kwargs": {"repo_url": origin_url}, "args": []},
                "status": scheduler_task_status,
                "id": 1,
            }
        ]

    if scheduler_task_run_status is None:
        mock_scheduler.get_task_runs.return_value = []
    else:
        mock_scheduler.get_task_runs.return_value = [
            {
                "backend_id": "f00c712c-e820-41ce-a07c-9bf8df914205",
                "ended": datetime.now(tz=timezone.utc) + timedelta(minutes=5),
                "id": 1,
                "metadata": {},
                "scheduled": datetime.now(tz=timezone.utc),
                "started": None,
                "status": scheduler_task_run_status,
                "task": 1,
            }
        ]

    mock_scheduler.create_tasks.return_value = [
        {
            "priority": "high",
            "policy": "oneshot",
            "type": "load-git",
            "arguments": {"kwargs": {"repo_url": origin_url}, "args": []},
            "status": "next_run_not_scheduled",
            "id": 1,
        }
    ]

    url = reverse(
        "api-1-save-origin", url_args={"visit_type": "git", "origin_url": origin_url}
    )

    mock_visit_date = mocker.patch(
        ("swh.web.common.origin_save." "_get_visit_info_for_save_request")
    )
    mock_visit_date.return_value = (visit_date, None)

    if expected_request_status != SAVE_REQUEST_REJECTED:
        response = check_api_post_responses(api_client, url, data=None, status_code=200)
        assert response.data["save_request_status"] == expected_request_status
        assert response.data["save_task_status"] == expected_task_status
    else:
        check_api_post_responses(api_client, url, data=None, status_code=403)


def check_save_request_status(
    api_client,
    mocker,
    origin_url,
    expected_request_status,
    expected_task_status,
    scheduler_task_status="next_run_not_scheduled",
    scheduler_task_run_status=None,
    visit_date=None,
    visit_status=None,
):
    mock_scheduler = mocker.patch("swh.web.common.origin_save.scheduler")
    mock_scheduler.get_tasks.return_value = [
        {
            "priority": "high",
            "policy": "oneshot",
            "type": "load-git",
            "arguments": {"kwargs": {"repo_url": origin_url}, "args": []},
            "status": scheduler_task_status,
            "id": 1,
        }
    ]

    if scheduler_task_run_status is None:
        mock_scheduler.get_task_runs.return_value = []
    else:
        mock_scheduler.get_task_runs.return_value = [
            {
                "backend_id": "f00c712c-e820-41ce-a07c-9bf8df914205",
                "ended": datetime.now(tz=timezone.utc) + timedelta(minutes=5),
                "id": 1,
                "metadata": {},
                "scheduled": datetime.now(tz=timezone.utc),
                "started": None,
                "status": scheduler_task_run_status,
                "task": 1,
            }
        ]

    url = reverse(
        "api-1-save-origin", url_args={"visit_type": "git", "origin_url": origin_url}
    )

    mock_visit_date = mocker.patch(
        ("swh.web.common.origin_save." "_get_visit_info_for_save_request")
    )
    mock_visit_date.return_value = (visit_date, visit_status)
    response = check_api_get_responses(api_client, url, status_code=200)
    save_request_data = response.data[0]

    assert save_request_data["save_request_status"] == expected_request_status
    assert save_request_data["save_task_status"] == expected_task_status
    assert save_request_data["visit_status"] == visit_status

    # Check that save task status is still available when
    # the scheduler task has been archived
    mock_scheduler.get_tasks.return_value = []
    response = check_api_get_responses(api_client, url, status_code=200)
    save_request_data = response.data[0]
    assert save_request_data["save_task_status"] == expected_task_status
    assert save_request_data["visit_status"] == visit_status


def test_save_request_rejected(api_client, mocker):
    origin_url = "https://github.com/user/illegal_repo"
    check_created_save_request_status(
        api_client, mocker, origin_url, expected_request_status=SAVE_REQUEST_REJECTED,
    )
    check_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_REJECTED,
        expected_task_status=SAVE_TASK_NOT_CREATED,
    )


def test_save_request_pending(api_client, mocker):
    origin_url = "https://unkwownforge.com/user/repo"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_PENDING,
        expected_task_status=SAVE_TASK_NOT_CREATED,
    )
    check_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_PENDING,
        expected_task_status=SAVE_TASK_NOT_CREATED,
    )


def test_save_request_succeed(api_client, mocker):
    origin_url = "https://github.com/Kitware/CMake"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
    )
    check_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_SCHEDULED,
        scheduler_task_status="next_run_scheduled",
        scheduler_task_run_status="scheduled",
    )
    check_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_SUCCEEDED,
        scheduler_task_status="completed",
        scheduler_task_run_status="eventful",
        visit_date=None,
    )
    visit_date = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    check_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_SUCCEEDED,
        scheduler_task_status="completed",
        scheduler_task_run_status="eventful",
        visit_date=visit_date,
        visit_status=VISIT_STATUS_FULL,
    )


def test_save_request_failed(api_client, mocker):
    origin_url = "https://gitlab.com/inkscape/inkscape"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
    )
    check_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_SCHEDULED,
        scheduler_task_status="next_run_scheduled",
        scheduler_task_run_status="scheduled",
    )
    check_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_FAILED,
        scheduler_task_status="disabled",
        scheduler_task_run_status="failed",
        visit_status=VISIT_STATUS_FAILED,
    )


def test_create_save_request_only_when_needed(api_client, mocker):
    origin_url = "https://github.com/webpack/webpack"
    SaveOriginRequest.objects.create(
        visit_type="git",
        origin_url=origin_url,
        status=SAVE_REQUEST_ACCEPTED,
        loading_task_id=56,
    )

    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        scheduler_task_status="next_run_not_scheduled",
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
    )

    sors = list(
        SaveOriginRequest.objects.filter(visit_type="git", origin_url=origin_url)
    )
    assert len(sors) == 1

    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        scheduler_task_status="next_run_scheduled",
        scheduler_task_run_status="scheduled",
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_SCHEDULED,
    )
    sors = list(
        SaveOriginRequest.objects.filter(visit_type="git", origin_url=origin_url)
    )
    assert len(sors) == 1

    visit_date = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        scheduler_task_status="completed",
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
        visit_date=visit_date,
    )
    sors = list(
        SaveOriginRequest.objects.filter(visit_type="git", origin_url=origin_url)
    )
    # check_api_post_responses sends two POST requests to check YAML and JSON response
    assert len(sors) == 3

    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        scheduler_task_status="disabled",
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
    )
    sors = list(
        SaveOriginRequest.objects.filter(visit_type="git", origin_url=origin_url)
    )
    assert len(sors) == 5


def test_get_save_requests_unknown_origin(api_client):
    unknown_origin_url = "https://gitlab.com/foo/bar"
    url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": "git", "origin_url": unknown_origin_url},
    )
    response = check_api_get_responses(api_client, url, status_code=404)
    assert response.data == {
        "exception": "NotFoundExc",
        "reason": (
            "No save requests found for visit of type " "git on origin with url %s."
        )
        % unknown_origin_url,
    }
