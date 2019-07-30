# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import base64
from collections import defaultdict
import magic
import pypandoc
import stat
import textwrap

from django.core.cache import cache
from django.utils.safestring import mark_safe
from django.utils.html import escape

from importlib import reload

from swh.model.identifiers import persistent_identifier
from swh.web.common import highlightjs, service
from swh.web.common.exc import NotFoundExc, http_status_code_message
from swh.web.common.origin_visits import get_origin_visit
from swh.web.common.utils import (
    reverse, format_utc_iso_date, get_swh_persistent_id,
    swh_object_icons
)
from swh.web.config import get_config


def get_directory_entries(sha1_git):
    """Function that retrieves the content of a directory
    from the archive.

    The directories entries are first sorted in lexicographical order.
    Sub-directories and regular files are then extracted.

    Args:
        sha1_git: sha1_git identifier of the directory

    Returns:
        A tuple whose first member corresponds to the sub-directories list
        and second member the regular files list

    Raises:
        NotFoundExc if the directory is not found
    """
    cache_entry_id = 'directory_entries_%s' % sha1_git
    cache_entry = cache.get(cache_entry_id)

    if cache_entry:
        return cache_entry

    entries = list(service.lookup_directory(sha1_git))
    for e in entries:
        e['perms'] = stat.filemode(e['perms'])
        if e['type'] == 'rev':
            # modify dir entry name to explicitly show it points
            # to a revision
            e['name'] = '%s @ %s' % (e['name'], e['target'][:7])

    dirs = [e for e in entries if e['type'] in ('dir', 'rev')]
    files = [e for e in entries if e['type'] == 'file']

    dirs = sorted(dirs, key=lambda d: d['name'])
    files = sorted(files, key=lambda f: f['name'])

    cache.set(cache_entry_id, (dirs, files))

    return dirs, files


def get_mimetype_and_encoding_for_content(content):
    """Function that returns the mime type and the encoding associated to
    a content buffer using the magic module under the hood.

    Args:
        content (bytes): a content buffer

    Returns:
        A tuple (mimetype, encoding), for instance ('text/plain', 'us-ascii'),
        associated to the provided content.

    """
    while True:
        try:
            magic_result = magic.detect_from_content(content)
            mime_type = magic_result.mime_type
            encoding = magic_result.encoding
            break
        except Exception:
            # workaround an issue with the magic module who can fail
            # if detect_from_content is called multiple times in
            # a short amount of time
            reload(magic)

    return mime_type, encoding


# maximum authorized content size in bytes for HTML display
# with code highlighting
content_display_max_size = get_config()['content_display_max_size']

snapshot_content_max_size = get_config()['snapshot_content_max_size']


def _re_encode_content(mimetype, encoding, content_data):
    # encode textual content to utf-8 if needed
    if mimetype.startswith('text/'):
        # probably a malformed UTF-8 content, re-encode it
        # by replacing invalid chars with a substitution one
        if encoding == 'unknown-8bit':
            content_data = content_data.decode('utf-8', 'replace')\
                                       .encode('utf-8')
        elif encoding not in ['utf-8', 'binary']:
            content_data = content_data.decode(encoding, 'replace')\
                                       .encode('utf-8')
    elif mimetype.startswith('application/octet-stream'):
        # file may detect a text content as binary
        # so try to decode it for display
        encodings = ['us-ascii']
        encodings += ['iso-8859-%s' % i for i in range(1, 17)]
        for encoding in encodings:
            try:
                content_data = content_data.decode(encoding)\
                                           .encode('utf-8')
            except Exception:
                pass
            else:
                # ensure display in content view
                mimetype = 'text/plain'
                break
    return mimetype, content_data


