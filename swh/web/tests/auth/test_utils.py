# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from base64 import urlsafe_b64encode
import hashlib
import re

from cryptography.fernet import InvalidToken
import pytest

from swh.web.auth.utils import decrypt_data, encrypt_data, gen_oidc_pkce_codes


def test_gen_oidc_pkce_codes():
    """
    Check generated PKCE codes respect the specification
    (see https://tools.ietf.org/html/rfc7636#section-4.1)
    """
    code_verifier, code_challenge = gen_oidc_pkce_codes()

    # check the code verifier only contains allowed characters
    assert re.match(r"[a-zA-Z0-9-\._~]+", code_verifier)

    # check minimum and maximum authorized length for the
    # code verifier
    assert len(code_verifier) >= 43
    assert len(code_verifier) <= 128

    # compute code challenge from code verifier
    challenge = hashlib.sha256(code_verifier.encode("ascii")).digest()
    challenge = urlsafe_b64encode(challenge).decode("ascii")
    challenge = challenge.replace("=", "")

    # check base64 padding is not present
    assert not code_challenge[-1].endswith("=")
    # check code challenge is valid
    assert code_challenge == challenge


def test_encrypt_decrypt_data_ok():
    data = b"some-data-to-encrypt"
    password = b"secret"
    salt = b"salt-value"

    encrypted_data = encrypt_data(data, password, salt)
    decrypted_data = decrypt_data(encrypted_data, password, salt)

    assert decrypted_data == data


def test_encrypt_decrypt_data_ko():
    data = b"some-data-to-encrypt"
    password1 = b"secret"
    salt1 = b"salt-value"

    password2 = b"secret2"
    salt2 = b"salt-value2"

    encrypted_data = encrypt_data(data, password1, salt1)

    for password, salt in ((password2, salt2), (password1, salt2), (password2, salt1)):
        with pytest.raises(InvalidToken):
            decrypt_data(encrypted_data, password2, salt2)
