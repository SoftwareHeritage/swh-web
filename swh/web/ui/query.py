# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


import re

from swh.core import hashutil


# Regexp to filter and check inputs
sha256_regexp = '[0-9a-f]{64}'
sha1_regexp = '[0-9a-f]{40}'


def categorize_hash(hash):
    """Categorize the hash string according to what it is.

    Args:
        hash: hash string representation (sha1 or sha256)

    Returns:
        A dictionary of hash indexed by their nature (sha1, sha256)
        The dictionary will be empty if nothing matches

    Raises:
        None

    """
    try:
        h = hashutil.hex_to_hash(hash)
    except ValueError:  # ignore silently to check the other inputs
        return {}

    if re.search(sha256_regexp, hash):
        return {'sha256': h}
    if re.search(sha1_regexp, hash):
        return {'sha1': h}
    return {}
