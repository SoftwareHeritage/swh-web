# Copyright (C) 2019-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import timedelta
from itertools import product
import random

from prometheus_client.exposition import CONTENT_TYPE_LATEST
import pytest

from swh.web.common.models import (
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
from swh.web.common.origin_save import (
    ACCEPTED_SAVE_REQUESTS_DELAY_METRIC,
    ACCEPTED_SAVE_REQUESTS_METRIC,
    SUBMITTED_SAVE_REQUESTS_METRIC,
    get_savable_visit_types,
)
from swh.web.common.utils import reverse
from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.utils import check_http_get_response


@pytest.mark.django_db
def test_origin_save_metrics(client):
    visit_types = get_savable_visit_types()
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

    for _ in range(random.randint(50, 100)):
        visit_type = random.choice(visit_types)
        request_satus = random.choice(request_statuses)
        load_task_status = random.choice(load_task_statuses)

        sor = SaveOriginRequest.objects.create(
            origin_url="origin",
            visit_type=visit_type,
            status=request_satus,
            loading_task_status=load_task_status,
        )

        if load_task_status in (SAVE_TASK_SUCCEEDED, SAVE_TASK_FAILED):
            delay = random.choice(range(60))
            sor.visit_date = sor.request_date + timedelta(seconds=delay)
            sor.save()
            # Note that this injects dates in the future for the sake of the test only

    url = reverse("metrics-prometheus")
    resp = check_http_get_response(
        client, url, status_code=200, content_type=CONTENT_TYPE_LATEST
    )

    accepted_requests = SaveOriginRequest.objects.filter(status=SAVE_REQUEST_ACCEPTED)

    labels_set = product(visit_types, load_task_statuses)

    for labels in labels_set:
        sor_count = accepted_requests.filter(
            visit_type=labels[0], loading_task_status=labels[1]
        ).count()

        metric_text = (
            f"{ACCEPTED_SAVE_REQUESTS_METRIC}{{"
            f'load_task_status="{labels[1]}",'
            f'visit_type="{labels[0]}"}} {float(sor_count)}\n'
        )

        assert_contains(resp, metric_text)

    labels_set = product(visit_types, request_statuses)

    for labels in labels_set:
        sor_count = SaveOriginRequest.objects.filter(
            visit_type=labels[0], status=labels[1]
        ).count()

        metric_text = (
            f"{SUBMITTED_SAVE_REQUESTS_METRIC}{{"
            f'status="{labels[1]}",'
            f'visit_type="{labels[0]}"}} {float(sor_count)}\n'
        )

        assert_contains(resp, metric_text)

    # delay metrics

    save_requests = SaveOriginRequest.objects.all()

    labels_set = product(visit_types, (SAVE_TASK_SUCCEEDED, SAVE_TASK_FAILED,))
    for labels in labels_set:
        sors = save_requests.filter(
            visit_type=labels[0],
            loading_task_status=labels[1],
            visit_date__isnull=False,
        )

        delay = 0
        for sor in sors:
            delay += sor.visit_date.timestamp() - sor.request_date.timestamp()

        metric_delay_text = (
            f"{ACCEPTED_SAVE_REQUESTS_DELAY_METRIC}{{"
            f'load_task_status="{labels[1]}",'
            f'visit_type="{labels[0]}"}} {float(delay)}\n'
        )

        assert_contains(resp, metric_delay_text)