def request_content(query_string, max_size=content_display_max_size,
                    raise_if_unavailable=True, re_encode=True):
    """Function that retrieves a content from the archive.

    Raw bytes content is first retrieved, then the content mime type.
    If the mime type is not stored in the archive, it will be computed
    using Python magic module.

    Args:
        query_string: a string of the form "[ALGO_HASH:]HASH" where
            optional ALGO_HASH can be either ``sha1``, ``sha1_git``,
            ``sha256``, or ``blake2s256`` (default to ``sha1``) and HASH
            the hexadecimal representation of the hash value
        max_size: the maximum size for a content to retrieve (default to 1MB,
            no size limit if None)

    Returns:
        A tuple whose first member corresponds to the content raw bytes
        and second member the content mime type

    Raises:
        NotFoundExc if the content is not found
    """
    content_data = service.lookup_content(query_string)
    filetype = None
    language = None
    license = None
    # requests to the indexer db may fail so properly handle
    # those cases in order to avoid content display errors
    try:
        filetype = service.lookup_content_filetype(query_string)
        language = service.lookup_content_language(query_string)
        license = service.lookup_content_license(query_string)
    except Exception:
        pass
    mimetype = 'unknown'
    encoding = 'unknown'
    if filetype:
        mimetype = filetype['mimetype']
        encoding = filetype['encoding']
        # workaround when encountering corrupted data due to implicit
        # conversion from bytea to text in the indexer db (see T818)
        # TODO: Remove that code when all data have been correctly converted
        if mimetype.startswith('\\'):
            filetype = None

    content_data['error_code'] = 200
    content_data['error_message'] = ''
    content_data['error_description'] = ''

    if not max_size or content_data['length'] < max_size:
        try:
            content_raw = service.lookup_content_raw(query_string)
        except Exception as e:
            if raise_if_unavailable:
                raise e
            else:
                content_data['raw_data'] = None
                content_data['error_code'] = 404
                content_data['error_description'] = \
                    'The bytes of the content are currently not available in the archive.' # noqa
                content_data['error_message'] = \
                    http_status_code_message[content_data['error_code']]
        else:
            content_data['raw_data'] = content_raw['data']

            if not filetype:
                mimetype, encoding = \
                    get_mimetype_and_encoding_for_content(content_data['raw_data']) # noqa

            if re_encode:
                mimetype, raw_data = _re_encode_content(
                    mimetype, encoding, content_data['raw_data'])
                content_data['raw_data'] = raw_data

    else:
        content_data['raw_data'] = None

    content_data['mimetype'] = mimetype
    content_data['encoding'] = encoding

    if language:
        content_data['language'] = language['lang']
    else:
        content_data['language'] = 'not detected'
    if license:
        content_data['licenses'] = ', '.join(license['facts'][0]['licenses'])
    else:
        content_data['licenses'] = 'not detected'

    return content_data


_browsers_supported_image_mimes = set(['image/gif', 'image/png',
                                       'image/jpeg', 'image/bmp',
                                       'image/webp', 'image/svg',
                                       'image/svg+xml'])


def prepare_content_for_display(content_data, mime_type, path):
    """Function that prepares a content for HTML display.

    The function tries to associate a programming language to a
    content in order to perform syntax highlighting client-side
    using highlightjs. The language is determined using either
    the content filename or its mime type.
    If the mime type corresponds to an image format supported
    by web browsers, the content will be encoded in base64
    for displaying the image.

    Args:
        content_data (bytes): raw bytes of the content
        mime_type (string): mime type of the content
        path (string): path of the content including filename

    Returns:
        A dict containing the content bytes (possibly different from the one
        provided as parameter if it is an image) under the key 'content_data
        and the corresponding highlightjs language class under the
        key 'language'.
    """

    language = highlightjs.get_hljs_language_from_filename(path)

    if not language:
        language = highlightjs.get_hljs_language_from_mime_type(mime_type)

    if not language:
        language = 'nohighlight'
    elif mime_type.startswith('application/'):
        mime_type = mime_type.replace('application/', 'text/')

    if mime_type.startswith('image/'):
        if mime_type in _browsers_supported_image_mimes:
            content_data = base64.b64encode(content_data)
        else:
            content_data = None

    if mime_type.startswith('image/svg'):
        mime_type = 'image/svg+xml'

    return {'content_data': content_data,
            'language': language,
            'mimetype': mime_type}


