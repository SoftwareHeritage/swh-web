# Copyright (C) 2019-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta, timezone
from functools import partial
import re

import pytest
import requests

from swh.core.pytest_plugin import get_response_cb
from swh.web.common.models import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_TASK_FAILED,
    SAVE_TASK_RUNNING,
    SAVE_TASK_SUCCEEDED,
    SaveOriginRequest,
)
from swh.web.common.origin_save import (
    get_save_origin_requests,
    get_save_origin_task_info,
)
from swh.web.common.typing import OriginVisitInfo
from swh.web.config import get_config

_es_url = "http://esnode1.internal.softwareheritage.org:9200"
_es_workers_index_url = "%s/swh_workers-*" % _es_url

_origin_url = "https://gitlab.com/inkscape/inkscape"
_visit_type = "git"
_task_id = 203525448


@pytest.fixture(autouse=True)
def requests_mock_datadir(datadir, requests_mock_datadir):
    """Override default behavior to deal with post method"""
    cb = partial(get_response_cb, datadir=datadir)
    requests_mock_datadir.post(re.compile("https?://"), body=cb)
    return requests_mock_datadir


@pytest.mark.django_db
def test_get_save_origin_archived_task_info(mocker):
    _get_save_origin_task_info_test(mocker, task_archived=True)


@pytest.mark.django_db
def test_get_save_origin_task_full_info_with_es(mocker):
    _get_save_origin_task_info_test(mocker, es_available=True)


@pytest.mark.django_db
def test_get_save_origin_task_info_with_es(mocker):
    _get_save_origin_task_info_test(mocker, es_available=True, full_info=False)


@pytest.mark.django_db
def test_get_save_origin_task_info_without_es(mocker):
    _get_save_origin_task_info_test(mocker, es_available=False)


def _mock_scheduler(
    mocker, task_status="completed", task_run_status="eventful", task_archived=False
):
    mock_scheduler = mocker.patch("swh.web.common.origin_save.scheduler")
    task = {
        "arguments": {"args": [], "kwargs": {"repo_url": _origin_url},},
        "current_interval": timedelta(days=64),
        "id": _task_id,
        "next_run": datetime.now(tz=timezone.utc) + timedelta(days=64),
        "policy": "oneshot",
        "priority": "high",
        "retries_left": 0,
        "status": task_status,
        "type": "load-git",
    }
    mock_scheduler.get_tasks.return_value = [dict(task) if not task_archived else None]

    task_run = {
        "backend_id": "f00c712c-e820-41ce-a07c-9bf8df914205",
        "ended": datetime.now(tz=timezone.utc) + timedelta(minutes=5),
        "id": 654270631,
        "metadata": {},
        "scheduled": datetime.now(tz=timezone.utc),
        "started": None,
        "status": task_run_status,
        "task": _task_id,
    }
    mock_scheduler.get_task_runs.return_value = [
        dict(task_run) if not task_archived else None
    ]
    return task, task_run


def _get_save_origin_task_info_test(
    mocker, task_archived=False, es_available=True, full_info=True
):
    swh_web_config = get_config()

    if es_available:
        swh_web_config.update({"es_workers_index_url": _es_workers_index_url})
    else:
        swh_web_config.update({"es_workers_index_url": ""})

    sor = SaveOriginRequest.objects.create(
        request_date=datetime.now(tz=timezone.utc),
        visit_type=_visit_type,
        origin_url="https://gitlab.com/inkscape/inkscape",
        status=SAVE_REQUEST_ACCEPTED,
        visit_date=datetime.now(tz=timezone.utc) + timedelta(hours=1),
        loading_task_id=_task_id,
    )

    task, task_run = _mock_scheduler(mocker, task_archived=task_archived)

    es_response = requests.post("%s/_search" % _es_workers_index_url).json()

    task_exec_data = es_response["hits"]["hits"][-1]["_source"]

    sor_task_info = get_save_origin_task_info(sor.id, full_info=full_info)

    expected_result = (
        {
            "type": task["type"],
            "arguments": task["arguments"],
            "id": task["id"],
            "backend_id": task_run["backend_id"],
            "scheduled": task_run["scheduled"],
            "started": task_run["started"],
            "ended": task_run["ended"],
            "status": task_run["status"],
        }
        if not task_archived
        else {}
    )

    if es_available and not task_archived:
        expected_result.update(
            {
                "message": task_exec_data["message"],
                "name": task_exec_data["swh_task_name"],
                "worker": task_exec_data["hostname"],
            }
        )

    if not full_info:
        expected_result.pop("id", None)
        expected_result.pop("backend_id", None)
        expected_result.pop("worker", None)
        if "message" in expected_result:
            message = ""
            message_lines = expected_result["message"].split("\n")
            for line in message_lines:
                if line.startswith("Traceback"):
                    break
                message += f"{line}\n"
            message += message_lines[-1]
            expected_result["message"] = message

    assert sor_task_info == expected_result


