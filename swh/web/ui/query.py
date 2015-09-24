# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import re

from swh.core import hashutil


def parse(query):
    """Parse a formalized get query.

    Args:
        query, a colon separated value hash

    Returns:
        List of hashes

    Raises:
        AttributeError if query is None

    """
    return query.split(':')


# Regexp to filter and check inputs
sha256_regexp='[0-9a-f]{64}'
sha1_regexp='[0-9a-f]{40}'


def group_by_checksums(hashes):
    """Check that the checksums have the right format.

    Args:
        hashes: a list of string which should represent hashes (sha1 or sha256)

    Returns:
        A dictionary of hash indexed by their nature (sha1, sha256)
        The dictionary will be empty if nothing matches

    Raises:
        None

    """
    hashes_m = {}
    for h in hashes:
        try:
            if re.search(sha256_regexp, h):
                hashes_m.update({'sha256': hashutil.hex_to_hash(h)})
            elif re.search(sha1_regexp, h):
                hashes_m.update({'sha1': hashutil.hex_to_hash(h)})
        except ValueError:  # ignore silently to check the other inputs
            continue

    return hashes_m