def process_snapshot_branches(snapshot):
    """
    Process a dictionary describing snapshot branches: extract those
    targeting revisions and releases, put them in two different lists,
    then sort those lists in lexicographical order of the branches' names.

    Args:
        snapshot_branches (dict): A dict describing the branches of a snapshot
            as returned for instance by
            :func:`swh.web.common.service.lookup_snapshot`

    Returns:
        tuple: A tuple whose first member is the sorted list of branches
            targeting revisions and second member the sorted list of branches
            targeting releases
    """
    snapshot_branches = snapshot['branches']
    branches = {}
    branch_aliases = {}
    releases = {}
    revision_to_branch = defaultdict(set)
    revision_to_release = defaultdict(set)
    release_to_branch = defaultdict(set)
    for branch_name, target in snapshot_branches.items():
        if not target:
            # FIXME: display branches with an unknown target anyway
            continue
        target_id = target['target']
        target_type = target['target_type']
        if target_type == 'revision':
            branches[branch_name] = {
                'name': branch_name,
                'revision': target_id,
            }
            revision_to_branch[target_id].add(branch_name)
        elif target_type == 'release':
            release_to_branch[target_id].add(branch_name)
        elif target_type == 'alias':
            branch_aliases[branch_name] = target_id
        # FIXME: handle pointers to other object types

    def _enrich_release_branch(branch, release):
        releases[branch] = {
            'name': release['name'],
            'branch_name': branch,
            'date': format_utc_iso_date(release['date']),
            'id': release['id'],
            'message': release['message'],
            'target_type': release['target_type'],
            'target': release['target'],
        }

    def _enrich_revision_branch(branch, revision):
        branches[branch].update({
            'revision': revision['id'],
            'directory': revision['directory'],
            'date': format_utc_iso_date(revision['date']),
            'message': revision['message']
        })

    releases_info = service.lookup_release_multiple(
        release_to_branch.keys()
    )
    for release in releases_info:
        branches_to_update = release_to_branch[release['id']]
        for branch in branches_to_update:
            _enrich_release_branch(branch, release)
        if release['target_type'] == 'revision':
            revision_to_release[release['target']].update(
                branches_to_update
            )

    revisions = service.lookup_revision_multiple(
        set(revision_to_branch.keys()) | set(revision_to_release.keys())
    )

    for revision in revisions:
        if not revision:
            continue
        for branch in revision_to_branch[revision['id']]:
            _enrich_revision_branch(branch, revision)
        for release in revision_to_release[revision['id']]:
            releases[release]['directory'] = revision['directory']

    for branch_alias, branch_target in branch_aliases.items():
        if branch_target in branches:
            branches[branch_alias] = dict(branches[branch_target])
        else:
            snp = service.lookup_snapshot(snapshot['id'],
                                          branches_from=branch_target,
                                          branches_count=1)
            if snp and branch_target in snp['branches']:

                if snp['branches'][branch_target] is None:
                    continue

                target_type = snp['branches'][branch_target]['target_type']
                target = snp['branches'][branch_target]['target']
                if target_type == 'revision':
                    branches[branch_alias] = snp['branches'][branch_target]
                    revision = service.lookup_revision(target)
                    _enrich_revision_branch(branch_alias, revision)
                elif target_type == 'release':
                    release = service.lookup_release(target)
                    _enrich_release_branch(branch_alias, release)

        if branch_alias in branches:
            branches[branch_alias]['name'] = branch_alias

    ret_branches = list(sorted(branches.values(), key=lambda b: b['name']))
    ret_releases = list(sorted(releases.values(), key=lambda b: b['name']))

    return ret_branches, ret_releases


def get_snapshot_content(snapshot_id):
    """Returns the lists of branches and releases
    associated to a swh snapshot.
    That list is put in  cache in order to speedup the navigation
    in the swh-web/browse ui.

    .. warning:: At most 1000 branches contained in the snapshot
        will be returned for performance reasons.

    Args:
        snapshot_id (str): hexadecimal representation of the snapshot
            identifier

    Returns:
        A tuple with two members. The first one is a list of dict describing
        the snapshot branches. The second one is a list of dict describing the
        snapshot releases.

    Raises:
        NotFoundExc if the snapshot does not exist
    """
    cache_entry_id = 'swh_snapshot_%s' % snapshot_id
    cache_entry = cache.get(cache_entry_id)

    if cache_entry:
        return cache_entry['branches'], cache_entry['releases']

    branches = []
    releases = []

    if snapshot_id:
        snapshot = service.lookup_snapshot(
            snapshot_id, branches_count=snapshot_content_max_size)
        branches, releases = process_snapshot_branches(snapshot)

    cache.set(cache_entry_id, {
        'branches': branches,
        'releases': releases,
    })

    return branches, releases


