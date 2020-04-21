# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime

from django.test import modify_settings
import pytest

from .keycloak_mock import mock_keycloak

from swh.web.common.utils import reverse


@pytest.mark.django_db
@modify_settings(
    MIDDLEWARE={"remove": ["swh.web.auth.middlewares.OIDCSessionRefreshMiddleware"]}
)
def test_oidc_session_refresh_middleware_disabled(client, mocker):
    # authenticate but make session expires immediately
    kc_oidc_mock = mock_keycloak(mocker, exp=int(datetime.now().timestamp()))
    client.login(code="", code_verifier="", redirect_uri="")
    kc_oidc_mock.authorization_code.assert_called()

    url = reverse("swh-web-homepage")
    resp = client.get(url)
    # no redirection for silent refresh
    assert resp.status_code != 302


@pytest.mark.django_db
def test_oidc_session_refresh_middleware_enabled(client, mocker):
    # authenticate but make session expires immediately
    kc_oidc_mock = mock_keycloak(mocker, exp=int(datetime.now().timestamp()))
    client.login(code="", code_verifier="", redirect_uri="")
    kc_oidc_mock.authorization_code.assert_called()

    url = reverse("swh-web-homepage")
    resp = client.get(url)

    # should redirect for silent session refresh
    assert resp.status_code == 302
    silent_refresh_url = reverse(
        "oidc-login", query_params={"next_path": url, "prompt": "none"}
    )
    assert resp["location"] == silent_refresh_url
