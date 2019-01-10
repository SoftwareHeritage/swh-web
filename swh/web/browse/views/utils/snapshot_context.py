# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# Utility module implementing Django views for browsing the archive
# in a snapshot context.
# Its purpose is to factorize code for the views reachable from the
# /origin/.* and /snapshot/.* endpoints.

from django.shortcuts import render, redirect
from django.template.defaultfilters import filesizeformat

from swh.model.identifiers import snapshot_identifier

from swh.web.browse.utils import (
    get_snapshot_context, get_directory_entries, gen_directory_link,
    gen_revision_link, request_content, gen_content_link,
    prepare_content_for_display, content_display_max_size,
    format_log_entries, gen_revision_log_link, gen_link,
    get_readme_to_display, get_swh_persistent_ids, process_snapshot_branches
)

from swh.web.common import service
from swh.web.common.exc import (
    handle_view_exception, NotFoundExc
)
from swh.web.common.utils import (
    reverse, gen_path_info, format_utc_iso_date, swh_object_icons
)

_empty_snapshot_id = snapshot_identifier({'branches': {}})


def _get_branch(branches, branch_name, snapshot_id):
    """
    Utility function to get a specific branch from a branches list.
    Its purpose is to get the default HEAD branch as some software origin
    (e.g those with svn type) does not have it. In that latter case, check
    if there is a master branch instead and returns it.
    """
    filtered_branches = \
        [b for b in branches if b['name'].endswith(branch_name)]
    if len(filtered_branches) > 0:
        return filtered_branches[0]
    elif branch_name == 'HEAD':
        filtered_branches = \
            [b for b in branches if b['name'].endswith('master')]
        if len(filtered_branches) > 0:
            return filtered_branches[0]
        elif len(branches) > 0:
            return branches[0]
    else:
        # case where a large branches list has been truncated
        snp = service.lookup_snapshot(snapshot_id,
                                      branches_from=branch_name,
                                      branches_count=1,
                                      target_types=['revision', 'alias'])
        snp_branch, _ = process_snapshot_branches(snp)
        if snp_branch:
            branches.append(snp_branch[0])
            return snp_branch[0]
    return None


def _get_release(releases, release_name):
    """
    Utility function to get a specific release from a releases list.
    Returns None if the release can not be found in the list.
    """
    filtered_releases = \
        [r for r in releases if r['name'] == release_name]
    if len(filtered_releases) > 0:
        return filtered_releases[0]
    else:
        return None


def _branch_not_found(branch_type, branch, branches, snapshot_id=None,
                      origin_info=None, timestamp=None, visit_id=None):
    """
    Utility function to raise an exception when a specified branch/release
    can not be found.
    """
    if branch_type == 'branch':
        branch_type = 'Branch'
        branch_type_plural = 'branches'
    else:
        branch_type = 'Release'
        branch_type_plural = 'releases'

    if snapshot_id and len(branches) == 0:
        msg = 'Snapshot with id %s has an empty list' \
              ' of %s!' % (snapshot_id, branch_type_plural)
    elif snapshot_id:
        msg = '%s %s for snapshot with id %s' \
              ' not found!' % (branch_type, branch, snapshot_id)
    elif visit_id and len(branches) == 0:
        msg = 'Origin with type %s and url %s' \
              ' for visit with id %s has an empty list' \
              ' of %s!' % (origin_info['type'], origin_info['url'], visit_id,
                           branch_type_plural)
    elif visit_id:
        msg = '%s %s associated to visit with' \
              ' id %s for origin with type %s and url %s' \
              ' not found!' % (branch_type, branch, visit_id,
                               origin_info['type'], origin_info['url'])
    elif len(branches) == 0:
        msg = 'Origin with type %s and url %s' \
                ' for visit with timestamp %s has an empty list' \
                ' of %s!' % (origin_info['type'], origin_info['url'],
                             timestamp, branch_type_plural)
    else:
        msg = '%s %s associated to visit with'  \
              ' timestamp %s for origin with type %s' \
              ' and url %s not found!' % (branch_type, branch, timestamp,
                                          origin_info['type'],
                                          origin_info['url'])
    raise NotFoundExc(msg)


