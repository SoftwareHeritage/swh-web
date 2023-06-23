# Copyright (C) 2021-2023  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from copy import deepcopy
import random

from pkg_resources import get_distribution
import pytest

from django.conf import settings

from swh.web.auth.utils import ADMIN_LIST_DEPOSIT_PERMISSION
from swh.web.config import SWH_WEB_SERVER_NAME, SWH_WEB_STAGING_SERVER_NAMES, get_config
from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.helpers import check_http_get_response, create_django_permission
from swh.web.utils import reverse

swh_web_version = get_distribution("swh.web").version


def test_layout_without_ribbon(client, config_updater):
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(
        client, url, status_code=200, server_name=SWH_WEB_SERVER_NAME
    )
    assert_not_contains(resp, "swh-corner-ribbon")

    config_updater({"show_corner_ribbon": False})
    resp = check_http_get_response(
        client, url, status_code=200, server_name="localhost"
    )
    assert_not_contains(resp, "swh-corner-ribbon")


def test_layout_with_staging_ribbon(client):
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(
        client,
        url,
        status_code=200,
        server_name=random.choice(SWH_WEB_STAGING_SERVER_NAMES),
    )
    assert_contains(resp, "swh-corner-ribbon")
    assert_contains(resp, "Staging")
    assert_contains(resp, f"v{swh_web_version}")


def test_layout_with_development_ribbon(client):
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(
        client,
        url,
        status_code=200,
        server_name="localhost",
    )
    assert_contains(resp, "swh-corner-ribbon")
    assert_contains(resp, "Development")
    assert_contains(resp, f"v{swh_web_version.split('+')[0]}")


def test_layout_with_oidc_auth_enabled(client):
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_contains(resp, reverse("oidc-login"))


def test_layout_without_oidc_auth_enabled(client, django_settings, mocker):
    config = deepcopy(get_config())
    config["keycloak"]["server_url"] = ""
    mock_get_config = mocker.patch("swh.web.config.get_config")
    mock_get_config.return_value = config

    django_settings.LOGIN_URL = "login"
    django_settings.LOGOUT_URL = "logout"
    django_settings.MIDDLEWARE = [
        mid
        for mid in django_settings.MIDDLEWARE
        if mid != "swh.auth.django.middlewares.OIDCSessionExpiredMiddleware"
    ]

    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_contains(resp, reverse(settings.LOGIN_URL))


def test_layout_swh_web_version_number_display(client):
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_contains(resp, f"swh-web v{swh_web_version}")


@pytest.mark.django_db
def test_layout_no_deposit_admin_for_anonymous_user(client):
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_not_contains(resp, "swh-deposit-admin-link")


@pytest.mark.django_db
def test_layout_deposit_admin_for_staff_user(client, staff_user):
    client.force_login(staff_user)
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_contains(resp, "swh-deposit-admin-link")


@pytest.mark.django_db
def test_layout_deposit_admin_for_user_with_permission(client, regular_user):
    regular_user.user_permissions.add(
        create_django_permission(ADMIN_LIST_DEPOSIT_PERMISSION)
    )
    client.force_login(regular_user)
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_contains(resp, "swh-deposit-admin-link")


def test_layout_no_matomo_by_default(client):
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_not_contains(resp, "https://piwik.inria.fr")


def test_layout_matomo_activated(client, config_updater):
    matomo_url = "https://piwik.inria.fr"
    site_id = 59
    config_updater({"matomo": {"url": matomo_url, "site_id": site_id}})
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_contains(resp, matomo_url)
    assert_contains(resp, f"['setSiteId', '{site_id}']")


def test_top_bar_no_links(client, config_updater):
    config_updater({"top_bar": {}, "status": {}})
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_not_contains(resp, "swh-topbar-link")
    assert_not_contains(resp, "swh-topbar-donate-link")
    assert_not_contains(resp, "swh-current-status")


def test_top_bar_custom_links(client, config_updater):
    home_link = "https://example.org/"
    dev_link = "https://example.org/dev"
    doc_link = "https://example.org/doc"
    donate_link = "https://example.org/donate"
    status_link = "https://example.org/status"

    config_updater(
        {
            "top_bar": {
                "links": {
                    "Home": home_link,
                    "Development": dev_link,
                    "Documentation": doc_link,
                },
                "donate_link": donate_link,
            },
            "status": {"server_url": status_link},
        }
    )
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)

    assert_contains(resp, "swh-topbar-link", 3)
    assert_contains(resp, "swh-topbar-donate-link")
    assert_contains(resp, "swh-current-status")

    assert_contains(resp, home_link)
    assert_contains(resp, dev_link)
    assert_contains(resp, doc_link)
    assert_contains(resp, donate_link)
    assert_contains(resp, status_link)
