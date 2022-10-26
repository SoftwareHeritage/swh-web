# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from copy import deepcopy

from requests import Response

from django.utils.html import escape

from swh.core.api import RemoteException
from swh.web.config import get_config
from swh.web.tests.django_asserts import assert_contains
from swh.web.utils.exc import handle_view_exception


def test_handle_view_exception_escape_remote_exception_text(request_factory, mocker):

    # we do not want to add traceback in error page as none will be
    # available in the context of that test
    config = deepcopy(get_config())
    config["debug"] = False
    mock_get_config = mocker.patch("swh.web.utils.exc.get_config")
    mock_get_config.return_value = config

    request = request_factory.get("/some/buggy/url")
    response = Response()
    response.status_code = 500
    remote_exception = RemoteException(
        payload={
            "type": "QueryCanceled",
            "args": ["canceling statement due to statement timeout\n"],
        },
        response=response,
    )

    resp = handle_view_exception(request, remote_exception)
    assert_contains(resp, escape(str(remote_exception)), status_code=500)
