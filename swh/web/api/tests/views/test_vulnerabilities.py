# Copyright (C) 2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import List

import pytest

from swh.vulns.grpc.swhvulns_pb2 import (
    DetectedVulnerability,
    Vulnerability,
    VulnerabilityDatabase,
    VulnerabilityDetectionTool,
)
from swh.web.tests.helpers import check_api_get_responses
from swh.web.utils import reverse


@pytest.fixture(autouse=True)
def graph_config(config_updater, vulns_grpc_server):
    config_updater(
        {
            "graph": {
                "server_url": "http://example.org/graph/",
                "max_edges": {"staff": 0, "user": 100000, "anonymous": 1000},
            },
            "vulns": {
                "address": vulns_grpc_server,
                "secure": False,
            },
            "unauthenticated_api_hosts": ["local.network"],
        }
    )


@pytest.fixture(scope="session")
def naive_vulns_server_data() -> List[DetectedVulnerability]:
    """Data served by the :class:`swh.vulns.naive_server.NaiveVulnerabilityServicer`
    spawned by the :func:`spawn_naive_grpc_server` fixture"""

    return [
        DetectedVulnerability(
            swhid=swhid,
            vulnerability=Vulnerability(id="TEST-GHSA-0001"),
            tool=VulnerabilityDetectionTool(name="swh-osv"),
            source=VulnerabilityDatabase(name="osv.dev"),
        )
        for swhid in [
            "swh:1:rev:0000000000000000000000000000000000000002",
            "swh:1:rev:0000000000000000000000000000000000000003",
            "swh:1:rev:0000000000000000000000000000000000000004",
        ]
    ]


def test_api_revision_vulnerability(api_client, archive_data) -> None:
    url = reverse(
        "api-1-revision-vulnerabilities",
        url_args={"sha1_git": "0000000000000000000000000000000000000002"},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)

    assert rv.data == [
        {
            "vulnerability": {"ids": "TEST-GHSA-0001"},
            "tool": {"name": "swh-osv", "variant": ""},
            "source": {"name": "osv.dev", "version": ""},
        }
    ]
