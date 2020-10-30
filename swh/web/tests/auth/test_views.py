# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from urllib.parse import urljoin, urlparse
import uuid

from keycloak.exceptions import KeycloakError
import pytest

from django.contrib.auth.models import AnonymousUser, User
from django.http import QueryDict

from swh.web.auth.models import OIDCUser, OIDCUserOfflineTokens
from swh.web.auth.utils import OIDC_SWH_WEB_CLIENT_ID
from swh.web.common.utils import reverse
from swh.web.config import get_config
from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.utils import (
    check_html_get_response,
    check_http_get_response,
    check_http_post_response,
)
from swh.web.urls import _default_view as homepage_view

from . import sample_data
from .keycloak_mock import mock_keycloak


@pytest.mark.django_db
def test_oidc_login_views_success(client, mocker):
    """
    Simulate a successful login authentication with OpenID Connect
    authorization code flow with PKCE.
    """
    # mock Keycloak client
    kc_oidc_mock = mock_keycloak(mocker)

    # user initiates login process
    login_url = reverse("oidc-login")

    # should redirect to Keycloak authentication page in order
    # for a user to login with its username / password
    response = check_html_get_response(client, login_url, status_code=302)
    request = response.wsgi_request

    assert isinstance(request.user, AnonymousUser)

    parsed_url = urlparse(response["location"])

    authorization_url = kc_oidc_mock.well_known()["authorization_endpoint"]
    query_dict = QueryDict(parsed_url.query)

    # check redirect url is valid
    assert urljoin(response["location"], parsed_url.path) == authorization_url
    assert "client_id" in query_dict
    assert query_dict["client_id"] == OIDC_SWH_WEB_CLIENT_ID
    assert "response_type" in query_dict
    assert query_dict["response_type"] == "code"
    assert "redirect_uri" in query_dict
    assert query_dict["redirect_uri"] == reverse("oidc-login-complete", request=request)
    assert "code_challenge_method" in query_dict
    assert query_dict["code_challenge_method"] == "S256"
    assert "scope" in query_dict
    assert query_dict["scope"] == "openid"
    assert "state" in query_dict
    assert "code_challenge" in query_dict

    # check a login_data has been registered in user session
    assert "login_data" in request.session
    login_data = request.session["login_data"]
    assert "code_verifier" in login_data
    assert "state" in login_data
    assert "redirect_uri" in login_data
    assert login_data["redirect_uri"] == query_dict["redirect_uri"]

    # once a user has identified himself in Keycloak, he is
    # redirected to the 'oidc-login-complete' view to
    # login in Django.

    # generate authorization code / session state in the same
    # manner as Keycloak
    code = f"{str(uuid.uuid4())}.{str(uuid.uuid4())}.{str(uuid.uuid4())}"
    session_state = str(uuid.uuid4())

    login_complete_url = reverse(
        "oidc-login-complete",
        query_params={
            "code": code,
            "state": login_data["state"],
            "session_state": session_state,
        },
    )

    # login process finalization, should redirect to root url by default
    response = check_html_get_response(client, login_complete_url, status_code=302)
    request = response.wsgi_request

    assert response["location"] == request.build_absolute_uri("/")

    # user should be authenticated
    assert isinstance(request.user, OIDCUser)

    # check remote user has not been saved to Django database
    with pytest.raises(User.DoesNotExist):
        User.objects.get(username=request.user.username)


@pytest.mark.django_db
def test_oidc_logout_view_success(client, mocker):
    """
    Simulate a successful logout operation with OpenID Connect.
    """
    # mock Keycloak client
    kc_oidc_mock = mock_keycloak(mocker)
    # login our test user
    client.login(code="", code_verifier="", redirect_uri="")
    kc_oidc_mock.authorization_code.assert_called()

    # user initiates logout
    oidc_logout_url = reverse("oidc-logout")

    # should redirect to logout page
    response = check_html_get_response(client, oidc_logout_url, status_code=302)
    request = response.wsgi_request

    logout_url = reverse("logout", query_params={"remote_user": 1})
    assert response["location"] == request.build_absolute_uri(logout_url)

    # should have been logged out in Keycloak
    kc_oidc_mock.logout.assert_called_with(sample_data.oidc_profile["refresh_token"])

    # check effective logout in Django
    assert isinstance(request.user, AnonymousUser)


