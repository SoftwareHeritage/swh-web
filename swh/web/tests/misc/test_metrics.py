# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from itertools import product
import random

from prometheus_client.exposition import CONTENT_TYPE_LATEST

import pytest

from swh.web.common.models import (
    SaveOriginRequest,
    SAVE_REQUEST_ACCEPTED,
    SAVE_REQUEST_REJECTED,
    SAVE_REQUEST_PENDING,
    SAVE_TASK_NOT_YET_SCHEDULED,
    SAVE_TASK_SCHEDULED,
    SAVE_TASK_SUCCEED,
    SAVE_TASK_FAILED,
    SAVE_TASK_RUNNING,
    SAVE_TASK_NOT_CREATED,
)
from swh.web.common.origin_save import (
    get_savable_visit_types,
    ACCEPTED_SAVE_REQUESTS_METRIC,
    SUBMITTED_SAVE_REQUESTS_METRIC,
)
from swh.web.common.utils import reverse
from swh.web.tests.django_asserts import assert_contains


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
        SAVE_TASK_SUCCEED,
        SAVE_TASK_FAILED,
        SAVE_TASK_RUNNING,
    )

    for _ in range(random.randint(50, 100)):
        visit_type = random.choice(visit_types)
        request_satus = random.choice(request_statuses)
        load_task_status = random.choice(load_task_statuses)

        SaveOriginRequest.objects.create(
            origin_url="origin",
            visit_type=visit_type,
            status=request_satus,
            loading_task_status=load_task_status,
        )

    url = reverse("metrics-prometheus")
    resp = client.get(url)

    assert resp.status_code == 200
    assert resp["Content-Type"] == CONTENT_TYPE_LATEST

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
