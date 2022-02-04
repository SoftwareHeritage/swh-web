# Copyright (C) 2020-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from base64 import urlsafe_b64encode
from typing import List

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from django.http.request import HttpRequest

OIDC_SWH_WEB_CLIENT_ID = "swh-web"

SWH_AMBASSADOR_PERMISSION = "swh.ambassador"
API_SAVE_ORIGIN_PERMISSION = "swh.web.api.save_origin"
ADMIN_LIST_DEPOSIT_PERMISSION = "swh.web.admin.list_deposits"
MAILMAP_PERMISSION = "swh.web.mailmap"


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


def privileged_user(request: HttpRequest, permissions: List[str] = []) -> bool:
    """Determine whether a user is authenticated and is a privileged one (e.g ambassador).
    This allows such user to have access to some more actions (e.g. bypass save code now
    review, access to 'archives' type...).
    A user is considered as privileged if he is a staff member or has any permission
    from those provided as parameters.

    Args:
        request: Input django HTTP request
        permissions: list of permission names to determine if user is privileged or not
    Returns:
        Whether the user is privileged or not.
    """
    user = request.user
    return user.is_authenticated and (
        user.is_staff or any([user.has_perm(perm) for perm in permissions])
    )
