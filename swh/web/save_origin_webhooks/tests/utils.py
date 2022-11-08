# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict

from swh.web.tests.helpers import check_api_post_responses
from swh.web.utils import reverse


def _django_http_headers(http_headers: Dict[str, Any]):
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

    resp = check_api_post_responses(
        api_client,
        url,
        status_code=200,
        data=payload,
        **_django_http_headers(http_headers),
    )

    assert resp.data["origin_url"] == expected_origin_url
    assert resp.data["visit_type"] == expected_visit_type

    tasks = swh_scheduler.search_tasks(task_type=f"load-{expected_visit_type}")
    assert tasks
    task = dict(tasks[0].items())
    assert task["arguments"]["kwargs"]["url"] == expected_origin_url


def origin_save_webhook_receiver_invalid_request_test(
    forge_type: str,
    http_headers: Dict[str, Any],
    payload: Dict[str, Any],
    api_client,
):
    url = reverse(f"api-1-origin-save-webhook-{forge_type.lower()}")

    resp = check_api_post_responses(
        api_client,
        url,
        status_code=400,
        data=payload,
        **_django_http_headers(http_headers),
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

    resp = check_api_post_responses(
        api_client,
        url,
        status_code=400,
        data=payload,
        **_django_http_headers(http_headers),
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

    resp = check_api_post_responses(
        api_client,
        url,
        status_code=400,
        data=payload,
        **_django_http_headers(http_headers),
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

    resp = check_api_post_responses(
        api_client,
        url,
        status_code=400,
        data=payload,
        **_django_http_headers(http_headers),
    )

    assert resp.data == {
        "exception": "BadInputExc",
        "reason": (
            f"Repository URL could not be extracted from {forge_type} webhook payload."
        ),
    }
