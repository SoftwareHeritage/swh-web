# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

from . import main

MAX_LIMIT = 50  # Top limit the users can ask for


def content_get(sha1_bin):
    """Lookup the content designed by {algo: hash_bin}.

    Args:
        sha1_bin: content's binary sha1.

    Returns:
        Content as dict with 'sha1' and 'data' keys.
        data representing its raw data.

    """
    contents = main.storage().content_get([sha1_bin])
    if contents and len(contents) >= 1:
        return contents[0]
    return None


def content_find(algo, hash_bin):
    """Retrieve the content with binary hash hash_bin

    Args:
        algo: nature of the hash hash_bin.
        hash_bin: content's hash searched for.

    Returns:
        A dict with keys sha1, sha1_git, sha256, ... if the content
        exist or None otherwise.

    """
    return main.storage().content_find({algo: hash_bin})


def content_find_provenance(algo, hash_bin):
    """Find the content's provenance information.

    Args:
        algo: nature of the hash hash_bin.
        hash_bin: content's hash corresponding to algo searched for.

    Yields:
        Yields the list of provenance information for that content if
        any (this can be empty if the cache is not populated)

    """
    return main.storage().content_find_provenance({algo: hash_bin})


def content_ctags_get(id):
    """Retrieve the list of ctags symbols for a specific sha1.

    Args:
        id (bytes): content's hash identifier

    Returns:
        dict of keys 'id' (bytes) and 'ctags' (list of dict)

    """
    return list(main.storage().content_ctags_get([id]))


def content_ctags_search(expression, last_sha1, limit=10):
    """Lookup the content designed by {algo: hash_bin}.

    Args:
        expression (str): Expression to lookup in indexed raw content
        last_sha1 (str): Last hash
        limit (int): Number of elements per page

    Returns:
        sha1 whose indexed content match the expression

    """
    limit = min(limit, MAX_LIMIT)
    return main.storage().content_ctags_search(expression,
                                               last_sha1=last_sha1,
                                               limit=limit)


def content_filetype_get(id):
    """Retrieve content's filetype information.

    """
    r = list(main.storage().content_mimetype_get([id]))
    if not r:
        return None
    return r[0]


def content_language_get(id):
    """Retrieve content's language information.

    """
    r = list(main.storage().content_language_get([id]))
    if not r:
        return None
    return r[0]


def content_license_get(id):
    """Retrieve content's license information.

    """
    r = list(main.storage().content_fossology_license_get([id]))
    if not r:
        return None
    return r[0]


def content_missing_per_sha1(sha1list):
    """List content missing from storage based on sha1

    Args:
        sha1s: Iterable of sha1 to check for absence
    Returns:
        an iterable of sha1s missing from the storage
    """
    return main.storage().content_missing_per_sha1(sha1list)


def directory_get(sha1_bin):
    """Retrieve information on one directory.

    Args:
        sha1_bin: Directory's identifier

    Returns:
        The directory's information.

    """
    res = main.storage().directory_get([sha1_bin])
    if res and len(res) >= 1:
        return res[0]


def origin_get(origin):
    """Return information about the origin matching dict origin.

    Args:
        origin: origin's dict with keys either 'id' or
        ('type' AND 'url')

    Returns:
        Origin information as dict.

    """
    return main.storage().origin_get(origin)


def person_get(person_id):
    """Return information about the person with id person_id.

    Args:
        person_id: person's identifier.

    Returns:
        Person information as dict.

    """
    res = main.storage().person_get([person_id])
    if res and len(res) >= 1:
        return res[0]


def directory_ls(sha1_git_bin, recursive=False):
    """Return information about the directory with id sha1_git.

    Args:
        sha1_git: directory's identifier.
        recursive: Optional recursive flag default to False

    Returns:
        Directory information as dict.

    """
    directory_entries = main.storage().directory_ls(sha1_git_bin, recursive)
    if not directory_entries:
        return []

    return directory_entries


def release_get(sha1_git_bin):
    """Return information about the release with sha1 sha1_git_bin.

    Args:
        sha1_git_bin: The release's sha1 as bytes.

    Returns:
        Release information as dict if found, None otherwise.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """

    res = main.storage().release_get([sha1_git_bin])

    if res and len(res) >= 1:
        return res[0]
    return None


def revision_get(sha1_git_bin):
    """Return information about the revision with sha1 sha1_git_bin.

    Args:
        sha1_git_bin: The revision's sha1 as bytes.

    Returns:
        Revision information as dict if found, None otherwise.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    res = main.storage().revision_get([sha1_git_bin])
    if res and len(res) >= 1:
        return res[0]
    return None


def revision_get_multiple(sha1_git_bin_list):
    """Return information about the revisions in sha1_git_bin_list

    Args:
        sha1_git_bin_list: The revisions' sha1s as a list of bytes.

    Returns:
        Revisions' information as an iterable of dicts if any found,
        an empty list otherwise

    Raises:
        ValueError if the identifier provided is not of sha1 nature.
    """
    res = main.storage().revision_get(sha1_git_bin_list)
    if res and len(res) >= 1:
        return res
    return []


def revision_log(sha1_git_bin, limit):
    """Return information about the revision with sha1 sha1_git_bin.

    Args:
        sha1_git_bin: The revision's sha1 as bytes.
        limit: the maximum number of revisions returned.

    Returns:
        Revision information as dict if found, None otherwise.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    return main.storage().revision_log([sha1_git_bin], limit)


def revision_log_by(origin_id, branch_name, ts, limit):
    """Return information about the revision matching the timestamp
    ts, from origin origin_id, in branch branch_name.

    Args:
        origin_id: origin of the revision
        - branch_name: revision's branch.
        - timestamp: revision's time frame.

    Returns:
        Information for the revision matching the criterions.

    """
    return main.storage().revision_log_by(origin_id,
                                          branch_name,
                                          ts,
                                          limit=limit)


def stat_counters():
    """Return the stat counters for Software Heritage

    Returns:
        A dict mapping textual labels to integer values.
    """
    return main.storage().stat_counters()


def lookup_origin_visits(origin_id, last_visit=None, limit=10):
    """Yields the origin origin_ids' visits.

    Args:
        origin_id (int): origin to list visits for
        last_visit (int): last visit to lookup from
        limit (int): Number of elements max to display

    Yields:
       Dictionaries of origin_visit for that origin

    """
    limit = min(limit, MAX_LIMIT)
    print(last_visit, limit)
    yield from main.storage().origin_visit_get(
        origin_id, last_visit=last_visit, limit=limit)


def lookup_origin_visit(origin_id, visit_id):
    """Return information about visit visit_id with origin origin_id.

    Args:
        origin_id: origin concerned by the visit
        visit_id: the visit identifier to lookup

    Yields:
       The dict origin_visit concerned

    """
    return main.storage().origin_visit_get_by(origin_id, visit_id)


def revision_get_by(origin_id, branch_name, timestamp):
    """Return occurrence information matching the criterions origin_id,
    branch_name, ts.

    """
    res = main.storage().revision_get_by(origin_id,
                                         branch_name,
                                         timestamp=timestamp,
                                         limit=1)
    if not res:
        return None
    return res[0]


def directory_entry_get_by_path(directory, path):
    """Return a directory entry by its path.

    """
    paths = path.strip(os.path.sep).split(os.path.sep)
    return main.storage().directory_entry_get_by_path(
        directory,
        list(map(lambda p: p.encode('utf-8'), paths)))


def entity_get(uuid):
    """Retrieve the entity per its uuid.

    """
    return main.storage().entity_get(uuid)
