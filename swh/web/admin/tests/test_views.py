# Copyright (C) 2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.tests.helpers import check_http_get_response
from swh.web.utils import reverse

pytestmark = pytest.mark.django_db


def test_regular_user_unauthorized(client, regular_user):
    client.force_login(regular_user)

    url = reverse("admin:index")

    response = check_http_get_response(client, url, status_code=302)

    # unauthorized user should be offered to login with a different user
    # account having permissions to access the admin UI
    assert response.headers["Location"] == "/manage/login/?next=/manage/"


def test_staff_user_authorized(client, staff_user):
    client.force_login(staff_user)

    url = reverse("admin:index")

    check_http_get_response(client, url, status_code=200)


def test_add_forge_now_moderator_authorized(client, add_forge_moderator):
    client.force_login(add_forge_moderator)

    url = reverse("admin:index")

    check_http_get_response(client, url, status_code=200)
