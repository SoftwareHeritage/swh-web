# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Tuple

import requests

from rest_framework.request import Request

from swh.web.save_origin_webhooks.generic_receiver import OriginSaveWebhookReceiver


class SourceforgeOriginSaveWebhookReceiver(OriginSaveWebhookReceiver):
    FORGE_TYPE = "SourceForge"
    WEBHOOK_GUIDE_URL = (
        "https://sourceforge.net/blog/"
        "how-to-use-webhooks-for-git-mercurial-and-svn-repositories/"
    )
    REPO_TYPES = "git, hg or svn"

    SOURCE_FORGE_API_PROJECT_URL_PATTERN = (
        "https://sourceforge.net/rest/p/{project_name}"
    )

    def is_forge_request(self, request: Request) -> bool:
        return (
            request.headers.get("User-Agent", "")
            == "Allura Webhook (https://allura.apache.org/)"
        )

    def is_push_event(self, request: Request) -> bool:
        # SourceForge only support webhooks for push events
        return True

    def extract_repo_info(self, request: Request) -> Tuple[str, str, bool]:
        repo_url = ""
        visit_type = ""
        private = False
        project_full_name = request.data.get("repository", {}).get("full_name")
        if project_full_name:
            project_name = project_full_name.split("/")[2]
            project_api_url = self.SOURCE_FORGE_API_PROJECT_URL_PATTERN.format(
                project_name=project_name
            )
            response = requests.get(project_api_url)
            if response.ok:
                project_data = response.json()
                private = project_data.get("private", False)
                for tool in project_data.get("tools", []):
                    if tool.get("mount_point") == "code" and tool.get(
                        "url", ""
                    ).endswith(project_full_name):
                        repo_url = tool.get(
                            "clone_url_https_anon", tool.get("clone_url_ro", "")
                        )
                        visit_type = tool.get("name", "")

        return repo_url, visit_type, private


api_origin_save_webhook_sourceforge = SourceforgeOriginSaveWebhookReceiver()
