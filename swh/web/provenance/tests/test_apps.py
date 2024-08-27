# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.urls import get_resolver

from swh.web.provenance.urls import urlpatterns


@pytest.mark.django_db
def test_provenance_deactivate(client, staff_user, django_settings):
    """Check provenance features are deactivated when the swh.web.provenance django
    application is not in installed apps."""

    django_settings.SWH_DJANGO_APPS = [
        app for app in django_settings.SWH_DJANGO_APPS if app != "swh.web.provenance"
    ]

    provenance_view_names = set(urlpattern.name for urlpattern in urlpatterns)
    all_view_names = set(get_resolver().reverse_dict.keys())
    assert provenance_view_names & all_view_names == set()
