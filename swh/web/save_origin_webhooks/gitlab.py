# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Tuple

from rest_framework.request import Request

from swh.web.save_origin_webhooks.generic_receiver import OriginSaveWebhookReceiver


class GitlabOriginSaveWebhookReceiver(OriginSaveWebhookReceiver):
    FORGE_TYPE = "GitLab"
    WEBHOOK_GUIDE_URL = (
        "https://docs.gitlab.com/ee/user/project/integrations/"
        "webhooks.html#configure-a-webhook-in-gitlab"
    )
    REPO_TYPES = "git"

    def is_forge_request(self, request: Request) -> bool:
        return (
            request.headers.get("User-Agent", "").startswith(f"{self.FORGE_TYPE}/")
            and "X-Gitlab-Event" in request.headers
        )

    def is_push_event(self, request: Request) -> bool:
        return request.headers["X-Gitlab-Event"] == "Push Hook"

    def extract_repo_info(self, request: Request) -> Tuple[str, str, bool]:
        repo_url = request.data.get("repository", {}).get("git_http_url", "")
        # visibility_level values: 0 = private, 10 = internal, 20 = public
        visibility_level = request.data.get("repository", {}).get(
            "visibility_level", 20
        )
        return repo_url, "git", visibility_level != 20


api_origin_save_webhook_gitlab = GitlabOriginSaveWebhookReceiver()
