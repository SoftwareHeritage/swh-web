# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.urls import get_resolver

from swh.web.save_code_now.urls import urlpatterns
from swh.web.tests.django_asserts import assert_not_contains
from swh.web.tests.helpers import check_html_get_response
from swh.web.utils import reverse


@pytest.mark.django_db
def test_save_code_now_deactivate(client, staff_user, origin, django_settings):
    """Check Save code now feature is deactivated when the swh.web.save_code_now django
    application is not in installed apps."""

    django_settings.SWH_DJANGO_APPS = [
        app for app in django_settings.SWH_DJANGO_APPS if app != "swh.web.save_code_now"
    ]

    url = reverse("swh-web-homepage")
    client.force_login(staff_user)
    resp = check_html_get_response(client, url, status_code=200)
    assert_not_contains(resp, "swh-origin-save-item")
    assert_not_contains(resp, "swh-origin-save-admin-item")

    url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": origin["url"]},
    )

    resp = check_html_get_response(client, url, status_code=200)
    assert_not_contains(resp, "swh-take-new-snashot")

    save_code_now_view_names = set(urlpattern.name for urlpattern in urlpatterns)
    all_view_names = set(get_resolver().reverse_dict.keys())
    assert save_code_now_view_names & all_view_names == set()