def _process_snapshot_request(request, snapshot_id=None, origin_type=None,
                              origin_url=None, timestamp=None, path=None,
                              browse_context='directory'):
    """
    Utility function to perform common input request processing
    for snapshot context views.
    """

    visit_id = request.GET.get('visit_id', None)

    snapshot_context = get_snapshot_context(snapshot_id, origin_type,
                                            origin_url, timestamp, visit_id)

    swh_type = snapshot_context['swh_type']
    origin_info = snapshot_context['origin_info']
    branches = snapshot_context['branches']
    releases = snapshot_context['releases']
    url_args = snapshot_context['url_args']
    query_params = snapshot_context['query_params']

    if snapshot_context['visit_info']:
        timestamp = format_utc_iso_date(snapshot_context['visit_info']['date'],
                                        '%Y-%m-%dT%H:%M:%SZ')
        snapshot_context['timestamp'] = \
            format_utc_iso_date(snapshot_context['visit_info']['date'])

    browse_view_name = 'browse-' + swh_type + '-' + browse_context

    root_sha1_git = None
    revision_id = request.GET.get('revision', None)
    release_name = request.GET.get('release', None)
    release_id = None
    branch_name = None

    snapshot_total_size = sum(snapshot_context['snapshot_size'].values())

    if snapshot_total_size and revision_id:
        revision = service.lookup_revision(revision_id)
        root_sha1_git = revision['directory']
        branches.append({'name': revision_id,
                         'revision': revision_id,
                         'directory': root_sha1_git,
                         'url': None})
        branch_name = revision_id
        query_params['revision'] = revision_id
    elif snapshot_total_size and release_name:
        release = _get_release(releases, release_name)
        try:
            root_sha1_git = release['directory']
            revision_id = release['target']
            release_id = release['id']
            query_params['release'] = release_name
        except Exception:
            _branch_not_found("release", release_name, releases, snapshot_id,
                              origin_info, timestamp, visit_id)
    elif snapshot_total_size:
        branch_name = request.GET.get('branch', None)
        if branch_name:
            query_params['branch'] = branch_name
        branch = _get_branch(branches, branch_name or 'HEAD',
                             snapshot_context['snapshot_id'])
        try:
            branch_name = branch['name']
            revision_id = branch['revision']
            root_sha1_git = branch['directory']
        except Exception:
            _branch_not_found("branch", branch_name, branches, snapshot_id,
                              origin_info, timestamp, visit_id)

    for b in branches:
        branch_url_args = dict(url_args)
        branch_query_params = dict(query_params)
        if 'release' in branch_query_params:
            del branch_query_params['release']
        branch_query_params['branch'] = b['name']
        if path:
            b['path'] = path
            branch_url_args['path'] = path
        b['url'] = reverse(browse_view_name,
                           url_args=branch_url_args,
                           query_params=branch_query_params)

    for r in releases:
        release_url_args = dict(url_args)
        release_query_params = dict(query_params)
        if 'branch' in release_query_params:
            del release_query_params['branch']
        release_query_params['release'] = r['name']
        if path:
            r['path'] = path
            release_url_args['path'] = path
        r['url'] = reverse(browse_view_name,
                           url_args=release_url_args,
                           query_params=release_query_params)

    snapshot_context['query_params'] = query_params
    snapshot_context['root_sha1_git'] = root_sha1_git
    snapshot_context['revision_id'] = revision_id
    snapshot_context['branch'] = branch_name
    snapshot_context['release'] = release_name
    snapshot_context['release_id'] = release_id

    return snapshot_context


