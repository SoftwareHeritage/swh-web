# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import os

import pytest
import requests

from .utils import (
    origin_save_webhook_receiver_invalid_content_type_test,
    origin_save_webhook_receiver_invalid_request_test,
    origin_save_webhook_receiver_no_repo_url_test,
    origin_save_webhook_receiver_private_repo_test,
    origin_save_webhook_receiver_test,
)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "payload_file,expected_origin_url,expected_visit_type",
    [
        (
            "sourceforge_webhook_payload_hg.json",
            "http://hg.code.sf.net/p/webhook-test-hg/code",
            "hg",
        ),
        (
            "sourceforge_webhook_payload_git.json",
            "https://git.code.sf.net/p/webhook-test-git/code",
            "git",
        ),
        (
            "sourceforge_webhook_payload_svn.json",
            "https://svn.code.sf.net/p/webhook-test-svn/code/",
            "svn",
        ),
    ],
)
def test_origin_save_sourceforge_webhook_receiver(
    api_client,
    swh_scheduler,
    datadir,
    requests_mock_datadir,
    payload_file,
    expected_origin_url,
    expected_visit_type,
):
    with open(os.path.join(datadir, payload_file), "rb") as payload:
        origin_save_webhook_receiver_test(
            forge_type="SourceForge",
            http_headers={
                "User-Agent": "Allura Webhook (https://allura.apache.org/)",
            },
            payload=json.load(payload),
            expected_origin_url=expected_origin_url,
            expected_visit_type=expected_visit_type,
            api_client=api_client,
            swh_scheduler=swh_scheduler,
        )


def test_origin_save_sourceforge_webhook_receiver_invalid_request(
    api_client,
):
    origin_save_webhook_receiver_invalid_request_test(
        forge_type="SourceForge",
        http_headers={},
        payload={},
        api_client=api_client,
    )


def test_origin_save_sourceforge_webhook_receiver_invalid_content_type(
    api_client,
):
    origin_save_webhook_receiver_invalid_content_type_test(
        forge_type="SourceForge",
        http_headers={
            "User-Agent": "Allura Webhook (https://allura.apache.org/)",
        },
        payload={},
        api_client=api_client,
    )


def test_origin_save_sourceforge_webhook_receiver_no_repo_url(api_client, datadir):
    with open(
        os.path.join(datadir, "sourceforge_webhook_payload_git.json"), "rb"
    ) as payload:
        payload = json.load(payload)
        del payload["repository"]
        origin_save_webhook_receiver_no_repo_url_test(
            forge_type="SourceForge",
            http_headers={
                "User-Agent": "Allura Webhook (https://allura.apache.org/)",
            },
            payload=payload,
            api_client=api_client,
        )


@pytest.mark.parametrize(
    "payload_file,origin_url,visit_type",
    [
        (
            "sourceforge_webhook_payload_hg.json",
            "http://hg.code.sf.net/p/webhook-test-hg/code",
            "hg",
        ),
        (
            "sourceforge_webhook_payload_git.json",
            "https://git.code.sf.net/p/webhook-test-git/code",
            "git",
        ),
        (
            "sourceforge_webhook_payload_svn.json",
            "https://svn.code.sf.net/p/webhook-test-svn/code/",
            "svn",
        ),
    ],
)
def test_origin_save_sourceforge_webhook_receiver_private_repo(
    api_client,
    datadir,
    requests_mock_datadir,
    requests_mock,
    payload_file,
    origin_url,
    visit_type,
):
    # override sourceforge REST API response
    repo_data_url = f"https://sourceforge.net/rest/p/webhook-test-{visit_type}"
    repo_data = requests.get(repo_data_url).json()
    repo_data["private"] = True
    requests_mock.get(repo_data_url, json=repo_data)

    with open(os.path.join(datadir, payload_file), "rb") as payload:
        origin_save_webhook_receiver_private_repo_test(
            forge_type="SourceForge",
            http_headers={
                "User-Agent": "Allura Webhook (https://allura.apache.org/)",
            },
            payload=json.load(payload),
            expected_origin_url=origin_url,
            api_client=api_client,
        )
