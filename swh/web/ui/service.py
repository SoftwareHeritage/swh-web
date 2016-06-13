# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from collections import defaultdict

from swh.core import hashutil
from swh.web.ui import converters, query, upload, backend
from swh.web.ui.exc import NotFoundExc


def lookup_multiple_hashes(hashes):
    """Lookup the passed hashes in a single DB connection, using batch processing.

    Args:
        An array of {filename: X, sha1: Y}, string X, hex sha1 string Y.
    Returns:
        The same array with elements updated with elem['found'] = true if
        the hash is present in storage, elem['found'] = false if not.
    """
    hashlist = [hashutil.hex_to_hash(elem['sha1']) for elem in hashes]
    content_missing = backend.content_missing_per_sha1(hashlist)
    missing = [hashutil.hash_to_hex(x) for x in content_missing]
    for x in hashes:
        x.update({'found': True})
    for h in hashes:
        if h['sha1'] in missing:
            h['found'] = False
    return hashes


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
    c = backend.content_find('sha1', h['sha1'])
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

    Returns: Dict with key found containing the hash info if the
    hash is present, None if not.

    """
    algo, hash = query.parse_hash(q)
    found = backend.content_find(algo, hash)
    return {'found': found,
            'algo': algo}


def search_hash(q):
    """Checks if the storage contains a given content checksum

    Args: query string of the form <hash_algo:hash>

    Returns: Dict with key found to True or False, according to
        whether the checksum is present or not

    """
    algo, hash = query.parse_hash(q)
    found = backend.content_find(algo, hash)
    return {'found': found is not None}


def lookup_hash_origin(q):
    """Return information about the checksum contained in the query q.

    Args: query string of the form <hash_algo:hash>

    Returns:
        origin as dictionary if found for the given content.

    """
    algo, hash = query.parse_hash(q)
    origin = backend.content_find_occurrence(algo, hash)
    return converters.from_origin(origin)


def lookup_origin(origin_id):
    """Return information about the origin with id origin_id.

    Args:
        origin_id as string

    Returns:
        origin information as dict.

    """
    return backend.origin_get(origin_id)


def lookup_person(person_id):
    """Return information about the person with id person_id.

    Args:
        person_id as string

    Returns:
        person information as dict.

    """
    person = backend.person_get(person_id)
    return converters.from_person(person)


def lookup_directory(sha1_git):
    """Return information about the directory with id sha1_git.

    Args:
        sha1_git as string

    Returns:
        directory information as dict.

    """
    _, sha1_git_bin = query.parse_hash_with_algorithms_or_throws(
        sha1_git,
        ['sha1'],  # HACK: sha1_git really
        'Only sha1_git is supported.')

    dir = backend.directory_get(sha1_git_bin)
    if not dir:
        return None

    directory_entries = backend.directory_ls(sha1_git_bin)
    return map(converters.from_directory_entry, directory_entries)


def lookup_directory_with_path(directory_sha1_git, path_string):
    """Return directory information for entry with path path_string w.r.t.
    root directory pointed by directory_sha1_git

    Args:
        - directory_sha1_git: sha1_git corresponding to the directory
        to which we append paths to (hopefully) find the entry
        - the relative path to the entry starting from the directory pointed by
        directory_sha1_git

    Raises:
        NotFoundExc if the directory entry is not found
    """
    _, sha1_git_bin = query.parse_hash_with_algorithms_or_throws(
        directory_sha1_git,
        ['sha1'],
        'Only sha1_git is supported.')

    queried_dir = backend.directory_entry_get_by_path(
        sha1_git_bin, path_string)

    if not queried_dir:
        raise NotFoundExc(('Directory entry with path %s from %s not found') %
                          (path_string, directory_sha1_git))

    return converters.from_directory_entry(queried_dir)


def lookup_release(release_sha1_git):
    """Return information about the release with sha1 release_sha1_git.

    Args:
        release_sha1_git: The release's sha1 as hexadecimal

    Returns:
        Release information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    _, sha1_git_bin = query.parse_hash_with_algorithms_or_throws(
        release_sha1_git,
        ['sha1'],
        'Only sha1_git is supported.')
    res = backend.release_get(sha1_git_bin)
    return converters.from_release(res)


