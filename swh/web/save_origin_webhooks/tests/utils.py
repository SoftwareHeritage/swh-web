# Copyright (C) 2022-2023  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import iso8601

from swh.web.save_code_now.models import SaveOriginRequest
from swh.web.save_code_now.origin_save import (
    SAVE_TASK_SUCCEEDED,
    WEBHOOK_REQUEST_COOLDOWN_INTERVAL,
    get_save_origin_request,
)
from swh.web.tests.helpers import check_api_post_response
from swh.web.utils import reverse


def django_http_headers(http_headers: Dict[str, Any]):
    return {f"HTTP_{k.upper().replace('-', '_')}": v for k, v in http_headers.items()}


def origin_save_webhook_receiver_test(
    forge_type: str,
    http_headers: Dict[str, Any],
    payload: Dict[str, Any],
    expected_origin_url: str,
    expected_visit_type: str,
    api_client,
    swh_scheduler,
):
    url = reverse(f"api-1-origin-save-webhook-{forge_type.lower()}")

    resp = check_api_post_response(
        api_client,
        url,
        status_code=200,
        data=payload,
        **django_http_headers(http_headers),
    )

    assert resp.data["origin_url"] == expected_origin_url
    assert resp.data["visit_type"] == expected_visit_type
    assert "id" in resp.data
    assert resp.data["request_url"] == reverse(
        "api-1-save-origin",
        url_args={"request_id": resp.data["id"]},
        request=resp.wsgi_request,  # type: ignore
    )

    tasks = swh_scheduler.search_tasks(task_type=f"load-{expected_visit_type}")
    assert tasks
    task = dict(tasks[0].items())
    assert task["arguments"]["kwargs"]["url"] == expected_origin_url

    request = SaveOriginRequest.objects.get(
        origin_url=expected_origin_url, visit_type=expected_visit_type
    )
    assert request.from_webhook


def origin_save_webhook_receiver_invalid_request_test(
    forge_type: str,
    http_headers: Dict[str, Any],
    payload: Dict[str, Any],
    api_client,
):
    url = reverse(f"api-1-origin-save-webhook-{forge_type.lower()}")

    resp = check_api_post_response(
        api_client,
        url,
        status_code=400,
        data=payload,
        **django_http_headers(http_headers),
    )

    assert resp.data == {
        "exception": "BadInputExc",
        "reason": (
            f"POST request was not sent by a {forge_type} webhook "
            "and has not been processed."
        ),
    }


def origin_save_webhook_receiver_invalid_event_test(
    forge_type: str,
    http_headers: Dict[str, Any],
    payload: Dict[str, Any],
    api_client,
):
    url = reverse(f"api-1-origin-save-webhook-{forge_type.lower()}")

    resp = check_api_post_response(
        api_client,
        url,
        status_code=400,
        data=payload,
        **django_http_headers(http_headers),
    )

    assert resp.data == {
        "exception": "BadInputExc",
        "reason": (
            f"Event sent by {forge_type} webhook is not a push one, request has "
            "not been processed."
        ),
    }


def origin_save_webhook_receiver_invalid_content_type_test(
    forge_type: str,
    http_headers: Dict[str, Any],
    payload: Dict[str, Any],
    api_client,
):
    url = reverse(f"api-1-origin-save-webhook-{forge_type.lower()}")

    bad_content_type = "application/x-www-form-urlencoded"
    http_headers["Content-Type"] = bad_content_type

    resp = check_api_post_response(
        api_client,
        url,
        status_code=400,
        data=payload,
        **django_http_headers(http_headers),
    )

    assert resp.data == {
        "exception": "BadInputExc",
        "reason": (
            f"Invalid content type '{bad_content_type}' for the POST request sent by "
            f"{forge_type} webhook, it should be 'application/json'."
        ),
    }


def origin_save_webhook_receiver_no_repo_url_test(
    forge_type: str,
    http_headers: Dict[str, Any],
    payload: Dict[str, Any],
    api_client,
):
    url = reverse(f"api-1-origin-save-webhook-{forge_type.lower()}")

    resp = check_api_post_response(
        api_client,
        url,
        status_code=400,
        data=payload,
        **django_http_headers(http_headers),
    )

    assert resp.data == {
        "exception": "BadInputExc",
        "reason": (
            f"Repository URL could not be extracted from {forge_type} webhook payload."
        ),
    }


