# Copyright (C) 2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.urls import get_resolver

from swh.web.vulns.urls import urlpatterns


@pytest.mark.django_db
def test_vulns_deactivate(client, staff_user, django_settings):
    """Check vulns features are deactivated when the swh.web.vulns django
    application is not in installed apps."""

    django_settings.SWH_DJANGO_APPS = [
        app for app in django_settings.SWH_DJANGO_APPS if app != "swh.web.vulns"
    ]

    vulns_view_names = set(urlpattern.name for urlpattern in urlpatterns)
    all_view_names = set(get_resolver().reverse_dict.keys())
    assert vulns_view_names & all_view_names == set()
