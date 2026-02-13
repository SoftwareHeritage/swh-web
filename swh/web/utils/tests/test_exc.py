# Copyright (C) 2022-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


import pytest
from requests import Response

from django.utils.html import escape

from swh.core.api import RemoteException
from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.helpers import check_api_get_responses, check_html_get_response
from swh.web.utils import reverse
from swh.web.utils.exc import (
    BadInputExc,
    ForbiddenExc,
    Http404,
    Ratelimited,
    UnauthorizedExc,
    exceptions,
)


def _error_response():
    response = Response()
    response.status_code = 500
    return response


@pytest.mark.parametrize(
    "exception, expected_status",
    [
        (
            RemoteException(
                payload={
                    "type": "QueryCanceled",
                    "args": ["canceling statement due to statement timeout\n"],
                },
                response=_error_response(),
            ),
            500,
        ),
        (BadInputExc("bad input"), 400),
        (UnauthorizedExc("requires authentication"), 401),
        (ForbiddenExc("forbidden"), 403),
        (exceptions.PermissionDenied(), 403),
        (Http404("404"), 404),
        (Ratelimited(), 429),
    ],
)
def test_django_views_exception_handler(
    client, mocker, exception, expected_status, caplog, config_updater
):
    # simulate production settings
    config_updater({"debug": False})

    # make homepage return an error
    mocker.patch("swh.web.webapp.urls.origin_visit_types").side_effect = exception

    resp = check_html_get_response(
        client, "/", status_code=expected_status, template_used="error.html"
    )

    assert_contains(resp, escape(str(exception)), status_code=expected_status)

    if expected_status == 500:
        # error 500 should log exception
        assert caplog.records
        assert caplog.records[0].exc_info[1] == exception
    else:
        assert not caplog.records


@pytest.mark.parametrize(
    "exception, expected_status",
    [
        (
            RemoteException(
                payload={
                    "type": "QueryCanceled",
                    "args": ["canceling statement due to statement timeout\n"],
                },
                response=_error_response(),
            ),
            500,
        ),
        (BadInputExc("bad input"), 400),
        (UnauthorizedExc("requires authentication"), 401),
        (ForbiddenExc("forbidden"), 403),
    ],
)
def test_drf_views_exception_handler(
    api_client, mocker, exception, expected_status, caplog, config_updater
):
    # simulate production settings
    config_updater({"debug": False})

    # make stats api view return an error
    mocker.patch("swh.web.api.views.stat.archive.stat_counters").side_effect = exception

    resp = check_api_get_responses(
        api_client, reverse("api-1-stat-counters"), status_code=expected_status
    )

    assert resp.data["reason"] == str(exception)

    if expected_status == 500:
        assert caplog.records
        assert caplog.records[0].exc_info[1] == exception
    else:
        assert not caplog.records
