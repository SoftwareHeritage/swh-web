# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.ui import main
from swh.web.ui import query


def lookup_hash(q):
    """Checks if the storage contains a given content checksum

    Args: query string

    Returns:
        True or False, according to whether the checksum is present or not

    """
    (algo, hash) = query.parse_hash(q)
    return main.storage().content_exist({algo: hash})


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
