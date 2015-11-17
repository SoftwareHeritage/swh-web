# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.core import hashutil
from swh.web.ui import converters, main, query, upload
from swh.web.ui.exc import BadInputExc


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
    return (hashutil.hash_to_hex(hash['sha1']),
            main.storage().content_exist(hash))


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

    Args: query string of the form <hash_algo:hash>

    Returns:
        True or False, according to whether the checksum is present or not

    """
    (algo, hash) = query.parse_hash(q)
    return main.storage().content_exist({algo: hash})


def lookup_hash_origin(q):
    """Return information about the checksum contained in the query q.

    Args: query string of the form <hash_algo:hash>

    Returns:
        True or False, according to whether the checksum is present or not

    """
    algo, h = query.parse_hash(q)
    origin = main.storage().content_find_occurrence({algo: h})
    return converters.from_origin(origin)


def lookup_origin(origin_id):
    """Return information about the origin with id origin_id.

    Args:
        origin_id as string

    Returns:
        origin information as dict.

    """
    return main.storage().origin_get({'id': origin_id})


def lookup_release(release_sha1_git):
    """Return information about the release with sha1 release_sha1_git.

    Args:
        release_sha1_git: The release's sha1 as hexadecimal

    Returns:
        Release information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    algo, hBinSha1 = query.parse_hash(release_sha1_git)
    if algo != 'sha1':  # HACK: sha1_git really but they are both sha1...
        raise BadInputExc('Only sha1_git is supported.')

    res = main.storage().release_get([hBinSha1])

    if res and len(res) >= 1:
        return converters.from_release(res[0])
    return None


def lookup_revision(rev_sha1_git, rev_type='git'):
    """Return information about the revision with sha1 revision_sha1_git.

    Args:
        revision_sha1_git: The revision's sha1 as hexadecimal

    Returns:
        Revision information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    algo, hBinSha1 = query.parse_hash(rev_sha1_git)
    if algo != 'sha1':  # HACK: sha1_git really but they are both sha1...
        raise BadInputExc('Only sha1_git is supported.')

    res = main.storage().revision_get([hBinSha1])

    if res and len(res) >= 1:
        return converters.from_revision(res[0])
    return None


def stat_counters():
    """Return the stat counters for Software Heritage

    Returns:
        A dict mapping textual labels to integer values.
    """
    return main.storage().stat_counters()
