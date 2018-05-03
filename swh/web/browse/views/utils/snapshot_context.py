# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# Utility module implementing Django views for browsing the SWH archive
# in a snapshot context.
# Its purpose is to factorize code for the views reachable from the
# /origin/.* and /snapshot/.* endpoints.

from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.template.defaultfilters import filesizeformat

from swh.web.browse.utils import (
    get_snapshot_context, get_directory_entries, gen_directory_link,
    gen_revision_link, request_content, gen_content_link,
    prepare_content_for_display, content_display_max_size,
    prepare_revision_log_for_display, gen_snapshot_directory_link,
    gen_revision_log_link, gen_link
)

from swh.web.common import service
from swh.web.common.exc import (
    handle_view_exception, NotFoundExc
)
from swh.web.common.utils import (
    reverse, gen_path_info, format_utc_iso_date
)


def _get_branch(branches, branch_name):
    """
    Utility function to get a specific branch from a branches list.
    Its purpose is to get the default HEAD branch as some SWH origin
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

    browse_view_name = 'browse-' + swh_type + '-' + browse_context

    for b in branches:
        branch_url_args = dict(url_args)
        branch_query_params = dict(query_params)
        branch_query_params['branch'] = b['name']
        if path:
            b['path'] = path
            branch_url_args['path'] = path
        b['url'] = reverse(browse_view_name,
                           kwargs=branch_url_args,
                           query_params=branch_query_params)

    for r in releases:
        release_url_args = dict(url_args)
        release_query_params = dict(query_params)
        release_query_params['release'] = r['name']
        if path:
            r['path'] = path
            release_url_args['path'] = path
        r['url'] = reverse(browse_view_name,
                           kwargs=release_url_args,
                           query_params=release_query_params)

    root_sha1_git = None
    revision_id = request.GET.get('revision', None)
    release_name = request.GET.get('release', None)
    branch_name = None

    if revision_id:
        revision = service.lookup_revision(revision_id)
        root_sha1_git = revision['directory']
        branches.append({'name': revision_id,
                         'revision': revision_id,
                         'directory': root_sha1_git,
                         'url': None})
        branch_name = revision_id
        query_params['revision'] = revision_id
    elif release_name:
        release = _get_release(releases, release_name)
        if release:
            root_sha1_git = release['directory']
            revision_id = release['target']
            query_params['release'] = release_name
        else:
            _branch_not_found("release", release_name, releases, snapshot_id,
                              origin_info, timestamp, visit_id)
    else:
        branch_name = request.GET.get('branch', None)
        if branch_name:
            query_params['branch'] = branch_name
        branch = _get_branch(branches, branch_name or 'HEAD')
        if branch:
            branch_name = branch['name']
            root_sha1_git = branch['directory']
            revision_id = branch['revision']

        else:
            _branch_not_found("branch", branch_name, branches, snapshot_id,
                              origin_info, timestamp, visit_id)

    snapshot_context['query_params'] = query_params
    snapshot_context['root_sha1_git'] = root_sha1_git
    snapshot_context['revision_id'] = revision_id
    snapshot_context['branch'] = branch_name
    snapshot_context['release'] = release_name

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
        if path:
            dir_info = service.lookup_directory_with_path(root_sha1_git, path)
            sha1_git = dir_info['target']

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
    breadcrumbs.append({'name': root_sha1_git[:7],
                        'url': reverse(browse_view_name,
                                       kwargs=url_args,
                                       query_params=query_params)})
    for pi in path_info:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = pi['path']
        breadcrumbs.append({'name': pi['name'],
                            'url': reverse(browse_view_name,
                                           kwargs=bc_url_args,
                                           query_params=query_params)})

    path = '' if path is None else (path + '/')

    for d in dirs:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = path + d['name']
        d['url'] = reverse(browse_view_name,
                           kwargs=bc_url_args,
                           query_params=query_params)

    sum_file_sizes = 0

    readme_name = None
    readme_url = None

    browse_view_name = 'browse-' + swh_type + '-content'

    for f in files:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = path + f['name']
        f['url'] = reverse(browse_view_name,
                           kwargs=bc_url_args,
                           query_params=query_params)
        sum_file_sizes += f['length']
        f['length'] = filesizeformat(f['length'])
        if f['name'].lower().startswith('readme'):
            readme_name = f['name']
            readme_sha1 = f['checksums']['sha1']
            readme_url = reverse('browse-content-raw',
                                 kwargs={'query_string': readme_sha1})

    browse_view_name = 'browse-' + swh_type + '-log'

    history_url = reverse(browse_view_name,
                          kwargs=url_args,
                          query_params=query_params)

    sum_file_sizes = filesizeformat(sum_file_sizes)

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
                    'number of regular files': len(files),
                    'number of subdirectories': len(dirs),
                    'sum of regular file sizes': sum_file_sizes,
                    'path': '/' + path,
                    'revision id': revision_id,
                    'revision': browse_rev_link,
                    'snapshot id': snapshot_id}

    if origin_info:
        dir_metadata['origin id'] = origin_info['id']
        dir_metadata['origin type'] = origin_info['type']
        dir_metadata['origin url'] = origin_info['url']
        dir_metadata['origin visit date'] = format_utc_iso_date(visit_info['date']), # noqa
        dir_metadata['origin visit id'] = visit_info['visit']
        snapshot_context_url = reverse('browse-snapshot-directory',
                                       kwargs={'snapshot_id': snapshot_id},
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

    return render(request, 'directory.html',
                  {'empty_browse': False,
                   'heading': 'Directory information',
                   'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text': 'Directory metadata',
                   'swh_object_metadata': dir_metadata,
                   'main_panel_visible': True,
                   'dirs': dirs,
                   'files': files,
                   'breadcrumbs': breadcrumbs,
                   'top_right_link': history_url,
                   'top_right_link_text': mark_safe(
                     '<i class="fa fa-history fa-fw" aria-hidden="true"></i>'
                     'History'
                   ),
                   'readme_name': readme_name,
                   'readme_url': readme_url,
                   'snapshot_context': snapshot_context,
                   'vault_cooking': vault_cooking,
                   'show_actions_menu': True})


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
        content_info = service.lookup_directory_with_path(root_sha1_git, path)
        sha1_git = content_info['target']
        query_string = 'sha1_git:' + sha1_git
        content_data = request_content(query_string)

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
    if content_data['raw_data'] is not None:
        content_display_data = prepare_content_for_display(
            content_data['raw_data'], content_data['mimetype'], path)
        content = content_display_data['content_data']
        language = content_display_data['language']

    filename = None
    path_info = None

    browse_view_name = 'browse-' + swh_type + '-directory'

    breadcrumbs = []

    split_path = path.split('/')
    filename = split_path[-1]
    path_info = gen_path_info(path[:-len(filename)])
    breadcrumbs.append({'name': root_sha1_git[:7],
                        'url': reverse(browse_view_name,
                                       kwargs=url_args,
                                       query_params=query_params)})
    for pi in path_info:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = pi['path']
        breadcrumbs.append({'name': pi['name'],
                            'url': reverse(browse_view_name,
                                           kwargs=bc_url_args,
                                           query_params=query_params)})

    breadcrumbs.append({'name': filename,
                        'url': None})

    browse_content_link = \
        gen_content_link(sha1_git, link_text='Browse',
                         link_attrs={'class': 'btn btn-default btn-sm',
                                     'role': 'button'})

    content_raw_url = reverse('browse-content-raw',
                              kwargs={'query_string': query_string},
                              query_params={'filename': filename})

    browse_rev_link = \
        gen_revision_link(revision_id,
                          snapshot_context=snapshot_context,
                          link_text='Browse',
                          link_attrs={'class': 'btn btn-default btn-sm',
                                      'role': 'button'})

    content_metadata = {
        'context-independent content': browse_content_link,
        'sha1 checksum': content_data['checksums']['sha1'],
        'sha1_git checksum': content_data['checksums']['sha1_git'],
        'sha256 checksum': content_data['checksums']['sha256'],
        'blake2s256 checksum': content_data['checksums']['blake2s256'],
        'mime type': content_data['mimetype'],
        'encoding': content_data['encoding'],
        'size': filesizeformat(content_data['length']),
        'language': content_data['language'],
        'licenses': content_data['licenses'],
        'path': '/' + path[:-len(filename)],
        'filename': filename,
        'revision id': revision_id,
        'revision': browse_rev_link,
        'snapshot id': snapshot_id
    }

    if origin_info:
        content_metadata['origin id'] = origin_info['id'],
        content_metadata['origin type'] = origin_info['type']
        content_metadata['origin url'] = origin_info['url']
        content_metadata['origin visit date'] = format_utc_iso_date(visit_info['date']) # noqa
        content_metadata['origin visit id'] = visit_info['visit']
        browse_snapshot_url = reverse('browse-snapshot-content',
                                      kwargs={'snapshot_id': snapshot_id,
                                              'path': path},
                                      query_params=request.GET)
        browse_snapshot_link = \
            gen_link(browse_snapshot_url, link_text='Browse',
                     link_attrs={'class': 'btn btn-default btn-sm',
                                 'role': 'button'})
        content_metadata['snapshot context'] = browse_snapshot_link

    return render(request, 'content.html',
                  {'empty_browse': False,
                   'heading': 'Content information',
                   'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text': 'Content metadata',
                   'swh_object_metadata': content_metadata,
                   'main_panel_visible': True,
                   'content': content,
                   'content_size': content_data['length'],
                   'max_content_size': content_display_max_size,
                   'mimetype': content_data['mimetype'],
                   'language': language,
                   'breadcrumbs': breadcrumbs,
                   'top_right_link': content_raw_url,
                   'top_right_link_text': mark_safe(
                       '<i class="fa fa-file-text fa-fw" aria-hidden="true">'
                       '</i>Raw File'),
                   'snapshot_context': snapshot_context,
                   'vault_cooking': None,
                   'show_actions_menu': False})


PER_PAGE = 20


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
        current_rev = revision_id
        per_page = int(request.GET.get('per_page', PER_PAGE))
        revs_breadcrumb = request.GET.get('revs_breadcrumb', None)

        if revs_breadcrumb:
            current_rev = revs_breadcrumb.split('/')[-1]
        revision_log = service.lookup_revision_log(current_rev,
                                                   limit=per_page+1)
        revision_log = list(revision_log)

    except Exception as exc:
        return handle_view_exception(request, exc)

    swh_type = snapshot_context['swh_type']
    origin_info = snapshot_context['origin_info']
    visit_info = snapshot_context['visit_info']
    url_args = snapshot_context['url_args']
    query_params = snapshot_context['query_params']
    snapshot_id = snapshot_context['snapshot_id']

    query_params['per_page'] = per_page

    revision_log_display_data = prepare_revision_log_for_display(
        revision_log, per_page, revs_breadcrumb, snapshot_context)

    browse_view_name = 'browse-' + swh_type + '-log'

    prev_rev = revision_log_display_data['prev_rev']
    prev_revs_breadcrumb = revision_log_display_data['prev_revs_breadcrumb']
    prev_log_url = None
    query_params['revs_breadcrumb'] = prev_revs_breadcrumb
    if prev_rev:
        prev_log_url = \
            reverse(browse_view_name,
                    kwargs=url_args,
                    query_params=query_params)

    next_rev = revision_log_display_data['next_rev']
    next_revs_breadcrumb = revision_log_display_data['next_revs_breadcrumb']
    next_log_url = None
    query_params['revs_breadcrumb'] = next_revs_breadcrumb
    if next_rev:
        next_log_url = \
            reverse(browse_view_name,
                    kwargs=url_args,
                    query_params=query_params)

    revision_log_data = revision_log_display_data['revision_log_data']

    for i, log in enumerate(revision_log_data):
        params = {
            'revision': revision_log[i]['id'],
        }
        if 'visit_id' in query_params:
            params['visit_id'] = query_params['visit_id']
        log['directory'] = gen_snapshot_directory_link(
            snapshot_context, revision_log[i]['id'],
            link_text='<i class="fa fa-folder-open fa-fw" aria-hidden="true">'
                      '</i>Browse files',
            link_attrs={'class': 'btn btn-default btn-sm',
                        'role': 'button'})

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
                                      kwargs={'snapshot_id': snapshot_id},
                                      query_params=request.GET)
        browse_snapshot_link = \
            gen_link(browse_snapshot_url, link_text='Browse',
                     link_attrs={'class': 'btn btn-default btn-sm',
                                 'role': 'button'})
        revision_metadata['snapshot context'] = browse_snapshot_link

    return render(request, 'revision-log.html',
                  {'empty_browse': False,
                   'heading': 'Revision history information',
                   'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text': 'Revision history metadata',
                   'swh_object_metadata': revision_metadata,
                   'main_panel_visible': True,
                   'revision_log': revision_log_data,
                   'next_log_url': next_log_url,
                   'prev_log_url': prev_log_url,
                   'breadcrumbs': None,
                   'top_right_link': None,
                   'top_right_link_text': None,
                   'snapshot_context': snapshot_context,
                   'vault_cooking': None,
                   'show_actions_menu': False})


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

    except Exception as exc:
        return handle_view_exception(request, exc)

    branches_offset = int(request.GET.get('branches_offset', 0))

    swh_type = snapshot_context['swh_type']
    origin_info = snapshot_context['origin_info']
    url_args = snapshot_context['url_args']
    query_params = snapshot_context['query_params']

    browse_view_name = 'browse-' + swh_type + '-directory'

    branches = snapshot_context['branches']

    displayed_branches = \
        branches[branches_offset:branches_offset+PER_PAGE]

    for branch in displayed_branches:
        if snapshot_id:
            revision_url = reverse('browse-revision',
                                   kwargs={'sha1_git': branch['revision']},
                                   query_params={'snapshot_id': snapshot_id})
        else:
            revision_url = reverse('browse-revision',
                                   kwargs={'sha1_git': branch['revision']},
                                   query_params={'origin_type': origin_info['type'], # noqa
                                                 'origin_url': origin_info['url']}) # noqa
        query_params['branch'] = branch['name']
        directory_url = reverse(browse_view_name,
                                kwargs=url_args,
                                query_params=query_params)
        del query_params['branch']
        branch['revision_url'] = revision_url
        branch['directory_url'] = directory_url

    browse_view_name = 'browse-' + swh_type + '-branches'

    prev_branches_url = None
    next_branches_url = None

    next_offset = branches_offset + PER_PAGE
    prev_offset = branches_offset - PER_PAGE
    if next_offset < len(branches):
        query_params['branches_offset'] = next_offset
        next_branches_url = reverse(browse_view_name,
                                    kwargs=url_args, query_params=query_params)
    query_params['branches_offset'] = None
    if prev_offset >= 0:
        if prev_offset != 0:
            query_params['branches_offset'] = prev_offset
        prev_branches_url = reverse(browse_view_name,
                                    kwargs=url_args, query_params=query_params)

    return render(request, 'branches.html',
                  {'empty_browse': False,
                   'heading': 'Origin branches list',
                   'top_panel_visible': False,
                   'top_panel_collapsible': False,
                   'top_panel_text': 'Branches list',
                   'swh_object_metadata': {},
                   'main_panel_visible': True,
                   'top_right_link': None,
                   'top_right_link_text': None,
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

    except Exception as exc:
        return handle_view_exception(request, exc)

    releases_offset = int(request.GET.get('releases_offset', 0))

    swh_type = snapshot_context['swh_type']
    origin_info = snapshot_context['origin_info']
    url_args = snapshot_context['url_args']
    query_params = snapshot_context['query_params']

    releases = snapshot_context['releases']

    displayed_releases = \
        releases[releases_offset:releases_offset+PER_PAGE]

    for release in displayed_releases:
        if snapshot_id:
            release_url = reverse('browse-release',
                                  kwargs={'sha1_git': release['id']},
                                  query_params={'snapshot_id': snapshot_id})
        else:
            release_url = reverse('browse-release',
                                  kwargs={'sha1_git': release['id']},
                                  query_params={'origin_type': origin_info['type'], # noqa
                                                'origin_url': origin_info['url']}) # noqa
        query_params['release'] = release['name']
        del query_params['release']
        release['release_url'] = release_url

    browse_view_name = 'browse-' + swh_type + '-releases'

    prev_releases_url = None
    next_releases_url = None

    next_offset = releases_offset + PER_PAGE
    prev_offset = releases_offset - PER_PAGE
    if next_offset < len(releases):
        query_params['releases_offset'] = next_offset
        next_releases_url = reverse(browse_view_name,
                                    kwargs=url_args, query_params=query_params)
    query_params['releases_offset'] = None
    if prev_offset >= 0:
        if prev_offset != 0:
            query_params['releases_offset'] = prev_offset
        prev_releases_url = reverse(browse_view_name,
                                    kwargs=url_args, query_params=query_params)

    return render(request, 'releases.html',
                  {'empty_browse': False,
                   'heading': 'Origin releases list',
                   'top_panel_visible': False,
                   'top_panel_collapsible': False,
                   'top_panel_text': 'Releases list',
                   'swh_object_metadata': {},
                   'main_panel_visible': True,
                   'top_right_link': None,
                   'top_right_link_text': None,
                   'displayed_releases': displayed_releases,
                   'prev_releases_url': prev_releases_url,
                   'next_releases_url': next_releases_url,
                   'snapshot_context': snapshot_context,
                   'vault_cooking': None,
                   'show_actions_menu': False})
