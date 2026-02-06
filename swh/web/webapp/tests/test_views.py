# Copyright (C) 2022-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime
from pathlib import Path

from django.templatetags.static import static
from django.utils import timezone

from swh.web import config
from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.helpers import check_html_get_response, check_http_get_response
from swh.web.utils import reverse
from swh.web.webapp.urls import SWH_FAVICON


def test_homepage_view(client):
    url = reverse("swh-web-homepage")
    check_html_get_response(client, url, status_code=200, template_used="homepage.html")


def test_homepage_view_no_counters_config(client, mocker):
    updated_config = dict(config.get_config())
    updated_config.pop("counters")
    mocker.patch.object(config, "swhweb_config", updated_config)
    url = reverse("swh-web-homepage")
    resp = check_html_get_response(
        client, url, status_code=200, template_used="homepage.html"
    )
    assert_not_contains(resp, "swh-counter")


def test_homepage_view_no_counters(client, mocker):
    mock_archive = mocker.patch("swh.web.webapp.urls.archive")
    mock_archive.stat_counters.return_value = {}
    url = reverse("swh-web-homepage")
    resp = check_html_get_response(
        client, url, status_code=200, template_used="homepage.html"
    )
    assert_not_contains(resp, "swh-counter")


def test_homepage_view_counters_missing(client, mocker):
    mock_archive = mocker.patch("swh.web.webapp.urls.archive")
    mock_archive.stat_counters.return_value = {
        "content": 150,
        "directory": 45,
        "revision": 78,
    }
    url = reverse("swh-web-homepage")
    resp = check_html_get_response(
        client, url, status_code=200, template_used="homepage.html"
    )
    assert_contains(resp, "swh-content-count")
    assert_contains(resp, "swh-directory-count")
    assert_contains(resp, "swh-revision-count")
    assert_not_contains(resp, "swh-person-count")
    assert_not_contains(resp, "swh-origin-count")
    assert_not_contains(resp, "swh-release-count")


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
