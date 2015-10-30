# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.ui import converters, main, query


def lookup_hash(q):
    """Checks if the storage contains a given content checksum

    Args: query string

    Returns:
        True or False, according to whether the checksum is present or not

    """
    (algo, hash) = query.parse_hash(q)
    return main.storage().content_exist({algo: hash})


def lookup_hash_origin(q):
    """Return information about the checksum contained in the query q.

    Args: query string

    Returns:
        True or False, according to whether the checksum is present or not

    """
    algo, h = query.parse_hash(q)
    origin = main.storage().content_find_occurrence({algo: h})
    return converters.from_origin(origin)


def stat_counters():
    """Return the stat counters for Software Heritage

    Returns:
        A dict mapping textual labels to integer values.
    """
    return main.storage().stat_counters()