def lookup_revision(rev_sha1_git):
    """Return information about the revision with sha1 revision_sha1_git.

    Args:
        revision_sha1_git: The revision's sha1 as hexadecimal

    Returns:
        Revision information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    _, sha1_git_bin = query.parse_hash_with_algorithms_or_throws(
        rev_sha1_git,
        ['sha1'],
        'Only sha1_git is supported.')

    revision = backend.revision_get(sha1_git_bin)
    return converters.from_revision(revision)


def lookup_revision_message(rev_sha1_git):
    """Return the raw message of the revision with sha1 revision_sha1_git.

    Args:
        revision_sha1_git: The revision's sha1 as hexadecimal

    Returns:
        Decoded revision message as dict {'message': <the_message>}

    Raises:
        ValueError if the identifier provided is not of sha1 nature.
        NotFoundExc if the revision is not found, or if it has no message

    """
    _, sha1_git_bin = query.parse_hash_with_algorithms_or_throws(
        rev_sha1_git,
        ['sha1'],
        'Only sha1_git is supported.')

    revision = backend.revision_get(sha1_git_bin)
    if not revision:
        raise NotFoundExc('Revision with sha1_git %s not found.'
                          % rev_sha1_git)
    if 'message' not in revision:
        raise NotFoundExc('No message for revision with sha1_git %s.'
                          % rev_sha1_git)
    res = {'message': revision['message']}
    return res


def lookup_revision_by(origin_id,
                       branch_name="refs/heads/master",
                       timestamp=None):
    """Lookup revisions by origin_id, branch_name and timestamp.

    If:
    - branch_name is not provided, lookup using 'refs/heads/master' as default.
    - ts is not provided, use the most recent

    Args:
        - origin_id: origin of the revision.
        - branch_name: revision's branch.
        - timestamp: revision's time frame.

    Yields:
        The revisions matching the criterions.

    """
    res = backend.revision_get_by(origin_id, branch_name, timestamp)
    return converters.from_revision(res)


def lookup_revision_log(rev_sha1_git, limit=100):
    """Return information about the revision with sha1 revision_sha1_git.

    Args:
        revision_sha1_git: The revision's sha1 as hexadecimal
        limit: the maximum number of revisions returned

    Returns:
        Revision information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    _, sha1_git_bin = query.parse_hash_with_algorithms_or_throws(
        rev_sha1_git,
        ['sha1'],
        'Only sha1_git is supported.')

    revision_entries = backend.revision_log(sha1_git_bin, limit)
    return map(converters.from_revision, revision_entries)


def lookup_revision_log_by(origin_id, branch_name, timestamp):
    """Return information about the revision with sha1 revision_sha1_git.

    Args:
        origin_id: origin of the revision
        branch_name: revision's branch
        timestamp: revision's time frame
        limit: the maximum number of revisions returned

    Returns:
        Revision information as dict.

    Raises:
        NotFoundExc if no revision corresponds to the criterion
        NotFoundExc if the corresponding revision has no log

    """
    revision_entries = backend.revision_log_by(origin_id,
                                               branch_name,
                                               timestamp)
    if not revision_entries:
        return None
    return map(converters.from_revision, revision_entries)


