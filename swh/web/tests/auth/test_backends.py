# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta
from unittest.mock import Mock

import pytest

from django.conf import settings
from django.contrib.auth import authenticate, get_backends
from rest_framework.exceptions import AuthenticationFailed

from swh.web.auth.backends import OIDCBearerTokenAuthentication
from swh.web.auth.models import OIDCUser
from swh.web.common.utils import reverse

from . import sample_data
from .keycloak_mock import mock_keycloak


def _authenticate_user(request_factory):
    request = request_factory.get(reverse("oidc-login-complete"))

    return authenticate(
        request=request,
        code="some-code",
        code_verifier="some-code-verifier",
        redirect_uri="https://localhost:5004",
    )


def _check_authenticated_user(user, decoded_token, kc_oidc_mock):
    assert user is not None
    assert isinstance(user, OIDCUser)
    assert user.id != 0
    assert user.username == decoded_token["preferred_username"]
    assert user.password == ""
    assert user.first_name == decoded_token["given_name"]
    assert user.last_name == decoded_token["family_name"]
    assert user.email == decoded_token["email"]
    assert user.is_staff == ("/staff" in decoded_token["groups"])
    assert user.sub == decoded_token["sub"]
    resource_access = decoded_token.get("resource_access", {})
    resource_access_client = resource_access.get(kc_oidc_mock, {})
    assert user.permissions == set(resource_access_client.get("roles", []))


@pytest.mark.django_db
def test_oidc_code_pkce_auth_backend_success(mocker, request_factory):
    """
    Checks successful login based on OpenID Connect with PKCE extension
    Django authentication backend (login from Web UI).
    """
    kc_oidc_mock = mock_keycloak(mocker, user_groups=["/staff"])
    oidc_profile = sample_data.oidc_profile
    user = _authenticate_user(request_factory)

    decoded_token = kc_oidc_mock.decode_token(user.access_token)
    _check_authenticated_user(user, decoded_token, kc_oidc_mock)

    auth_datetime = datetime.fromtimestamp(decoded_token["auth_time"])
    exp_datetime = datetime.fromtimestamp(decoded_token["exp"])
    refresh_exp_datetime = auth_datetime + timedelta(
        seconds=oidc_profile["refresh_expires_in"]
    )

    assert user.access_token == oidc_profile["access_token"]
    assert user.expires_at == exp_datetime
    assert user.id_token == oidc_profile["id_token"]
    assert user.refresh_token == oidc_profile["refresh_token"]
    assert user.refresh_expires_at == refresh_exp_datetime
    assert user.scope == oidc_profile["scope"]
    assert user.session_state == oidc_profile["session_state"]

    backend_path = "swh.web.auth.backends.OIDCAuthorizationCodePKCEBackend"
    assert user.backend == backend_path
    backend_idx = settings.AUTHENTICATION_BACKENDS.index(backend_path)
    assert get_backends()[backend_idx].get_user(user.id) == user


@pytest.mark.django_db
def test_oidc_code_pkce_auth_backend_failure(mocker, request_factory):
    """
    Checks failed login based on OpenID Connect with PKCE extension Django
    authentication backend (login from Web UI).
    """
    mock_keycloak(mocker, auth_success=False)

    user = _authenticate_user(request_factory)

    assert user is None


@pytest.mark.django_db
def test_oidc_code_pkce_auth_backend_refresh_token_success(mocker, request_factory):
    """
    Checks access token renewal success using refresh token.
    """
    kc_oidc_mock = mock_keycloak(mocker)

    oidc_profile = sample_data.oidc_profile
    decoded_token = kc_oidc_mock.decode_token(oidc_profile["access_token"])
    new_access_token = "new_access_token"

    def _refresh_token(refresh_token):
        oidc_profile = dict(sample_data.oidc_profile)
        oidc_profile["access_token"] = new_access_token
        return oidc_profile

    def _decode_token(access_token):
        if access_token != new_access_token:
            raise Exception("access token token has expired")
        else:
            return decoded_token

    kc_oidc_mock.decode_token = Mock()
    kc_oidc_mock.decode_token.side_effect = _decode_token
    kc_oidc_mock.refresh_token.side_effect = _refresh_token

    user = _authenticate_user(request_factory)

    kc_oidc_mock.refresh_token.assert_called_with(
        sample_data.oidc_profile["refresh_token"]
    )

    assert user is not None