def browse_snapshot_directory(request, snapshot_id=None, origin_type=None,
                              origin_url=None, timestamp=None, path=None):
    """
    Django view implementation for browsing a directory in a snapshot context.
    """
    try:

        snapshot_context = _process_snapshot_request(request, snapshot_id,
                                                     origin_type, origin_url,
                                                     timestamp, path,
                                                     browse_context='directory') # noqa

        root_sha1_git = snapshot_context['root_sha1_git']
        sha1_git = root_sha1_git
        if root_sha1_git and path:
            dir_info = service.lookup_directory_with_path(root_sha1_git, path)
            # some readme files can reference assets reachable from the
            # browsed directory, handle that special case in order to
            # correctly displayed them
            if dir_info and dir_info['type'] == 'file':
                file_raw_url = reverse(
                    'browse-content-raw',
                    url_args={'query_string': dir_info['checksums']['sha1']})
                return redirect(file_raw_url)
            sha1_git = dir_info['target']

        dirs = []
        files = []
        if sha1_git:
            dirs, files = get_directory_entries(sha1_git)

    except Exception as exc:
        return handle_view_exception(request, exc)

    swh_type = snapshot_context['swh_type']
    origin_info = snapshot_context['origin_info']
    visit_info = snapshot_context['visit_info']
    url_args = snapshot_context['url_args']
    query_params = snapshot_context['query_params']
    revision_id = snapshot_context['revision_id']
    snapshot_id = snapshot_context['snapshot_id']

    path_info = gen_path_info(path)

    browse_view_name = 'browse-' + swh_type + '-directory'

    breadcrumbs = []
    if root_sha1_git:
        breadcrumbs.append({'name': root_sha1_git[:7],
                            'url': reverse(browse_view_name,
                                           url_args=url_args,
                                           query_params=query_params)})
    for pi in path_info:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = pi['path']
        breadcrumbs.append({'name': pi['name'],
                            'url': reverse(browse_view_name,
                                           url_args=bc_url_args,
                                           query_params=query_params)})

    path = '' if path is None else (path + '/')

    for d in dirs:
        if d['type'] == 'rev':
            d['url'] = reverse('browse-revision',
                               url_args={'sha1_git': d['target']})
        else:
            bc_url_args = dict(url_args)
            bc_url_args['path'] = path + d['name']
            d['url'] = reverse(browse_view_name,
                               url_args=bc_url_args,
                               query_params=query_params)

    sum_file_sizes = 0

    readmes = {}

    browse_view_name = 'browse-' + swh_type + '-content'

    for f in files:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = path + f['name']
        f['url'] = reverse(browse_view_name,
                           url_args=bc_url_args,
                           query_params=query_params)
        if f['length'] is not None:
            sum_file_sizes += f['length']
            f['length'] = filesizeformat(f['length'])
        if f['name'].lower().startswith('readme'):
            readmes[f['name']] = f['checksums']['sha1']

    readme_name, readme_url, readme_html = get_readme_to_display(readmes)

    browse_view_name = 'browse-' + swh_type + '-log'

    history_url = None
    if snapshot_id != _empty_snapshot_id:
        history_url = reverse(browse_view_name,
                              url_args=url_args,
                              query_params=query_params)

    nb_files = None
    nb_dirs = None
    sum_file_sizes = None
    dir_path = None
    if root_sha1_git:
        nb_files = len(files)
        nb_dirs = len(dirs)
        sum_file_sizes = filesizeformat(sum_file_sizes)
        dir_path = '/' + path

    browse_dir_link = \
        gen_directory_link(sha1_git, link_text='Browse',
                           link_attrs={'class': 'btn btn-default btn-sm',
                                       'role': 'button'})

    browse_rev_link = \
        gen_revision_link(revision_id,
                          snapshot_context=snapshot_context,
                          link_text='Browse',
                          link_attrs={'class': 'btn btn-default btn-sm',
                                      'role': 'button'})

    dir_metadata = {'id': sha1_git,
                    'context-independent directory': browse_dir_link,
                    'number of regular files': nb_files,
                    'number of subdirectories': nb_dirs,
                    'sum of regular file sizes': sum_file_sizes,
                    'path': dir_path,
                    'revision id': revision_id,
                    'revision': browse_rev_link,
                    'snapshot id': snapshot_id}

    if origin_info:
        dir_metadata['origin id'] = origin_info['id']
        dir_metadata['origin type'] = origin_info['type']
        dir_metadata['origin url'] = origin_info['url']
        dir_metadata['origin visit date'] = format_utc_iso_date(visit_info['date']) # noqa
        dir_metadata['origin visit id'] = visit_info['visit']
        snapshot_context_url = reverse('browse-snapshot-directory',
                                       url_args={'snapshot_id': snapshot_id},
                                       query_params=request.GET)
        browse_snapshot_link = \
            gen_link(snapshot_context_url, link_text='Browse',
                     link_attrs={'class': 'btn btn-default btn-sm',
                                 'role': 'button'})
        dir_metadata['snapshot context'] = browse_snapshot_link

    vault_cooking = {
        'directory_context': True,
        'directory_id': sha1_git,
        'revision_context': True,
        'revision_id': revision_id
    }

    swh_objects = [{'type': 'directory',
                    'id': sha1_git},
                   {'type': 'revision',
                    'id': revision_id},
                   {'type': 'snapshot',
                    'id': snapshot_id}]

    release_id = snapshot_context['release_id']
    if release_id:
        swh_objects.append({'type': 'release',
                            'id': release_id})

    swh_ids = get_swh_persistent_ids(swh_objects, snapshot_context)

    dir_path = '/'.join([bc['name'] for bc in breadcrumbs]) + '/'
    context_found = 'snapshot: %s' % snapshot_context['snapshot_id']
    if origin_info:
        context_found = 'origin: %s' % origin_info['url']
    heading = 'Directory - %s - %s - %s' %\
        (dir_path, snapshot_context['branch'], context_found)

    return render(request, 'browse/directory.html',
                  {'heading': heading,
                   'swh_object_name': 'Directory',
                   'swh_object_metadata': dir_metadata,
                   'dirs': dirs,
                   'files': files,
                   'breadcrumbs': breadcrumbs if root_sha1_git else [],
                   'top_right_link': {
                       'url': history_url,
                       'icon': swh_object_icons['revisions history'],
                       'text': 'History'
                    },
                   'readme_name': readme_name,
                   'readme_url': readme_url,
                   'readme_html': readme_html,
                   'snapshot_context': snapshot_context,
                   'vault_cooking': vault_cooking,
                   'show_actions_menu': True,
                   'swh_ids': swh_ids})


