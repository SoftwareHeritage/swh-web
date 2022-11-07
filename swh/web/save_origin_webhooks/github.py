# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Tuple

from rest_framework.request import Request

from swh.web.save_origin_webhooks.generic_receiver import OriginSaveWebhookReceiver


class GitHubOriginSaveWebhookReceiver(OriginSaveWebhookReceiver):
    FORGE_TYPE = "GitHub"
    WEBHOOK_GUIDE_URL = (
        "https://docs.github.com/en/developers/webhooks-and-events/"
        "webhooks/creating-webhooks#setting-up-a-webhook"
    )
    REPO_TYPES = "git"

    def is_forge_request(self, request: Request) -> bool:
        return (
            request.headers.get("User-Agent", "").startswith(
                f"{self.FORGE_TYPE}-Hookshot/"
            )
            and f"X-{self.FORGE_TYPE}-Event" in request.headers
        )

    def is_push_event(self, request: Request) -> bool:
        return request.headers[f"X-{self.FORGE_TYPE}-Event"] == "push"

    def extract_repo_url_and_visit_type(self, request: Request) -> Tuple[str, str]:
        return request.data.get("repository", {}).get("html_url", ""), "git"


api_origin_save_webhook_github = GitHubOriginSaveWebhookReceiver()