def get_origin_visit_snapshot(origin_info, visit_ts=None, visit_id=None,
                              snapshot_id=None):
    """Returns the lists of branches and releases
    associated to a swh origin for a given visit.
    The visit is expressed by a timestamp. In the latter case,
    the closest visit from the provided timestamp will be used.
    If no visit parameter is provided, it returns the list of branches
    found for the latest visit.
    That list is put in  cache in order to speedup the navigation
    in the swh-web/browse ui.

    .. warning:: At most 1000 branches contained in the snapshot
        will be returned for performance reasons.

    Args:
        origin_info (dict): a dict filled with origin information
            (id, url, type)
        visit_ts (int or str): an ISO date string or Unix timestamp to parse
        visit_id (int): optional visit id for disambiguation in case
            several visits have the same timestamp

    Returns:
        A tuple with two members. The first one is a list of dict describing
        the origin branches for the given visit.
        The second one is a list of dict describing the origin releases
        for the given visit.

    Raises:
        NotFoundExc if the origin or its visit are not found
    """

    visit_info = get_origin_visit(origin_info, visit_ts, visit_id, snapshot_id)

    return get_snapshot_content(visit_info['snapshot'])


def gen_link(url, link_text=None, link_attrs=None):
    """
    Utility function for generating an HTML link to insert
    in Django templates.

    Args:
        url (str): an url
        link_text (str): optional text for the produced link,
            if not provided the url will be used
        link_attrs (dict): optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form '<a href="url">link_text</a>'

    """
    attrs = ' '
    if link_attrs:
        for k, v in link_attrs.items():
            attrs += '%s="%s" ' % (k, v)
    if not link_text:
        link_text = url
    link = '<a%shref="%s">%s</a>' \
        % (attrs, escape(url), escape(link_text))
    return mark_safe(link)


def _snapshot_context_query_params(snapshot_context):
    query_params = None
    if snapshot_context and snapshot_context['origin_info']:
        origin_info = snapshot_context['origin_info']
        query_params = {'origin': origin_info['url']}
        if 'timestamp' in snapshot_context['url_args']:
            query_params['timestamp'] = \
                 snapshot_context['url_args']['timestamp']
        if 'visit_id' in snapshot_context['query_params']:
            query_params['visit_id'] = \
                snapshot_context['query_params']['visit_id']
    elif snapshot_context:
        query_params = {'snapshot_id': snapshot_context['snapshot_id']}
    return query_params


def gen_person_link(person_id, person_name, snapshot_context=None,
                    link_attrs=None):
    """
    Utility function for generating a link to a person HTML view
    to insert in Django templates.

    Args:
        person_id (int): a person id
        person_name (str): the associated person name
        link_attrs (dict): optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form '<a href="person_view_url">person_name</a>'

    """
    query_params = _snapshot_context_query_params(snapshot_context)
    person_url = reverse('browse-person', url_args={'person_id': person_id},
                         query_params=query_params)
    return gen_link(person_url, person_name or 'None', link_attrs)


def gen_revision_url(revision_id, snapshot_context=None):
    """
    Utility function for generating an url to a revision.

    Args:
        revision_id (str): a revision id
        snapshot_context (dict): if provided, generate snapshot-dependent
            browsing url

    Returns:
        str: The url to browse the revision

    """
    query_params = _snapshot_context_query_params(snapshot_context)

    return reverse('browse-revision',
                   url_args={'sha1_git': revision_id},
                   query_params=query_params)