@pytest.mark.django_db
def test_oidc_login_view_failure(client, mocker):
    """
    Simulate a failed authentication with OpenID Connect.
    """
    # mock Keycloak client
    mock_keycloak(mocker, auth_success=False)

    # user initiates login process
    login_url = reverse("oidc-login")
    # should render an error page
    response = check_html_get_response(
        client, login_url, status_code=500, template_used="error.html"
    )
    request = response.wsgi_request

    # no users should be logged in
    assert isinstance(request.user, AnonymousUser)


# Simulate possible errors with OpenID Connect in the login complete view.


def test_oidc_login_complete_view_no_login_data(client, mocker):
    # user initiates login process
    login_url = reverse("oidc-login-complete")
    # should render an error page
    response = check_html_get_response(
        client, login_url, status_code=500, template_used="error.html"
    )

    assert_contains(
        response, "Login process has not been initialized.", status_code=500
    )


def test_oidc_login_complete_view_missing_parameters(client, mocker):
    # simulate login process has been initialized
    session = client.session
    session["login_data"] = {
        "code_verifier": "",
        "state": str(uuid.uuid4()),
        "redirect_uri": "",
        "next_path": "",
        "prompt": "",
    }
    session.save()

    # user initiates login process
    login_url = reverse("oidc-login-complete")
    # should render an error page
    response = check_html_get_response(
        client, login_url, status_code=400, template_used="error.html"
    )
    request = response.wsgi_request
    assert_contains(
        response, "Missing query parameters for authentication.", status_code=400
    )

    # no user should be logged in
    assert isinstance(request.user, AnonymousUser)


def test_oidc_login_complete_wrong_csrf_token(client, mocker):
    # mock Keycloak client
    mock_keycloak(mocker)

    # simulate login process has been initialized
    session = client.session
    session["login_data"] = {
        "code_verifier": "",
        "state": str(uuid.uuid4()),
        "redirect_uri": "",
        "next_path": "",
        "prompt": "",
    }
    session.save()

    # user initiates login process
    login_url = reverse(
        "oidc-login-complete", query_params={"code": "some-code", "state": "some-state"}
    )

    # should render an error page
    response = check_html_get_response(
        client, login_url, status_code=400, template_used="error.html"
    )
    request = response.wsgi_request
    assert_contains(
        response, "Wrong CSRF token, aborting login process.", status_code=400
    )

    # no user should be logged in
    assert isinstance(request.user, AnonymousUser)


@pytest.mark.django_db
def test_oidc_login_complete_wrong_code_verifier(client, mocker):
    # mock Keycloak client
    mock_keycloak(mocker, auth_success=False)

    # simulate login process has been initialized
    session = client.session
    session["login_data"] = {
        "code_verifier": "",
        "state": str(uuid.uuid4()),
        "redirect_uri": "",
        "next_path": "",
        "prompt": "",
    }
    session.save()

    # check authentication error is reported
    login_url = reverse(
        "oidc-login-complete",
        query_params={"code": "some-code", "state": session["login_data"]["state"]},
    )

    # should render an error page
    response = check_html_get_response(
        client, login_url, status_code=500, template_used="error.html"
    )
    request = response.wsgi_request
    assert_contains(response, "User authentication failed.", status_code=500)

    # no user should be logged in
    assert isinstance(request.user, AnonymousUser)


@pytest.mark.django_db
def test_oidc_logout_view_failure(client, mocker):
    """
    Simulate a failed logout operation with OpenID Connect.
    """
    # mock Keycloak client
    kc_oidc_mock = mock_keycloak(mocker)
    # login our test user
    client.login(code="", code_verifier="", redirect_uri="")

    err_msg = "Authentication server error"
    kc_oidc_mock.logout.side_effect = Exception(err_msg)

    # user initiates logout process
    logout_url = reverse("oidc-logout")
    # should render an error page
    response = check_html_get_response(
        client, logout_url, status_code=500, template_used="error.html"
    )
    request = response.wsgi_request
    assert_contains(response, err_msg, status_code=500)

    # user should be logged out from Django anyway
    assert isinstance(request.user, AnonymousUser)


