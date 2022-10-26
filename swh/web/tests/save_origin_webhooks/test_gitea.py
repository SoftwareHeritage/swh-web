# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import os

import pytest

from swh.web.save_code_now.models import SaveAuthorizedOrigin

from .utils import (
    origin_save_webhook_receiver_invalid_content_type_test,
    origin_save_webhook_receiver_invalid_event_test,
    origin_save_webhook_receiver_invalid_request_test,
    origin_save_webhook_receiver_no_repo_url_test,
    origin_save_webhook_receiver_test,
)


@pytest.mark.django_db
def test_origin_save_gitea_webhook_receiver(api_client, swh_scheduler, datadir):
    SaveAuthorizedOrigin.objects.create(url="https://try.gitea.io/")
    with open(os.path.join(datadir, "gitea_webhook_payload.json"), "rb") as payload:
        origin_save_webhook_receiver_test(
            forge_type="Gitea",
            http_headers={
                "X-Gitea-Event": "push",
            },
            payload=json.load(payload),
            expected_origin_url="https://try.gitea.io/johndoe/webhook-test.git",
            expected_visit_type="git",
            api_client=api_client,
            swh_scheduler=swh_scheduler,
        )


def test_origin_save_gitea_webhook_receiver_invalid_request(
    api_client,
):
    origin_save_webhook_receiver_invalid_request_test(
        forge_type="Gitea",
        http_headers={},
        payload={},
        api_client=api_client,
    )


def test_origin_save_gitea_webhook_receiver_invalid_event(
    api_client,
):
    origin_save_webhook_receiver_invalid_event_test(
        forge_type="Gitea",
        http_headers={
            "X-Gitea-Event": "issues",
        },
        payload={},
        api_client=api_client,
    )


def test_origin_save_gitea_webhook_receiver_invalid_content_type(
    api_client,
):
    origin_save_webhook_receiver_invalid_content_type_test(
        forge_type="Gitea",
        http_headers={
            "X-Gitea-Event": "push",
        },
        payload={},
        api_client=api_client,
    )


def test_origin_save_gitea_webhook_receiver_no_repo_url(api_client, datadir):
    with open(os.path.join(datadir, "gitea_webhook_payload.json"), "rb") as payload:
        payload = json.load(payload)
        del payload["repository"]
        origin_save_webhook_receiver_no_repo_url_test(
            forge_type="Gitea",
            http_headers={
                "X-Gitea-Event": "push",
            },
            payload=payload,
            api_client=api_client,
        )
