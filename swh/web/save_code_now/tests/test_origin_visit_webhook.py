# Copyright (C) 2023-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import uuid

import pytest

from swh.model.hashutil import hash_to_bytes
from swh.model.model import Origin, OriginVisit, OriginVisitStatus
from swh.storage.utils import now
from swh.web.save_code_now.models import (
    SAVE_TASK_PENDING,
    SAVE_TASK_RUNNING,
    SAVE_TASK_SUCCEEDED,
    SaveAuthorizedOrigin,
    SaveOriginRequest,
)
from swh.web.save_code_now.origin_visit_webhook import webhooks_available
from swh.web.tests.helpers import check_api_post_responses, check_http_post_response
from swh.web.utils import reverse
from swh.web.utils.typing import OriginExistenceCheckInfo

pytestmark = [
    pytest.mark.django_db,
    pytest.mark.skipif(not webhooks_available, reason="swh-webhooks is not available"),
]


@pytest.fixture(autouse=True)
def populated_db():
    SaveAuthorizedOrigin.objects.create(url="https://git.example.org/")


def _send_origin_visit_webhook(
    client,
    mocker,
    payload,
    add_webhook_headers=True,
    invalid_signature=False,
    status_code=200,
):
    from swh.webhooks.utils import sign_webhook_payload

    webhook_url = reverse("origin-save-visit-webhook")
    webhook_timestamp = now()
    webhook_secret = "whsec_" + "c" * 32
    webhook_msgid = "some-id"
    if invalid_signature:
        webhook_signature = "foo"
    else:
        webhook_signature = sign_webhook_payload(
            payload=json.dumps(payload),
            timestamp=webhook_timestamp,
            msg_id=webhook_msgid,
            secret=webhook_secret,
        )

    mocker.patch(
        "swh.web.save_code_now.origin_visit_webhook.get_config"
    ).return_value = {"save_code_now_webhook_secret": webhook_secret}

    webhook_headers = {}
    if add_webhook_headers:
        webhook_headers = {
            "HTTP_WEBHOOK_ID": webhook_msgid,
            "HTTP_WEBHOOK_TIMESTAMP": str(int(webhook_timestamp.timestamp())),
            "HTTP_WEBHOOK_SIGNATURE": webhook_signature,
        }

    return check_http_post_response(
        client,
        webhook_url,
        status_code=status_code,
        data=payload,
        HTTP_X_SWH_EVENT="origin.visit",
        **webhook_headers,
    )


def test_save_origin_visit_webhook_invalid_request(client):
    webhook_url = reverse("origin-save-visit-webhook")
    resp = check_http_post_response(client, webhook_url, status_code=400, data={})
    assert b"POST request is not a Software Heritage webhook" in resp.content


def test_save_origin_visit_webhook_missing_webhook_headers(client, mocker):
    resp = _send_origin_visit_webhook(
        client,
        mocker,
        status_code=400,
        payload={"origin_url": "https://git.example.org/user/project"},
        add_webhook_headers=False,
    )
    assert b"Webhook body verification" in resp.content


def test_save_origin_visit_webhook_invalid_signature(client, mocker):
    resp = _send_origin_visit_webhook(
        client,
        mocker,
        status_code=400,
        payload={"origin_url": "https://git.example.org/user/project"},
        invalid_signature=True,
    )
    assert b"Webhook body verification" in resp.content


def test_save_origin_visit_webhook_noop(client, mocker):
    origin_url = "https://git.example.org/user/project"
    resp = _send_origin_visit_webhook(
        client,
        mocker,
        payload={"origin_url": origin_url},
    )
    assert (
        resp.content.decode()
        == f"No Save Code Now request to update for origin {origin_url}"
    )


def test_save_origin_visit_webhook(
    api_client, client, archive_data, mocker, swh_scheduler, snapshot
):
    origin_url = "https://git.example.org/user/project"
    mock_origin_exists = mocker.patch("swh.web.save_code_now.origin_save.origin_exists")
    mock_origin_exists.return_value = OriginExistenceCheckInfo(
        origin_url=origin_url, exists=True, last_modified=None, content_length=None
    )

    # create save request
    url = reverse(
        "api-1-save-origin", url_args={"visit_type": "git", "origin_url": origin_url}
    )
    resp = check_api_post_responses(api_client, url, status_code=200)

    save_request = SaveOriginRequest.objects.first()
    assert save_request.loading_task_status == SAVE_TASK_PENDING
    assert save_request.snapshot_swhid is None

    # simulate loading task scheduling and execution
    task_id = resp.data["loading_task_id"]
    backend_id = str(uuid.uuid4())
    swh_scheduler.schedule_task_run(task_id, backend_id)
    swh_scheduler.start_task_run(backend_id)

    archive_data.origin_add([Origin(url=origin_url)])
    date = now()
    visit = OriginVisit(origin=origin_url, date=date, type="git")
    visit = archive_data.origin_visit_add([visit])[0]
    visit_status = OriginVisitStatus(
        origin=origin_url,
        visit=visit.visit,
        date=date,
        status="ongoing",
        snapshot=None,
    )
    archive_data.origin_visit_status_add([visit_status])

    # send webhook notifying origin visit is ongoing
    webhook_payload = {
        "origin_url": origin_url,
        "visit_type": "git",
        "visit_date": date.isoformat(),
        "visit_status": "ongoing",
        "snapshot_swhid": None,
    }

    assert (
        _send_origin_visit_webhook(client, mocker, webhook_payload).content.decode()
        == f"Status of Save Code Now request updated for origin {origin_url}."
    )

    # check save request status was updated
    save_request = SaveOriginRequest.objects.first()
    assert save_request.loading_task_status == SAVE_TASK_RUNNING
    assert save_request.snapshot_swhid is None

    # simulate end of loading task execution
    swh_scheduler.end_task_run(backend_id, "eventful")
    date = now()
    visit_status = OriginVisitStatus(
        origin=origin_url,
        visit=visit.visit,
        date=date,
        status="full",
        snapshot=hash_to_bytes(snapshot),
    )
    archive_data.origin_visit_status_add([visit_status])

    # send webhook notifying origin visit was successful
    snapshot_swhid = f"swh:1:snp:{snapshot}"
    webhook_payload = {
        "origin_url": origin_url,
        "visit_type": "git",
        "visit_date": date.isoformat(),
        "visit_status": "full",
        "snapshot_swhid": snapshot_swhid,
    }

    assert _send_origin_visit_webhook(
        client, mocker, webhook_payload
    ).content.decode() == (
        f"Status of Save Code Now request updated for origin {origin_url}.\n"
        "Origin was also scheduled for recurrent visits."
    )

    # check save request status was updated
    save_request = SaveOriginRequest.objects.first()
    assert save_request.loading_task_status == SAVE_TASK_SUCCEEDED
    assert save_request.snapshot_swhid == snapshot_swhid

    # check next webhook processing is a noop
    assert (
        _send_origin_visit_webhook(client, mocker, webhook_payload).content.decode()
        == f"No Save Code Now request to update for origin {origin_url}"
    )
