# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.urls.exceptions import NoReverseMatch

from swh.web.utils import reverse


@pytest.mark.django_db
def test_admin_deactivate(client, staff_user, django_settings):
    """Check admin site feature is deactivated when the swh.web.admin django
    application is not in installed apps."""

    assert reverse("admin:index") is not None

    django_settings.SWH_DJANGO_APPS = [
        app for app in django_settings.SWH_DJANGO_APPS if app != "swh.web.admin"
    ]

    with pytest.raises(NoReverseMatch, match="'admin' is not a registered namespace"):
        reverse("admin:index")
