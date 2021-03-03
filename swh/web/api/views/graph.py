# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from distutils.util import strtobool
import json
from typing import Dict, Iterator, Union

import requests

from django.http.response import StreamingHttpResponse
from rest_framework.decorators import renderer_classes
from rest_framework.request import Request
from rest_framework.response import Response

from swh.model.hashutil import hash_to_hex
from swh.model.identifiers import ExtendedObjectType, ExtendedSWHID
from swh.model.model import Sha1Git
from swh.web.api.apidoc import api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.renderers import PlainTextRenderer
from swh.web.common import archive
from swh.web.config import SWH_WEB_INTERNAL_SERVER_NAME, get_config

API_GRAPH_PERM = "swh.web.api.graph"


def _resolve_origin_swhid(swhid: str, origin_urls: Dict[Sha1Git, str]) -> str:
    """
    Resolve origin url from its swhid sha1 representation.
    """
    parsed_swhid = ExtendedSWHID.from_string(swhid)
    if parsed_swhid.object_type == ExtendedObjectType.ORIGIN:
        if parsed_swhid.object_id in origin_urls:
            return origin_urls[parsed_swhid.object_id]
        else:
            origin_info = list(
                archive.lookup_origins_by_sha1s([hash_to_hex(parsed_swhid.object_id)])
            )[0]
            assert origin_info is not None
            origin_urls[parsed_swhid.object_id] = origin_info["url"]
            return origin_info["url"]
    else:
        return swhid


def _resolve_origin_swhids_in_graph_response(
    response: requests.Response,
) -> Iterator[bytes]:
    """
    Resolve origin urls from their swhid sha1 representations in graph service
    responses.
    """
    content_type = response.headers["Content-Type"]
    origin_urls: Dict[Sha1Git, str] = {}
    if content_type == "application/x-ndjson":
        for line in response.iter_lines():
            swhids = json.loads(line.decode("utf-8"))
            processed_line = []
            for swhid in swhids:
                processed_line.append(_resolve_origin_swhid(swhid, origin_urls))
            yield (json.dumps(processed_line) + "\n").encode()
    elif content_type == "text/plain":
        for line in response.iter_lines():
            processed_line = []
            swhids = line.decode("utf-8").split(" ")
            for swhid in swhids:
                processed_line.append(_resolve_origin_swhid(swhid, origin_urls))
            yield (" ".join(processed_line) + "\n").encode()
    else:
        for line in response.iter_lines():
            yield line + b"\n"


@api_route(r"/graph/", "api-1-graph-doc")
@api_doc("/graph/")
def api_graph(request: Request) -> None:
    """
    .. http:get:: /api/1/graph/(graph_query)/

        Provide fast access to the graph representation of the Software Heritage
        archive.

        That endpoint acts as a proxy for the `Software Heritage Graph service
        <https://docs.softwareheritage.org/devel/swh-graph/index.html>`_.

        It provides fast access to the `graph representation
        <https://docs.softwareheritage.org/devel/swh-model/data-model.html#data-structure>`_
        of the Software Heritage archive.

        For more details please refer to the `Graph REST API documentation
        <https://docs.softwareheritage.org/devel/swh-graph/api.html>`_.

        .. warning::
            That endpoint is not publicly available and requires authentication and
            special user permission in order to be able to request it.

        :param string graph_query: query to forward to the Software Heritage Graph
            archive (see its `documentation
            <https://docs.softwareheritage.org/devel/swh-graph/api.html>`_)
        :query boolean resolve_origins: extra parameter defined by that proxy enabling
            to resolve origin urls from their sha1 representations

        :statuscode 200: no error
        :statuscode 400: an invalid graph query has been provided
        :statuscode 404: provided graph node cannot be found

        **Examples:**

        .. parsed-literal::

            :swh_web_api:`graph/leaves/swh:1:dir:432d1b21c1256f7408a07c577b6974bbdbcc1323/`
            :swh_web_api:`graph/neighbors/swh:1:rev:f39d7d78b70e0f39facb1e4fab77ad3df5c52a35/`
            :swh_web_api:`graph/randomwalk/swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2/ori?direction=backward`
            :swh_web_api:`graph/randomwalk/swh:1:cnt:94a9ed024d3859793618152ea559a168bbcbb5e2/ori?direction=backward&limit=-2`
            :swh_web_api:`graph/visit/nodes/swh:1:snp:40f9f177b8ab0b7b3d70ee14bbc8b214e2b2dcfc?direction=backward&resolve_origins=true`
            :swh_web_api:`graph/visit/edges/swh:1:snp:40f9f177b8ab0b7b3d70ee14bbc8b214e2b2dcfc?direction=backward&resolve_origins=true`
            :swh_web_api:`graph/visit/paths/swh:1:dir:644dd466d8ad527ea3a609bfd588a3244e6dafcb?direction=backward&resolve_origins=true`

    """
    return None


@api_route(r"/graph/(?P<graph_query>.+)/", "api-1-graph")
@renderer_classes([PlainTextRenderer])
def api_graph_proxy(
    request: Request, graph_query: str
) -> Union[Response, StreamingHttpResponse]:
    if request.get_host() != SWH_WEB_INTERNAL_SERVER_NAME:
        if not bool(request.user and request.user.is_authenticated):
            return Response("Authentication credentials were not provided.", status=401)
        if not request.user.has_perm(API_GRAPH_PERM):
            return Response(
                "You do not have permission to perform this action.", status=403
            )
    graph_query_url = get_config()["graph"]["server_url"]
    graph_query_url += graph_query
    if request.GET:
        graph_query_url += "?" + request.GET.urlencode(safe="/;:")
    response = requests.get(graph_query_url, stream=True)
    # graph stats and counter endpoint responses are not streamed
    if response.headers.get("Transfer-Encoding") != "chunked":
        return Response(
            response.text,
            status=response.status_code,
            content_type=response.headers["Content-Type"],
        )
    # other endpoint responses are streamed
    else:
        resolve_origins = strtobool(request.GET.get("resolve_origins", "false"))
        if response.status_code == 200 and resolve_origins:
            response_stream = _resolve_origin_swhids_in_graph_response(response)
        else:
            response_stream = map(lambda line: line + b"\n", response.iter_lines())
        return StreamingHttpResponse(
            response_stream,
            status=response.status_code,
            content_type=response.headers["Content-Type"],
        )
