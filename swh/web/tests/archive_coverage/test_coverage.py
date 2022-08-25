# Copyright (C) 2021-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import copy
from datetime import datetime, timezone
from itertools import chain
import os
from random import choices, randint
import uuid

import pytest

from django.conf import settings
from django.utils.html import escape

from swh.scheduler.model import LastVisitStatus, ListedOrigin, OriginVisitStats
from swh.web.archive_coverage.views import (
    deposited_origins,
    legacy_origins,
    listed_origins,
)
from swh.web.config import SWH_WEB_SERVER_NAME
from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.helpers import check_html_get_response, check_http_get_response
from swh.web.utils import reverse


def test_coverage_view_no_metrics(client, swh_scheduler):
    """
    Check coverage view can be rendered when scheduler metrics and deposits
    data are not available.
    """
    url = reverse("swh-coverage")
    check_html_get_response(
        client, url, status_code=200, template_used="archive-coverage.html"
    )


visit_types = ["git", "hg", "svn", "bzr", "cvs"]


@pytest.fixture
def archive_coverage_data(mocker, swh_scheduler):
    """Generate some sample scheduler metrics and some sample deposits
    that will be consumed by the archive coverage view.
    """
    # mock calls to get nixguix origin counts
    mock_archive = mocker.patch("swh.web.archive_coverage.views.archive")
    mock_archive.lookup_latest_origin_snapshot.return_value = {"id": "some-snapshot"}
    mock_archive.lookup_snapshot_sizes.return_value = {"release": 30095}

    listers = []
    for origins in listed_origins["origins"]:
        # create some instances for each lister
        for instance in range(randint(1, 5)):
            lister = swh_scheduler.get_or_create_lister(
                origins["type"], f"instance-{instance}"
            )
            listers.append(lister)
            # record some sample listed origins
            _origins = []
            origin_visit_stats = []
            for i, visit_type in enumerate(visit_types):
                url = str(uuid.uuid4())
                _origins.append(
                    ListedOrigin(
                        lister_id=lister.id,
                        url=url,
                        visit_type=visit_type,
                        extra_loader_arguments={},
                    )
                )
                # set origin visit stats to some origins
                if i % 2 == 0:
                    now = datetime.now(tz=timezone.utc)
                    origin_visit_stats.append(
                        OriginVisitStats(
                            url=url,
                            visit_type=visit_type,
                            last_successful=now,
                            last_visit=now,
                            last_visit_status=LastVisitStatus.successful,
                            last_snapshot=os.urandom(20),
                        )
                    )
            # send origins data to scheduler
            swh_scheduler.record_listed_origins(_origins)
            swh_scheduler.origin_visit_stats_upsert(origin_visit_stats)

    # compute scheduler metrics
    swh_scheduler.update_metrics()

    # add some sample deposits
    deposits = []
    for origins in deposited_origins["origins"]:
        for _ in range(randint(2, 10)):
            deposits.append(
                {
                    "origin_url": f"https://{origins['search_pattern']}/{uuid.uuid4()}",
                    "status": "done",
                }
            )
    get_deposits_list = mocker.patch("swh.web.archive_coverage.views.get_deposits_list")
    get_deposits_list.return_value = deposits


def test_coverage_view_with_metrics(client, archive_coverage_data):

    # check view gets rendered without errors
    url = reverse("swh-coverage")
    resp = check_html_get_response(
        client, url, status_code=200, template_used="archive-coverage.html"
    )

    # check logos and origins search links are present in the rendered page
    for origins in chain(
        listed_origins["origins"],
        legacy_origins["origins"],
        deposited_origins["origins"],
    ):
        logo_url = f'{settings.STATIC_URL}img/logos/{origins["type"].lower()}.png'
        assert_contains(resp, f'src="{logo_url}"')

        origin_visit_types = set()

        if "instances" in origins:
            for visit_types_ in origins["instances"].values():
                origin_visit_types.update(visit_types_.keys())
                for data in visit_types_.values():
                    if data["count"] and data["search_url"]:
                        assert_contains(resp, f'<a href="{escape(data["search_url"])}"')
        else:
            for search_url in origins["search_urls"].values():
                assert_contains(resp, f'<a href="{escape(search_url)}"')

    for visit_type in origin_visit_types:
        assert_contains(resp, f"<td>{visit_type}</td>")

    # check request as in production with cache enabled
    check_http_get_response(
        client, url, status_code=200, server_name=SWH_WEB_SERVER_NAME
    )


