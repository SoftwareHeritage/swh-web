# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import os

import pytest

from swh.web.tests.helpers import check_api_post_responses
from swh.web.utils import reverse

from .utils import (
    django_http_headers,
    origin_save_webhook_receiver_invalid_content_type_test,
    origin_save_webhook_receiver_invalid_event_test,
    origin_save_webhook_receiver_invalid_request_test,
    origin_save_webhook_receiver_no_repo_url_test,
    origin_save_webhook_receiver_private_repo_test,
    origin_save_webhook_receiver_test,
)


@pytest.mark.django_db
def test_origin_save_github_webhook_receiver(api_client, swh_scheduler, datadir):
    with open(os.path.join(datadir, "github_webhook_payload.json"), "rb") as payload:
        origin_save_webhook_receiver_test(
            forge_type="GitHub",
            http_headers={
                "User-Agent": "GitHub-Hookshot/ede37db",
                "X-GitHub-Event": "push",
            },
            payload=json.load(payload),
            expected_origin_url="https://github.com/johndoe/webhook-test",
            expected_visit_type="git",
            api_client=api_client,
            swh_scheduler=swh_scheduler,
        )


def test_origin_save_github_webhook_receiver_invalid_request(
    api_client,
):
    origin_save_webhook_receiver_invalid_request_test(
        forge_type="GitHub",
        http_headers={},
        payload={},
        api_client=api_client,
    )


def test_origin_save_github_webhook_receiver_invalid_event(
    api_client,
):
    origin_save_webhook_receiver_invalid_event_test(
        forge_type="GitHub",
        http_headers={
            "User-Agent": "GitHub-Hookshot/ede37db",
            "X-GitHub-Event": "issues",
        },
        payload={},
        api_client=api_client,
    )


def test_origin_save_github_webhook_receiver_invalid_content_type(
    api_client,
):
    origin_save_webhook_receiver_invalid_content_type_test(
        forge_type="GitHub",
        http_headers={
            "User-Agent": "GitHub-Hookshot/ede37db",
            "X-GitHub-Event": "push",
        },
        payload={},
        api_client=api_client,
    )


def test_origin_save_github_webhook_receiver_no_repo_url(api_client, datadir):
    with open(os.path.join(datadir, "github_webhook_payload.json"), "rb") as payload:
        payload = json.load(payload)
        del payload["repository"]
        origin_save_webhook_receiver_no_repo_url_test(
            forge_type="GitHub",
            http_headers={
                "User-Agent": "GitHub-Hookshot/ede37db",
                "X-GitHub-Event": "push",
            },
            payload=payload,
            api_client=api_client,
        )


def test_origin_save_github_webhook_receiver_ping_event(api_client):
    url = reverse("api-1-origin-save-webhook-github")

    resp = check_api_post_responses(
        api_client,
        url,
        status_code=200,
        **django_http_headers(
            {
                "User-Agent": "GitHub-Hookshot/ede37db",
                "X-GitHub-Event": "ping",
            }
        ),
    )

    assert resp.data == {"message": "pong"}


def test_origin_save_github_webhook_receiver_private_repo(api_client, datadir):
    with open(os.path.join(datadir, "github_webhook_payload.json"), "rb") as payload:
        payload = json.load(payload)
        payload["repository"]["private"] = True
        origin_save_webhook_receiver_private_repo_test(
            forge_type="GitHub",
            http_headers={
                "User-Agent": "GitHub-Hookshot/ede37db",
                "X-GitHub-Event": "push",
            },
            payload=payload,
            api_client=api_client,
            expected_origin_url="https://github.com/johndoe/webhook-test",
        )
