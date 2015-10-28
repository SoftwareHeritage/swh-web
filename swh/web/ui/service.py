# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
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
        present = main.storage().content_exist(hash)
        return 'Found!' if present else 'Not Found'
    return """This is not a hash.
Hint: hexadecimal string with length either 20 (sha1) or 32 (sha256)."""


def _origin_seen(hash, data):
    """Given an origin, compute a message string with the right information.

    Args:
        origin: a dictionary with keys:
          - origin: a dictionary with type and url keys
          - occurrence: a dictionary with a validity range

    Returns:
        message as a string

    """
    if data is None:
        return 'Content with hash %s is unknown as of now.' % hash

    origin_type = data['origin_type']
    origin_url = data['origin_url']
    revision = data['revision']
    branch = data['branch']
    path = data['path']

    return """The content with hash %s has been seen on origin with type '%s'
at url '%s'. The revision was identified at '%s' on branch '%s'.
The file's path referenced was '%s'.""" % (hash,
                                           origin_type,
                                           origin_url,
                                           revision,
                                           branch,
                                           path)


def lookup_hash_origin(hash):
    """Given a hash, return the origin of such content if any is found.

    Args:
        hash: key/value dictionary

    Returns:
        The origin for such hash if it's found.

    Raises:
        OSError (no route to host), etc... Network issues in general
    """
    data = main.storage().content_find_occurrence(hash)
    return _origin_seen(hash, data)


def stat_counters():
    """Return the stat counters for Software Heritage

    Returns:
        A dict mapping textual labels to integer values.
    """
    return main.storage().stat_counters()
