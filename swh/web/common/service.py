# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

from collections import defaultdict

from swh.model import hashutil

from swh.storage.algos import revisions_walker

from swh.web.common import converters
from swh.web.common import query
from swh.web.common.exc import NotFoundExc
from swh.web import config

storage = config.storage()
vault = config.vault()
idx_storage = config.indexer_storage()


MAX_LIMIT = 50  # Top limit the users can ask for


def _first_element(l):
    """Returns the first element in the provided list or None
    if it is empty or None"""
    return next(iter(l or []), None)


def lookup_multiple_hashes(hashes):
    """Lookup the passed hashes in a single DB connection, using batch
    processing.

    Args:
        An array of {filename: X, sha1: Y}, string X, hex sha1 string Y.
    Returns:
        The same array with elements updated with elem['found'] = true if
        the hash is present in storage, elem['found'] = false if not.

    """
    hashlist = [hashutil.hash_to_bytes(elem['sha1']) for elem in hashes]
    content_missing = storage.content_missing_per_sha1(hashlist)
    missing = [hashutil.hash_to_hex(x) for x in content_missing]
    for x in hashes:
        x.update({'found': True})
    for h in hashes:
        if h['sha1'] in missing:
            h['found'] = False
    return hashes


def lookup_expression(expression, last_sha1, per_page):
    """Lookup expression in raw content.

    Args:
        expression (str): An expression to lookup through raw indexed
        content
        last_sha1 (str): Last sha1 seen
        per_page (int): Number of results per page

    Returns:
        List of ctags whose content match the expression

    """

    limit = min(per_page, MAX_LIMIT)
    ctags = idx_storage.content_ctags_search(expression,
                                             last_sha1=last_sha1,
                                             limit=limit)

    for ctag in ctags:
        ctag = converters.from_swh(ctag, hashess={'id'})
        ctag['sha1'] = ctag['id']
        ctag.pop('id')
        yield ctag


def lookup_hash(q):
    """Checks if the storage contains a given content checksum

    Args: query string of the form <hash_algo:hash>

    Returns: Dict with key found containing the hash info if the
    hash is present, None if not.

    """
    algo, hash = query.parse_hash(q)
    found = storage.content_find({algo: hash})
    return {'found': found,
            'algo': algo}


def search_hash(q):
    """Checks if the storage contains a given content checksum

    Args: query string of the form <hash_algo:hash>

    Returns: Dict with key found to True or False, according to
        whether the checksum is present or not

    """
    algo, hash = query.parse_hash(q)
    found = storage.content_find({algo: hash})
    return {'found': found is not None}


def lookup_content_provenance(q):
    """Return provenance information from a specified content.

    Args:
        q: query string of the form <hash_algo:hash>

    Yields:
        provenance information (dict) list if the content is found.

    """
    algo, hash = query.parse_hash(q)
    provenances = storage.content_find_provenance({algo: hash})
    if not provenances:
        return None
    return (converters.from_provenance(p) for p in provenances)


def _lookup_content_sha1(q):
    """Given a possible input, query for the content's sha1.

    Args:
        q: query string of the form <hash_algo:hash>

    Returns:
        binary sha1 if found or None

    """
    algo, hash = query.parse_hash(q)
    if algo != 'sha1':
        hashes = storage.content_find({algo: hash})
        if not hashes:
            return None
        return hashes['sha1']
    return hash


def lookup_content_ctags(q):
    """Return ctags information from a specified content.

    Args:
        q: query string of the form <hash_algo:hash>

    Yields:
        ctags information (dict) list if the content is found.

    """
    sha1 = _lookup_content_sha1(q)

    if not sha1:
        return None

    ctags = list(idx_storage.content_ctags_get([sha1]))
    if not ctags:
        return None

    for ctag in ctags:
        yield converters.from_swh(ctag, hashess={'id'})


def lookup_content_filetype(q):
    """Return filetype information from a specified content.

    Args:
        q: query string of the form <hash_algo:hash>

    Yields:
        filetype information (dict) list if the content is found.

    """
    sha1 = _lookup_content_sha1(q)
    if not sha1:
        return None
    filetype = _first_element(list(idx_storage.content_mimetype_get([sha1])))
    if not filetype:
        return None
    return converters.from_filetype(filetype)


