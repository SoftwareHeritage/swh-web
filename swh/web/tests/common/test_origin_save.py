# Copyright (C) 2019-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta, timezone
from functools import partial
import re
from typing import Optional

import iso8601
import pytest
import requests

from swh.core.pytest_plugin import get_response_cb
from swh.web.common.exc import BadInputExc
from swh.web.common.models import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_TASK_FAILED,
    SAVE_TASK_RUNNING,
    SAVE_TASK_SCHEDULED,
    SAVE_TASK_SUCCEEDED,
    VISIT_STATUS_FULL,
    SaveOriginRequest,
)
from swh.web.common.origin_save import (
    _check_origin_exists,
    _check_visit_type_savable,
    _visit_type_task,
    _visit_type_task_privileged,
    get_savable_visit_types,
    get_save_origin_requests,
    get_save_origin_task_info,
    origin_exists,
    refresh_save_origin_request_statuses,
)
from swh.web.common.typing import (
    OriginExistenceCheckInfo,
    OriginVisitInfo,
    SaveOriginRequestInfo,
)
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
    mocker,
    task_status="completed",
    task_run_status="eventful",
    task_archived=False,
    visit_started_date=None,
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
        "started": visit_started_date,
        "status": task_run_status,
        "task": _task_id,
    }
    mock_scheduler.get_task_runs.return_value = [
        dict(task_run) if not task_archived else None
    ]
    return task, task_run


@pytest.mark.parametrize(
    "wrong_type,privileged_user",
    [
        ("dummy", True),
        ("dumb", False),
        ("archives", False),  # when no privilege, this is rejected
    ],
)
def test__check_visit_type_savable(wrong_type, privileged_user):

    with pytest.raises(BadInputExc, match="Allowed types"):
        _check_visit_type_savable(wrong_type, privileged_user)

    # when privileged_user, the following is accepted though
    _check_visit_type_savable("archives", True)


def test_get_savable_visit_types():
    default_list = list(_visit_type_task.keys())

    assert set(get_savable_visit_types()) == set(default_list)

    privileged_list = default_list.copy()
    privileged_list += list(_visit_type_task_privileged.keys())

    assert set(get_savable_visit_types(privileged_user=True)) == set(privileged_list)


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
            "visit_status": sor.visit_status,
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


def _get_save_origin_requests(
    mocker, load_status, visit_status, request_date: Optional[datetime] = None
):
    """Wrapper around the get_origin_save_origin_request call.

    """
    SaveOriginRequest.objects.create(
        request_date=datetime.now(tz=timezone.utc),
        visit_type=_visit_type,
        visit_status=visit_status,
        origin_url=_origin_url,
        status=SAVE_REQUEST_ACCEPTED,
        visit_date=None,
        loading_task_id=_task_id,
    )

    # mock scheduler and archives
    _mock_scheduler(
        mocker, task_status="next_run_scheduled", task_run_status=load_status
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
        snapshot="",  # make mypy happy
        status=visit_status,
        type=_visit_type,
        url="",
        visit=34,
    )
    mock_get_origin_visits.return_value = [visit_info]

    sors = get_save_origin_requests(_visit_type, _origin_url)
    mock_get_origin_visits.assert_called_once()

    return sors


@pytest.mark.parametrize("visit_date", [None, "some-date"])
def test_from_save_origin_request_to_save_request_info_dict(visit_date):
    """Ensure save request to json serializable dict is fine

    """
    request_date = datetime.now(tz=timezone.utc)
    _visit_date = request_date + timedelta(minutes=5) if visit_date else None
    request_date = datetime.now(tz=timezone.utc)
    sor = SaveOriginRequest(
        request_date=request_date,
        visit_type=_visit_type,
        visit_status=VISIT_STATUS_FULL,
        origin_url=_origin_url,
        status=SAVE_REQUEST_ACCEPTED,
        loading_task_status=None,
        visit_date=_visit_date,
        loading_task_id=1,
    )

    assert sor.to_dict() == SaveOriginRequestInfo(
        id=sor.id,
        origin_url=sor.origin_url,
        visit_type=sor.visit_type,
        save_request_date=sor.request_date.isoformat(),
        save_request_status=sor.status,
        save_task_status=sor.loading_task_status,
        visit_status=sor.visit_status,
        visit_date=_visit_date.isoformat() if _visit_date else None,
        loading_task_id=sor.loading_task_id,
    )


def test__check_origin_exists_404(requests_mock):
    url_ko = "https://example.org/some-inexistant-url"
    requests_mock.head(url_ko, status_code=404)

    with pytest.raises(BadInputExc, match="not exist"):
        _check_origin_exists(url_ko)


def test__check_origin_exists_200(requests_mock):
    url = "https://example.org/url"
    requests_mock.head(url, status_code=200)

    # passes the check
    actual_metadata = _check_origin_exists(url)

    # and we actually may have retrieved some metadata on the origin
    assert actual_metadata == origin_exists(url)