def gen_revision_link(revision_id, shorten_id=False, snapshot_context=None,
                      link_text='Browse',
                      link_attrs={'class': 'btn btn-default btn-sm',
                                  'role': 'button'}):
    """
    Utility function for generating a link to a revision HTML view
    to insert in Django templates.

    Args:
        revision_id (str): a revision id
        shorten_id (boolean): whether to shorten the revision id to 7
            characters for the link text
        snapshot_context (dict): if provided, generate snapshot-dependent
            browsing link
        link_text (str): optional text for the generated link
            (the revision id will be used by default)
        link_attrs (dict): optional attributes (e.g. class)
            to add to the link

    Returns:
        str: An HTML link in the form '<a href="revision_url">revision_id</a>'

    """
    if not revision_id:
        return None

    revision_url = gen_revision_url(revision_id, snapshot_context)

    if shorten_id:
        return gen_link(revision_url, revision_id[:7], link_attrs)
    else:
        if not link_text:
            link_text = revision_id
        return gen_link(revision_url, link_text, link_attrs)


def gen_directory_link(sha1_git, snapshot_context=None, link_text='Browse',
                       link_attrs={'class': 'btn btn-default btn-sm',
                                   'role': 'button'}):
    """
    Utility function for generating a link to a directory HTML view
    to insert in Django templates.

    Args:
        sha1_git (str): directory identifier
        link_text (str): optional text for the generated link
            (the directory id will be used by default)
        link_attrs (dict): optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form '<a href="directory_view_url">link_text</a>'

    """
    if not sha1_git:
        return None

    query_params = _snapshot_context_query_params(snapshot_context)

    directory_url = reverse('browse-directory',
                            url_args={'sha1_git': sha1_git},
                            query_params=query_params)

    if not link_text:
        link_text = sha1_git
    return gen_link(directory_url, link_text, link_attrs)


def gen_snapshot_link(snapshot_id, snapshot_context=None, link_text='Browse',
                      link_attrs={'class': 'btn btn-default btn-sm',
                                  'role': 'button'}):
    """
    Utility function for generating a link to a snapshot HTML view
    to insert in Django templates.

    Args:
        snapshot_id (str): snapshot identifier
        link_text (str): optional text for the generated link
            (the snapshot id will be used by default)
        link_attrs (dict): optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form '<a href="snapshot_view_url">link_text</a>'

    """

    query_params = _snapshot_context_query_params(snapshot_context)

    snapshot_url = reverse('browse-snapshot',
                           url_args={'snapshot_id': snapshot_id},
                           query_params=query_params)
    if not link_text:
        link_text = snapshot_id
    return gen_link(snapshot_url, link_text, link_attrs)


def gen_content_link(sha1_git, snapshot_context=None, link_text='Browse',
                     link_attrs={'class': 'btn btn-default btn-sm',
                                 'role': 'button'}):
    """
    Utility function for generating a link to a content HTML view
    to insert in Django templates.

    Args:
        sha1_git (str): content identifier
        link_text (str): optional text for the generated link
            (the content sha1_git will be used by default)
        link_attrs (dict): optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form '<a href="content_view_url">link_text</a>'

    """
    if not sha1_git:
        return None

    query_params = _snapshot_context_query_params(snapshot_context)

    content_url = reverse('browse-content',
                          url_args={'query_string': 'sha1_git:' + sha1_git},
                          query_params=query_params)
    if not link_text:
        link_text = sha1_git
    return gen_link(content_url, link_text, link_attrs)


def get_revision_log_url(revision_id, snapshot_context=None):
    """
    Utility function for getting the URL for a revision log HTML view
    (possibly in the context of an origin).

    Args:
        revision_id (str): revision identifier the history heads to
        snapshot_context (dict): if provided, generate snapshot-dependent
            browsing link
    Returns:
        The revision log view URL
    """
    query_params = {'revision': revision_id}
    if snapshot_context and snapshot_context['origin_info']:
        origin_info = snapshot_context['origin_info']
        url_args = {'origin_url': origin_info['url']}
        if 'timestamp' in snapshot_context['url_args']:
            url_args['timestamp'] = \
                snapshot_context['url_args']['timestamp']
        if 'visit_id' in snapshot_context['query_params']:
            query_params['visit_id'] = \
                snapshot_context['query_params']['visit_id']
        revision_log_url = reverse('browse-origin-log',
                                   url_args=url_args,
                                   query_params=query_params)
    elif snapshot_context:
        url_args = {'snapshot_id': snapshot_context['snapshot_id']}
        revision_log_url = reverse('browse-snapshot-log',
                                   url_args=url_args,
                                   query_params=query_params)
    else:
        revision_log_url = reverse('browse-revision-log',
                                   url_args={'sha1_git': revision_id})
    return revision_log_url


