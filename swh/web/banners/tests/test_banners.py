# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.helpers import check_html_get_response
from swh.web.utils import reverse


def test_fundraising_banner(client, requests_mock):
    nb_donations = 40
    requests_mock.get(
        "https://www.softwareheritage.org/give-api/v1/forms/",
        json={"forms": [{"stats": {"total": {"donations": nb_donations}}}]},
    )
    url = reverse("swh-fundraising-banner")
    resp = check_html_get_response(
        client, url, status_code=200, template_used="fundraising-banner.html"
    )
    assert_contains(resp, f'aria-valuenow="{nb_donations}"')


def test_fundraising_banner_languages(client, requests_mock):
    nb_donations = 40
    requests_mock.get(
        "https://www.softwareheritage.org/give-api/v1/forms/",
        json={"forms": [{"stats": {"total": {"donations": nb_donations}}}]},
    )

    url = reverse("swh-fundraising-banner")
    resp = check_html_get_response(
        client, url, status_code=200, template_used="fundraising-banner.html"
    )
    assert_contains(resp, "Become a donor")

    url = reverse("swh-fundraising-banner", query_params={"lang": "fr"})
    resp = check_html_get_response(
        client, url, status_code=200, template_used="fundraising-banner.html"
    )
    assert_contains(resp, "Devenez donateur")


def test_fundraising_banner_give_api_error(client, requests_mock):
    requests_mock.get(
        "https://www.softwareheritage.org/give-api/v1/forms/",
        exc=Exception("HTTP error"),
    )
    url = reverse("swh-fundraising-banner")
    resp = check_html_get_response(
        client, url, status_code=200, template_used="fundraising-banner.html"
    )
    assert_not_contains(resp, 'class="progress-bar"')


def test_downtime_banner(client):
    url = reverse("swh-downtime-banner")
    resp = check_html_get_response(
        client, url, status_code=200, template_used="./downtime-banner.html"
    )
    assert_contains(resp, "Downtime expected for SWH services")
