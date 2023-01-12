# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
from typing import Optional, cast

from django.conf import settings
from rest_framework.request import Request

from swh.model.hashutil import hash_to_hex
from swh.model.swhids import CoreSWHID
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import APIUrls, api_route
from swh.web.auth.utils import (
    API_SAVE_ORIGIN_PERMISSION,
    SWH_AMBASSADOR_PERMISSION,
    privileged_user,
)
from swh.web.save_code_now.origin_save import (
    create_save_origin_request,
    get_savable_visit_types,
    get_save_origin_request,
    get_save_origin_requests,
)
from swh.web.utils import reverse


def _savable_visit_types() -> str:
    docstring = ""
    if os.environ.get("DJANGO_SETTINGS_MODULE") != "swh.web.settings.tests":
        visit_types = sorted(get_savable_visit_types())
        docstring = ""
        for visit_type in visit_types[:-1]:
            docstring += f"**{visit_type}**, "
        docstring += f"and **{visit_types[-1]}**"
    return docstring


def _webhook_info_doc() -> str:
    docstring = ""
    if "swh.web.save_origin_webhooks" in settings.SWH_DJANGO_APPS:
        docstring = """
        :>json boolean from_webhook: indicates if the save request was created
            from a popular forge webhook receiver
            (see :http:post:`/api/1/origin/save/webhook/github/` for instance)
        :>json string webhook_origin: indicates which forge type sent the webhook,
            currently the supported types are:"""

        # instantiate webhook receivers
        from swh.web.save_origin_webhooks import urls  # noqa
        from swh.web.save_origin_webhooks.generic_receiver import SUPPORTED_FORGE_TYPES

        webhook_forge_types = sorted(list(SUPPORTED_FORGE_TYPES))
        for visit_type in webhook_forge_types[:-1]:
            docstring += f"**{visit_type}**, "
        docstring += f"and **{webhook_forge_types[-1]}**"
    return docstring


save_code_now_api_urls = APIUrls()


@api_route(
    r"/origin/save/(?P<visit_type>.+)/url/(?P<origin_url>.+)/",
    "api-1-save-origin",
    methods=["GET", "POST"],
    throttle_scope="swh_save_origin",
    never_cache=True,
    api_urls=save_code_now_api_urls,
)
@api_route(
    r"/origin/save/(?P<request_id>[0-9]+)/",
    "api-1-save-origin",
    methods=["GET"],
    throttle_scope="swh_save_origin",
    never_cache=True,
    api_urls=save_code_now_api_urls,
)
@api_doc("/origin/save/", category="Request archival")
@format_docstring(
    visit_types=_savable_visit_types(), webhook_info_doc=_webhook_info_doc()
)
def api_save_origin(
    request: Request,
    visit_type: Optional[str] = None,
    origin_url: Optional[str] = None,
    request_id: int = 0,
):
    """
    .. http:get:: /api/1/origin/save/(visit_type)/url/(origin_url)/
    .. http:post:: /api/1/origin/save/(visit_type)/url/(origin_url)/
    .. http:get:: /api/1/origin/save/(request_id)/

        Request the saving of a software origin into the archive
        or check the status of previously created save requests.

        That endpoint enables to create a saving task for a software origin
        through a POST request.

        Depending of the provided origin url, the save request can either be:

            * immediately **accepted**, for well known code hosting providers
              like for instance GitHub or GitLab
            * **rejected**, in case the url is blacklisted by Software Heritage
            * **put in pending state** until a manual check is done in order to
              determine if it can be loaded or not

        Once a saving request has been accepted, its associated saving task
        status can then be checked through a GET request on the same url.
        Returned status can either be:

            * **not created**: no saving task has been created
            * **not yet scheduled**: saving task has been created but its
              execution has not yet been scheduled
            * **scheduled**: the task execution has been scheduled
            * **succeeded**: the saving task has been successfully executed
            * **failed**: the saving task has been executed but it failed

        When issuing a POST request an object will be returned while a GET
        request will return an array of objects (as multiple save requests
        might have been submitted for the same origin).

        It is also possible to get info about a specific save request by
        sending a GET request to the ``/api/1/origin/save/(request_id)/``
        endpoint.

        :param string visit_type: the type of visit to perform
            (currently the supported types are {visit_types})
        :param string origin_url: the url of the origin to save
        :param number request_id: a save request identifier

        {common_headers}

        :>json number id: the save request identifier
        :>json string request_url: Web API URL to follow up on that request
        :>json string origin_url: the url of the origin to save
        :>json string visit_type: the type of visit to perform
        :>json string save_request_date: the date (in iso format) the save
            request was issued
        :>json string save_request_status: the status of the save request,
            either **accepted**, **rejected** or **pending**
        :>json string save_task_status: the status of the origin saving task,
            either **not created**, **not yet scheduled**, **scheduled**,
            **succeeded** or **failed**
        :>json string visit_date: the date (in iso format) of the visit if a visit
            occurred, null otherwise.
        :>json string visit_status: the status of the visit, either **full**,
            **partial**, **not_found** or **failed** if a visit occurred, null
            otherwise.
        :>json string note: optional note giving details about the save request,
            for instance why it has been rejected
        :>json string snapshot_swhid: SWHID of snapshot associated to the visit
            (null if it is missing or unknown)
        :>json string snapshot_url: Web API URL to retrieve snapshot data
        {webhook_info_doc}

        :statuscode 200: no error
        :statuscode 400: an invalid visit type or origin url has been provided
        :statuscode 403: the provided origin url is blacklisted
        :statuscode 404: no save requests have been found for a given origin

    """

    def _cleanup_and_enrich_sor_data(sor):
        if "swh.web.save_origin_webhooks" not in settings.SWH_DJANGO_APPS:
            del sor["from_webhook"]
            del sor["webhook_origin"]
        if sor["snapshot_swhid"]:
            snapshot_id = hash_to_hex(
                CoreSWHID.from_string(sor["snapshot_swhid"]).object_id
            )
            sor["snapshot_url"] = reverse(
                "api-1-snapshot", url_args={"snapshot_id": snapshot_id}, request=request
            )
        sor["request_url"] = reverse(
            "api-1-save-origin", url_args={"request_id": sor["id"]}, request=request
        )
        return sor

    data = request.data or {}
    if request.method == "POST":
        assert visit_type is not None
        assert origin_url is not None
        sor = create_save_origin_request(
            visit_type,
            origin_url,
            privileged_user(
                request,
                permissions=[SWH_AMBASSADOR_PERMISSION, API_SAVE_ORIGIN_PERMISSION],
            ),
            user_id=cast(Optional[int], request.user.id),
            **data,
        )
        return _cleanup_and_enrich_sor_data(sor)

    else:
        if visit_type and origin_url:
            sors = get_save_origin_requests(visit_type, origin_url)
            return [_cleanup_and_enrich_sor_data(sor) for sor in sors]
        else:
            return _cleanup_and_enrich_sor_data(get_save_origin_request(request_id))