def gen_revision_log_link(revision_id, snapshot_context=None,
                          link_text='Browse',
                          link_attrs={'class': 'btn btn-default btn-sm',
                                      'role': 'button'}):
    """
    Utility function for generating a link to a revision log HTML view
    (possibly in the context of an origin) to insert in Django templates.

    Args:
        revision_id (str): revision identifier the history heads to
        snapshot_context (dict): if provided, generate snapshot-dependent
            browsing link
        link_text (str): optional text to use for the generated link
            (the revision id will be used by default)
        link_attrs (dict): optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form
        '<a href="revision_log_view_url">link_text</a>'
    """
    if not revision_id:
        return None

    revision_log_url = get_revision_log_url(revision_id, snapshot_context)

    if not link_text:
        link_text = revision_id
    return gen_link(revision_log_url, link_text, link_attrs)


def gen_release_link(sha1_git, snapshot_context=None, link_text='Browse',
                     link_attrs={'class': 'btn btn-default btn-sm',
                                 'role': 'button'}):
    """
    Utility function for generating a link to a release HTML view
    to insert in Django templates.

    Args:
        sha1_git (str): release identifier
        link_text (str): optional text for the generated link
            (the release id will be used by default)
        link_attrs (dict): optional attributes (e.g. class)
            to add to the link

    Returns:
        An HTML link in the form '<a href="release_view_url">link_text</a>'

    """

    query_params = _snapshot_context_query_params(snapshot_context)

    release_url = reverse('browse-release',
                          url_args={'sha1_git': sha1_git},
                          query_params=query_params)
    if not link_text:
        link_text = sha1_git
    return gen_link(release_url, link_text, link_attrs)


def format_log_entries(revision_log, per_page, snapshot_context=None):
    """
    Utility functions that process raw revision log data for HTML display.
    Its purpose is to:

        * add links to relevant browse views
        * format date in human readable format
        * truncate the message log

    Args:
        revision_log (list): raw revision log as returned by the swh-web api
        per_page (int): number of log entries per page
        snapshot_context (dict): if provided, generate snapshot-dependent
            browsing link


    """
    revision_log_data = []
    for i, rev in enumerate(revision_log):
        if i == per_page:
            break
        author_name = 'None'
        author_fullname = 'None'
        committer_fullname = 'None'
        if rev['author']:
            author_name = rev['author']['name'] or rev['author']['fullname']
            author_fullname = rev['author']['fullname']
        if rev['committer']:
            committer_fullname = rev['committer']['fullname']
        author_date = format_utc_iso_date(rev['date'])
        committer_date = format_utc_iso_date(rev['committer_date'])

        tooltip = 'revision %s\n' % rev['id']
        tooltip += 'author: %s\n' % author_fullname
        tooltip += 'author date: %s\n' % author_date
        tooltip += 'committer: %s\n' % committer_fullname
        tooltip += 'committer date: %s\n\n' % committer_date
        if rev['message']:
            tooltip += textwrap.indent(rev['message'], ' '*4)

        revision_log_data.append({
            'author': author_name,
            'id': rev['id'][:7],
            'message': rev['message'],
            'date': author_date,
            'commit_date': committer_date,
            'url': gen_revision_url(rev['id'], snapshot_context),
            'tooltip': tooltip
        })
    return revision_log_data


# list of origin types that can be found in the swh archive
# TODO: retrieve it dynamically in an efficient way instead
#       of hardcoding it
_swh_origin_types = ['git', 'svn', 'deb', 'hg', 'ftp', 'deposit',
                     'pypi', 'npm']


