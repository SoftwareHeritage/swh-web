# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from collections import defaultdict

from swh.core import hashutil
from swh.web.ui import converters, main, query, upload
from swh.web.ui.exc import BadInputExc, NotFoundExc


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
    h = hashutil.hashfile(filepath)
    c = main.storage().content_find(h)
    if c:
        r = converters.from_content(c)
        r['found'] = True
        return r
    else:
        return {'sha1': hashutil.hash_to_hex(h['sha1']),
                'found': False}


def upload_and_search(file):
    """Upload a file and compute its hash.

    """
    tmpdir, filename, filepath = upload.save_in_upload_folder(file)
    res = {'filename': filename}
    try:
        content = hash_and_search(filepath)
        res.update(content)
        return res
    finally:
        # clean up
        if tmpdir:
            upload.cleanup(tmpdir)


def lookup_hash(q):
    """Checks if the storage contains a given content checksum

    Args: query string of the form <hash_algo:hash>

    Returns: Dict with key found to True or False, according to
        whether the checksum is present or not

    """
    (algo, hash) = query.parse_hash(q)
    found = main.storage().content_find({algo: hash})
    return {'found': found,
            'algo': algo}


def lookup_hash_origin(q):
    """Return information about the checksum contained in the query q.

    Args: query string of the form <hash_algo:hash>

    Returns:
        origin as dictionary if found for the given content.

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


def lookup_person(person_id):
    """Return information about the person with id person_id.

    Args:
        person_id as string

    Returns:
        person information as dict.

    """
    persons = main.storage().person_get([person_id])
    if not persons:
        return None
    return converters.from_person(persons[0])


def lookup_directory(sha1_git):
    """Return information about the directory with id sha1_git.

    Args:
        sha1_git as string

    Returns:
        directory information as dict.

    """
    algo, hBinSha1 = query.parse_hash(sha1_git)
    if algo != 'sha1':  # HACK: sha1_git really but they are both sha1...
        raise BadInputExc('Only sha1_git is supported.')

    directory_entries = main.storage().directory_get(hBinSha1)
    if not directory_entries:
        return None

    return map(converters.from_directory_entry, directory_entries)


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


def lookup_revision(rev_sha1_git):
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


def lookup_revision_log(rev_sha1_git):
    """Return information about the revision with sha1 revision_sha1_git.

    Args:
        revision_sha1_git: The revision's sha1 as hexadecimal

    Returns:
        Revision information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    algo, bin_sha1 = query.parse_hash(rev_sha1_git)
    if algo != 'sha1':  # HACK: sha1_git really but they are both sha1...
        raise BadInputExc('Only sha1_git is supported.')

    revision_entries = main.storage().revision_log(bin_sha1)

    return map(converters.from_revision, revision_entries)


def lookup_revision_with_context(sha1_git_root, sha1_git):
    """Return information about revision sha1_git, limited to the
    sub-graph of all transitive parents of sha1_git_root.

    In other words, sha1_git is an ancestor of sha1_git_root.

    Args:
        sha1_git_root: latest revision of the browsed history
        sha1_git: one of sha1_git_root's ancestors

    Returns:
        Information on sha1_git if it is an ancestor of sha1_git_root
        including children leading to sha1_git_root

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash
        NotFoundExc if either revision is not found or if sha1_git is not an
        ancestor of sha1_git_root

    """
    revision = lookup_revision(sha1_git)
    if not revision:
        raise NotFoundExc('Revision %s not found' % sha1_git)

    revision_root = lookup_revision(sha1_git_root)
    if not revision_root:
        raise NotFoundExc('Revision %s not found' % sha1_git_root)

    bin_sha1_root = hashutil.hex_to_hash(sha1_git_root)

    revision_log = main.storage().revision_log(bin_sha1_root)

    parents = {}
    children = defaultdict(list)

    for rev in revision_log:
        rev_id = hashutil.hash_to_hex(rev['id'])
        parents[rev_id] = []
        for parent_id in rev['parents']:
            parent_id = hashutil.hash_to_hex(parent_id)
            parents[rev_id].append(parent_id)
            children[parent_id].append(rev_id)

    if revision['id'] not in parents:
        raise NotFoundExc('Revision %s is not an ancestor of %s' %
                          (sha1_git, sha1_git_root))

    revision['children'] = children[revision['id']]

    return revision


def lookup_content(q):
    """Lookup the content designed by q.

    Args:
        q: The release's sha1 as hexadecimal

    """
    (algo, hash) = query.parse_hash(q)
    c = main.storage().content_find({algo: hash})
    if c:
        return converters.from_content(c)
    return None


def lookup_content_raw(q):
    """Lookup the content designed by q.

    Args:
        q: query string of the form <hash_algo:hash>

    Returns:
        dict with 'sha1' and 'data' keys.
        data representing its raw data decoded.

    """
    (algo, hash) = query.parse_hash(q)
    c = main.storage().content_find({algo: hash})
    if not c:
        return None

    sha1 = c['sha1']
    contents = main.storage().content_get([sha1])
    if contents and len(contents) >= 1:
        return converters.from_content(contents[0])
    return None


def stat_counters():
    """Return the stat counters for Software Heritage

    Returns:
        A dict mapping textual labels to integer values.
    """
    return main.storage().stat_counters()
