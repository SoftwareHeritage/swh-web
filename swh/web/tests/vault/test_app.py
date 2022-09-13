# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.urls import get_resolver

from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.helpers import check_html_get_response
from swh.web.utils import reverse
from swh.web.vault.urls import urlpatterns


@pytest.mark.django_db
def test_banners_deactivate(client, django_settings, directory):
    """Check vault feature is deactivated when the swh.web.vault django
    application is not in installed apps."""

    url = reverse("browse-directory", url_args={"sha1_git": directory})

    resp = check_html_get_response(client, url, status_code=200)
    assert_contains(resp, "swh-vault-item")
    assert_contains(resp, "swh-vault-download")

    django_settings.SWH_DJANGO_APPS = [
        app for app in django_settings.SWH_DJANGO_APPS if app != "swh.web.vault"
    ]

    resp = check_html_get_response(client, url, status_code=200)
    assert_not_contains(resp, "swh-vault-item")
    assert_not_contains(resp, "swh-vault-download")

    vault_view_names = set(urlpattern.name for urlpattern in urlpatterns)
    all_view_names = set(get_resolver().reverse_dict.keys())
    assert vault_view_names & all_view_names == set()
