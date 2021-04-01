# Copyright (C) 2020-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from urllib.parse import urljoin, urlparse
import uuid

import pytest

from django.http import QueryDict

from swh.web.auth.models import OIDCUserOfflineTokens
from swh.web.auth.utils import OIDC_SWH_WEB_CLIENT_ID, decrypt_data
from swh.web.common.utils import reverse
from swh.web.config import get_config
from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.utils import (
    check_html_get_response,
    check_http_get_response,
    check_http_post_response,
)
from swh.web.urls import _default_view as homepage_view


def _check_oidc_login_code_flow_data(
    request, response, keycloak_oidc, redirect_uri, scope="openid"
):
    parsed_url = urlparse(response["location"])

    authorization_url = keycloak_oidc.well_known()["authorization_endpoint"]
    query_dict = QueryDict(parsed_url.query)

    # check redirect url is valid
    assert urljoin(response["location"], parsed_url.path) == authorization_url
    assert "client_id" in query_dict
    assert query_dict["client_id"] == OIDC_SWH_WEB_CLIENT_ID
    assert "response_type" in query_dict
    assert query_dict["response_type"] == "code"
    assert "redirect_uri" in query_dict
    assert query_dict["redirect_uri"] == redirect_uri
    assert "code_challenge_method" in query_dict
    assert query_dict["code_challenge_method"] == "S256"
    assert "scope" in query_dict
    assert query_dict["scope"] == scope
    assert "state" in query_dict
    assert "code_challenge" in query_dict

    # check a login_data has been registered in user session
    assert "login_data" in request.session
    login_data = request.session["login_data"]
    assert "code_verifier" in login_data
    assert "state" in login_data
    assert "redirect_uri" in login_data
    assert login_data["redirect_uri"] == query_dict["redirect_uri"]
    return login_data


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
    check_http_get_response(client, url, status_code=403)


def _generate_and_test_bearer_token(client, kc_oidc_mock):
    # user authenticates
    client.login(
        code="code", code_verifier="code-verifier", redirect_uri="redirect-uri"
    )
    # user initiates bearer token generation flow
    url = reverse("oidc-generate-bearer-token")
    response = check_http_get_response(client, url, status_code=302)
    request = response.wsgi_request
    redirect_uri = reverse("oidc-generate-bearer-token-complete", request=request)
    # check login data and redirection to Keycloak is valid
    login_data = _check_oidc_login_code_flow_data(
        request,
        response,
        kc_oidc_mock,
        redirect_uri=redirect_uri,
        scope="openid offline_access",
    )

    # once a user has identified himself in Keycloak, he is
    # redirected to the 'oidc-generate-bearer-token-complete' view
    # to get and save bearer token

    # generate authorization code / session state in the same
    # manner as Keycloak
    code = f"{str(uuid.uuid4())}.{str(uuid.uuid4())}.{str(uuid.uuid4())}"
    session_state = str(uuid.uuid4())

    token_complete_url = reverse(
        "oidc-generate-bearer-token-complete",
        query_params={
            "code": code,
            "state": login_data["state"],
            "session_state": session_state,
        },
    )

    nb_tokens = len(OIDCUserOfflineTokens.objects.all())
    response = check_http_get_response(client, token_complete_url, status_code=302)
    request = response.wsgi_request

    # check token has been generated and saved encrypted to database
    assert len(OIDCUserOfflineTokens.objects.all()) == nb_tokens + 1
    encrypted_token = OIDCUserOfflineTokens.objects.last().offline_token
    secret = get_config()["secret_key"].encode()
    salt = request.user.sub.encode()
    decrypted_token = decrypt_data(encrypted_token, secret, salt)
    oidc_profile = kc_oidc_mock.authorization_code(code=code, redirect_uri=redirect_uri)
    assert decrypted_token.decode("ascii") == oidc_profile["refresh_token"]

    # should redirect to tokens management Web UI
    assert response["location"] == reverse("oidc-profile") + "#tokens"

    return decrypted_token


@pytest.mark.django_db
def test_oidc_generate_bearer_token_authenticated_user_success(client, keycloak_oidc):
    """
    Authenticated user should be able to generate a bearer token using OIDC
    Authorization Code Flow.
    """
    _generate_and_test_bearer_token(client, keycloak_oidc)


def test_oidc_list_bearer_tokens_anonymous_user(client):
    """
    Anonymous user should be refused access with forbidden response.
    """
    url = reverse(
        "oidc-list-bearer-tokens", query_params={"draw": 1, "start": 0, "length": 10}
    )
    check_http_get_response(client, url, status_code=403)


@pytest.mark.django_db
def test_oidc_list_bearer_tokens(client, keycloak_oidc):
    """
    User with correct credentials should be allowed to list his tokens.
    """
    nb_tokens = 3

    for _ in range(nb_tokens):
        _generate_and_test_bearer_token(client, keycloak_oidc)

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
def test_oidc_get_bearer_token(client, keycloak_oidc):
    """
    User with correct credentials should be allowed to display a token.
    """
    nb_tokens = 3

    for i in range(nb_tokens):
        token = _generate_and_test_bearer_token(client, keycloak_oidc)

        url = reverse("oidc-get-bearer-token")

        response = check_http_post_response(
            client,
            url,
            status_code=200,
            data={"token_id": i + 1},
            content_type="text/plain",
        )
        assert response.content == token


def test_oidc_revoke_bearer_tokens_anonymous_user(client):
    """
    Anonymous user should be refused access with forbidden response.
    """
    url = reverse("oidc-revoke-bearer-tokens")
    check_http_post_response(client, url, status_code=403)


@pytest.mark.django_db
def test_oidc_revoke_bearer_tokens(client, keycloak_oidc):
    """
    User with correct credentials should be allowed to revoke tokens.
    """
    nb_tokens = 3

    for _ in range(nb_tokens):
        _generate_and_test_bearer_token(client, keycloak_oidc)

    url = reverse("oidc-revoke-bearer-tokens")

    check_http_post_response(
        client, url, status_code=200, data={"token_ids": [1]},
    )
    assert len(OIDCUserOfflineTokens.objects.all()) == 2

    check_http_post_response(
        client, url, status_code=200, data={"token_ids": [2, 3]},
    )
    assert len(OIDCUserOfflineTokens.objects.all()) == 0


def test_oidc_profile_view_anonymous_user(client):
    """
    Non authenticated users should be redirected to login page when
    requesting profile view.
    """
    url = reverse("oidc-profile")
    login_url = reverse("oidc-login", query_params={"next_path": url})
    resp = check_http_get_response(client, url, status_code=302)
    assert resp["location"] == login_url


@pytest.mark.django_db
def test_oidc_profile_view(client, keycloak_oidc):
    """
    Authenticated users should be able to request the profile page
    and link to Keycloak account UI should be present.
    """
    url = reverse("oidc-profile")
    kc_config = get_config()["keycloak"]
    user_permissions = ["perm1", "perm2"]
    keycloak_oidc.user_permissions = user_permissions
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
