# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import csv
import io
from typing import Any, Dict, List, Optional, Set, Tuple, TypedDict
from urllib.parse import urlparse
from uuid import UUID

from django.core.paginator import EmptyPage, Paginator
from django.utils.encoding import force_str
from rest_framework.decorators import parser_classes
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser, JSONParser
from rest_framework.request import Request
from rest_framework.response import Response

from swh.model.swhids import CoreSWHID, ObjectType, QualifiedSWHID
from swh.scheduler.utils import create_oneshot_task
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import APIUrls, api_route
from swh.web.api.parsers import YAMLParser
from swh.web.auth.utils import API_SAVE_BULK_PERMISSION
from swh.web.config import get_config, scheduler
from swh.web.save_bulk.models import SaveBulkOrigin, SaveBulkRequest
from swh.web.save_code_now.origin_save import validate_origin_url
from swh.web.utils import datetime_to_utc, reverse
from swh.web.utils.exc import BadInputExc, ForbiddenExc, NotFoundExc, UnauthorizedExc

save_bulk_api_urls = APIUrls()

SUPPORTED_VISIT_TYPES = {"bzr", "cvs", "hg", "git", "svn", "tarball-directory"}


def _register_request_and_origins_in_db(
    user_id: str, origins: Set[Tuple[str, str]]
) -> str:
    save_bulk_request = SaveBulkRequest.objects.create(user_id=user_id)

    # create new submitted origins in database
    save_bulk_origins = SaveBulkOrigin.objects.bulk_create(
        [
            SaveBulkOrigin(origin_url=origin_url, visit_type=visit_type)
            for origin_url, visit_type in origins
        ],
        update_conflicts=True,
        update_fields=["origin_url", "visit_type"],
        unique_fields=["origin_url", "visit_type"],
    )

    # associate origins with request
    SaveBulkOrigin.requests.through.objects.bulk_create(
        [
            SaveBulkOrigin.requests.through(
                savebulkorigin_id=save_bulk_origin.id,
                savebulkrequest_id=save_bulk_request.id,
            )
            for save_bulk_origin in save_bulk_origins
        ]
    )

    return str(save_bulk_request.id)


def _rejected_response(
    error_reason: str,
    status: int = 400,
    rejected_origins: Optional[List[Dict[str, str]]] = None,
) -> Response:
    resp_data: Dict[str, Any] = {
        "status": "rejected",
        "reason": error_reason,
    }
    if rejected_origins:
        resp_data["rejected_origins"] = rejected_origins
    return Response(
        resp_data,
        status=status,
    )


class OriginsDataCSVParser(BaseParser):
    media_type = "text/csv"

    def parse(self, stream, media_type=None, parser_context=None):
        try:
            reader = csv.DictReader(
                io.StringIO(stream.read().decode()),
                fieldnames=["origin_url", "visit_type"],
            )
            return [row for row in reader]
        except csv.Error as e:
            raise ParseError(f"CSV data failed to be parsed: {force_str(e)}.")


