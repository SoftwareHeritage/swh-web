# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.contrib.auth.models import AnonymousUser, User

from swh.web.auth.models import OIDCUser
from swh.web.common.utils import reverse

from .keycloak_mock import mock_keycloak
from . import sample_data


@pytest.mark.django_db
def test_drf_django_session_auth_success(mocker, client):
    """
    Check user gets authenticated when querying the web api
    through a web browser.
    """
    url = reverse("api-1-stat-counters")

    mock_keycloak(mocker)
    client.login(code="", code_verifier="", redirect_uri="")

    response = client.get(url)
    request = response.wsgi_request

    assert response.status_code == 200

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

    access_token = sample_data.oidc_profile["access_token"]

    mock_keycloak(mocker)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    response = api_client.get(url)
    request = response.wsgi_request

    assert response.status_code == 200

    # user should be authenticated
    assert isinstance(request.user, OIDCUser)

    # check remoter used has not been saved to Django database
    with pytest.raises(User.DoesNotExist):
        User.objects.get(username=request.user.username)


@pytest.mark.django_db
def test_drf_oidc_bearer_token_auth_failure(mocker, api_client):
    url = reverse("api-1-stat-counters")

    access_token = sample_data.oidc_profile["access_token"]

    # check for failed authentication but with expected token format
    mock_keycloak(mocker, auth_success=False)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    response = api_client.get(url)
    request = response.wsgi_request

    assert response.status_code == 403
    assert isinstance(request.user, AnonymousUser)

    # check for failed authentication when token format is invalid
    mock_keycloak(mocker)
    api_client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token-format")

    response = api_client.get(url)
    request = response.wsgi_request

    assert response.status_code == 403
    assert isinstance(request.user, AnonymousUser)


def test_drf_oidc_auth_invalid_or_missing_authorization_type(api_client):
    url = reverse("api-1-stat-counters")

    access_token = sample_data.oidc_profile["access_token"]

    # missing authorization type
    api_client.credentials(HTTP_AUTHORIZATION=f"{access_token}")

    response = api_client.get(url)
    request = response.wsgi_request

    assert response.status_code == 403
    assert isinstance(request.user, AnonymousUser)

    # invalid authorization type
    api_client.credentials(HTTP_AUTHORIZATION="Foo token")

    response = api_client.get(url)
    request = response.wsgi_request

    assert response.status_code == 403
    assert isinstance(request.user, AnonymousUser)