def get_origin_info(origin_url, origin_type=None):
    """
    Get info about a software origin.
    Its main purpose is to automatically find an origin type
    when it is not provided as parameter.

    Args:
        origin_url (str): complete url of a software origin
        origin_type (str): optional origin type

    Returns:
        A dict with the following entries:
            * type: the origin type
            * url: the origin url
            * id: the internal id of the origin
    """
    if origin_type:
        return service.lookup_origin({'type': origin_type,
                                      'url': origin_url})
    else:
        for origin_type in _swh_origin_types:
            try:
                origin_info = service.lookup_origin({'type': origin_type,
                                                     'url': origin_url})
                return origin_info
            except Exception:
                pass
    raise NotFoundExc('Origin with url %s not found!' % escape(origin_url))


def get_snapshot_context(snapshot_id=None, origin_type=None, origin_url=None,
                         timestamp=None, visit_id=None):
    """
    Utility function to compute relevant information when navigating
    the archive in a snapshot context. The snapshot is either
    referenced by its id or it will be retrieved from an origin visit.

    Args:
        snapshot_id (str): hexadecimal representation of a snapshot identifier,
            all other parameters will be ignored if it is provided
        origin_type (str): the origin type (git, svn, deposit, ...)
        origin_url (str): the origin_url
            (e.g. https://github.com/(user)/(repo)/)
        timestamp (str): a datetime string for retrieving the closest
            visit of the origin
        visit_id (int): optional visit id for disambiguation in case
            of several visits with the same timestamp

    Returns:
        A dict with the following entries:
            * origin_info: dict containing origin information
            * visit_info: dict containing visit information
            * branches: the list of branches for the origin found
              during the visit
            * releases: the list of releases for the origin found
              during the visit
            * origin_browse_url: the url to browse the origin
            * origin_branches_url: the url to browse the origin branches
            * origin_releases_url': the url to browse the origin releases
            * origin_visit_url: the url to browse the snapshot of the origin
              found during the visit
            * url_args: dict containing url arguments to use when browsing in
              the context of the origin and its visit

    Raises:
        NotFoundExc: if no snapshot is found for the visit of an origin.
    """
    origin_info = None
    visit_info = None
    url_args = None
    query_params = {}
    branches = []
    releases = []
    browse_url = None
    visit_url = None
    branches_url = None
    releases_url = None
    swh_type = 'snapshot'
    if origin_url:
        swh_type = 'origin'
        origin_info = get_origin_info(origin_url, origin_type)

        visit_info = get_origin_visit(origin_info, timestamp, visit_id,
                                      snapshot_id)
        fmt_date = format_utc_iso_date(visit_info['date'])
        visit_info['fmt_date'] = fmt_date
        snapshot_id = visit_info['snapshot']

        if not snapshot_id:
            raise NotFoundExc('No snapshot associated to the visit of origin '
                              '%s on %s' % (escape(origin_url), fmt_date))

        # provided timestamp is not necessarily equals to the one
        # of the retrieved visit, so get the exact one in order
        # use it in the urls generated below
        if timestamp:
            timestamp = visit_info['date']

        branches, releases = \
            get_origin_visit_snapshot(origin_info, timestamp, visit_id,
                                      snapshot_id)

        url_args = {'origin_type': origin_type,
                    'origin_url': origin_info['url']}

        query_params = {'visit_id': visit_id}

        browse_url = reverse('browse-origin-visits',
                             url_args=url_args)

        if timestamp:
            url_args['timestamp'] = format_utc_iso_date(timestamp,
                                                        '%Y-%m-%dT%H:%M:%S')
        visit_url = reverse('browse-origin-directory',
                            url_args=url_args,
                            query_params=query_params)
        visit_info['url'] = visit_url

        branches_url = reverse('browse-origin-branches',
                               url_args=url_args,
                               query_params=query_params)

        releases_url = reverse('browse-origin-releases',
                               url_args=url_args,
                               query_params=query_params)
    elif snapshot_id:
        branches, releases = get_snapshot_content(snapshot_id)
        url_args = {'snapshot_id': snapshot_id}
        browse_url = reverse('browse-snapshot',
                             url_args=url_args)
        branches_url = reverse('browse-snapshot-branches',
                               url_args=url_args)

        releases_url = reverse('browse-snapshot-releases',
                               url_args=url_args)

    releases = list(reversed(releases))

    snapshot_size = service.lookup_snapshot_size(snapshot_id)

    is_empty = sum(snapshot_size.values()) == 0

    swh_snp_id = persistent_identifier('snapshot', snapshot_id)

    return {
        'swh_type': swh_type,
        'swh_object_id': swh_snp_id,
        'snapshot_id': snapshot_id,
        'snapshot_size': snapshot_size,
        'is_empty': is_empty,
        'origin_info': origin_info,
        # keep track if the origin type was provided as url argument
        'origin_type': origin_type,
        'visit_info': visit_info,
        'branches': branches,
        'releases': releases,
        'branch': None,
        'release': None,
        'browse_url': browse_url,
        'branches_url': branches_url,
        'releases_url': releases_url,
        'url_args': url_args,
        'query_params': query_params
    }


