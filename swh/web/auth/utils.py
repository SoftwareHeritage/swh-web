# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from base64 import urlsafe_b64encode

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

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