@api_doc("/origin/save/bulk/", category="Request archival")
@format_docstring()
@api_route(
    r"/origin/save/bulk/",
    "api-1-save-origin-bulk",
    methods=["POST"],
    never_cache=True,
    api_urls=save_bulk_api_urls,
)
@parser_classes([OriginsDataCSVParser, JSONParser, YAMLParser])
def api_origin_save_bulk(request: Request) -> Response:
    """
    .. http:post:: /api/1/origin/save/bulk/

        Request the saving of multiple software origins into the archive.

        That endpoint enables to request the archival of multiple software origins through
        a POST request containing a list of origin URLs and their visit types in its body.

        The following visit types are supported: ``bzr``, ``cvs``, ``hg``, ``git``,
        ``svn`` and ``tarball-directory``.

        The origins list data can be provided using the following content types:

        - ``text/csv`` (default)

          When using CSV format, first column must contain origin URLs and second
          column the visit types.

          .. code-block::

              "https://git.example.org/user/project","git"
              "https://download.example.org/project/source.tar.gz","tarball-directory"

          To post the content of such file to the endpoint, you can use the following
          ``curl`` command.

          .. code-block:: shell

            $ curl -X POST -H "Authorization: Bearer ****" \\
                -H "Content-Type: text/csv" \\
                --data-binary @/path/to/origins.csv \\
                https://archive.softwareheritage.org/api/1/origin/save/bulk/


        - ``application/json``

          When using JSON format, the following schema must be used.

          .. code-block:: json

              [
                  {{
                      "origin_url": "https://git.example.org/user/project",
                      "visit_type": "git"
                  }},
                  {{
                      "origin_url": "https://download.example.org/project/source.tar.gz",
                      "visit_type": "tarball-directory"
                  }}
              ]

          To post the content of such file to the endpoint, you can use the following
          ``curl`` command.

          .. code-block:: shell

            $ curl -X POST -H "Authorization: Bearer ****" \\
                -H "Content-Type: application/json" \\
                --data-binary @/path/to/origins.json \\
                https://archive.softwareheritage.org/api/1/origin/save/bulk/

        - ``application/yaml``

          When using YAML format, the following schema must be used.

          .. code-block:: yaml

              - origin_url: https://git.example.org/user/project
                visit_type: git

              - origin_url: https://download.example.org/project/source.tar.gz
                visit_type: tarball-directory

          To post the content of such file to the endpoint, you can use the following
          ``curl`` command.

          .. code-block:: shell

            $ curl -X POST -H "Authorization: Bearer ****" \\
                -H "Content-Type: application/yaml" \\
                --data-binary @/path/to/origins.yaml \\
                https://archive.softwareheritage.org/api/1/origin/save/bulk/


        Once received, origins data are checked for correctness by validating URLs and
        verifying if visit types are supported. A request cannot be accepted if at least
        one origin is not valid. All origins with invalid format will be reported in the
        rejected request response.

        .. warning::
            That endpoint is not publicly available and requires authentication and
            special user permission in order to request it.

        {common_headers}

        :reqheader Content-Type: the content type of posted data,
            either ``text/csv`` (default), ``application/json`` or ``application/yaml``

        :>json string status: either ``accepted`` or ``rejected``
        :>json string reason: details about why a request got rejected
        :>json string request_id: request identifier (only when it its accepted)
        :>json array rejected_origins: list of rejected origins and details about the reasons
            (only when the request is rejected)

        :statuscode 200: no error
        :statuscode 400: provided origins data are not valid
        :statuscode 401: request is not authenticated
        :statuscode 403: user does not have permission to query the endpoint
        :statuscode 415: payload format is not supported
    """  # noqa
    # authentication and permission checks
    if not bool(request.user and request.user.is_authenticated):
        return _rejected_response(
            "This API endpoint requires authentication.", status=401
        )
    if not request.user.has_perm(API_SAVE_BULK_PERMISSION):
        return _rejected_response(
            "This API endpoint requires a special user permission.", status=403
        )

    # request data basic checks
    if not request.body:
        return _rejected_response("No origins data were provided in POST request body.")
    if not isinstance(request.data, list):
        return _rejected_response("Origins data must be a list of dict.")

    # check origin URLs are well formed and visit types are supported
    rejected_origins = []
    origins = set()
    for origin in sorted(request.data, key=lambda d: d.get("origin_url", "")):
        origin_url = origin.get("origin_url")
        visit_type = origin.get("visit_type")
        origin_data = (origin_url, visit_type)
        if origin_data in origins:
            continue
        origins.add(origin_data)
        if (not origin_url or not visit_type) or not (
            isinstance(origin_url, str) and isinstance(visit_type, str)
        ):
            rejected_origins.append(
                {
                    "origin": origin,
                    "rejection_reason": (
                        "Provided origin data are malformed, please check provided values."
                    ),
                }
            )
        else:
            try:
                validate_origin_url(origin_url)
            except BadInputExc as e:
                rejected_origins.append(
                    {
                        "origin": origin,
                        "rejection_reason": force_str(e),
                    }
                )
            else:
                if visit_type not in SUPPORTED_VISIT_TYPES:
                    rejected_origins.append(
                        {
                            "origin": origin,
                            "rejection_reason": f"Visit type '{visit_type}' is not supported.",
                        }
                    )

    if rejected_origins:
        return _rejected_response(
            "Some origins data could not be validated.",
            rejected_origins=rejected_origins,
        )

    # register origins data to swh-web database
    save_bulk_request_id = _register_request_and_origins_in_db(
        user_id=str(request.user.id), origins=origins
    )

    # generate URL to be queried by the save-bulk lister
    origins_list_url = reverse(
        "save-origin-bulk-origins-list",
        url_args={"request_id": save_bulk_request_id},
        request=request,
    )
    if get_config().get("instance_name", "").endswith("docker.softwareheritage.org"):
        # modify URL if executed in SWH docker environment to ensure lister can query it
        origins_list_url = (
            urlparse(origins_list_url)._replace(scheme="http", netloc="nginx").geturl()
        )

    # create the save-bulk listing task
    task = create_oneshot_task(
        "list-save-bulk",
        url=origins_list_url,
        instance=save_bulk_request_id,
        per_page=10,
    )

    scheduler().create_tasks([task])

    return Response(
        {
            "status": "accepted",
            "request_id": save_bulk_request_id,
            "request_info_url": reverse(
                "api-1-save-origin-bulk-request-info",
                url_args={"request_id": save_bulk_request_id},
                request=request,
            ),
        }
    )


