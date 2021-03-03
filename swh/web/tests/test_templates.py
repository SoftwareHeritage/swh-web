# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from swh.web.common.utils import reverse
from swh.web.config import STAGING_SERVER_NAMES
from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.utils import check_http_get_response


def test_layout_without_staging_ribbon(client):
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_not_contains(resp, "swh-corner-ribbon")


def test_layout_with_staging_ribbon(client):
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(
        client, url, status_code=200, server_name=random.choice(STAGING_SERVER_NAMES),
    )
    assert_contains(resp, "swh-corner-ribbon")
