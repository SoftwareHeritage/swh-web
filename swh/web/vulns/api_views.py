# Copyright (C) 2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import grpc

from rest_framework.request import Request

from swh.vulns.grpc.swhvulns_pb2 import AffectingVulnerabilitiesRequest
from swh.vulns.grpc.swhvulns_pb2_grpc import VulnerabilityServiceStub
from swh.web.api.apidoc import api_doc
from swh.web.api.apiurls import APIUrls, api_route
from swh.web.config import get_config
from swh.web.utils.url_path_converters import register_url_path_converters

_GRPC_CHANNEL = None

vulns_api_urls = APIUrls()

register_url_path_converters()


def _grpc_channel():
    global _GRPC_CHANNEL
    if _GRPC_CHANNEL is None:
        config = get_config()["vulns"]
        if config["secure"]:
            _GRPC_CHANNEL = grpc.secure_channel(config["address"])
        else:
            _GRPC_CHANNEL = grpc.insecure_channel(config["address"])
    return _GRPC_CHANNEL


@api_route(
    r"/revision/(?P<sha1_git>[0-9a-f]+)/vulnerabilities/",
    "api-1-revision-vulnerabilities",
    checksum_args=["sha1_git"],
    api_urls=vulns_api_urls,
)
@api_doc("/revision/vulnerabilities/", category="Metadata")
def api_revision_vulnerabilities(request: Request, sha1_git: str):
    """
    .. http:get:: /api/1/revision/(sha1_git)/vulnerabilities/

        Get known vulnerabilities affecting the revision identified by ``sha1_git``.

        :statuscode 200: no error
        :statuscode 400: an invalid **sha1_git** value has been provided

        :>jsonarr array vulnerability.ids: array of strings, each of which is
            an identifier of the vulnerability
        :>jsonarr string tool.name: name of the tool used to identify the revision is
            vulnerable to this vulnerability
        :>jsonarr string tool.variant: optional human-readable description of
            the tool's configuration
        :>jsonarr string source.name: name of the database the vulnerability report
            comes from
        :>jsonarr string source.version: optional date of the database capture

    """
    # we never return 404 because:
    # 1. we may, theoretically, have vulnerability reports that reference revisions
    #    that we don't know about
    # 2. even if a revision is masked or taken down, there is no reason to hide
    #    vulnerability reports that mention it (like we don't hide git submodules
    #    that reference it either)

    grpc_request = AffectingVulnerabilitiesRequest(
        swhid=[f"swh:1:rev:{sha1_git}"],
    )
    stub = VulnerabilityServiceStub(_grpc_channel())
    response = stub.AffectingVulnerabilities(grpc_request)

    results = [
        {
            "vulnerability": {
                "ids": list(item.vulnerability.id),
            },
            "tool": item.tool
            and {
                "name": item.tool.name,
                "variant": item.tool.variant,
            },
            "source": item.source
            and {
                "name": item.source.name,
                "version": item.source.version,
            },
        }
        for item in response
    ]
    return {"results": results}
