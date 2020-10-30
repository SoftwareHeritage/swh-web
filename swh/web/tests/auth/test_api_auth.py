# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.contrib.auth.models import AnonymousUser, User

from swh.web.auth.models import OIDCUser
from swh.web.common.utils import reverse
from swh.web.tests.utils import check_api_get_responses, check_http_get_response

from . import sample_data
from .keycloak_mock import mock_keycloak


@pytest.mark.django_db
def test_drf_django_session_auth_success(mocker, client):
    """
    Check user gets authenticated when querying the web api
    through a web browser.
    """
    url = reverse("api-1-stat-counters")

    mock_keycloak(mocker)
    client.login(code="", code_verifier="", redirect_uri="")

    response = check_http_get_response(client, url, status_code=200)
    request = response.wsgi_request

    # user should be authenticated
    assert isinstance(request.user, OIDCUser)

    # check remoter used has not been saved to Django database
    with pytest.raises(User.DoesNotExist):
        User.objects.get(username=request.user.username)


@pytest.mark.django_db
def test_drf_oidc_bearer_token_auth_success(mocker, api_client):
    """
    Check user gets authenticated when querying the web api
    through an HTTP client using bearer token authentication.
    """
    url = reverse("api-1-stat-counters")

    refresh_token = sample_data.oidc_profile["refresh_token"]

    mock_keycloak(mocker)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh_token}")

    response = check_api_get_responses(api_client, url, status_code=200)
    request = response.wsgi_request

    # user should be authenticated
    assert isinstance(request.user, OIDCUser)

    # check remoter used has not been saved to Django database
    with pytest.raises(User.DoesNotExist):
        User.objects.get(username=request.user.username)


@pytest.mark.django_db
def test_drf_oidc_bearer_token_auth_failure(mocker, api_client):
    url = reverse("api-1-stat-counters")

    refresh_token = sample_data.oidc_profile["refresh_token"]

    # check for failed authentication but with expected token format
    mock_keycloak(mocker, auth_success=False)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh_token}")

    response = check_api_get_responses(api_client, url, status_code=403)
    request = response.wsgi_request

    assert isinstance(request.user, AnonymousUser)

    # check for failed authentication when token format is invalid
    api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token-format-ééàà")

    response = check_api_get_responses(api_client, url, status_code=400)
    request = response.wsgi_request

    assert isinstance(request.user, AnonymousUser)


def test_drf_oidc_auth_invalid_or_missing_authorization_type(api_client):
    url = reverse("api-1-stat-counters")

    refresh_token = sample_data.oidc_profile["refresh_token"]

    # missing authorization type
    api_client.credentials(HTTP_AUTHORIZATION=f"{refresh_token}")

    response = check_api_get_responses(api_client, url, status_code=403)
    request = response.wsgi_request

    assert isinstance(request.user, AnonymousUser)

    # invalid authorization type
    api_client.credentials(HTTP_AUTHORIZATION="Foo token")

    response = check_api_get_responses(api_client, url, status_code=403)
    request = response.wsgi_request

    assert isinstance(request.user, AnonymousUser)
