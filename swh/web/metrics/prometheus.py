# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from itertools import product

from prometheus_client import Gauge
from prometheus_client.registry import CollectorRegistry

from swh.web.save_code_now.models import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_REQUEST_PENDING,
    SAVE_REQUEST_REJECTED,
    SAVE_TASK_FAILED,
    SAVE_TASK_NOT_CREATED,
    SAVE_TASK_NOT_YET_SCHEDULED,
    SAVE_TASK_RUNNING,
    SAVE_TASK_SCHEDULED,
    SAVE_TASK_SUCCEEDED,
    SaveOriginRequest,
)
from swh.web.save_code_now.origin_save import get_savable_visit_types

SWH_WEB_METRICS_REGISTRY = CollectorRegistry(auto_describe=True)

SUBMITTED_SAVE_REQUESTS_METRIC = "swh_web_submitted_save_requests"

_submitted_save_requests_gauge = Gauge(
    name=SUBMITTED_SAVE_REQUESTS_METRIC,
    documentation="Number of submitted origin save requests",
    labelnames=["status", "visit_type"],
    registry=SWH_WEB_METRICS_REGISTRY,
)


ACCEPTED_SAVE_REQUESTS_METRIC = "swh_web_accepted_save_requests"

_accepted_save_requests_gauge = Gauge(
    name=ACCEPTED_SAVE_REQUESTS_METRIC,
    documentation="Number of accepted origin save requests",
    labelnames=["load_task_status", "visit_type"],
    registry=SWH_WEB_METRICS_REGISTRY,
)


# Metric on the delay of save code now request per status and visit_type. This is the
# time difference between the save code now is requested and the time it got ingested.
ACCEPTED_SAVE_REQUESTS_DELAY_METRIC = "swh_web_save_requests_delay_seconds"

_accepted_save_requests_delay_gauge = Gauge(
    name=ACCEPTED_SAVE_REQUESTS_DELAY_METRIC,
    documentation="Save Requests Duration",
    labelnames=["load_task_status", "visit_type"],
    registry=SWH_WEB_METRICS_REGISTRY,
)


def compute_save_requests_metrics() -> None:
    """Compute Prometheus metrics related to origin save requests:

    - Number of submitted origin save requests
    - Number of accepted origin save requests
    - Save Code Now requests delay between request time and actual time of ingestion

    """

    request_statuses = (
        SAVE_REQUEST_ACCEPTED,
        SAVE_REQUEST_REJECTED,
        SAVE_REQUEST_PENDING,
    )

    load_task_statuses = (
        SAVE_TASK_NOT_CREATED,
        SAVE_TASK_NOT_YET_SCHEDULED,
        SAVE_TASK_SCHEDULED,
        SAVE_TASK_SUCCEEDED,
        SAVE_TASK_FAILED,
        SAVE_TASK_RUNNING,
    )

    # for metrics, we want access to all visit types
    visit_types = get_savable_visit_types(privileged_user=True)

    labels_set = product(request_statuses, visit_types)

    for labels in labels_set:
        _submitted_save_requests_gauge.labels(*labels).set(0)

    labels_set = product(load_task_statuses, visit_types)

    for labels in labels_set:
        _accepted_save_requests_gauge.labels(*labels).set(0)

    duration_load_task_statuses = (
        SAVE_TASK_FAILED,
        SAVE_TASK_SUCCEEDED,
    )

    for labels in product(duration_load_task_statuses, visit_types):
        _accepted_save_requests_delay_gauge.labels(*labels).set(0)

    for sor in SaveOriginRequest.objects.all():
        if sor.status == SAVE_REQUEST_ACCEPTED:
            _accepted_save_requests_gauge.labels(
                load_task_status=sor.loading_task_status,
                visit_type=sor.visit_type,
            ).inc()

        _submitted_save_requests_gauge.labels(
            status=sor.status, visit_type=sor.visit_type
        ).inc()

        if (
            sor.loading_task_status in (SAVE_TASK_SUCCEEDED, SAVE_TASK_FAILED)
            and sor.visit_date is not None
            and sor.request_date is not None
        ):
            delay = sor.visit_date.timestamp() - sor.request_date.timestamp()
            _accepted_save_requests_delay_gauge.labels(
                load_task_status=sor.loading_task_status,
                visit_type=sor.visit_type,
            ).inc(delay)
