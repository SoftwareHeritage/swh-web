# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.core import hashutil
from swh.web.ui import converters, main, query, upload


def hash_and_search(filepath):
    """Hash the filepath's content as sha1, then search in storage if
    it exists.

    Args:
        Filepath of the file to hash and search.

    Returns:
        Tuple (hex sha1, found as True or false).
        The found boolean, according to whether the sha1 of the file
        is present or not.

    """
    hash = hashutil.hashfile(filepath)
    sha1 = hash['sha1']
    return (hashutil.hash_to_hex(sha1),
            main.storage().content_exist({'sha1': sha1}))


def upload_and_search(file):
    """Upload a file and compute its hash.

    """
    tmpdir, filename, filepath = upload.save_in_upload_folder(file)
    try:
        sha1, found = None, None
        if filepath:
            sha1, found = hash_and_search(filepath)
        return filename, sha1, found
    finally:
        # clean up
        if tmpdir:
            upload.cleanup(tmpdir)


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