def browse_snapshot_content(request, snapshot_id=None, origin_type=None,
                            origin_url=None, timestamp=None, path=None):
    """
    Django view implementation for browsing a content in a snapshot context.
    """
    try:

        snapshot_context = _process_snapshot_request(request, snapshot_id,
                                                     origin_type, origin_url,
                                                     timestamp, path,
                                                     browse_context='content')

        root_sha1_git = snapshot_context['root_sha1_git']
        sha1_git = None
        query_string = None
        content_data = None
        if root_sha1_git:
            content_info = service.lookup_directory_with_path(root_sha1_git,
                                                              path)
            sha1_git = content_info['target']
            query_string = 'sha1_git:' + sha1_git
            content_data = request_content(query_string,
                                           raise_if_unavailable=False)

    except Exception as exc:
        return handle_view_exception(request, exc)

    swh_type = snapshot_context['swh_type']
    url_args = snapshot_context['url_args']
    query_params = snapshot_context['query_params']
    revision_id = snapshot_context['revision_id']
    origin_info = snapshot_context['origin_info']
    visit_info = snapshot_context['visit_info']
    snapshot_id = snapshot_context['snapshot_id']

    content = None
    language = None
    mimetype = None
    if content_data and content_data['raw_data'] is not None:
        content_display_data = prepare_content_for_display(
            content_data['raw_data'], content_data['mimetype'], path)
        content = content_display_data['content_data']
        language = content_display_data['language']
        mimetype = content_display_data['mimetype']

    filename = None
    path_info = None

    browse_view_name = 'browse-' + swh_type + '-directory'

    breadcrumbs = []

    split_path = path.split('/')
    filename = split_path[-1]
    path_info = gen_path_info(path[:-len(filename)])
    if root_sha1_git:
        breadcrumbs.append({'name': root_sha1_git[:7],
                            'url': reverse(browse_view_name,
                                           url_args=url_args,
                                           query_params=query_params)})
    for pi in path_info:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = pi['path']
        breadcrumbs.append({'name': pi['name'],
                            'url': reverse(browse_view_name,
                                           url_args=bc_url_args,
                                           query_params=query_params)})

    breadcrumbs.append({'name': filename,
                        'url': None})

    browse_content_link = \
        gen_content_link(sha1_git, link_text='Browse',
                         link_attrs={'class': 'btn btn-default btn-sm',
                                     'role': 'button'})

    content_raw_url = None
    if query_string:
        content_raw_url = reverse('browse-content-raw',
                                  url_args={'query_string': query_string},
                                  query_params={'filename': filename})

    browse_rev_link = \
        gen_revision_link(revision_id,
                          snapshot_context=snapshot_context,
                          link_text='Browse',
                          link_attrs={'class': 'btn btn-default btn-sm',
                                      'role': 'button'})

    content_metadata = {
        'context-independent content': browse_content_link,
        'path': None,
        'filename': None,
        'revision id': revision_id,
        'revision': browse_rev_link,
        'snapshot id': snapshot_id
    }

    cnt_sha1_git = None
    content_size = None
    error_code = 200
    error_description = ''
    error_message = ''
    if content_data:
        content_metadata['sha1 checksum'] = \
            content_data['checksums']['sha1']
        content_metadata['sha1_git checksum'] = \
            content_data['checksums']['sha1_git']
        content_metadata['sha256 checksum'] = \
            content_data['checksums']['sha256']
        content_metadata['blake2s256 checksum'] = \
            content_data['checksums']['blake2s256']
        content_metadata['mime type'] = content_data['mimetype']
        content_metadata['encoding'] = content_data['encoding']
        content_metadata['size'] = filesizeformat(content_data['length'])
        content_metadata['language'] = content_data['language']
        content_metadata['licenses'] = content_data['licenses']
        content_metadata['path'] = '/' + path[:-len(filename)]
        content_metadata['filename'] = filename

        cnt_sha1_git = content_data['checksums']['sha1_git']
        content_size = content_data['length']
        error_code = content_data['error_code']
        error_message = content_data['error_message']
        error_description = content_data['error_description']

    if origin_info:
        content_metadata['origin id'] = origin_info['id']
        content_metadata['origin type'] = origin_info['type']
        content_metadata['origin url'] = origin_info['url']
        content_metadata['origin visit date'] = format_utc_iso_date(visit_info['date']) # noqa
        content_metadata['origin visit id'] = visit_info['visit']
        browse_snapshot_url = reverse('browse-snapshot-content',
                                      url_args={'snapshot_id': snapshot_id,
                                                'path': path},
                                      query_params=request.GET)
        browse_snapshot_link = \
            gen_link(browse_snapshot_url, link_text='Browse',
                     link_attrs={'class': 'btn btn-default btn-sm',
                                 'role': 'button'})
        content_metadata['snapshot context'] = browse_snapshot_link

    swh_objects = [{'type': 'content',
                    'id': cnt_sha1_git},
                   {'type': 'revision',
                    'id': revision_id},
                   {'type': 'snapshot',
                    'id': snapshot_id}]

    release_id = snapshot_context['release_id']
    if release_id:
        swh_objects.append({'type': 'release',
                            'id': release_id})

    swh_ids = get_swh_persistent_ids(swh_objects, snapshot_context)

    content_path = '/'.join([bc['name'] for bc in breadcrumbs])
    context_found = 'snapshot: %s' % snapshot_context['snapshot_id']
    if origin_info:
        context_found = 'origin: %s' % origin_info['url']
    heading = 'Content - %s - %s - %s' %\
        (content_path, snapshot_context['branch'], context_found)

    return render(request, 'browse/content.html',
                  {'heading': heading,
                   'swh_object_name': 'Content',
                   'swh_object_metadata': content_metadata,
                   'content': content,
                   'content_size': content_size,
                   'max_content_size': content_display_max_size,
                   'mimetype': mimetype,
                   'language': language,
                   'breadcrumbs': breadcrumbs if root_sha1_git else [],
                   'top_right_link': {
                        'url': content_raw_url,
                        'icon': swh_object_icons['content'],
                        'text': 'Raw File'
                    },
                   'snapshot_context': snapshot_context,
                   'vault_cooking': None,
                   'show_actions_menu': True,
                   'swh_ids': swh_ids,
                   'error_code': error_code,
                   'error_message': error_message,
                   'error_description': error_description},
                  status=error_code)