def test_origin_exists_404(requests_mock):
    """Origin which does not exist should be reported as inexistent"""
    url_ko = "https://example.org/some-inexistant-url"
    requests_mock.head(url_ko, status_code=404)

    actual_result = origin_exists(url_ko)
    assert actual_result == OriginExistenceCheckInfo(
        origin_url=url_ko, exists=False, last_modified=None, content_length=None,
    )


def test_origin_exists_200_no_data(requests_mock):
    """Existing origin should be reported as such (no extra information)"""
    url = "http://example.org/real-url"
    requests_mock.head(
        url, status_code=200,
    )

    actual_result = origin_exists(url)
    assert actual_result == OriginExistenceCheckInfo(
        origin_url=url, exists=True, last_modified=None, content_length=None,
    )


def test_origin_exists_200_with_data(requests_mock):
    """Existing origin should be reported as such (+ extra information)"""
    url = "http://example.org/real-url"
    requests_mock.head(
        url,
        status_code=200,
        headers={
            "content-length": "10",
            "last-modified": "Sun, 21 Aug 2011 16:26:32 GMT",
        },
    )

    actual_result = origin_exists(url)
    assert actual_result == OriginExistenceCheckInfo(
        origin_url=url,
        exists=True,
        content_length=10,
        last_modified="2011-08-21T16:26:32",
    )


def test_origin_exists_200_with_data_unexpected_date_format(requests_mock):
    """Existing origin should be ok, unexpected last modif time result in no time"""
    url = "http://example.org/real-url2"
    # this is parsable but not as expected
    unexpected_format_date = "Sun, 21 Aug 2021 16:26:32"
    requests_mock.head(
        url, status_code=200, headers={"last-modified": unexpected_format_date,},
    )

    actual_result = origin_exists(url)
    # so the resulting date is None
    assert actual_result == OriginExistenceCheckInfo(
        origin_url=url, exists=True, content_length=None, last_modified=None,
    )


@pytest.mark.django_db
@pytest.mark.parametrize("visit_status", ["created", "ongoing",])
def test_get_save_origin_requests_no_visit_date_found(mocker, visit_status):
    """Uneventful visits with failed visit status are marked as failed

    """
    sors = _get_save_origin_requests(
        mocker, load_status="scheduled", visit_status=visit_status,
    )
    # check no visit date has been found
    assert len(sors) == 1
    assert sors[0]["save_task_status"] == SAVE_TASK_RUNNING
    assert sors[0]["visit_date"] is None
    assert sors[0]["visit_status"] == visit_status


@pytest.mark.django_db
@pytest.mark.parametrize("visit_status", ["not_found", "failed",])
def test_get_save_origin_requests_no_failed_status_override(mocker, visit_status):
    """Uneventful visits with failed statuses (failed, not found) are marked as failed

    """
    sors = _get_save_origin_requests(
        mocker, load_status="uneventful", visit_status=visit_status
    )
    assert len(sors) == 1

    assert sors[0]["save_task_status"] == SAVE_TASK_FAILED
    visit_date = sors[0]["visit_date"]
    if visit_status == "failed":
        assert visit_date is None
    else:
        assert visit_date is not None

    sors = get_save_origin_requests(_visit_type, _origin_url)
    assert len(sors) == 1
    assert sors[0]["save_task_status"] == SAVE_TASK_FAILED
    assert sors[0]["visit_status"] == visit_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "load_status,visit_status",
    [("eventful", "full"), ("eventful", "partial"), ("uneventful", "partial"),],
)
def test_get_visit_info_for_save_request_succeeded(mocker, load_status, visit_status):
    """Nominal scenario, below 30 days, returns something"""
    sors = _get_save_origin_requests(
        mocker, load_status=load_status, visit_status=visit_status
    )
    assert len(sors) == 1

    assert sors[0]["save_task_status"] == SAVE_TASK_SUCCEEDED
    assert sors[0]["visit_date"] is not None
    assert sors[0]["visit_status"] == visit_status

    sors = get_save_origin_requests(_visit_type, _origin_url)
    assert sors[0]["save_task_status"] == SAVE_TASK_SUCCEEDED
    assert sors[0]["visit_status"] == visit_status


@pytest.mark.django_db
@pytest.mark.parametrize("load_status", ["eventful", "uneventful",])
def test_get_visit_info_incomplete_visit_still_successful(mocker, load_status):
    """Incomplete visit information, yet the task is updated partially

    """
    sors = _get_save_origin_requests(
        mocker, load_status=load_status, visit_status=None,
    )
    assert len(sors) == 1

    assert sors[0]["save_task_status"] == SAVE_TASK_SUCCEEDED
    # As the entry is missing the following information though
    assert sors[0]["visit_date"] is None
    assert sors[0]["visit_status"] is None

    # It's still detected as to be updated by the refresh routine
    sors = refresh_save_origin_request_statuses()
    assert len(sors) == 1

    assert sors[0]["save_task_status"] == SAVE_TASK_SUCCEEDED
    assert sors[0]["visit_date"] is None
    assert sors[0]["visit_status"] is None