@pytest.mark.django_db
def test_oidc_silent_refresh_failure(client, mocker):
    # mock Keycloak client
    mock_keycloak(mocker)

    next_path = reverse("swh-web-homepage")

    # silent session refresh initialization
    login_url = reverse(
        "oidc-login", query_params={"next_path": next_path, "prompt": "none"}
    )
    response = check_http_get_response(client, login_url, status_code=302)
    request = response.wsgi_request

    login_data = request.session["login_data"]

    # check prompt value has been registered in user session
    assert "prompt" in login_data
    assert login_data["prompt"] == "none"

    # simulate a failed silent session refresh
    session_state = str(uuid.uuid4())

    login_complete_url = reverse(
        "oidc-login-complete",
        query_params={
            "error": "login_required",
            "state": login_data["state"],
            "session_state": session_state,
        },
    )

    # login process finalization, should redirect to logout page
    response = check_http_get_response(client, login_complete_url, status_code=302)
    request = response.wsgi_request
    logout_url = reverse(
        "logout", query_params={"next_path": next_path, "remote_user": 1}
    )
    assert response["location"] == logout_url


def test_view_rendering_when_user_not_set_in_request(request_factory):
    request = request_factory.get("/")
    # Django RequestFactory do not set any user by default
    assert not hasattr(request, "user")

    response = homepage_view(request)
    assert response.status_code == 200


def test_oidc_generate_bearer_token_anonymous_user(client):
    """
    Anonymous user should be refused access with forbidden response.
    """
    url = reverse("oidc-generate-bearer-token")
    check_http_post_response(client, url, data={"password": "secret"}, status_code=403)


def _generate_bearer_token(client, password):
    client.login(
        code="code", code_verifier="code-verifier", redirect_uri="redirect-uri"
    )
    url = reverse("oidc-generate-bearer-token")
    return client.post(
        url, data={"password": password}, content_type="application/json"
    )


@pytest.mark.django_db
def test_oidc_generate_bearer_token_authenticated_user_success(client, mocker):
    """
    User with correct credentials should be allowed to generate a token.
    """
    kc_mock = mock_keycloak(mocker)
    password = "secret"
    response = _generate_bearer_token(client, password)
    user = response.wsgi_request.user
    assert response.status_code == 200
    assert response.content.decode("ascii") == kc_mock.offline_token(
        username=user.username, password=password
    )


@pytest.mark.django_db
def test_oidc_generate_bearer_token_authenticated_user_failure(client, mocker):
    """
    User with wrong credentials should not be allowed to generate a token.
    """
    response_code = 401
    kc_mock = mock_keycloak(mocker)
    kc_mock.offline_token.side_effect = KeycloakError(
        error_message="Invalid password", response_code=response_code
    )
    response = _generate_bearer_token(client, password="invalid-password")
    assert response.status_code == response_code


def test_oidc_list_bearer_tokens_anonymous_user(client):
    """
    Anonymous user should be refused access with forbidden response.
    """
    url = reverse(
        "oidc-list-bearer-tokens", query_params={"draw": 1, "start": 0, "length": 10}
    )
    check_http_get_response(client, url, status_code=403)


@pytest.mark.django_db
def test_oidc_list_bearer_tokens(client, mocker):
    """
    User with correct credentials should be allowed to list his tokens.
    """
    mock_keycloak(mocker)
    nb_tokens = 3
    password = "secret"

    for _ in range(nb_tokens):
        response = _generate_bearer_token(client, password)

    url = reverse(
        "oidc-list-bearer-tokens", query_params={"draw": 1, "start": 0, "length": 10}
    )

    response = check_http_get_response(client, url, status_code=200)
    tokens_data = list(reversed(json.loads(response.content.decode("utf-8"))["data"]))

    for oidc_token in OIDCUserOfflineTokens.objects.all():
        assert (
            oidc_token.creation_date.isoformat()
            == tokens_data[oidc_token.id - 1]["creation_date"]
        )


