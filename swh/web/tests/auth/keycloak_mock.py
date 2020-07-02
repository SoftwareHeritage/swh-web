# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from copy import copy
from unittest.mock import Mock

from django.utils import timezone

from swh.web.auth.keycloak import KeycloakOpenIDConnect
from swh.web.auth.utils import OIDC_SWH_WEB_CLIENT_ID
from swh.web.config import get_config

from .sample_data import oidc_profile, realm_public_key, userinfo


class KeycloackOpenIDConnectMock(KeycloakOpenIDConnect):
    def __init__(
        self, auth_success=True, exp=None, user_groups=[], user_permissions=[]
    ):
        swhweb_config = get_config()
        super().__init__(
            swhweb_config["keycloak"]["server_url"],
            swhweb_config["keycloak"]["realm_name"],
            OIDC_SWH_WEB_CLIENT_ID,
        )
        self.auth_success = auth_success
        self.exp = exp
        self.user_groups = user_groups
        self.user_permissions = user_permissions
        self._keycloak.public_key = lambda: realm_public_key
        self._keycloak.well_know = lambda: {
            "issuer": f"{self.server_url}realms/{self.realm_name}",
            "authorization_endpoint": (
                f"{self.server_url}realms/"
                f"{self.realm_name}/protocol/"
                "openid-connect/auth"
            ),
            "token_endpoint": (
                f"{self.server_url}realms/{self.realm_name}/"
                "protocol/openid-connect/token"
            ),
            "token_introspection_endpoint": (
                f"{self.server_url}realms/"
                f"{self.realm_name}/protocol/"
                "openid-connect/token/"
                "introspect"
            ),
            "userinfo_endpoint": (
                f"{self.server_url}realms/{self.realm_name}/"
                "protocol/openid-connect/userinfo"
            ),
            "end_session_endpoint": (
                f"{self.server_url}realms/"
                f"{self.realm_name}/protocol/"
                "openid-connect/logout"
            ),
            "jwks_uri": (
                f"{self.server_url}realms/{self.realm_name}/"
                "protocol/openid-connect/certs"
            ),
        }
        self.authorization_code = Mock()
        self.userinfo = Mock()
        self.logout = Mock()
        if auth_success:
            self.authorization_code.return_value = copy(oidc_profile)
            self.userinfo.return_value = copy(userinfo)
        else:
            self.authorization_url = Mock()
            exception = Exception("Authentication failed")
            self.authorization_code.side_effect = exception
            self.authorization_url.side_effect = exception
            self.userinfo.side_effect = exception
            self.logout.side_effect = exception

    def decode_token(self, token):
        options = {}
        if self.auth_success:
            # skip signature expiration check as we use a static oidc_profile
            # for the tests with expired tokens in it
            options["verify_exp"] = False
        decoded = super().decode_token(token, options)
        # tweak auth and exp time for tests
        expire_in = decoded["exp"] - decoded["auth_time"]
        if self.exp is not None:
            decoded["exp"] = self.exp
            decoded["auth_time"] = self.exp - expire_in
        else:
            decoded["auth_time"] = int(timezone.now().timestamp())
            decoded["exp"] = decoded["auth_time"] + expire_in
        decoded["groups"] = self.user_groups
        if self.user_permissions:
            decoded["resource_access"][self.client_id] = {
                "roles": self.user_permissions
            }
        return decoded


def mock_keycloak(
    mocker, auth_success=True, exp=None, user_groups=[], user_permissions=[]
):
    kc_oidc_mock = KeycloackOpenIDConnectMock(
        auth_success, exp, user_groups, user_permissions
    )
    mock_get_oidc_client = mocker.patch("swh.web.auth.views.get_oidc_client")
    mock_get_oidc_client.return_value = kc_oidc_mock
    mocker.patch("swh.web.auth.backends._oidc_client", kc_oidc_mock)
    return kc_oidc_mock