@pytest.mark.django_db
def test_refresh_in_progress_save_request_statuses(mocker, api_client, archive_data):
    """Refresh a pending save origins requests and update if the status changes
    """
    date_now = datetime.now(tz=timezone.utc)
    date_pivot = date_now - timedelta(days=30)
    visit_started_date = date_now - timedelta(minutes=1)

    # returned visit status
    sors = _get_save_origin_requests(
        mocker, load_status=SAVE_TASK_SCHEDULED, visit_status="created",
    )
    assert len(sors) == 1

    # make the scheduler return a running event
    _mock_scheduler(
        mocker,
        task_status="next_run_scheduled",
        task_run_status="started",
        visit_started_date=visit_started_date,
    )

    # The visit is detected but still running
    sors = refresh_save_origin_request_statuses()
    assert len(sors) == 1

    for sor in sors:
        assert iso8601.parse_date(sor["save_request_date"]) >= date_pivot
        # The status is updated
        assert sor["save_task_status"] == SAVE_TASK_RUNNING
        # but the following entries are missing so it's not updated
        assert sor["visit_date"] is None
        assert sor["visit_status"] == "created"

    # make the visit status completed
    # make the scheduler return a running event
    _mock_scheduler(
        mocker,
        task_status="completed",
        task_run_status="eventful",
        visit_started_date=visit_started_date,
    )

    # This time around, the origin returned will have all information updated
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
        snapshot="",  # make mypy happy
        status="full",
        type=_visit_type,
        url="",
        visit=34,
    )
    mock_get_origin_visits.return_value = [visit_info]

    # Detected entry, this time it should be updated
    sors = refresh_save_origin_request_statuses()
    assert len(sors) == 1

    for sor in sors:
        assert iso8601.parse_date(sor["save_request_date"]) >= date_pivot
        # as it turns out, in this test, this won't update anything as no new status got
        # returned by the scheduler
        assert sor["save_task_status"] == SAVE_TASK_SUCCEEDED
        assert sor["visit_date"] == visit_date
        assert sor["visit_status"] == "full"

    # Once in final state, a sor should not be updated anymore
    sors = refresh_save_origin_request_statuses()
    assert len(sors) == 0


@pytest.mark.django_db
def test_refresh_save_request_statuses(mocker, api_client, archive_data):
    """Refresh filters save origins requests and update if changes

    """
    date_now = datetime.now(tz=timezone.utc)
    date_pivot = date_now - timedelta(days=30)
    # returned visit status
    sors = _get_save_origin_requests(
        mocker, load_status=SAVE_TASK_SCHEDULED, visit_status=None,
    )
    assert len(sors) == 1

    # no changes so refresh does detect the entry but does nothing
    sors = refresh_save_origin_request_statuses()
    assert len(sors) == 1

    for sor in sors:
        assert iso8601.parse_date(sor["save_request_date"]) >= date_pivot
        # as it turns out, in this test, this won't update anything as no new status got
        # returned by the scheduler
        assert sor["save_task_status"] == SAVE_TASK_SCHEDULED
        # Information is empty
        assert sor["visit_date"] is None
        assert sor["visit_status"] is None

    # make the scheduler return eventful event for that origin
    _mock_scheduler(mocker)
    # updates will be detected, entry should be updated but we are still missing info
    sors = refresh_save_origin_request_statuses()
    assert len(sors) == 1

    for sor in sors:
        assert iso8601.parse_date(sor["save_request_date"]) >= date_pivot
        # The status is updated
        assert sor["save_task_status"] == SAVE_TASK_SUCCEEDED
        # but the following entries are missing so it's not updated
        assert sor["visit_date"] is None
        assert sor["visit_status"] is None

    # This time around, the origin returned will have all information updated
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
        snapshot="",  # make mypy happy
        status="full",
        type=_visit_type,
        url="",
        visit=34,
    )
    mock_get_origin_visits.return_value = [visit_info]

    # Detected entry, this time it should be updated
    sors = refresh_save_origin_request_statuses()
    assert len(sors) == 1

    for sor in sors:
        assert iso8601.parse_date(sor["save_request_date"]) >= date_pivot
        # as it turns out, in this test, this won't update anything as no new status got
        # returned by the scheduler
        assert sor["save_task_status"] == SAVE_TASK_SUCCEEDED
        assert sor["visit_date"] == visit_date
        assert sor["visit_status"] == "full"

    # This time, nothing left to update
    sors = refresh_save_origin_request_statuses()
    assert len(sors) == 0
