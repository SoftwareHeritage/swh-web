# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import abc
from typing import Any, Dict, Tuple

from rest_framework.request import Request

from swh.web.api.apidoc import api_doc
from swh.web.api.apiurls import APIUrls, api_route
from swh.web.save_code_now.origin_save import create_save_origin_request
from swh.web.utils import reverse
from swh.web.utils.exc import BadInputExc

webhooks_api_urls = APIUrls()


SUPPORTED_FORGE_TYPES = set()


class OriginSaveWebhookReceiver(abc.ABC):
    FORGE_TYPE: str
    WEBHOOK_GUIDE_URL: str
    REPO_TYPES: str

    @abc.abstractmethod
    def is_forge_request(self, request: Request) -> bool:
        ...

    def is_ping_event(self, request: Request) -> bool:
        return False

    @abc.abstractmethod
    def is_push_event(self, request: Request) -> bool:
        ...

    @abc.abstractmethod
    def extract_repo_info(self, request: Request) -> Tuple[str, str, bool]:
        """Extract and return a tuple (repository_url, visit_type, private) from
        the forge webhook payload."""
        ...

    def __init__(self):
        self.__doc__ = f"""
        .. http:post:: /api/1/origin/save/webhook/{self.FORGE_TYPE.lower()}/

            Webhook receiver for {self.FORGE_TYPE} to request or update the archival of
            a repository when new commits are pushed to it.

            To add such webhook to one of your {self.REPO_TYPES} repository hosted on
            {self.FORGE_TYPE}, please follow `{self.FORGE_TYPE}'s webhooks guide
            <{self.WEBHOOK_GUIDE_URL}>`_.

            The expected content type for the webhook payload must be ``application/json``.

            :>json number id: the save request identifier
            :>json string request_url: Web API URL to follow up on that request
            :>json string origin_url: the url of the origin to save
            :>json string visit_type: the type of visit to perform
            :>json string save_request_date: the date (in iso format) the save
                request was issued
            :>json string save_request_status: the status of the save request,
                either **accepted**, **rejected** or **pending**

            :statuscode 200: save request for repository has been successfully created
                from the webhook payload.
            :statuscode 400: no save request has been created due to invalid POST
                request or missing data in webhook payload
        """
        self.__name__ = "api_origin_save_webhook_{self.FORGE_TYPE.lower()}"
        SUPPORTED_FORGE_TYPES.add(self.FORGE_TYPE.lower())
        api_doc(
            f"/origin/save/webhook/{self.FORGE_TYPE.lower()}/",
            category="Request archival",
        )(self)
        api_route(
            f"/origin/save/webhook/{self.FORGE_TYPE.lower()}/",
            f"api-1-origin-save-webhook-{self.FORGE_TYPE.lower()}",
            methods=["POST"],
            api_urls=webhooks_api_urls,
        )(self)

    def __call__(
        self,
        request: Request,
    ) -> Dict[str, Any]:

        if not self.is_forge_request(request):
            raise BadInputExc(
                f"POST request was not sent by a {self.FORGE_TYPE} webhook and "
                "has not been processed."
            )

        if self.is_ping_event(request):
            return {"message": "pong"}

        if not self.is_push_event(request):
            raise BadInputExc(
                f"Event sent by {self.FORGE_TYPE} webhook is not a push one, request "
                "has not been processed."
            )

        content_type = request.headers.get("Content-Type")
        if content_type and not content_type.startswith("application/json"):
            raise BadInputExc(
                f"Invalid content type '{content_type}' for the POST request sent by "
                f"{self.FORGE_TYPE} webhook, it should be 'application/json'."
            )

        repo_url, visit_type, private = self.extract_repo_info(request)
        if not repo_url:
            raise BadInputExc(
                f"Repository URL could not be extracted from {self.FORGE_TYPE} webhook "
                f"payload."
            )
        if not visit_type:
            raise BadInputExc(
                f"Visit type could not be determined for repository {repo_url}."
            )
        if private:
            raise BadInputExc(
                f"Repository {repo_url} is private and cannot be cloned without authentication."
            )

        save_request = create_save_origin_request(
            visit_type=visit_type,
            origin_url=repo_url,
            from_webhook=True,
            webhook_origin=self.FORGE_TYPE.lower(),
        )

        return {
            "id": save_request["id"],
            "request_url": reverse(
                "api-1-save-origin",
                url_args={"request_id": save_request["id"]},
                request=request,
            ),
            "origin_url": save_request["origin_url"],
            "visit_type": save_request["visit_type"],
            "save_request_date": save_request["save_request_date"],
            "save_request_status": save_request["save_request_status"],
        }