def test_oidc_get_bearer_token_anonymous_user(client):
    """
    Anonymous user should be refused access with forbidden response.
    """
    url = reverse("oidc-get-bearer-token")
    check_http_post_response(client, url, status_code=403)


@pytest.mark.django_db
def test_oidc_get_bearer_token(client, mocker):
    """
    User with correct credentials should be allowed to display a token.
    """
    mock_keycloak(mocker)
    nb_tokens = 3
    password = "secret"

    for i in range(nb_tokens):
        response = _generate_bearer_token(client, password)
        token = response.content

        url = reverse("oidc-get-bearer-token")

        response = check_http_post_response(
            client,
            url,
            status_code=200,
            data={"password": password, "token_id": i + 1},
            content_type="text/plain",
        )
        assert response.content == token


@pytest.mark.django_db
def test_oidc_get_bearer_token_invalid_password(client, mocker):
    """
    User with wrong credentials should not be allowed to display a token.
    """
    mock_keycloak(mocker)
    password = "secret"
    _generate_bearer_token(client, password)

    url = reverse("oidc-get-bearer-token")
    check_http_post_response(
        client,
        url,
        status_code=401,
        data={"password": "invalid-password", "token_id": 1},
    )


def test_oidc_revoke_bearer_tokens_anonymous_user(client):
    """
    Anonymous user should be refused access with forbidden response.
    """
    url = reverse("oidc-revoke-bearer-tokens")
    check_http_post_response(client, url, status_code=403)


@pytest.mark.django_db
def test_oidc_revoke_bearer_tokens(client, mocker):
    """
    User with correct credentials should be allowed to revoke tokens.
    """
    mock_keycloak(mocker)
    nb_tokens = 3
    password = "secret"

    for _ in range(nb_tokens):
        _generate_bearer_token(client, password)

    url = reverse("oidc-revoke-bearer-tokens")

    check_http_post_response(
        client, url, status_code=200, data={"password": password, "token_ids": [1]},
    )
    assert len(OIDCUserOfflineTokens.objects.all()) == 2

    check_http_post_response(
        client, url, status_code=200, data={"password": password, "token_ids": [2, 3]},
    )
    assert len(OIDCUserOfflineTokens.objects.all()) == 0


@pytest.mark.django_db
def test_oidc_revoke_bearer_token_invalid_password(client, mocker):
    """
    User with wrong credentials should not be allowed to revoke tokens.
    """
    mock_keycloak(mocker)
    password = "secret"

    _generate_bearer_token(client, password)

    url = reverse("oidc-revoke-bearer-tokens")

    check_http_post_response(
        client,
        url,
        status_code=401,
        data={"password": "invalid-password", "token_ids": [1]},
    )


def test_oidc_profile_view_anonymous_user(client):
    """
    Non authenticated users should be redirected to login page when
    requesting profile view.
    """
    url = reverse("oidc-profile")
    login_url = reverse("oidc-login", query_params={"next_path": url})
    resp = check_html_get_response(client, url, status_code=302)
    assert resp["location"] == login_url


@pytest.mark.django_db
def test_oidc_profile_view(client, mocker):
    """
    Authenticated users should be able to request the profile page
    and link to Keycloak account UI should be present.
    """
    url = reverse("oidc-profile")
    kc_config = get_config()["keycloak"]
    user_permissions = ["perm1", "perm2"]
    mock_keycloak(mocker, user_permissions=user_permissions)
    client.login(code="", code_verifier="", redirect_uri="")
    resp = check_html_get_response(
        client, url, status_code=200, template_used="auth/profile.html"
    )
    user = resp.wsgi_request.user
    kc_account_url = (
        f"{kc_config['server_url']}realms/{kc_config['realm_name']}/account/"
    )
    assert_contains(resp, kc_account_url)
    assert_contains(resp, user.username)
    assert_contains(resp, user.first_name)
    assert_contains(resp, user.last_name)
    assert_contains(resp, user.email)
    for perm in user_permissions:
        assert_contains(resp, perm)