def lookup_content_language(q):
    """Return language information from a specified content.

    Args:
        q: query string of the form <hash_algo:hash>

    Yields:
        language information (dict) list if the content is found.

    """
    sha1 = _lookup_content_sha1(q)
    if not sha1:
        return None
    lang = _first_element(list(idx_storage.content_language_get([sha1])))
    if not lang:
        return None
    return converters.from_swh(lang, hashess={'id'})


def lookup_content_license(q):
    """Return license information from a specified content.

    Args:
        q: query string of the form <hash_algo:hash>

    Yields:
        license information (dict) list if the content is found.

    """
    sha1 = _lookup_content_sha1(q)
    if not sha1:
        return None
    lic = _first_element(idx_storage.content_fossology_license_get([sha1]))

    if not lic:
        return None
    return converters.from_swh({'id': sha1, 'facts': lic[sha1]},
                               hashess={'id'})


def lookup_origin(origin):
    """Return information about the origin matching dict origin.

    Args:
        origin: origin's dict with keys either 'id' or
        ('type' AND 'url')

    Returns:
        origin information as dict.

    """
    origin_info = storage.origin_get(origin)
    if not origin_info:
        if 'id' in origin and origin['id']:
            msg = 'Origin with id %s not found!' % origin['id']
        else:
            msg = 'Origin with type %s and url %s not found!' % \
                (origin['type'], origin['url'])
        raise NotFoundExc(msg)
    return converters.from_origin(origin_info)


def search_origin(url_pattern, offset=0, limit=50, regexp=False,
                  with_visit=False):
    """Search for origins whose urls contain a provided string pattern
    or match a provided regular expression.

    Args:
        url_pattern: the string pattern to search for in origin urls
        offset: number of found origins to skip before returning results
        limit: the maximum number of found origins to return

    Returns:
        list of origin information as dict.

    """
    origins = storage.origin_search(url_pattern, offset, limit, regexp,
                                    with_visit)
    return map(converters.from_origin, origins)


def search_origin_metadata(fulltext, limit=50):
    """Search for origins whose metadata match a provided string pattern.

    Args:
        fulltext: the string pattern to search for in origin metadata
        offset: number of found origins to skip before returning results
        limit: the maximum number of found origins to return

    Returns:
        list of origin metadata as dict.

    """
    results = idx_storage.origin_intrinsic_metadata_search_fulltext(
        conjunction=[fulltext], limit=limit)
    for result in results:
        result['from_revision'] = hashutil.hash_to_hex(result['from_revision'])
    return results


def lookup_person(person_id):
    """Return information about the person with id person_id.

    Args:
        person_id as string

    Returns:
        person information as dict.

    Raises:
        NotFoundExc if there is no person with the provided id.

    """
    person = _first_element(storage.person_get([person_id]))
    if not person:
        raise NotFoundExc('Person with id %s not found' % person_id)
    return converters.from_person(person)


def _to_sha1_bin(sha1_hex):
    _, sha1_git_bin = query.parse_hash_with_algorithms_or_throws(
        sha1_hex,
        ['sha1'],  # HACK: sha1_git really
        'Only sha1_git is supported.')
    return sha1_git_bin


def lookup_directory(sha1_git):
    """Return information about the directory with id sha1_git.

    Args:
        sha1_git as string

    Returns:
        directory information as dict.

    """
    empty_dir_sha1 = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'

    if sha1_git == empty_dir_sha1:
        return []

    sha1_git_bin = _to_sha1_bin(sha1_git)

    directory_entries = storage.directory_ls(sha1_git_bin)
    if directory_entries:
        return map(converters.from_directory_entry, directory_entries)
    else:
        raise NotFoundExc('Directory with sha1_git %s not found' % sha1_git)


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
    sha1_git_bin = _to_sha1_bin(directory_sha1_git)

    paths = path_string.strip(os.path.sep).split(os.path.sep)
    queried_dir = storage.directory_entry_get_by_path(
        sha1_git_bin, list(map(lambda p: p.encode('utf-8'), paths)))

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
    sha1_git_bin = _to_sha1_bin(release_sha1_git)
    release = _first_element(storage.release_get([sha1_git_bin]))
    if not release:
        raise NotFoundExc('Release with sha1_git %s not found.'
                          % release_sha1_git)
    return converters.from_release(release)


