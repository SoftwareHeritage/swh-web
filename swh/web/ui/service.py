# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.ui import main
from swh.web.ui import query


def lookup_hash(q):
    """Given a string query q of hashes, lookup its hash to the backend.

    Args:
         query, string of ':' delimited hashes (sha1, sha256, etc...)

    Returns:
         a string message (found, not found or a potential error explanation)

    Raises:
         OSError (no route to host), etc... Network issues in general
    """
    hashes = query.group_by_checksums(query.parse(q))
    if hashes != {}:
        present = main.storage().content_present(hashes)
        return 'Found!' if present else 'Not Found'
    return """This is not a hash.
Hint: hexadecimal string with length either 20 (sha1) or 32 (sha256)."""