# list of common readme names ordered by preference
# (lower indices have higher priority)
_common_readme_names = [
    "readme.markdown",
    "readme.md",
    "readme.rst",
    "readme.txt",
    "readme"
]


def get_readme_to_display(readmes):
    """
    Process a list of readme files found in a directory
    in order to find the adequate one to display.

    Args:
        readmes: a list of dict where keys are readme file names and values
            are readme sha1s

    Returns:
        A tuple (readme_name, readme_sha1)
    """
    readme_name = None
    readme_url = None
    readme_sha1 = None
    readme_html = None

    lc_readmes = {k.lower(): {'orig_name': k, 'sha1': v}
                  for k, v in readmes.items()}

    # look for readme names according to the preference order
    # defined by the _common_readme_names list
    for common_readme_name in _common_readme_names:
        if common_readme_name in lc_readmes:
            readme_name = lc_readmes[common_readme_name]['orig_name']
            readme_sha1 = lc_readmes[common_readme_name]['sha1']
            readme_url = reverse('browse-content-raw',
                                 url_args={'query_string': readme_sha1},
                                 query_params={'re_encode': 'true'})
            break

    # otherwise pick the first readme like file if any
    if not readme_name and len(readmes.items()) > 0:
        readme_name = next(iter(readmes))
        readme_sha1 = readmes[readme_name]
        readme_url = reverse('browse-content-raw',
                             url_args={'query_string': readme_sha1},
                             query_params={'re_encode': 'true'})

    # convert rst README to html server side as there is
    # no viable solution to perform that task client side
    if readme_name and readme_name.endswith('.rst'):
        cache_entry_id = 'readme_%s' % readme_sha1
        cache_entry = cache.get(cache_entry_id)

        if cache_entry:
            readme_html = cache_entry
        else:
            try:
                rst_doc = request_content(readme_sha1)
                readme_html = pypandoc.convert_text(rst_doc['raw_data'],
                                                    'html', format='rst')
                cache.set(cache_entry_id, readme_html)
            except Exception:
                readme_html = 'Readme bytes are not available'

    return readme_name, readme_url, readme_html


def get_swh_persistent_ids(swh_objects, snapshot_context=None):
    """
    Returns a list of dict containing info related to persistent
    identifiers of swh objects.

    Args:
        swh_objects (list): a list of dict with the following keys:
            * type: swh object type
                (content/directory/release/revision/snapshot)
            * id: swh object id
        snapshot_context (dict): optional parameter describing the snapshot in
            which the object has been found

    Returns:
        list: a list of dict with the following keys:
            * object_type: the swh object type
                (content/directory/release/revision/snapshot)
            * object_icon: the swh object icon to use in HTML views
            * swh_id: the computed swh object persistent identifier
            * swh_id_url: the url resolving the persistent identifier
            * show_options: boolean indicating if the persistent id options
                must be displayed in persistent ids HTML view
    """
    swh_ids = []
    for swh_object in swh_objects:
        if not swh_object['id']:
            continue
        swh_id = get_swh_persistent_id(swh_object['type'], swh_object['id'])
        show_options = swh_object['type'] == 'content' or \
            (snapshot_context and snapshot_context['origin_info'] is not None)

        object_icon = swh_object_icons[swh_object['type']]

        swh_ids.append({
            'object_type': swh_object['type'],
            'object_icon': object_icon,
            'swh_id': swh_id,
            'swh_id_url': reverse('browse-swh-id',
                                  url_args={'swh_id': swh_id}),
            'show_options': show_options
        })
    return swh_ids