class SumbittedOriginInfo(TypedDict):
    origin_url: str
    visit_type: str
    status: str
    last_scheduling_date: Optional[str]
    last_visit_date: Optional[str]
    last_visit_status: Optional[str]
    last_snapshot_swhid: Optional[str]
    rejection_reason: Optional[str]
    browse_url: Optional[str]


@api_doc("/origin/save/bulk/request/", category="Request archival")
@format_docstring()
@api_route(
    "/origin/save/bulk/request/<uuid:request_id>/",
    "api-1-save-origin-bulk-request-info",
    never_cache=True,
    api_urls=save_bulk_api_urls,
)
def api_origin_save_bulk_request_info(request: Request, request_id: UUID):
    """
    .. http:get:: /api/1/origin/save/bulk/request/(request_id)/

        Get feedback about loading statuses of origins submitted through a save bulk request.

        That endpoint enables to track the archival statuses of origins sumitted through a POST
        request using the :http:post:`/api/1/origin/save/bulk/` endpoint. Info about submitted
        origins are returned in a paginated way.

        .. note::
            Only origin visits whose dates are greater than the request date are reported by
            that endpoint.

        .. warning::
            That endpoint is not publicly available and requires authentication and
            special user permission in order to request it. Staff users are also
            allowed to query it.

        .. warning::
            Only the user that created a save bulk request or a staff user can get
            feedback about it.

        :param string request_id: UUID identifier of a save bulk request

        :query number page: The submitted origins info page number to retrieve
        :query number per_page: Number of submitted origins info per page, default to 1000,
            maximum is 10000

        :>jsonarr string origin_url: URL of submitted origin
        :>jsonarr string visit_type: visit type for the origin
        :>jsonarr string status: submitted origin status, either ``pending``, ``accepted``
            or ``rejected``
        :>jsonarr date last_scheduling_date: ISO8601/RFC3339 representation of the last date
            (in UTC) when the origin was scheduled for loading into the archive, ``null`` if
            the origin got rejected
        :>jsonarr date last_visit_date: ISO8601/RFC3339 representation of the last date
            (in UTC) when the origin was visited by Software Heritage, ``null`` if the origin
            got rejected or was not visited yet
        :>jsonarr string last_visit_status: last visit status for the origin, either
            ``successful`` or ``failed``, ``null`` if the origin got rejected or was not
            visited yet
        :>jsonarr string last_snapshot_swhid: last produced snapshot SWHID associated to the
            visit, ``null`` if the origin got rejected or was not visited yet
        :>jsonarr string rejection_reason: if the origin got rejected gives more details
            about it
        :>jsonarr string browse_url: URL to browse the submitted origin if it got accepted
            and loaded into the archive, ``null`` if the origin got rejected or was not
            visited yet

        {common_headers}
        {resheader_link}

        :statuscode 200: no error
        :statuscode 401: request is not authenticated
        :statuscode 403: user does not have permission to query the endpoint or get feedback
            about a request he did not submit
    """
    # authentication and permission checks
    if not bool(request.user and request.user.is_authenticated):
        raise UnauthorizedExc("This API endpoint requires authentication.")
    if (
        not request.user.has_perm(API_SAVE_BULK_PERMISSION)
        and not request.user.is_staff
    ):
        raise ForbiddenExc("This API endpoint requires a special user permission.")

    request_id_str = str(request_id)

    # fetch request info
    try:
        save_bulk_request = SaveBulkRequest.objects.get(id=request_id_str)
    except SaveBulkRequest.DoesNotExist:
        raise NotFoundExc(f"Save bulk request with id {request_id_str} not found!")

    # only the user that created the request can retrieve its detailed info
    if save_bulk_request.user_id != str(request.user.id) and not request.user.is_staff:
        raise ForbiddenExc(
            f"Save bulk request with id {request_id_str} was not created with "
            "your user account!"
        )

    # get the lister associated to the request
    lister = scheduler().get_lister("save-bulk", instance_name=request_id_str)

    # get list of origins rejected by the lister
    lister_state = lister.current_state if lister else {}
    rejected_origins = {
        (rejected_origin["origin_url"], rejected_origin["visit_type"]): rejected_origin
        for rejected_origin in lister_state.get("rejected_origins", [])
    }

    # fetch the page of submitted origins to get loadings info
    page_num = int(request.GET.get("page", 1))
    per_page = int(request.GET.get("per_page", 1000))
    per_page = min(per_page, 10000)

    submitted_origins = SaveBulkOrigin.objects.filter(
        requests__in=[save_bulk_request]
    ).order_by("origin_url")

    paginator = Paginator(submitted_origins, per_page)
    try:
        page = paginator.page(page_num)
    except EmptyPage:
        return []

    # fetch listed origins filtered by URLs
    listed_origins = {}
    if lister:
        listed_origins = {
            (listed_origin.url, listed_origin.visit_type): listed_origin
            for listed_origin in scheduler()
            .get_listed_origins(
                lister.id,
                urls=[origin.origin_url for origin in page.object_list],
                limit=per_page,
            )
            .results
        }

    # get origin visit statistics from scheduler
    origin_visit_stats = {
        (visit_stats.url, visit_stats.visit_type): visit_stats
        for visit_stats in scheduler().origin_visit_stats_get(
            (origin.origin_url, origin.visit_type) for origin in page.object_list
        )
    }

    # build response
    response_data = []
    for origin in page.object_list:
        origin_key = (origin.origin_url, origin.visit_type)
        status = "pending"
        last_scheduled = None
        last_visit_date = None
        last_visit_status = None
        last_snapshot = None
        rejection_reason = None
        browse_url = None
        if origin_key in rejected_origins:
            # origin rejected by lister, add rejection reason
            status = "rejected"
            rejection_reason = rejected_origins[origin_key]["reason"]
        elif origin_key in listed_origins:
            # origin accepted by lister, get origin visit stats
            status = "accepted"
            if origin_key in origin_visit_stats:
                last_scheduled = origin_visit_stats[origin_key].last_scheduled
                last_visit_date = origin_visit_stats[origin_key].last_visit
                last_visit_status = origin_visit_stats[origin_key].last_visit_status
                last_snapshot = origin_visit_stats[origin_key].last_snapshot
            if last_snapshot:
                browse_url = reverse(
                    "browse-swhid",
                    url_args={
                        "swhid": QualifiedSWHID(
                            object_type=ObjectType.SNAPSHOT,
                            object_id=last_snapshot,
                            origin=origin.origin_url,
                        )
                    },
                    request=request,
                )
            if last_scheduled and last_scheduled > save_bulk_request.request_date:
                # only report visit date greater than request date
                if last_visit_date and last_visit_date < save_bulk_request.request_date:
                    last_visit_date = None
                    last_visit_status = None
                    last_snapshot = None
                    browse_url = None
        # add submitted origin info to response data
        response_data.append(
            SumbittedOriginInfo(
                origin_url=origin.origin_url,
                visit_type=origin.visit_type,
                status=status,
                last_scheduling_date=(
                    datetime_to_utc(last_scheduled).isoformat()
                    if last_scheduled
                    else None
                ),
                last_visit_date=(
                    datetime_to_utc(last_visit_date).isoformat()
                    if last_visit_date
                    else None
                ),
                last_visit_status=(
                    last_visit_status.value if last_visit_status else None
                ),
                last_snapshot_swhid=(
                    str(
                        CoreSWHID(
                            object_type=ObjectType.SNAPSHOT, object_id=last_snapshot
                        )
                    )
                    if last_snapshot
                    else None
                ),
                rejection_reason=rejection_reason,
                browse_url=browse_url,
            )
        )

    response: Dict[str, Any] = {"results": response_data, "headers": {}}

    # compute link header for pagination
    if page.has_previous():
        response["headers"]["link-prev"] = reverse(
            "api-1-save-origin-bulk-request-info",
            url_args={"request_id": request_id},
            query_params={"per_page": str(per_page), "page": str(page_num - 1)},
            request=request,
        )

    if page.has_next():
        response["headers"]["link-next"] = reverse(
            "api-1-save-origin-bulk-request-info",
            url_args={"request_id": request_id},
            query_params={"per_page": str(per_page), "page": str(page_num + 1)},
            request=request,
        )

    return response