def origin_save_webhook_receiver_private_repo_test(
    forge_type: str,
    http_headers: Dict[str, Any],
    payload: Dict[str, Any],
    api_client,
    expected_origin_url: str,
):
    url = reverse(f"api-1-origin-save-webhook-{forge_type.lower()}")

    resp = check_api_post_response(
        api_client,
        url,
        status_code=400,
        data=payload,
        **django_http_headers(http_headers),
    )

    assert resp.data == {
        "exception": "BadInputExc",
        "reason": (
            f"Repository {expected_origin_url} is private and cannot be cloned "
            "without authentication."
        ),
    }


def origin_save_webhook_receiver_cooldown_requests_test(
    forge_type: str,
    http_headers: Dict[str, Any],
    payload: Dict[str, Any],
    api_client,
    swh_scheduler,
):
    url = reverse(f"api-1-origin-save-webhook-{forge_type.lower()}")

    resp = check_api_post_response(
        api_client,
        url,
        status_code=200,
        data=payload,
        **django_http_headers(http_headers),
    )

    # first webhook request should be executed immediately
    first_sor = get_save_origin_request(resp.data["id"])
    task = swh_scheduler.get_tasks([first_sor["loading_task_id"]])[0]
    assert task["next_run"] <= datetime.now(tz=timezone.utc)

    # simulate first task successful execution
    last_sor = SaveOriginRequest.objects.first()
    assert last_sor is not None
    last_sor.loading_task_status = SAVE_TASK_SUCCEEDED
    last_sor.visit_date = datetime.now(tz=timezone.utc)
    last_sor.visit_status = "full"
    last_sor.save()

    resp = check_api_post_response(
        api_client,
        url,
        status_code=200,
        data=payload,
        **django_http_headers(http_headers),
    )

    second_sor = get_save_origin_request(resp.data["id"])
    task = swh_scheduler.get_tasks([second_sor["loading_task_id"]])[0]

    # second webhook request in a row should delay loading task execution
    assert second_sor["id"] != first_sor["id"]
    assert task["next_run"] > datetime.now(tz=timezone.utc)
    assert task["next_run"] == iso8601.parse_date(
        first_sor["save_request_date"]
    ) + timedelta(minutes=WEBHOOK_REQUEST_COOLDOWN_INTERVAL)

    resp = check_api_post_response(
        api_client,
        url,
        status_code=200,
        data=payload,
        **django_http_headers(http_headers),
    )

    third_sor = get_save_origin_request(resp.data["id"])

    # third webhook request in a row should return the same request as previously
    assert third_sor["id"] == second_sor["id"]

    # modify request dates in order for the next request to be accepted
    # and executed immediately
    for sor_id in (first_sor["id"], second_sor["id"]):
        sor = SaveOriginRequest.objects.get(id=sor_id)
        sor.request_date = sor.request_date - timedelta(
            minutes=WEBHOOK_REQUEST_COOLDOWN_INTERVAL
        )
        sor.loading_task_status = SAVE_TASK_SUCCEEDED
        sor.visit_date = datetime.now(tz=timezone.utc)
        sor.visit_status = "full"
        sor.save()
    swh_scheduler.set_status_tasks(
        [task["id"]],
        next_run=datetime.now(tz=timezone.utc)
        - timedelta(minutes=WEBHOOK_REQUEST_COOLDOWN_INTERVAL),
    )

    resp = check_api_post_response(
        api_client,
        url,
        status_code=200,
        data=payload,
        **django_http_headers(http_headers),
    )

    fourth_sor = get_save_origin_request(resp.data["id"])
    task = swh_scheduler.get_tasks([fourth_sor["loading_task_id"]])[0]

    # fourth webhhok request should be executed immediately
    assert fourth_sor["id"] != third_sor["id"]
    assert task["next_run"] <= datetime.now(tz=timezone.utc)