PER_PAGE = 100


def browse_snapshot_log(request, snapshot_id=None, origin_type=None,
                        origin_url=None, timestamp=None):
    """
    Django view implementation for browsing a revision history in a
    snapshot context.
    """
    try:

        snapshot_context = _process_snapshot_request(request, snapshot_id,
                                                     origin_type, origin_url,
                                                     timestamp, browse_context='log') # noqa

        revision_id = snapshot_context['revision_id']

        per_page = int(request.GET.get('per_page', PER_PAGE))
        offset = int(request.GET.get('offset', 0))
        revs_ordering = request.GET.get('revs_ordering', 'committer_date')
        session_key = 'rev_%s_log_ordering_%s' % (revision_id, revs_ordering)
        rev_log_session = request.session.get(session_key, None)
        rev_log = []
        revs_walker_state = None
        if rev_log_session:
            rev_log = rev_log_session['rev_log']
            revs_walker_state = rev_log_session['revs_walker_state']

        if len(rev_log) < offset+per_page:
            revs_walker = \
                service.get_revisions_walker(revs_ordering,
                                             revision_id,
                                             max_revs=offset+per_page+1,
                                             state=revs_walker_state)
            rev_log += list(revs_walker)
            revs_walker_state = revs_walker.export_state()

        revision_log = rev_log[offset:offset+per_page]

        request.session[session_key] = {
            'rev_log': rev_log,
            'revs_walker_state': revs_walker_state
        }

    except Exception as exc:
        return handle_view_exception(request, exc)

    swh_type = snapshot_context['swh_type']
    origin_info = snapshot_context['origin_info']
    visit_info = snapshot_context['visit_info']
    url_args = snapshot_context['url_args']
    query_params = snapshot_context['query_params']
    snapshot_id = snapshot_context['snapshot_id']

    query_params['per_page'] = per_page
    revs_ordering = request.GET.get('revs_ordering', '')
    query_params['revs_ordering'] = revs_ordering

    browse_view_name = 'browse-' + swh_type + '-log'

    prev_log_url = None
    if len(rev_log) > offset + per_page:
        query_params['offset'] = offset + per_page
        prev_log_url = reverse(browse_view_name,
                               url_args=url_args,
                               query_params=query_params)

    next_log_url = None
    if offset != 0:
        query_params['offset'] = offset - per_page
        next_log_url = reverse(browse_view_name,
                               url_args=url_args,
                               query_params=query_params)

    revision_log_data = format_log_entries(revision_log, per_page,
                                           snapshot_context)

    browse_log_link = \
        gen_revision_log_link(revision_id, link_text='Browse',
                              link_attrs={'class': 'btn btn-default btn-sm',
                                          'role': 'button'})

    revision_metadata = {
        'context-independent revision history': browse_log_link,
        'snapshot id': snapshot_id
    }

    if origin_info:
        revision_metadata['origin id'] = origin_info['id']
        revision_metadata['origin type'] = origin_info['type']
        revision_metadata['origin url'] = origin_info['url']
        revision_metadata['origin visit date'] = format_utc_iso_date(visit_info['date']) # noqa
        revision_metadata['origin visit id'] = visit_info['visit']
        browse_snapshot_url = reverse('browse-snapshot-log',
                                      url_args={'snapshot_id': snapshot_id},
                                      query_params=request.GET)
        browse_snapshot_link = \
            gen_link(browse_snapshot_url, link_text='Browse',
                     link_attrs={'class': 'btn btn-default btn-sm',
                                 'role': 'button'})
        revision_metadata['snapshot context'] = browse_snapshot_link

    swh_objects = [{'type': 'revision',
                    'id': revision_id},
                   {'type': 'snapshot',
                    'id': snapshot_id}]

    release_id = snapshot_context['release_id']
    if release_id:
        swh_objects.append({'type': 'release',
                            'id': release_id})

    swh_ids = get_swh_persistent_ids(swh_objects, snapshot_context)

    context_found = 'snapshot: %s' % snapshot_context['snapshot_id']
    if origin_info:
        context_found = 'origin: %s' % origin_info['url']
    heading = 'Revision history - %s - %s' %\
        (snapshot_context['branch'], context_found)

    return render(request, 'browse/revision-log.html',
                  {'heading': heading,
                   'swh_object_name': 'Revisions history',
                   'swh_object_metadata': revision_metadata,
                   'revision_log': revision_log_data,
                   'revs_ordering': revs_ordering,
                   'next_log_url': next_log_url,
                   'prev_log_url': prev_log_url,
                   'breadcrumbs': None,
                   'top_right_link': None,
                   'snapshot_context': snapshot_context,
                   'vault_cooking': None,
                   'show_actions_menu': True,
                   'swh_ids': swh_ids})


