# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.urls import get_resolver


def test_swh_web_urls_have_trailing_slash():
    urls = set(
        value[1]
        for key, value in get_resolver().reverse_dict.items()
        if key != "browse-swhid"  # (see T3234)
    )
    for url in urls:
        if url != "$":
            assert url.endswith("/$")


def test_urls_registration_error_for_not_found_django_app(django_settings):
    app_name = "swh.web.foobar"
    with pytest.raises(
        AssertionError, match=f"Django application {app_name} not found !"
    ):
        django_settings.SWH_DJANGO_APPS = django_settings.SWH_DJANGO_APPS + [app_name]
