# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from keycloak import KeycloakOpenID


class KeycloakOpenIDConnect:
    """
    Wrapper class around python-keycloak to ease the interaction with Keycloak
    for managing authentication and user permissions with OpenID Connect.
    """

    def __init__(
        self,
        server_url: str,
        realm_name: str,
        client_id: str,
        realm_public_key: str = "",
    ):
        """
        Args:
            server_url: URL of the Keycloak server
            realm_name: The realm name
            client_id: The OpenID Connect client identifier
            realm_public_key: The realm public key (will be dynamically
                retrieved if not provided)
        """
        self._keycloak = KeycloakOpenID(
            server_url=server_url, client_id=client_id, realm_name=realm_name,
        )

        self.server_url = server_url
        self.realm_name = realm_name
        self.client_id = client_id
        self.realm_public_key = realm_public_key

    def well_known(self) -> Dict[str, Any]:
        """
        Retrieve the OpenID Connect Well-Known URI registry from Keycloak.

        Returns:
            A dictionary filled with OpenID Connect URIS.
        """
        return self._keycloak.well_know()

    def authorization_url(self, redirect_uri: str, **extra_params: str) -> str:
        """
        Get OpenID Connect authorization URL to authenticate users.

        Args:
            redirect_uri: URI to redirect to once a user is authenticated
            extra_params: Extra query parameters to add to the
                authorization URL
        """
        auth_url = self._keycloak.auth_url(redirect_uri)
        if extra_params:
            auth_url += "&%s" % urlencode(extra_params)
        return auth_url

    def authorization_code(
        self, code: str, redirect_uri: str, **extra_params: str
    ) -> Dict[str, Any]:
        """
        Get OpenID Connect authentication tokens using Authorization
        Code flow.

        Args:
            code: Authorization code provided by Keycloak
            redirect_uri: URI to redirect to once a user is authenticated
                (must be the same as the one provided to authorization_url):
            extra_params: Extra parameters to add in the authorization request
                payload.
        """
        return self._keycloak.token(
            grant_type="authorization_code",
            code=code,
            redirect_uri=redirect_uri,
            **extra_params,
        )

    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Request a new access token from Keycloak using a refresh token.

        Args:
            refresh_token: A refresh token provided by Keycloak

        Returns:
            A dictionary filled with tokens info
        """
        return self._keycloak.refresh_token(refresh_token)

    def decode_token(
        self, token: str, options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Try to decode a JWT token.

        Args:
            token: A JWT token to decode
            options: Options for jose.jwt.decode

        Returns:
            A dictionary filled with decoded token content
        """
        if not self.realm_public_key:
            realm_public_key = self._keycloak.public_key()
            self.realm_public_key = "-----BEGIN PUBLIC KEY-----\n"
            self.realm_public_key += realm_public_key
            self.realm_public_key += "\n-----END PUBLIC KEY-----"

        return self._keycloak.decode_token(
            token, key=self.realm_public_key, options=options
        )

    def logout(self, refresh_token: str) -> None:
        """
        Logout a user by closing its authenticated session.

        Args:
            refresh_token: A refresh token provided by Keycloak
        """
        self._keycloak.logout(refresh_token)

    def userinfo(self, access_token: str) -> Dict[str, Any]:
        """
        Return user information from its access token.

        Args:
            access_token: An access token provided by Keycloak

        Returns:
            A dictionary fillled with user information
        """
        return self._keycloak.userinfo(access_token)


# stores instances of KeycloakOpenIDConnect class
# dict keys are (realm_name, client_id) tuples
_keycloak_oidc: Dict[Tuple[str, str], KeycloakOpenIDConnect] = {}


def get_keycloak_oidc_client(
    server_url: str, realm_name: str, client_id: str
) -> KeycloakOpenIDConnect:
    """
    Instantiate a KeycloakOpenIDConnect class for a given client in a
    given realm.

    Args:
        server_url: Base URL of a Keycloak server
        realm_name: Name of the realm in Keycloak
        client_id: Client identifier in the realm

    Returns:
        An object to ease the interaction with the Keycloak server
    """
    realm_client_key = (realm_name, client_id)
    if realm_client_key not in _keycloak_oidc:
        _keycloak_oidc[realm_client_key] = KeycloakOpenIDConnect(
            server_url, realm_name, client_id
        )
    return _keycloak_oidc[realm_client_key]