def browse_snapshot_branches(request, snapshot_id=None, origin_type=None,
                             origin_url=None, timestamp=None):
    """
    Django view implementation for browsing a list of branches in a snapshot
    context.
    """
    try:
        snapshot_context = _process_snapshot_request(request, snapshot_id,
                                                     origin_type, origin_url,
                                                     timestamp)

        branches_bc = request.GET.get('branches_breadcrumbs', '')
        branches_bc = \
            branches_bc.split(',') if branches_bc else []
        branches_from = branches_bc[-1] if branches_bc else ''

        swh_type = snapshot_context['swh_type']
        origin_info = snapshot_context['origin_info']
        url_args = snapshot_context['url_args']
        query_params = snapshot_context['query_params']

        browse_view_name = 'browse-' + swh_type + '-directory'

        snapshot = \
            service.lookup_snapshot(snapshot_context['snapshot_id'],
                                    branches_from, PER_PAGE+1,
                                    target_types=['revision', 'alias'])

        displayed_branches, _ = process_snapshot_branches(snapshot)

    except Exception as exc:
        return handle_view_exception(request, exc)

    for branch in displayed_branches:
        if snapshot_id:
            revision_url = reverse('browse-revision',
                                   url_args={'sha1_git': branch['revision']},
                                   query_params={'snapshot_id': snapshot_id})
        else:
            revision_url = reverse('browse-revision',
                                   url_args={'sha1_git': branch['revision']},
                                   query_params={'origin_type': origin_type,
                                                 'origin': origin_info['url']})
        query_params['branch'] = branch['name']
        directory_url = reverse(browse_view_name,
                                url_args=url_args,
                                query_params=query_params)
        del query_params['branch']
        branch['revision_url'] = revision_url
        branch['directory_url'] = directory_url

    browse_view_name = 'browse-' + swh_type + '-branches'

    prev_branches_url = None
    next_branches_url = None

    if branches_bc:
        query_params_prev = dict(query_params)

        query_params_prev['branches_breadcrumbs'] = \
            ','.join(branches_bc[:-1])
        prev_branches_url = reverse(browse_view_name, url_args=url_args,
                                    query_params=query_params_prev)
    elif branches_from:
        prev_branches_url = reverse(browse_view_name, url_args=url_args,
                                    query_params=query_params)

    if len(displayed_branches) > PER_PAGE:
        query_params_next = dict(query_params)
        next_branch = displayed_branches[-1]['name']
        del displayed_branches[-1]
        branches_bc.append(next_branch)
        query_params_next['branches_breadcrumbs'] = \
            ','.join(branches_bc)
        next_branches_url = reverse(browse_view_name, url_args=url_args,
                                    query_params=query_params_next)

    heading = 'Branches - '
    if origin_info:
        heading += 'origin: %s' % origin_info['url']
    else:
        heading += 'snapshot: %s' % snapshot_id

    return render(request, 'browse/branches.html',
                  {'heading': heading,
                   'swh_object_name': 'Branches',
                   'swh_object_metadata': {},
                   'top_right_link': None,
                   'displayed_branches': displayed_branches,
                   'prev_branches_url': prev_branches_url,
                   'next_branches_url': next_branches_url,
                   'snapshot_context': snapshot_context})