@pytest.mark.django_db
def test_oidc_code_pkce_auth_backend_refresh_token_failure(mocker, request_factory):
    """
    Checks access token renewal failure using refresh token.
    """
    kc_oidc_mock = mock_keycloak(mocker)

    def _refresh_token(refresh_token):
        raise Exception("OIDC session has expired")

    def _decode_token(access_token):
        raise Exception("access token token has expired")

    kc_oidc_mock.decode_token = Mock()
    kc_oidc_mock.decode_token.side_effect = _decode_token
    kc_oidc_mock.refresh_token.side_effect = _refresh_token

    user = _authenticate_user(request_factory)

    kc_oidc_mock.refresh_token.assert_called_with(
        sample_data.oidc_profile["refresh_token"]
    )

    assert user is None


@pytest.mark.django_db
def test_oidc_code_pkce_auth_backend_permissions(mocker, request_factory):
    """
    Checks that a permission defined with OpenID Connect is correctly mapped
    to a Django one when logging from Web UI.
    """
    permission = "webapp.some-permission"
    mock_keycloak(mocker, user_permissions=[permission])
    user = _authenticate_user(request_factory)
    assert user.has_perm(permission)
    assert user.get_all_permissions() == {permission}
    assert user.get_group_permissions() == {permission}
    assert user.has_module_perms("webapp")
    assert not user.has_module_perms("foo")


@pytest.mark.django_db
def test_drf_oidc_bearer_token_auth_backend_success(mocker, api_request_factory):
    """
    Checks successful login based on OpenID Connect bearer token Django REST
    Framework authentication backend (Web API login).
    """
    url = reverse("api-1-stat-counters")
    drf_auth_backend = OIDCBearerTokenAuthentication()

    kc_oidc_mock = mock_keycloak(mocker)

    refresh_token = sample_data.oidc_profile["refresh_token"]
    access_token = sample_data.oidc_profile["access_token"]

    decoded_token = kc_oidc_mock.decode_token(access_token)

    request = api_request_factory.get(url, HTTP_AUTHORIZATION=f"Bearer {refresh_token}")

    user, _ = drf_auth_backend.authenticate(request)
    _check_authenticated_user(user, decoded_token, kc_oidc_mock)
    # oidc_profile is not filled when authenticating through bearer token
    assert hasattr(user, "access_token") and user.access_token is None


@pytest.mark.django_db
def test_drf_oidc_bearer_token_auth_backend_failure(mocker, api_request_factory):
    """
    Checks failed login based on OpenID Connect bearer token Django REST
    Framework authentication backend (Web API login).
    """
    url = reverse("api-1-stat-counters")
    drf_auth_backend = OIDCBearerTokenAuthentication()

    # simulate a failed authentication with a bearer token in expected format
    mock_keycloak(mocker, auth_success=False)

    refresh_token = sample_data.oidc_profile["refresh_token"]

    request = api_request_factory.get(url, HTTP_AUTHORIZATION=f"Bearer {refresh_token}")

    with pytest.raises(AuthenticationFailed):
        drf_auth_backend.authenticate(request)

    # simulate a failed authentication with an invalid bearer token format
    request = api_request_factory.get(
        url, HTTP_AUTHORIZATION="Bearer invalid-token-format"
    )

    with pytest.raises(AuthenticationFailed):
        drf_auth_backend.authenticate(request)


def test_drf_oidc_auth_invalid_or_missing_auth_type(api_request_factory):
    """
    Checks failed login based on OpenID Connect bearer token Django REST
    Framework authentication backend (Web API login) due to invalid
    authorization header value.
    """
    url = reverse("api-1-stat-counters")
    drf_auth_backend = OIDCBearerTokenAuthentication()

    refresh_token = sample_data.oidc_profile["refresh_token"]

    # Invalid authorization type
    request = api_request_factory.get(url, HTTP_AUTHORIZATION="Foo token")

    with pytest.raises(AuthenticationFailed):
        drf_auth_backend.authenticate(request)

    # Missing authorization type
    request = api_request_factory.get(url, HTTP_AUTHORIZATION=f"{refresh_token}")

    with pytest.raises(AuthenticationFailed):
        drf_auth_backend.authenticate(request)


@pytest.mark.django_db
def test_drf_oidc_bearer_token_auth_backend_permissions(mocker, api_request_factory):
    """
    Checks that a permission defined with OpenID Connect is correctly mapped
    to a Django one when using bearer token authentication.
    """
    permission = "webapp.some-permission"
    mock_keycloak(mocker, user_permissions=[permission])

    drf_auth_backend = OIDCBearerTokenAuthentication()
    refresh_token = sample_data.oidc_profile["refresh_token"]
    url = reverse("api-1-stat-counters")
    request = api_request_factory.get(url, HTTP_AUTHORIZATION=f"Bearer {refresh_token}")
    user, _ = drf_auth_backend.authenticate(request)

    assert user.has_perm(permission)
    assert user.get_all_permissions() == {permission}
    assert user.get_group_permissions() == {permission}
    assert user.has_module_perms("webapp")
    assert not user.has_module_perms("foo")
