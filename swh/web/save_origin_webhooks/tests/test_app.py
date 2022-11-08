# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.urls import get_resolver

from swh.web.save_origin_webhooks.urls import urlpatterns


@pytest.mark.django_db
def test_save_origin_webhooks_deactivate(django_settings):
    """Check webhooks feature is deactivated when the swh.web.save_origin_webhooks
    django application is not in installed apps."""

    django_settings.SWH_DJANGO_APPS = [
        app
        for app in django_settings.SWH_DJANGO_APPS
        if app != "swh.web.save_origin_webhooks"
    ]

    save_origin_webhooks_view_names = set(urlpattern.name for urlpattern in urlpatterns)
    all_view_names = set(get_resolver().reverse_dict.keys())
    assert save_origin_webhooks_view_names & all_view_names == set()
