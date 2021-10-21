# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.auth.utils import ADMIN_LIST_DEPOSIT_PERMISSION
from swh.web.common.utils import reverse
from swh.web.tests.utils import check_html_get_response, create_django_permission


def test_deposit_admin_view_not_available_for_anonymous_user(client):
    url = reverse("admin-deposit")
    resp = check_html_get_response(client, url, status_code=302)
    assert resp["location"] == reverse("login", query_params={"next": url})


@pytest.mark.django_db
def test_deposit_admin_view_available_for_staff_user(client, staff_user):
    client.force_login(staff_user)
    url = reverse("admin-deposit")
    check_html_get_response(
        client, url, status_code=200, template_used="admin/deposit.html"
    )


@pytest.mark.django_db
def test_deposit_admin_view_available_for_user_with_permission(client, regular_user):
    regular_user.user_permissions.add(
        create_django_permission(ADMIN_LIST_DEPOSIT_PERMISSION)
    )
    client.force_login(regular_user)
    url = reverse("admin-deposit")
    check_html_get_response(
        client, url, status_code=200, template_used="admin/deposit.html"
    )
