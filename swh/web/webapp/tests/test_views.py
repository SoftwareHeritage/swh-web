# Copyright (C) 2022-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information
from datetime import datetime
from pathlib import Path

from django.templatetags.static import static
from django.utils import timezone

from swh.web.tests.helpers import check_html_get_response, check_http_get_response
from swh.web.utils import reverse
from swh.web.webapp.urls import SWH_FAVICON


def test_homepage_view(client):
    url = reverse("swh-web-homepage")
    check_html_get_response(client, url, status_code=200, template_used="homepage.html")


def test_stat_counters_view(client):
    url = reverse("stat-counters")
    check_http_get_response(client, url, status_code=200)


def test_js_reverse_view(client):
    url = reverse("js-reverse")
    check_http_get_response(client, url, status_code=200)


def test_favicon_view(client):
    url = reverse("favicon")
    resp = check_http_get_response(client, url, status_code=301)
    assert resp["location"] == static(SWH_FAVICON)


def test_securitytxt_static(settings):
    security_txt = Path(settings.STATIC_DIR) / "security.txt"
    # static/security.txt contains a static expiration date, this test will fail
    # if it expires in less than 30 days so we can check the file content is still
    # valid
    expiration_date = datetime.fromisoformat(
        security_txt.read_text().splitlines()[1].split(": ")[1]
    )
    delta = expiration_date - timezone.now()
    assert delta.days > 30
