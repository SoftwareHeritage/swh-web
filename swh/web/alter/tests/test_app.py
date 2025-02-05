# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.helpers import check_html_get_response
from swh.web.utils import reverse


@pytest.mark.parametrize("activated", [True, False])
def test_activated(client, django_settings, activated):
    if not activated:
        django_settings.SWH_DJANGO_APPS = [
            app for app in django_settings.SWH_DJANGO_APPS if app != "swh.web.alter"
        ]

    resp = check_html_get_response(
        client,
        reverse("swh-web-homepage"),
        status_code=200,
        template_used="includes/footer.html",
    )
    if activated:
        assert_contains(resp, "swh-web-alter-content-policy")
    else:
        assert_not_contains(resp, "swh-web-alter-content-policy")
