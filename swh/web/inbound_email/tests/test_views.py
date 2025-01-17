# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from http import HTTPStatus
from io import BytesIO

import pytest

from django.test.client import MULTIPART_CONTENT

from swh.web.tests.helpers import check_http_get_response, check_http_post_response
from swh.web.utils import reverse

from .common_tests import *  # noqa


@pytest.fixture
def receive_inbound_message(client, inbound_message):
    def do_it(expect_failure=False, shared_key="shared_key"):
        url = reverse("process-inbound-email")
        check_http_post_response(
            client,
            url,
            status_code=HTTPStatus.BAD_REQUEST if expect_failure else HTTPStatus.OK,
            request_content_type=MULTIPART_CONTENT,
            data={"shared_key": shared_key, "email": BytesIO(inbound_message)},
        )

        return inbound_message

    return do_it


@pytest.mark.inbound_message(b"")
def test_empty_email(receive_inbound_message):
    with pytest.raises(AssertionError, match="email.*The submitted file is empty."):
        receive_inbound_message()


@pytest.mark.inbound_message(b"some message")
def test_invalid_shared_key(receive_inbound_message):
    with pytest.raises(AssertionError, match="Invalid shared key!"):
        receive_inbound_message(shared_key="invalid")


def test_get_is_not_allowed(client):
    check_http_get_response(
        client,
        reverse("process-inbound-email"),
        status_code=HTTPStatus.METHOD_NOT_ALLOWED,
    )