def browse_snapshot_releases(request, snapshot_id=None, origin_type=None,
                             origin_url=None, timestamp=None):
    """
    Django view implementation for browsing a list of releases in a snapshot
    context.
    """
    try:
        snapshot_context = _process_snapshot_request(request, snapshot_id,
                                                     origin_type, origin_url,
                                                     timestamp)

        rel_bc = request.GET.get('releases_breadcrumbs', '')
        rel_bc = \
            rel_bc.split(',') if rel_bc else []
        rel_from = rel_bc[-1] if rel_bc else ''

        swh_type = snapshot_context['swh_type']
        origin_info = snapshot_context['origin_info']
        url_args = snapshot_context['url_args']
        query_params = snapshot_context['query_params']

        snapshot = \
            service.lookup_snapshot(snapshot_context['snapshot_id'],
                                    rel_from, PER_PAGE+1,
                                    target_types=['release', 'alias'])

        _, displayed_releases = process_snapshot_branches(snapshot)

    except Exception as exc:
        return handle_view_exception(request, exc)

    for release in displayed_releases:
        if snapshot_id:
            query_params_tgt = {'snapshot_id': snapshot_id}
        else:
            query_params_tgt = {'origin': origin_info['url']}
        release_url = reverse('browse-release',
                              url_args={'sha1_git': release['id']},
                              query_params=query_params_tgt)

        target_url = ''
        if release['target_type'] == 'revision':
            target_url = reverse('browse-revision',
                                 url_args={'sha1_git': release['target']},
                                 query_params=query_params_tgt)
        elif release['target_type'] == 'directory':
            target_url = reverse('browse-directory',
                                 url_args={'sha1_git': release['target']},
                                 query_params=query_params_tgt)
        elif release['target_type'] == 'content':
            target_url = reverse('browse-content',
                                 url_args={'query_string': release['target']},
                                 query_params=query_params_tgt)
        elif release['target_type'] == 'release':
            target_url = reverse('browse-release',
                                 url_args={'sha1_git': release['target']},
                                 query_params=query_params_tgt)

        release['release_url'] = release_url
        release['target_url'] = target_url

    browse_view_name = 'browse-' + swh_type + '-releases'

    prev_releases_url = None
    next_releases_url = None

    if rel_bc:
        query_params_prev = dict(query_params)

        query_params_prev['releases_breadcrumbs'] = \
            ','.join(rel_bc[:-1])
        prev_releases_url = reverse(browse_view_name, url_args=url_args,
                                    query_params=query_params_prev)
    elif rel_from:
        prev_releases_url = reverse(browse_view_name, url_args=url_args,
                                    query_params=query_params)

    if len(displayed_releases) > PER_PAGE:
        query_params_next = dict(query_params)
        next_rel = displayed_releases[-1]['branch_name']
        del displayed_releases[-1]
        rel_bc.append(next_rel)
        query_params_next['releases_breadcrumbs'] = \
            ','.join(rel_bc)
        next_releases_url = reverse(browse_view_name, url_args=url_args,
                                    query_params=query_params_next)

    heading = 'Releases - '
    if origin_info:
        heading += 'origin: %s' % origin_info['url']
    else:
        heading += 'snapshot: %s' % snapshot_id

    return render(request, 'browse/releases.html',
                  {'heading': heading,
                   'top_panel_visible': False,
                   'top_panel_collapsible': False,
                   'swh_object_name': 'Releases',
                   'swh_object_metadata': {},
                   'top_right_link': None,
                   'displayed_releases': displayed_releases,
                   'prev_releases_url': prev_releases_url,
                   'next_releases_url': next_releases_url,
                   'snapshot_context': snapshot_context,
                   'vault_cooking': None,
                   'show_actions_menu': False})
