# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import csv
import io
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from django.utils.encoding import force_str
from rest_framework.decorators import parser_classes
from rest_framework.exceptions import ParseError
from rest_framework.parsers import BaseParser, JSONParser
from rest_framework.request import Request
from rest_framework.response import Response

from swh.scheduler.utils import create_oneshot_task
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import APIUrls, api_route
from swh.web.api.parsers import YAMLParser
from swh.web.auth.utils import API_SAVE_BULK_PERMISSION
from swh.web.config import get_config, scheduler
from swh.web.save_bulk.models import SaveBulkOrigin, SaveBulkRequest
from swh.web.save_code_now.origin_save import validate_origin_url
from swh.web.utils import reverse
from swh.web.utils.exc import BadInputExc

save_bulk_api_urls = APIUrls()

SUPPORTED_VISIT_TYPES = {"bzr", "cvs", "hg", "git", "svn", "tarball-directory"}


def _register_request_and_origins_in_db(
    user_id: str, origins: List[Dict[str, str]]
) -> str:
    save_bulk_request = SaveBulkRequest.objects.create(user_id=user_id)

    # create new submitted origins in database
    save_bulk_origins = SaveBulkOrigin.objects.bulk_create(
        [
            SaveBulkOrigin(
                origin_url=origin["origin_url"], visit_type=origin["visit_type"]
            )
            for origin in origins
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
                -H "Content-Type : application/json" \\
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
                -H "Content-Type : application/yaml" \\
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
    for origin in sorted(request.data, key=lambda d: d.get("origin_url", "")):
        origin_url = origin.get("origin_url")
        visit_type = origin.get("visit_type")
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
        user_id=str(request.user.id), origins=request.data
    )

    # generate URL to be queried by the bulk-save lister
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

    # create the bulk-save listing task
    task = create_oneshot_task(
        "list-bulk-save",
        url=origins_list_url,
        instance=save_bulk_request_id,
        per_page=10,
    )

    scheduler().create_tasks([task])

    return Response({"status": "accepted", "request_id": save_bulk_request_id})
