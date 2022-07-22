# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.urls import get_resolver

from swh.web.add_forge_now.urls import urlpatterns
from swh.web.tests.django_asserts import assert_not_contains
from swh.web.tests.helpers import check_html_get_response
from swh.web.utils import reverse


@pytest.mark.django_db
def test_add_forge_now_deactivate(client, staff_user, django_settings):
    """Check Add forge now feature is deactivated when the swh.web.add_forge_now django
    application is not in installed apps."""

    django_settings.SWH_DJANGO_APPS = [
        app for app in django_settings.SWH_DJANGO_APPS if app != "swh.web.add_forge_now"
    ]

    url = reverse("swh-web-homepage")
    client.force_login(staff_user)
    resp = check_html_get_response(client, url, status_code=200)
    assert_not_contains(resp, "swh-add-forge-now-item")
    assert_not_contains(resp, "swh-add-forge-now-moderation-item")

    add_forge_now_view_names = set(urlpattern.name for urlpattern in urlpatterns)
    all_view_names = set(get_resolver().reverse_dict.keys())
    assert add_forge_now_view_names & all_view_names == set()
