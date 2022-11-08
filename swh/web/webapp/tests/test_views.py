# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.templatetags.static import static

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
