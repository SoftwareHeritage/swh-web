# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.ui import main
from swh.web.ui import query


def lookup_hash(q):
    """Given a string query q of one hash, lookup its hash to the backend.

    Args:
         query, hash as a string (sha1, sha256, etc...)

    Returns:
         a string message (found, not found or a potential error explanation)

    Raises:
         OSError (no route to host), etc... Network issues in general
    """
    hash = query.categorize_hash(q)
    if hash != {}:
        present = main.storage().content_find(hash)
        return 'Found!' if present else 'Not Found'
    return """This is not a hash.
Hint: hexadecimal string with length either 20 (sha1) or 32 (sha256)."""