def lookup_revision_with_context_by(origin_id, branch_name, ts, sha1_git,
                                    limit=100):
    """Return information about revision sha1_git, limited to the
    sub-graph of all transitive parents of sha1_git_root.
    sha1_git_root being resolved through the lookup of a revision by origin_id,
    branch_name and ts.

    In other words, sha1_git is an ancestor of sha1_git_root.

    Args:
        - origin_id: origin of the revision.
        - branch_name: revision's branch.
        - timestamp: revision's time frame.
        - sha1_git: one of sha1_git_root's ancestors.
        - limit: limit the lookup to 100 revisions back.

    Returns:
        Pair of (root_revision, revision).
        Information on sha1_git if it is an ancestor of sha1_git_root
        including children leading to sha1_git_root

    Raises:
        - BadInputExc in case of unknown algo_hash or bad hash.
        - NotFoundExc if either revision is not found or if sha1_git is not an
        ancestor of sha1_git_root.

    """
    rev_root = backend.revision_get_by(origin_id, branch_name, ts)
    if not rev_root:
        raise NotFoundExc('Revision with (origin_id: %s, branch_name: %s'
                          ', ts: %s) not found.' % (origin_id,
                                                    branch_name,
                                                    ts))

    return (converters.from_revision(rev_root),
            lookup_revision_with_context(rev_root, sha1_git, limit))


def lookup_revision_with_context(sha1_git_root, sha1_git, limit=100):
    """Return information about revision sha1_git, limited to the
    sub-graph of all transitive parents of sha1_git_root.

    In other words, sha1_git is an ancestor of sha1_git_root.

    Args:
        sha1_git_root: latest revision. The type is either a sha1 (as an hex
        string) or a non converted dict.
        sha1_git: one of sha1_git_root's ancestors
        limit: limit the lookup to 100 revisions back

    Returns:
        Information on sha1_git if it is an ancestor of sha1_git_root
        including children leading to sha1_git_root

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash
        NotFoundExc if either revision is not found or if sha1_git is not an
        ancestor of sha1_git_root

    """
    _, sha1_git_bin = query.parse_hash_with_algorithms_or_throws(
        sha1_git,
        ['sha1'],
        'Only sha1_git is supported.')

    revision = backend.revision_get(sha1_git_bin)
    if not revision:
        raise NotFoundExc('Revision %s not found' % sha1_git)

    if isinstance(sha1_git_root, str):
        _, sha1_git_root_bin = query.parse_hash_with_algorithms_or_throws(
            sha1_git_root,
            ['sha1'],
            'Only sha1_git is supported.')

        revision_root = backend.revision_get(sha1_git_root_bin)
        if not revision_root:
            raise NotFoundExc('Revision root %s not found' % sha1_git_root)
    else:
        sha1_git_root_bin = sha1_git_root['id']

    revision_log = backend.revision_log(sha1_git_root_bin, limit)

    parents = {}
    children = defaultdict(list)

    for rev in revision_log:
        rev_id = rev['id']
        parents[rev_id] = []
        for parent_id in rev['parents']:
            parents[rev_id].append(parent_id)
            children[parent_id].append(rev_id)

    if revision['id'] not in parents:
        raise NotFoundExc('Revision %s is not an ancestor of %s' %
                          (sha1_git, sha1_git_root))

    revision['children'] = children[revision['id']]

    return converters.from_revision(revision)


def lookup_directory_with_revision(sha1_git, dir_path=None, with_data=False):
    """Return information on directory pointed by revision with sha1_git.
    If dir_path is not provided, display top level directory.
    Otherwise, display the directory pointed by dir_path (if it exists).

    Args:
        sha1_git: revision's hash.
        dir_path: optional directory pointed to by that revision.
        with_data: boolean that indicates to retrieve the raw data if the path
        resolves to a content. Default to False (for the api)

    Returns:
        Information on the directory pointed to by that revision.

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash.
        NotFoundExc either if the revision is not found or the path referenced
        does not exist.
        NotImplementedError in case of dir_path exists but do not reference a
        type 'dir' or 'file'.

    """
    _, sha1_git_bin = query.parse_hash_with_algorithms_or_throws(
        sha1_git,
        ['sha1'],
        'Only sha1_git is supported.')

    revision = backend.revision_get(sha1_git_bin)
    if not revision:
        raise NotFoundExc('Revision %s not found' % sha1_git)

    dir_sha1_git_bin = revision['directory']

    if dir_path:
        entity = backend.directory_entry_get_by_path(dir_sha1_git_bin,
                                                     dir_path)

        if not entity:
            raise NotFoundExc(
                "Directory or File '%s' pointed to by revision %s not found"
                % (dir_path, sha1_git))
    else:
        entity = {'type': 'dir', 'target': dir_sha1_git_bin}

    if entity['type'] == 'dir':
        directory_entries = backend.directory_ls(entity['target'])

        return {'type': 'dir',
                'path': '.' if not dir_path else dir_path,
                'revision': sha1_git,
                'content': map(converters.from_directory_entry,
                               directory_entries)}
    elif entity['type'] == 'file':  # content
        content = backend.content_find('sha1_git', entity['target'])
        if with_data:
            content['data'] = backend.content_get(content['sha1'])['data']

        return {'type': 'file',
                'path': '.' if not dir_path else dir_path,
                'revision': sha1_git,
                'content': converters.from_content(content)}
    else:
        raise NotImplementedError('Entity of type %s not implemented.'
                                  % entity['type'])


