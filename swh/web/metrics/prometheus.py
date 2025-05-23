# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from itertools import product

from prometheus_client import Gauge
from prometheus_client.registry import CollectorRegistry

from django.db.models import Count, DurationField, ExpressionWrapper, F, Sum

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
from swh.web.save_origin_webhooks.generic_receiver import SUPPORTED_FORGE_TYPES

SWH_WEB_METRICS_REGISTRY = CollectorRegistry(auto_describe=True)

SUBMITTED_SAVE_REQUESTS_METRIC = "swh_web_submitted_save_requests"

_submitted_save_requests_gauge = Gauge(
    name=SUBMITTED_SAVE_REQUESTS_METRIC,
    documentation="Number of submitted origin save requests",
    labelnames=["status", "visit_type"],
    registry=SWH_WEB_METRICS_REGISTRY,
)

SUBMITTED_SAVE_REQUESTS_FROM_WEBHOOKS_METRIC = (
    "swh_web_submitted_save_requests_from_webhooks"
)

_submitted_save_requests_from_webhooks_gauge = Gauge(
    name=SUBMITTED_SAVE_REQUESTS_FROM_WEBHOOKS_METRIC,
    documentation="Number of submitted origin save requests through forge webhook receivers",
    labelnames=["status", "webhook_origin"],
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

    labels_set = product(request_statuses, SUPPORTED_FORGE_TYPES)

    for labels in labels_set:
        _submitted_save_requests_from_webhooks_gauge.labels(*labels).set(0)

    labels_set = product(load_task_statuses, visit_types)

    for labels in labels_set:
        _accepted_save_requests_gauge.labels(*labels).set(0)

    duration_load_task_statuses = (
        SAVE_TASK_FAILED,
        SAVE_TASK_SUCCEEDED,
    )

    for labels in product(duration_load_task_statuses, visit_types):
        _accepted_save_requests_delay_gauge.labels(*labels).set(0)

    counts = (
        SaveOriginRequest.objects.values(
            "status",
            "loading_task_status",
            "visit_type",
            "from_webhook",
            "webhook_origin",
        )
        .order_by()
        .annotate(Count("id"))
    )
    for count in counts:
        _submitted_save_requests_gauge.labels(
            status=count["status"],
            visit_type=count["visit_type"],
        ).inc(count["id__count"])
        if count["status"] == "accepted":
            _accepted_save_requests_gauge.labels(
                load_task_status=count["loading_task_status"],
                visit_type=count["visit_type"],
            ).inc(count["id__count"])
        if count["from_webhook"]:
            _submitted_save_requests_from_webhooks_gauge.labels(
                status=count["status"],
                webhook_origin=count["webhook_origin"],
            ).inc(count["id__count"])

    accepted_save_requests_delays = (
        SaveOriginRequest.objects.values("loading_task_status", "visit_type")
        .filter(visit_date__gt=F("request_date"))
        .filter(loading_task_status__in=[SAVE_TASK_SUCCEEDED, SAVE_TASK_FAILED])
        .order_by()
        .annotate(
            delay=Sum(
                ExpressionWrapper(
                    F("visit_date") - F("request_date"), output_field=DurationField()
                )
            )
        )
    )
    for accepted_save_requests_delay in accepted_save_requests_delays:
        _accepted_save_requests_delay_gauge.labels(
            load_task_status=accepted_save_requests_delay["loading_task_status"],
            visit_type=accepted_save_requests_delay["visit_type"],
        ).inc(accepted_save_requests_delay["delay"].total_seconds())
