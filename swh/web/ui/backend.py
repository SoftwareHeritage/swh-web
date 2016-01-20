# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

from swh.web.ui import main


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
        A triplet (sha1, sha1_git, sha256) if the content exist
        or None otherwise.

    """
    return main.storage().content_find({algo: hash_bin})


def content_find_occurrence(algo, hash_bin):
    """Find the content's occurrence.

    Args:
        algo: nature of the hash hash_bin.
        hash_bin: content's hash searched for.

    Returns:
        The occurrence of the content.

    """
    return main.storage().content_find_occurrence({algo: hash_bin})


def origin_get(origin_id):
    """Return information about the origin with id origin_id.

    Args:
        origin_id: origin's identifier

    Returns:
        Origin information as dict.

    """
    return main.storage().origin_get({'id': origin_id})


def person_get(person_id):
    """Return information about the person with id person_id.

    Args:
        person_id: person's identifier.v

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
        return None

    return directory_entries


def release_get(sha1_git_bin):
    """Return information about the release with sha1 sha1_git_bin.

    Args:
        sha1_git_bin: The release's sha1 as hexadecimal.

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
        sha1_git_bin: The revision's sha1 as hexadecimal.

    Returns:
        Revision information as dict if found, None otherwise.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    res = main.storage().revision_get([sha1_git_bin])
    if res and len(res) >= 1:
        return res[0]
    return None


def revision_log(sha1_git_bin, limit=100):
    """Return information about the revision with sha1 sha1_git_bin.

    Args:
        sha1_git_bin: The revision's sha1 as hexadecimal.
        limit: the maximum number of revisions returned.

    Returns:
        Revision information as dict if found, None otherwise.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    return main.storage().revision_log([sha1_git_bin], limit)


def stat_counters():
    """Return the stat counters for Software Heritage

    Returns:
        A dict mapping textual labels to integer values.
    """
    return main.storage().stat_counters()


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
