# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from rest_framework.request import Request

from swh.provenance import get_provenance
from swh.provenance.interface import ProvenanceInterface
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import APIUrls, api_route
from swh.web.auth.utils import API_PROVENANCE_PERMISSION
from swh.web.config import get_config
from swh.web.utils.exc import BadInputExc, ForbiddenExc, UnauthorizedExc
from swh.web.utils.identifiers import parse_core_swhid
from swh.web.utils.url_path_converters import register_url_path_converters

provenance_api_urls = APIUrls()

register_url_path_converters()


def _provenance() -> ProvenanceInterface:
    return get_provenance(**get_config()["provenance"])


def _check_auth_and_permission(request: Request):
    if not bool(request.user and request.user.is_authenticated):
        raise UnauthorizedExc("This API endpoint requires authentication.")
    if (
        not request.user.has_perm(API_PROVENANCE_PERMISSION)
        and not request.user.is_staff
    ):
        raise ForbiddenExc("This API endpoint requires a special user permission.")


@api_route(
    "/provenance/whereis/<swhid:target>/",
    "api-1-provenance-whereis",
    api_urls=provenance_api_urls,
)
@api_doc("/provenance/whereis/", category="Provenance")
@format_docstring()
def api_provenance_whereis(request: Request, target: str):
    """
    .. http:get:: /api/1/provenance/whereis/(target)/

        Given a core SWHID return a qualified SWHID with some provenance info:

        - the release or revision containing that content or directory
        - the url of the origin containing that content or directory

        This can also be called for revision, release or snapshot to retrieve
        origin url information if any. When using a revision, the anchor will
        be an associated release if any.

        .. note::

            The quality of the result is not guaranteed whatsoever. Since the
            definition of "best" likely vary from one usage to the next, this API
            will evolve in the futur when this notion get better defined.

        .. warning::

            That endpoint is not publicly available and requires authentication and
            special user permission in order to request it.

        :param string target: a core SWHID targeting an archived object

        The response is a string containing a qualified SWHID with provenance info.

        {common_headers}

        :statuscode 200: no error
        :statuscode 400: provided core SWHID is invalid
        :statuscode 401: request is not authenticated
        :statuscode 403: user does not have permission to query the endpoint

        **Example:**

        .. parsed-literal::

            :swh_web_api:`provenance/whereis/swh:1:cnt:dcb2d732994e615aab0777bfe625bd1f07e486ac/`
    """
    _check_auth_and_permission(request)
    core_swhid = parse_core_swhid(target)
    provenance = _provenance().whereis(swhid=core_swhid)
    return str(provenance) if provenance is not None else None


@api_route(
    "/provenance/whereare/",
    "api-1-provenance-whereare",
    api_urls=provenance_api_urls,
    methods=["POST"],
)
@api_doc("/provenance/whereare/", category="Provenance")
@format_docstring()
def api_provenance_whereare(request: Request):
    """
    .. http:post:: /api/1/provenance/whereare/

        Given a list of core SWHIDs return qualified SWHIDs with some provenance info.

        See :http:get:`/api/1/provenance/whereis/(target)/` documentation for more details.

        .. warning::

            That endpoint is not publicly available and requires authentication and
            special user permission in order to request it.

        :<jsonarr string -: input array of core SWHIDs

        The response is a JSON array of strings containing qualified SWHIDs with
        provenance info.

        {common_headers}

        :statuscode 200: no error
        :statuscode 400: provided core SWHID is invalid
        :statuscode 401: request is not authenticated
        :statuscode 403: user does not have permission to query the endpoint
    """
    _check_auth_and_permission(request)
    if not request.data or not isinstance(request.data, list):
        raise BadInputExc("A list of core SWHIDS must be provided in POST data.")
    swhids = [parse_core_swhid(swhid) for swhid in request.data]
    provenances = _provenance().whereare(swhids=swhids)
    return [str(provenance) if provenance else None for provenance in provenances]
