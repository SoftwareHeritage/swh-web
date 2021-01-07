# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


import pytest

from django.core.cache import cache
from django.test import modify_settings

from swh.web.common.utils import reverse
from swh.web.tests.utils import check_html_get_response

from .keycloak_mock import mock_keycloak


@pytest.mark.django_db
@modify_settings(
    MIDDLEWARE={"remove": ["swh.web.auth.middlewares.OIDCSessionExpiredMiddleware"]}
)
def test_oidc_session_expired_middleware_disabled(client, mocker):
    # authenticate user
    kc_oidc_mock = mock_keycloak(mocker)
    client.login(code="", code_verifier="", redirect_uri="")
    kc_oidc_mock.authorization_code.assert_called()

    url = reverse("swh-web-homepage")

    # visit url first to get user from response
    response = check_html_get_response(client, url, status_code=200)

    # simulate OIDC session expiration
    cache.delete(f"oidc_user_{response.wsgi_request.user.id}")

    # no redirection when session has expired
    check_html_get_response(client, url, status_code=200)


@pytest.mark.django_db
def test_oidc_session_expired_middleware_enabled(client, mocker):
    # authenticate user
    kc_oidc_mock = mock_keycloak(mocker)
    client.login(code="", code_verifier="", redirect_uri="")
    kc_oidc_mock.authorization_code.assert_called()

    url = reverse("swh-web-homepage")

    # visit url first to get user from response
    response = check_html_get_response(client, url, status_code=200)

    # simulate OIDC session expiration
    cache.delete(f"oidc_user_{response.wsgi_request.user.id}")

    # should redirect to logout page
    resp = check_html_get_response(client, url, status_code=302)
    silent_refresh_url = reverse(
        "logout", query_params={"next_path": url, "remote_user": 1}
    )
    assert resp["location"] == silent_refresh_url