def lookup_content(q):
    """Lookup the content designed by q.

    Args:
        q: The release's sha1 as hexadecimal

    """
    algo, hash = query.parse_hash(q)
    c = backend.content_find(algo, hash)
    return converters.from_content(c)


def lookup_content_raw(q):
    """Lookup the content defined by q.

    Args:
        q: query string of the form <hash_algo:hash>

    Returns:
        dict with 'sha1' and 'data' keys.
        data representing its raw data decoded.

    """
    algo, hash = query.parse_hash(q)
    c = backend.content_find(algo, hash)
    if not c:
        return None

    content = backend.content_get(c['sha1'])
    return converters.from_content(content)


def stat_counters():
    """Return the stat counters for Software Heritage

    Returns:
        A dict mapping textual labels to integer values.
    """
    return backend.stat_counters()


def lookup_entity_by_uuid(uuid):
    """Return the entity's hierarchy from its uuid.

    Args:
        uuid: entity's identifier.

    Returns:
        List of hierarchy entities from the entity with uuid.

    """
    uuid = query.parse_uuid4(uuid)
    return backend.entity_get(uuid)


def lookup_revision_through(revision, limit=100):
    """Retrieve a revision from the criterion stored in revision dictionary.

    Args:
        revision: Dictionary of criterion to lookup the revision with.
        Here are the supported combination of possible values:
        - origin_id, branch_name, ts, sha1_git
        - origin_id, branch_name, ts
        - sha1_git_root, sha1_git
        - sha1_git

    Returns:
        None if the revision is not found or the actual revision.

    """
    if 'origin_id' in revision and \
       'branch_name' in revision and \
       'ts' in revision and \
       'sha1_git' in revision:
        return lookup_revision_with_context_by(revision['origin_id'],
                                               revision['branch_name'],
                                               revision['ts'],
                                               revision['sha1_git'],
                                               limit)
    if 'origin_id' in revision and \
       'branch_name' in revision and \
       'ts' in revision:
        return lookup_revision_by(revision['origin_id'],
                                  revision['branch_name'],
                                  revision['ts'])
    if 'sha1_git_root' in revision and \
       'sha1_git' in revision:
        return lookup_revision_with_context(revision['sha1_git_root'],
                                            revision['sha1_git'],
                                            limit)
    if 'sha1_git' in revision:
        return lookup_revision(revision['sha1_git'])

    # this should not happen
    raise NotImplementedError('Should not happen!')


def lookup_directory_through_revision(revision, path=None,
                                      limit=100, with_data=False):
    """Retrieve the directory information from the revision.

    Args:
        revision: dictionary of criterion representing a revision to lookup
        path: directory's path to lookup.
        limit: optional query parameter to limit the revisions log.
        (default to 100). For now, note that this limit could impede the
        transitivity conclusion about sha1_git not being an ancestor of.
        with_data: indicate to retrieve the content's raw data if path resolves
        to a content.

    Returns:
        The directory pointing to by the revision criterions at path.

    """
    rev = lookup_revision_through(revision, limit)

    if not rev:
        raise NotFoundExc('Revision with criterion %s not found!' % revision)
    return (rev['id'],
            lookup_directory_with_revision(rev['id'], path, with_data))