@pytest.mark.django_db
def test_get_save_origin_requests_find_visit_date(mocker):
    # create a save request
    SaveOriginRequest.objects.create(
        request_date=datetime.now(tz=timezone.utc),
        visit_type=_visit_type,
        origin_url=_origin_url,
        status=SAVE_REQUEST_ACCEPTED,
        visit_date=None,
        loading_task_id=_task_id,
    )

    # mock scheduler and archive
    _mock_scheduler(mocker)
    mock_archive = mocker.patch("swh.web.common.origin_save.archive")
    mock_archive.lookup_origin.return_value = {"url": _origin_url}
    mock_get_origin_visits = mocker.patch(
        "swh.web.common.origin_save.get_origin_visits"
    )
    # create a visit for the save request
    visit_date = datetime.now(tz=timezone.utc).isoformat()
    visit_info = OriginVisitInfo(
        date=visit_date,
        formatted_date="",
        metadata={},
        origin=_origin_url,
        snapshot="",
        status="full",
        type=_visit_type,
        url="",
        visit=34,
    )
    mock_get_origin_visits.return_value = [visit_info]

    # check visit date has been correctly found
    sors = get_save_origin_requests(_visit_type, _origin_url)
    assert len(sors) == 1
    assert sors[0]["save_task_status"] == SAVE_TASK_SUCCEEDED
    assert sors[0]["visit_date"] == visit_date
    mock_get_origin_visits.assert_called_once()

    # check visit is not searched again when it has been found
    get_save_origin_requests(_visit_type, _origin_url)
    mock_get_origin_visits.assert_called_once()

    # check visit date are not searched for save requests older than
    # one month
    sor = SaveOriginRequest.objects.create(
        visit_type=_visit_type,
        origin_url=_origin_url,
        status=SAVE_REQUEST_ACCEPTED,
        loading_task_id=_task_id,
        visit_date=None,
    )
    sor.request_date = datetime.now(tz=timezone.utc) - timedelta(days=31)
    sor.save()

    _mock_scheduler(mocker, task_status="disabled", task_run_status="failed")

    sors = get_save_origin_requests(_visit_type, _origin_url)

    assert len(sors) == 2
    assert sors[0]["save_task_status"] == SAVE_TASK_FAILED
    assert sors[0]["visit_date"] is None
    mock_get_origin_visits.assert_called_once()


@pytest.mark.django_db
def test_get_save_origin_requests_no_visit_date_found(mocker):
    # create a save request
    SaveOriginRequest.objects.create(
        request_date=datetime.now(tz=timezone.utc),
        visit_type=_visit_type,
        origin_url=_origin_url,
        status=SAVE_REQUEST_ACCEPTED,
        visit_date=None,
        loading_task_id=_task_id,
    )

    # mock scheduler and archives
    _mock_scheduler(
        mocker, task_status="next_run_scheduled", task_run_status="scheduled"
    )
    mock_archive = mocker.patch("swh.web.common.origin_save.archive")
    mock_archive.lookup_origin.return_value = {"url": _origin_url}
    mock_get_origin_visits = mocker.patch(
        "swh.web.common.origin_save.get_origin_visits"
    )
    # create a visit for the save request with status created
    visit_date = datetime.now(tz=timezone.utc).isoformat()
    visit_info = OriginVisitInfo(
        date=visit_date,
        formatted_date="",
        metadata={},
        origin=_origin_url,
        snapshot=None,
        status="created",
        type=_visit_type,
        url="",
        visit=34,
    )
    mock_get_origin_visits.return_value = [visit_info]

    # check no visit date has been found
    sors = get_save_origin_requests(_visit_type, _origin_url)
    assert len(sors) == 1
    assert sors[0]["save_task_status"] == SAVE_TASK_RUNNING
    assert sors[0]["visit_date"] is None
    mock_get_origin_visits.assert_called_once()
