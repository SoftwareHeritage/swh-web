# Copyright (C) 2022-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from copy import deepcopy

import pytest
from requests import Response

from django.utils.html import escape

from swh.core.api import RemoteException
from swh.web.config import get_config
from swh.web.tests.django_asserts import assert_contains
from swh.web.utils.exc import (
    BadInputExc,
    ForbiddenExc,
    Http404,
    Ratelimited,
    UnauthorizedExc,
    exceptions,
    handle_view_exception,
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
def test_handle_view_exception_escape_remote_exception_text(
    request_factory, mocker, exception, expected_status
):
    # we do not want to add traceback in error page as none will be
    # available in the context of that test
    config = deepcopy(get_config())
    config["debug"] = False
    mock_get_config = mocker.patch("swh.web.utils.exc.get_config")
    mock_get_config.return_value = config

    request = request_factory.get("/some/buggy/url", HTTP_ACCEPT="text/html")

    resp = handle_view_exception(request, exception)
    assert_contains(resp, escape(str(exception)), status_code=expected_status)
