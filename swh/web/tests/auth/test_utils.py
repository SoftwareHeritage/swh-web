# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import hashlib
import re

from base64 import urlsafe_b64encode

from swh.web.auth.utils import gen_oidc_pkce_codes


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