def lookup_release_multiple(sha1_git_list):
    """Return information about the revisions identified with
    their sha1_git identifiers.

    Args:
        sha1_git_list: A list of revision sha1_git identifiers

    Returns:
        Release information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    sha1_bin_list = (_to_sha1_bin(sha1_git) for sha1_git in sha1_git_list)
    releases = storage.release_get(sha1_bin_list) or []
    return (converters.from_release(r) for r in releases)


def lookup_revision(rev_sha1_git):
    """Return information about the revision with sha1 revision_sha1_git.

    Args:
        revision_sha1_git: The revision's sha1 as hexadecimal

    Returns:
        Revision information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.
        NotFoundExc if there is no revision with the provided sha1_git.

    """
    sha1_git_bin = _to_sha1_bin(rev_sha1_git)
    revision = _first_element(storage.revision_get([sha1_git_bin]))
    if not revision:
        raise NotFoundExc('Revision with sha1_git %s not found.'
                          % rev_sha1_git)
    return converters.from_revision(revision)


def lookup_revision_multiple(sha1_git_list):
    """Return information about the revisions identified with
    their sha1_git identifiers.

    Args:
        sha1_git_list: A list of revision sha1_git identifiers

    Returns:
        Generator of revisions information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    sha1_bin_list = (_to_sha1_bin(sha1_git) for sha1_git in sha1_git_list)
    revisions = storage.revision_get(sha1_bin_list) or []
    return (converters.from_revision(r) for r in revisions)


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
    sha1_git_bin = _to_sha1_bin(rev_sha1_git)

    revision = _first_element(storage.revision_get([sha1_git_bin]))
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

    Raises:
        NotFoundExc if no revision corresponds to the criterion

    """
    res = _first_element(storage.revision_get_by(origin_id,
                                                 branch_name,
                                                 timestamp=timestamp,
                                                 limit=1))
    if not res:
        raise NotFoundExc('Revision for origin %s and branch %s not found.'
                          % (origin_id, branch_name))
    return converters.from_revision(res)


def lookup_revision_log(rev_sha1_git, limit):
    """Return information about the revision with sha1 revision_sha1_git.

    Args:
        revision_sha1_git: The revision's sha1 as hexadecimal
        limit: the maximum number of revisions returned

    Returns:
        Revision information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.
        NotFoundExc if there is no revision with the provided sha1_git.

    """
    sha1_git_bin = _to_sha1_bin(rev_sha1_git)

    revision_entries = storage.revision_log([sha1_git_bin], limit)
    if not revision_entries:
        raise NotFoundExc('Revision with sha1_git %s not found.'
                          % rev_sha1_git)
    return map(converters.from_revision, revision_entries)


def lookup_revision_log_by(origin_id, branch_name, timestamp, limit):
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

    """
    revision_entries = storage.revision_log_by(origin_id,
                                               branch_name,
                                               timestamp,
                                               limit=limit)
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
    rev_root = _first_element(storage.revision_get_by(origin_id,
                                                      branch_name,
                                                      timestamp=ts,
                                                      limit=1))
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
    sha1_git_bin = _to_sha1_bin(sha1_git)

    revision = _first_element(storage.revision_get([sha1_git_bin]))
    if not revision:
        raise NotFoundExc('Revision %s not found' % sha1_git)

    if isinstance(sha1_git_root, str):
        sha1_git_root_bin = _to_sha1_bin(sha1_git_root)

        revision_root = _first_element(storage.revision_get([sha1_git_root_bin])) # noqa
        if not revision_root:
            raise NotFoundExc('Revision root %s not found' % sha1_git_root)
    else:
        sha1_git_root_bin = sha1_git_root['id']

    revision_log = storage.revision_log([sha1_git_root_bin], limit)

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
    sha1_git_bin = _to_sha1_bin(sha1_git)

    revision = _first_element(storage.revision_get([sha1_git_bin]))
    if not revision:
        raise NotFoundExc('Revision %s not found' % sha1_git)

    dir_sha1_git_bin = revision['directory']

    if dir_path:
        paths = dir_path.strip(os.path.sep).split(os.path.sep)
        entity = storage.directory_entry_get_by_path(
            dir_sha1_git_bin, list(map(lambda p: p.encode('utf-8'), paths)))

        if not entity:
            raise NotFoundExc(
                "Directory or File '%s' pointed to by revision %s not found"
                % (dir_path, sha1_git))
    else:
        entity = {'type': 'dir', 'target': dir_sha1_git_bin}

    if entity['type'] == 'dir':
        directory_entries = storage.directory_ls(entity['target']) or []
        return {'type': 'dir',
                'path': '.' if not dir_path else dir_path,
                'revision': sha1_git,
                'content': map(converters.from_directory_entry,
                               directory_entries)}
    elif entity['type'] == 'file':  # content
        content = storage.content_find({'sha1_git': entity['target']})
        if with_data:
            c = _first_element(storage.content_get([content['sha1']]))
            content['data'] = c['data']
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

    Raises:
        NotFoundExc if the requested content is not found

    """
    algo, hash = query.parse_hash(q)
    c = storage.content_find({algo: hash})
    if not c:
        raise NotFoundExc('Content with %s checksum equals to %s not found!' %
                          (algo, hashutil.hash_to_hex(hash)))
    return converters.from_content(c)


def lookup_content_raw(q):
    """Lookup the content defined by q.

    Args:
        q: query string of the form <hash_algo:hash>

    Returns:
        dict with 'sha1' and 'data' keys.
        data representing its raw data decoded.

    Raises:
        NotFoundExc if the requested content is not found or
        if the content bytes are not available in the storage

    """
    c = lookup_content(q)
    content = _first_element(storage.content_get([c['checksums']['sha1']]))
    if not content:
        algo, hash = query.parse_hash(q)
        raise NotFoundExc('Bytes of content with %s checksum equals to %s '
                          'are not available!' %
                          (algo, hashutil.hash_to_hex(hash)))
    return converters.from_content(content)


def stat_counters():
    """Return the stat counters for Software Heritage

    Returns:
        A dict mapping textual labels to integer values.
    """
    return storage.stat_counters()


def _lookup_origin_visits(origin_id, last_visit=None, limit=10):
    """Yields the origin origin_ids' visits.

    Args:
        origin_id (int): origin to list visits for
        last_visit (int): last visit to lookup from
        limit (int): Number of elements max to display

    Yields:
       Dictionaries of origin_visit for that origin

    """
    limit = min(limit, MAX_LIMIT)
    yield from storage.origin_visit_get(
        origin_id, last_visit=last_visit, limit=limit)


def lookup_origin_visits(origin_id, last_visit=None, per_page=10):
    """Yields the origin origin_ids' visits.

    Args:
        origin_id: origin to list visits for

    Yields:
       Dictionaries of origin_visit for that origin

    """
    visits = _lookup_origin_visits(origin_id, last_visit=last_visit,
                                   limit=per_page)
    for visit in visits:
        yield converters.from_origin_visit(visit)


def lookup_origin_visit(origin_id, visit_id):
    """Return information about visit visit_id with origin origin_id.

    Args:
        origin_id: origin concerned by the visit
        visit_id: the visit identifier to lookup

    Yields:
       The dict origin_visit concerned

    """
    visit = storage.origin_visit_get_by(origin_id, visit_id)
    if not visit:
        raise NotFoundExc('Origin with id %s or its visit '
                          'with id %s not found!' % (origin_id, visit_id))
    return converters.from_origin_visit(visit)


def lookup_snapshot_size(snapshot_id):
    """Count the number of branches in the snapshot with the given id

    Args:
        snapshot_id (str): sha1 identifier of the snapshot

    Returns:
        dict: A dict whose keys are the target types of branches and
        values their corresponding amount
    """
    snapshot_id_bin = _to_sha1_bin(snapshot_id)
    snapshot_size = storage.snapshot_count_branches(snapshot_id_bin)
    if 'revision' not in snapshot_size:
        snapshot_size['revision'] = 0
    if 'release' not in snapshot_size:
        snapshot_size['release'] = 0
    return snapshot_size


def lookup_snapshot(snapshot_id, branches_from='', branches_count=None,
                    target_types=None):
    """Return information about a snapshot, aka the list of named
    branches found during a specific visit of an origin.

    Args:
        snapshot_id (str): sha1 identifier of the snapshot
        branches_from (str): optional parameter used to skip branches
            whose name is lesser than it before returning them
        branches_count (int): optional parameter used to restrain
            the amount of returned branches
        target_types (list): optional parameter used to filter the
            target types of branch to return (possible values that can be
            contained in that list are `'content', 'directory',
            'revision', 'release', 'snapshot', 'alias'`)

    Returns:
        A dict filled with the snapshot content.
    """
    snapshot_id_bin = _to_sha1_bin(snapshot_id)
    snapshot = storage.snapshot_get_branches(snapshot_id_bin,
                                             branches_from.encode(),
                                             branches_count, target_types)
    if not snapshot:
        raise NotFoundExc('Snapshot with id %s not found!' % snapshot_id)
    return converters.from_snapshot(snapshot)


def lookup_latest_origin_snapshot(origin_id, allowed_statuses=None):
    """Return information about the latest snapshot of an origin.

    .. warning:: At most 1000 branches contained in the snapshot
        will be returned for performance reasons.

    Args:
        origin_id: integer identifier of the origin
        allowed_statuses: list of visit statuses considered
            to find the latest snapshot for the visit. For instance,
            ``allowed_statuses=['full']`` will only consider visits that
            have successfully run to completion.

    Returns:
        A dict filled with the snapshot content.
    """
    snapshot = storage.snapshot_get_latest(origin_id, allowed_statuses)
    return converters.from_snapshot(snapshot)


def lookup_entity_by_uuid(uuid):
    """Return the entity's hierarchy from its uuid.

    Args:
        uuid: entity's identifier.

    Returns:
        List of hierarchy entities from the entity with uuid.

    """
    uuid = query.parse_uuid4(uuid)
    for entity in storage.entity_get(uuid):
        entity = converters.from_swh(entity,
                                     convert={'last_seen', 'uuid'},
                                     convert_fn=lambda x: str(x))
        yield entity


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
        limit: optional query parameter to limit the revisions log (default to
            100). For now, note that this limit could impede the transitivity
            conclusion about sha1_git not being an ancestor of.
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


def vault_cook(obj_type, obj_id, email=None):
    """Cook a vault bundle.
    """
    return vault.cook(obj_type, obj_id, email=email)


def vault_fetch(obj_type, obj_id):
    """Fetch a vault bundle.
    """
    return vault.fetch(obj_type, obj_id)


def vault_progress(obj_type, obj_id):
    """Get the current progress of a vault bundle.
    """
    return vault.progress(obj_type, obj_id)


def diff_revision(rev_id):
    """Get the list of file changes (insertion / deletion / modification /
    renaming) for a particular revision.
    """
    rev_sha1_git_bin = _to_sha1_bin(rev_id)

    changes = storage.diff_revision(rev_sha1_git_bin, track_renaming=True)

    for change in changes:
        change['from'] = converters.from_directory_entry(change['from'])
        change['to'] = converters.from_directory_entry(change['to'])
        if change['from_path']:
            change['from_path'] = change['from_path'].decode('utf-8')
        if change['to_path']:
            change['to_path'] = change['to_path'].decode('utf-8')

    return changes


class _RevisionsWalkerProxy(object):
    """
    Proxy class wrapping a revisions walker iterator from
    swh-storage and performing needed conversions.
    """
    def __init__(self, rev_walker_type, rev_start, *args, **kwargs):
        rev_start_bin = hashutil.hash_to_bytes(rev_start)
        self.revisions_walker = \
            revisions_walker.get_revisions_walker(rev_walker_type,
                                                  storage,
                                                  rev_start_bin,
                                                  *args, **kwargs)

    def export_state(self):
        return self.revisions_walker.export_state()

    def __next__(self):
        return converters.from_revision(next(self.revisions_walker))

    def __iter__(self):
        return self


def get_revisions_walker(rev_walker_type, rev_start, *args, **kwargs):
    """
    Utility function to instantiate a revisions walker of a given type,
    see :mod:`swh.storage.algos.revisions_walker`.

    Args:
        rev_walker_type (str): the type of revisions walker to return,
            possible values are: ``committer_date``, ``dfs``, ``dfs_post``,
            ``bfs`` and ``path``
        rev_start (str): hexadecimal representation of a revision identifier
        args (list): position arguments to pass to the revisions walker
            constructor
        kwargs (dict): keyword arguments to pass to the revisions walker
            constructor

    """
    # first check if the provided revision is valid
    lookup_revision(rev_start)
    return _RevisionsWalkerProxy(rev_walker_type, rev_start, *args, **kwargs)
