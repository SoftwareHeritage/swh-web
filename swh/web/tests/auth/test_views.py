# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from urllib.parse import urljoin, urlparse
import uuid

from django.http import QueryDict
from django.contrib.auth.models import AnonymousUser, User

import pytest

from swh.web.auth.models import OIDCUser
from swh.web.auth.utils import OIDC_SWH_WEB_CLIENT_ID
from swh.web.common.utils import reverse
from swh.web.tests.django_asserts import assert_template_used, assert_contains
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
    response = client.get(login_url)
    request = response.wsgi_request

    # should redirect to Keycloak authentication page in order
    # for a user to login with its username / password
    assert response.status_code == 302
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

    # login process finalization
    response = client.get(login_complete_url)
    request = response.wsgi_request

    # should redirect to root url by default
    assert response.status_code == 302
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
    response = client.get(oidc_logout_url)
    request = response.wsgi_request

    # should redirect to logout page
    assert response.status_code == 302
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
    response = client.get(login_url)
    request = response.wsgi_request

    # should render an error page
    assert response.status_code == 500
    assert_template_used(response, "error.html")

    # no users should be logged in
    assert isinstance(request.user, AnonymousUser)


# Simulate possible errors with OpenID Connect in the login complete view.


def test_oidc_login_complete_view_no_login_data(client, mocker):
    # user initiates login process
    login_url = reverse("oidc-login-complete")
    response = client.get(login_url)

    # should render an error page
    assert_template_used(response, "error.html")
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
    response = client.get(login_url)
    request = response.wsgi_request

    # should render an error page
    assert_template_used(response, "error.html")
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

    response = client.get(login_url)
    request = response.wsgi_request

    # should render an error page
    assert_template_used(response, "error.html")
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

    response = client.get(login_url)
    request = response.wsgi_request

    # should render an error page
    assert_template_used(response, "error.html")
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
    response = client.get(logout_url)
    request = response.wsgi_request

    # should render an error page
    assert_template_used(response, "error.html")
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
    response = client.get(login_url)
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

    # login process finalization
    response = client.get(login_complete_url)
    request = response.wsgi_request

    # should redirect to logout page
    assert response.status_code == 302
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
