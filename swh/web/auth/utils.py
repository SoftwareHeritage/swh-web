# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from base64 import urlsafe_b64encode
import hashlib
import secrets
from typing import Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from swh.web.auth.keycloak import KeycloakOpenIDConnect, get_keycloak_oidc_client
from swh.web.config import get_config


def gen_oidc_pkce_codes() -> Tuple[str, str]:
    """
    Generates a code verifier and a code challenge to be used
    with the OpenID Connect authorization code flow with PKCE
    ("Proof Key for Code Exchange", see https://tools.ietf.org/html/rfc7636).

    PKCE replaces the static secret used in the standard authorization
    code flow with a temporary one-time challenge, making it feasible
    to use in public clients.

    The implementation is inspired from that blog post:
    https://www.stefaanlippens.net/oauth-code-flow-pkce.html
    """
    # generate a code verifier which is a long enough random alphanumeric
    # string, only to be used "client side"
    code_verifier_str = secrets.token_urlsafe(60)

    # create the PKCE code challenge by hashing the code verifier with SHA256
    # and encoding the result in URL-safe base64 (without padding)
    code_challenge = hashlib.sha256(code_verifier_str.encode("ascii")).digest()
    code_challenge_str = urlsafe_b64encode(code_challenge).decode("ascii")
    code_challenge_str = code_challenge_str.replace("=", "")

    return code_verifier_str, code_challenge_str


OIDC_SWH_WEB_CLIENT_ID = "swh-web"


def _get_fernet(password: bytes, salt: bytes) -> Fernet:
    """
    Instantiate a Fernet system from a password and a salt value
    (see https://cryptography.io/en/latest/fernet/).

    Args:
        password: user password that will be used to generate a Fernet key
            derivation function
        salt: value that will be used to generate a Fernet key
            derivation function

    Returns:
        The Fernet system
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
        backend=default_backend(),
    )
    key = urlsafe_b64encode(kdf.derive(password))
    return Fernet(key)


def encrypt_data(data: bytes, password: bytes, salt: bytes) -> bytes:
    """
    Encrypt data using Fernet system (symmetric encryption).

    Args:
        data: input data to encrypt
        password: user password that will be used to generate a Fernet key
            derivation function
        salt: value that will be used to generate a Fernet key
            derivation function
    Returns:
        The encrypted data
    """
    return _get_fernet(password, salt).encrypt(data)


def decrypt_data(data: bytes, password: bytes, salt: bytes) -> bytes:
    """
    Decrypt data using Fernet system (symmetric encryption).

    Args:
        data: input data to decrypt
        password: user password that will be used to generate a Fernet key
            derivation function
        salt: value that will be used to generate a Fernet key
            derivation function
    Returns:
        The decrypted data
    """
    return _get_fernet(password, salt).decrypt(data)


def get_oidc_client(client_id: str = OIDC_SWH_WEB_CLIENT_ID) -> KeycloakOpenIDConnect:
    """
    Instantiate a KeycloakOpenIDConnect class for a given client in the
    SoftwareHeritage realm.

    Args:
        client_id: client identifier in the SoftwareHeritage realm

    Returns:
        An object to ease the interaction with the Keycloak server
    """
    swhweb_config = get_config()
    return get_keycloak_oidc_client(
        swhweb_config["keycloak"]["server_url"],
        swhweb_config["keycloak"]["realm_name"],
        client_id,
    )