@api_doc("/origin/save/bulk/requests/", category="Request archival")
@format_docstring()
@api_route(
    "/origin/save/bulk/requests/",
    "api-1-save-origin-bulk-requests",
    never_cache=True,
    api_urls=save_bulk_api_urls,
)
def api_origin_save_bulk_requests(request: Request):
    """
    .. http:get:: /api/1/origin/save/bulk/requests/

        List previously submitted save bulk requests.

        That endpoint enables to list the save bulk requests submitted by
        your user account and get their info URLs
        (see :http:get:`/api/1/origin/save/bulk/request/(request_id)/`).
        That list is returned in a paginated way if the number or requests
        is large.

        .. warning::
            That endpoint is not publicly available and requires authentication and
            special user permission in order to request it.

        :query number page: The submitted requests page number to retrieve
        :query number per_page: Number of submitted requests per page, default to 1000,
            maximum is 10000

        :>jsonarr string request_id: UUID identifier of the request
        :>jsonarr date request_date: the date the request was submitted
        :>jsonarr string request_info_url: URL to get detailed info about the request

        {common_headers}
        {resheader_link}

        :statuscode 200: no error
        :statuscode 401: request is not authenticated
        :statuscode 403: user does not have permission to query the endpoint

    """

    if not bool(request.user and request.user.is_authenticated):
        raise UnauthorizedExc("This API endpoint requires authentication.")
    if not request.user.has_perm(API_SAVE_BULK_PERMISSION):
        raise ForbiddenExc("This API endpoint requires a special user permission.")

    save_bulk_requests = SaveBulkRequest.objects.filter(
        user_id=str(request.user.id)
    ).order_by("-request_date")

    page_num = int(request.GET.get("page", 1))
    per_page = int(request.GET.get("per_page", 1000))
    per_page = min(per_page, 10000)

    paginator = Paginator(save_bulk_requests, per_page)
    try:
        page = paginator.page(page_num)
    except EmptyPage:
        return []

    response_data = [
        {
            "request_id": str(save_bulk_request.id),
            "request_date": save_bulk_request.request_date.isoformat(),
            "request_info_url": reverse(
                "api-1-save-origin-bulk-request-info",
                url_args={"request_id": str(save_bulk_request.id)},
                request=request,
            ),
        }
        for save_bulk_request in page.object_list
    ]

    response: Dict[str, Any] = {"results": response_data, "headers": {}}

    if page.has_previous():
        response["headers"]["link-prev"] = reverse(
            "api-1-save-origin-bulk-requests",
            query_params={"per_page": str(per_page), "page": str(page_num - 1)},
            request=request,
        )

    if page.has_next():
        response["headers"]["link-next"] = reverse(
            "api-1-save-origin-bulk-requests",
            query_params={"per_page": str(per_page), "page": str(page_num + 1)},
            request=request,
        )

    return response
