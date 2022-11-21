# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Tuple

from rest_framework.request import Request

from swh.web.save_origin_webhooks.generic_receiver import OriginSaveWebhookReceiver


class BitbucketOriginSaveWebhookReceiver(OriginSaveWebhookReceiver):
    FORGE_TYPE = "Bitbucket"
    WEBHOOK_GUIDE_URL = (
        "https://support.atlassian.com/bitbucket-cloud/docs/manage-webhooks/"
    )
    REPO_TYPES = "git"

    def is_forge_request(self, request: Request) -> bool:
        return (
            request.headers.get("User-Agent", "").startswith(
                f"{self.FORGE_TYPE}-Webhooks/"
            )
            and "X-Event-Key" in request.headers
        )

    def is_push_event(self, request: Request) -> bool:
        return request.headers["X-Event-Key"] == "repo:push"

    def extract_repo_info(self, request: Request) -> Tuple[str, str, bool]:
        repo_url = (
            request.data.get("repository", {})
            .get("links", {})
            .get("html", {})
            .get("href", "")
        )
        if repo_url:
            repo_url += ".git"

        private = request.data.get("repository", {}).get("is_private", False)

        return repo_url, "git", private


api_origin_save_webhook_bitbucket = BitbucketOriginSaveWebhookReceiver()
