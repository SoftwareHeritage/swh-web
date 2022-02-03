# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.auth.utils import MAILMAP_PERMISSION
from swh.web.common.utils import reverse
from swh.web.tests.utils import check_api_post_response, create_django_permission


@pytest.fixture
def mailmap_user(regular_user):
    regular_user.user_permissions.add(create_django_permission(MAILMAP_PERMISSION))
    return regular_user


@pytest.mark.django_db(transaction=True)
@pytest.mark.parametrize("view_name", ["profile-mailmap-add", "profile-mailmap-update"])
def test_mailmap_endpoints_anonymous_user(api_client, view_name):
    url = reverse(view_name)
    check_api_post_response(api_client, url, status_code=403)


@pytest.mark.django_db(transaction=True)
def test_mailmap_endpoints_user_with_permission(api_client, mailmap_user):
    api_client.force_login(mailmap_user)
    for view_name in ("profile-mailmap-add", "profile-mailmap-update"):
        url = reverse(view_name)
        check_api_post_response(
            api_client,
            url,
            data={"from_email": "bar@example.org", "display_name": "bar"},
            status_code=200,
        )


@pytest.mark.django_db(transaction=True)
def test_mailmap_endpoints_error_response(api_client, mailmap_user):
    api_client.force_login(mailmap_user)
    for view_name in ("profile-mailmap-add", "profile-mailmap-update"):
        url = reverse(view_name)
        resp = check_api_post_response(api_client, url, status_code=500)
        assert "exception" in resp.data
