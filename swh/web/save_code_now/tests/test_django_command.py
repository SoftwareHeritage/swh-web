# Copyright (C) 2021-2023  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta, timezone
import hashlib
from io import StringIO
import os

import pytest

from django.core.management import call_command

from swh.core.api.classes import stream_results
from swh.web.config import get_config
from swh.web.save_code_now.models import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_TASK_FAILED,
    SAVE_TASK_SCHEDULED,
    SAVE_TASK_SUCCEEDED,
    VISIT_STATUS_FAILED,
    VISIT_STATUS_FULL,
    VISIT_STATUS_PARTIAL,
    SaveOriginRequest,
)
from swh.web.utils.typing import SaveOriginRequestInfo

MODULE_FQDN = "swh.web.save_code_now.management.commands"
COMMAND_NAME = "refresh_savecodenow_statuses"

AUTHORIZED_ORIGIN_URL = "https://scm.ourproject.org/anonscm/%s"


@pytest.fixture
def mock_refresh(mocker):
    return mocker.patch(
        f"{MODULE_FQDN}.{COMMAND_NAME}.refresh_save_origin_request_statuses"
    )


@pytest.fixture
def mock_scheduler(mocker, swh_scheduler):
    mock_scheduler = mocker.patch("swh.web.save_code_now.origin_save.scheduler")
    mock_scheduler.return_value = swh_scheduler

    return mock_scheduler


@pytest.mark.parametrize("nb_results", [0, 10, 20])
def test_command_refresh_with_statuses_refreshed(
    mock_scheduler, mock_refresh, nb_results
):
    """Refresh status command reports non-terminal statuses updates."""
    # fake returned refreshed status for 'archives' visit type
    mock_refresh.return_value = [
        {
            "visit_type": "archives",
        }
    ] * nb_results

    out = StringIO()
    call_command(COMMAND_NAME, stdout=out)

    actual_output = out.getvalue()
    if nb_results > 0:
        assert f"updated {nb_results}" in actual_output
    else:
        assert "Nothing" in actual_output

    assert mock_scheduler.called
    assert mock_refresh.called


@pytest.fixture
def fake_refreshed_data():
    """Prepare test data within the scheduler and the swh-web model db"""
    duplicated_origin_url = AUTHORIZED_ORIGIN_URL % "specific-origin"
    entries = [
        {
            "visit_type": "archives",  # ignored from recurring task scheduling
            "visit_status": VISIT_STATUS_FULL,
            "task_status": SAVE_TASK_SUCCEEDED,
        },
        {
            "visit_type": "hg",  # scheduled as recurring task
            "visit_status": VISIT_STATUS_PARTIAL,
            "task_status": SAVE_TASK_SUCCEEDED,
        },
        {
            "visit_type": "svn",  # scheduled as recurring task
            "visit_status": VISIT_STATUS_PARTIAL,
            "task_status": SAVE_TASK_SCHEDULED,
        },
        {
            "visit_type": "svn",  # ignored from recurring task scheduling
            "visit_status": VISIT_STATUS_FAILED,
            "task_status": SAVE_TASK_FAILED,
        },
        {
            "visit_type": "hg",  # ignored from recurring task scheduling
            "visit_status": "created",
            "task_status": SAVE_TASK_SCHEDULED,
        },
    ] + [
        {
            "visit_type": "git",
            "visit_status": VISIT_STATUS_FULL,
            "task_status": SAVE_TASK_SUCCEEDED,
            "origin": duplicated_origin_url,
        }
    ] * 3  # only 1 of the origin duplicates will be scheduled as recurring task

    time_now = datetime.now(tz=timezone.utc) - timedelta(days=len(entries))
    return [
        SaveOriginRequestInfo(
            visit_type=meta["visit_type"],
            visit_status=meta["visit_status"],
            origin_url=(
                meta["origin"] if "origin" in meta else AUTHORIZED_ORIGIN_URL % i
            ),
            save_request_date=time_now + timedelta(days=i - 1),
            save_request_status=SAVE_REQUEST_ACCEPTED,
            visit_date=time_now + timedelta(days=i),
            save_task_status=meta["task_status"],
            id=i,
            loading_task_id=i,
            note=None,
        )
        for i, meta in enumerate(entries)
    ]


def test_command_refresh_with_recurrent_tasks_scheduling(
    mock_scheduler, mock_refresh, fake_refreshed_data, swh_scheduler
):
    """Refresh status command report updates of statuses. The successful ones without the
    type 'archived' are also scheduled recurringly.

    """
    mock_refresh.return_value = fake_refreshed_data

    # only visit types (git, hg, svn) types with status (full, partial) are taken into
    # account for scheduling, so only 3 of those matches in the fake data set.
    expected_nb_scheduled = 0

    origins = set()
    expected_nb_scheduled = 0
    for entry in fake_refreshed_data:
        visit_type = entry["visit_type"]
        if visit_type == "archives":  # only deal with git, svn, hg
            continue
        if entry["visit_status"] not in ("partial", "full"):
            continue
        origin = entry["origin_url"]
        if (visit_type, origin) in origins:
            continue
        origins.add((visit_type, origin))
        expected_nb_scheduled += 1

    assert expected_nb_scheduled == 3

    out = StringIO()
    call_command(COMMAND_NAME, stdout=out)

    actual_output = out.getvalue()
    assert f"Successfully updated {len(fake_refreshed_data)}" in actual_output
    assert f"{expected_nb_scheduled} origins were also scheduled for recurrent visits"

    lister = swh_scheduler.get_or_create_lister(
        name="save-code-now", instance_name=get_config()["instance_name"]
    )

    result = list(stream_results(swh_scheduler.get_listed_origins, lister.id))
    assert len(result) == expected_nb_scheduled

    assert mock_scheduler.called
    assert mock_refresh.called


DUMP_SCN_DATA_COMMAND_NAME = "dump_savecodenow_data"


@pytest.mark.django_db
def test_dump_savecodenow_data_command(tmp_path):
    SaveOriginRequest.objects.create(
        request_date=datetime.now(tz=timezone.utc),
        visit_type="git",
        origin_url="https://git.example.com/user/project",
        status=SAVE_REQUEST_ACCEPTED,
        visit_status=VISIT_STATUS_FULL,
    )
    SaveOriginRequest.objects.create(
        request_date=datetime.now(tz=timezone.utc),
        visit_type="git",
        origin_url="https://git.example.com/user/project",
        status=SAVE_REQUEST_ACCEPTED,
        visit_status=VISIT_STATUS_FULL,
        user_ids="16787568",
    )

    output_path = os.path.join(tmp_path, "output.csv")

    call_command(DUMP_SCN_DATA_COMMAND_NAME, output_file=output_path)

    with open(output_path, "r") as csv_file:
        csv = csv_file.read()

    expected_content = (
        "request_date,visit_type,origin_url,request_status,"
        "visit_status,from_webhook,user_id\n"
    )
    for scn_request in SaveOriginRequest.objects.all():
        expected_content += (
            ",".join(
                [
                    str(scn_request.request_date),
                    scn_request.visit_type,
                    scn_request.origin_url,
                    scn_request.status,
                    scn_request.visit_status,
                    str(scn_request.from_webhook).lower(),
                    (
                        hashlib.sha1(scn_request.user_ids.encode()).hexdigest()[:7]
                        if scn_request.user_ids
                        else ""
                    ),
                ]
            )
            + "\n"
        )

    assert csv == expected_content
