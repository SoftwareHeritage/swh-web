# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from cryptography.fernet import InvalidToken
import pytest

from swh.web.auth.utils import decrypt_data, encrypt_data


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
