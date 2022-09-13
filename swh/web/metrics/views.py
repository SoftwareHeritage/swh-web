# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from prometheus_client.exposition import CONTENT_TYPE_LATEST, generate_latest

from django.http import HttpResponse

from swh.web.metrics.prometheus import (
    SWH_WEB_METRICS_REGISTRY,
    compute_save_requests_metrics,
)


def prometheus_metrics(request):

    compute_save_requests_metrics()

    return HttpResponse(
        content=generate_latest(registry=SWH_WEB_METRICS_REGISTRY),
        content_type=CONTENT_TYPE_LATEST,
    )