def test_coverage_view_with_focus(client, archive_coverage_data):

    origins = (
        listed_origins["origins"]
        + legacy_origins["origins"]
        + deposited_origins["origins"]
    )

    focus = choices([o["type"] for o in origins], k=randint(1, 3))

    # check view gets rendered without errors
    url = reverse("swh-coverage", query_params={"focus": ",".join(focus)})
    resp = check_html_get_response(
        client, url, status_code=200, template_used="archive-coverage.html"
    )

    # check focused elements
    assert_contains(
        resp,
        "swh-coverage-focus",
        count=len([o for o in origins if o["type"] in focus]),
    )

    # check bootstrap cards are expanded
    assert_contains(
        resp,
        'class="collapse show"',
        count=len(origins),
    )


@pytest.fixture
def archive_coverage_data_with_non_visited_origins(mocker, swh_scheduler):
    # mock calls to get nixguix origin counts
    mock_archive = mocker.patch("swh.web.archive_coverage.views.archive")
    mock_archive.lookup_latest_origin_snapshot.return_value = {"id": "some-snapshot"}
    mock_archive.lookup_snapshot_sizes.return_value = {"release": 30095}

    listers = []
    for i, origins in enumerate(listed_origins["origins"]):
        # create one instances for each lister
        lister = swh_scheduler.get_or_create_lister(
            origins["type"], f"instance-{origins['type']}"
        )
        listers.append(lister)

        if i % 2 == 1 or origins["type"] in ("guix", "nixos"):
            # do not declare origins for lister with odd index
            continue

        _origins = []
        origin_visit_stats = []
        for j, visit_type in enumerate(visit_types):
            url = str(uuid.uuid4())
            _origins.append(
                ListedOrigin(
                    lister_id=lister.id,
                    url=url,
                    visit_type=visit_type,
                    extra_loader_arguments={},
                )
            )
            # do not declare visit for visit type with even index
            if j % 2 != 0:
                now = datetime.now(tz=timezone.utc)
                origin_visit_stats.append(
                    OriginVisitStats(
                        url=url,
                        visit_type=visit_type,
                        last_successful=now,
                        last_visit=now,
                        last_visit_status=LastVisitStatus.successful,
                        last_snapshot=os.urandom(20),
                    )
                )
        # send origins data to scheduler
        swh_scheduler.record_listed_origins(_origins)
        swh_scheduler.origin_visit_stats_upsert(origin_visit_stats)

    # compute scheduler metrics
    swh_scheduler.update_metrics()

    # set deposit origins as empty
    get_deposits_list = mocker.patch("swh.web.archive_coverage.views.get_deposits_list")
    get_deposits_list.return_value = []


def test_coverage_view_filter_out_non_visited_origins(
    client, archive_coverage_data_with_non_visited_origins
):

    origins = copy.copy(listed_origins)

    # check view gets rendered without errors
    url = reverse("swh-coverage")
    resp = check_html_get_response(
        client,
        url,
        status_code=200,
        template_used="archive-coverage.html",
        server_name=SWH_WEB_SERVER_NAME,
    )

    for i, origins in enumerate(origins["origins"]):
        if origins["type"] in ("guix", "nixos"):
            continue
        if i % 2 == 1:
            # counters for lister with odd index should not be displayed
            assert_not_contains(resp, f'id="{origins["type"]}"')
        else:
            # counters for lister with even index should be displayed
            assert_contains(resp, f'id="{origins["type"]}"')
            for j, visit_type in enumerate(visit_types):
                if j % 2 == 0:
                    # counter for visit type with even index should be displayed
                    assert_not_contains(resp, f'id="{origins["type"]}-{visit_type}"')
                else:
                    # counter for visit type with odd index should not be displayed
                    assert_contains(resp, f'id="{origins["type"]}-{visit_type}"')
