# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import dateutil

from django.shortcuts import render
from django.template.defaultfilters import filesizeformat

from swh.web.common import service
from swh.web.common.utils import reverse, format_utc_iso_date
from swh.web.common.exc import NotFoundExc, handle_view_exception
from swh.web.browse.utils import (
    get_origin_visits, get_origin_visit_branches,
    gen_path_info, get_directory_entries, request_content,
    prepare_content_for_display, gen_link,
    prepare_revision_log_for_display
)
from swh.web.browse.browseurls import browse_route


@browse_route(r'origin/(?P<origin_id>[0-9]+)/',
              r'origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/',
              view_name='browse-origin')
def origin_browse(request, origin_id=None, origin_type=None,
                  origin_url=None):
    """Django view that produces an HTML display of a swh origin identified
    by its id or its url.

    The url scheme that points to it is :http:get:`/browse/origin/(origin_id)/`.

    Args:
        request: input django http request
        origin_id: a swh origin id
        origin_type: type of origin (git, svn, ...)
        origin_url: url of the origin (e.g. https://github.com/<user>/<repo>)

    Returns:
        The HMTL rendering for the metadata of the provided origin.
    """ # noqa
    try:
        if origin_id:
            origin_request_params = {
                'id': origin_id,
            }
        else:
            origin_request_params = {
                'type': origin_type,
                'url': origin_url
            }
        origin_info = service.lookup_origin(origin_request_params)
        origin_id = origin_info['id']
        origin_visits = get_origin_visits(origin_id)
    except Exception as exc:
        return handle_view_exception(request, exc)

    origin_info['last swh visit browse url'] = \
        reverse('browse-origin-directory',
                kwargs={'origin_id': origin_id})

    origin_visits_data = []
    for visit in origin_visits:
        visit_date = dateutil.parser.parse(visit['date'])
        visit['date'] = format_utc_iso_date(visit['date'])
        visit['browse_url'] = reverse('browse-origin-directory',
                                      kwargs={'origin_id': origin_id,
                                              'visit_id': visit['visit']})
        origin_visits_data.append(
            {'date': visit_date.timestamp()})

    return render(request, 'origin.html',
                  {'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text_left': 'SWH object: Origin',
                   'top_panel_text_right': 'Url: ' + origin_info['url'],
                   'swh_object_metadata': origin_info,
                   'main_panel_visible': True,
                   'origin_visits_data': origin_visits_data,
                   'visits': list(reversed(origin_visits)),
                   'browse_url_base': '/browse/origin/%s/' %
                   origin_id})


def _get_origin_branches_and_url_args(origin_id, visit_id, ts):
    if not visit_id and ts:
        branches = get_origin_visit_branches(origin_id, visit_ts=ts)
        url_args = {'origin_id': origin_id,
                    'timestamp': ts}
    else:
        branches = get_origin_visit_branches(origin_id, visit_id)
        url_args = {'origin_id': origin_id,
                    'visit_id': visit_id}
    return branches, url_args


def _raise_exception_if_branch_not_found(origin_id, visit_id, ts, branch):
    if visit_id:
        raise NotFoundExc('Branch %s associated to visit with'
                          ' id %s for origin with id %s'
                          ' not found!' %
                          (branch, visit_id, origin_id))
    else:
        raise NotFoundExc('Branch %s associated to visit with'
                          ' timestamp %s for origin with id %s'
                          ' not found!' %
                          (branch, ts, origin_id))


def _get_branch(branches, branch_name):
    """
    Utility function to get a specific branch from an origin branches list.
    Its purpose is to get the default HEAD branch as some SWH origin
    (e.g those with svn type) does not have it. In that latter case, check
    if there is a master branch instead and returns it.
    """
    filtered_branches = [b for b in branches if b['name'].endswith(branch_name)] # noqa
    if len(filtered_branches) > 0:
        return filtered_branches[0]
    elif branch_name == 'HEAD':
        filtered_branches = [b for b in branches if b['name'].endswith('master')] # noqa
        if len(filtered_branches) > 0:
            return filtered_branches[0]
    return None


@browse_route(r'origin/(?P<origin_id>[0-9]+)/directory/',
              r'origin/(?P<origin_id>[0-9]+)/directory/(?P<path>.+)/',
              r'origin/(?P<origin_id>[0-9]+)/visit/(?P<visit_id>[0-9]+)/directory/', # noqa
              r'origin/(?P<origin_id>[0-9]+)/visit/(?P<visit_id>[0-9]+)/directory/(?P<path>.+)/', # noqa
              r'origin/(?P<origin_id>[0-9]+)/ts/(?P<timestamp>.+)/directory/', # noqa
              r'origin/(?P<origin_id>[0-9]+)/ts/(?P<timestamp>.+)/directory/(?P<path>.+)/', # noqa
              view_name='browse-origin-directory')
def origin_directory_browse(request, origin_id, visit_id=None,
                            timestamp=None, path=None):
    """Django view for browsing the content of a swh directory associated
    to an origin for a given visit.

    The url scheme that points to it is the following:

        * :http:get:`/browse/origin/(origin_id)/directory/[(path)/]`
        * :http:get:`/browse/origin/(origin_id)/visit/(visit_id)/directory/[(path)/]`
        * :http:get:`/browse/origin/(origin_id)/ts/(timestamp)/directory/[(path)/]`

    Args:
        request: input django http request
        origin_id: a swh origin id
        visit_id: optionnal visit id parameter
            (the last one will be used by default)
        timestamp: optionnal visit timestamp parameter
            (the last one will be used by default)
        path: optionnal path parameter used to navigate in directories
              reachable from the origin root one
        branch: optionnal query parameter that specifies the origin branch
            from which to retrieve the directory
        revision: optional query parameter to specify the origin revision
            from which to retrieve the directory

    Returns:
        The HTML rendering for the content of the directory associated
        to the provided origin and visit.
    """ # noqa
    try:

        if not visit_id and not timestamp:
            origin_visits = get_origin_visits(origin_id)
            if not origin_visits:
                raise NotFoundExc('No SWH visit associated to '
                                  'origin with id %s' % origin_id)
            return origin_directory_browse(request, origin_id,
                                           origin_visits[-1]['visit'],
                                           path=path)

        origin_info = service.lookup_origin({'id': origin_id})
        branches, url_args = _get_origin_branches_and_url_args(origin_id,
                                                               visit_id,
                                                               timestamp)

        for b in branches:
            branch_url_args = dict(url_args)
            if path:
                b['path'] = path
                branch_url_args['path'] = path
            b['url'] = reverse('browse-origin-directory',
                               kwargs=branch_url_args,
                               query_params={'branch': b['name']})

        revision_id = request.GET.get('revision', None)

        if revision_id:
            revision = service.lookup_revision(revision_id)
            root_sha1_git = revision['directory']
            branches.append({'name': revision_id,
                             'revision': revision_id,
                             'directory': root_sha1_git,
                             'url': None})
            branch_name = revision_id
        else:
            branch_name = request.GET.get('branch', 'HEAD')
            branch = _get_branch(branches, branch_name)
            if branch:
                branch_name = branch['name']
                root_sha1_git = branch['directory']
            else:
                _raise_exception_if_branch_not_found(origin_id, visit_id,
                                                     timestamp, branch_name)

        sha1_git = root_sha1_git
        if path:
            dir_info = service.lookup_directory_with_path(root_sha1_git, path)
            sha1_git = dir_info['target']

        dirs, files = get_directory_entries(sha1_git)

    except Exception as exc:
        return handle_view_exception(request, exc)

    if revision_id:
        query_params = {'revision': revision_id}
    else:
        query_params = {'branch': branch_name}

    path_info = gen_path_info(path)

    breadcrumbs = []
    breadcrumbs.append({'name': root_sha1_git[:7],
                        'url': reverse('browse-origin-directory',
                                       kwargs=url_args,
                                       query_params=query_params)})
    for pi in path_info:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = pi['path']
        breadcrumbs.append({'name': pi['name'],
                            'url': reverse('browse-origin-directory',
                                           kwargs=bc_url_args,
                                           query_params=query_params)})

    path = '' if path is None else (path + '/')

    for d in dirs:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = path + d['name']
        d['url'] = reverse('browse-origin-directory',
                           kwargs=bc_url_args,
                           query_params=query_params)

    sum_file_sizes = 0

    for f in files:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = path + f['name']
        f['url'] = reverse('browse-origin-content',
                           kwargs=bc_url_args,
                           query_params=query_params)
        sum_file_sizes += f['length']
        f['length'] = filesizeformat(f['length'])

    history_url = reverse('browse-origin-log',
                          kwargs=url_args,
                          query_params=query_params)

    sum_file_sizes = filesizeformat(sum_file_sizes)

    dir_metadata = {'id': sha1_git,
                    'number of regular files': len(files),
                    'number of subdirectories': len(dirs),
                    'sum of regular file sizes': sum_file_sizes,
                    'origin id': origin_info['id'],
                    'origin type': origin_info['type'],
                    'origin url': origin_info['url'],
                    'path': '/' + path}

    return render(request, 'directory.html',
                  {'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text_left': 'SWH object: Directory',
                   'top_panel_text_right': 'Origin: ' + origin_info['url'],
                   'swh_object_metadata': dir_metadata,
                   'main_panel_visible': True,
                   'dirs': dirs,
                   'files': files,
                   'breadcrumbs': breadcrumbs,
                   'branches': branches,
                   'branch': branch_name,
                   'top_right_link': history_url,
                   'top_right_link_text': 'History'})


@browse_route(r'origin/(?P<origin_id>[0-9]+)/content/(?P<path>.+)/',
              r'origin/(?P<origin_id>[0-9]+)/visit/(?P<visit_id>[0-9]+)/content/(?P<path>.+)/', # noqa
              r'origin/(?P<origin_id>[0-9]+)/ts/(?P<timestamp>.+)/content/(?P<path>.+)/', # noqa
              view_name='browse-origin-content')
def origin_content_display(request, origin_id, path,
                           visit_id=None, timestamp=None):
    """Django view that produces an HTML display of a swh content
    associated to an origin for a given visit.

    The url scheme that points to it is the following:

        * :http:get:`/browse/origin/(origin_id)/content/(path)/`
        * :http:get:`/browse/origin/(origin_id)/visit/(visit_id)/content/(path)/`
        * :http:get:`/browse/origin/(origin_id)/ts/(timestamp)/content/(path)/`

    Args:
        request: input django http request
        origin_id: id of a swh origin
        path: path of the content relative to the origin root directory
        visit_id: optionnal visit id parameter
            (the last one will be used by default)
        timestamp: optionnal visit timestamp parameter
            (the last one will be used by default)
        branch: optionnal query parameter that specifies the origin branch
            from which to retrieve the content
        revision: optional query parameter to specify the origin revision
            from which to retrieve the content

    Returns:
        The HTML rendering of the requested content associated to
        the provided origin and visit.

    """ # noqa
    try:

        if not visit_id and not timestamp:
            origin_visits = get_origin_visits(origin_id)
            if not origin_visits:
                raise NotFoundExc('No SWH visit associated to '
                                  'origin with id %s' % origin_id)
            return origin_content_display(request, origin_id, path,
                                          origin_visits[-1]['visit'])

        origin_info = service.lookup_origin({'id': origin_id})
        branches, url_args = _get_origin_branches_and_url_args(origin_id,
                                                               visit_id,
                                                               timestamp)

        for b in branches:
            bc_url_args = dict(url_args)
            bc_url_args['path'] = path
            b['url'] = reverse('browse-origin-content',
                               kwargs=bc_url_args,
                               query_params={'branch': b['name']})

        revision_id = request.GET.get('revision', None)

        if revision_id:
            revision = service.lookup_revision(revision_id)
            root_sha1_git = revision['directory']
            branches.append({'name': revision_id,
                             'revision': revision_id,
                             'directory': root_sha1_git,
                             'url': None})
            branch_name = revision_id
        else:
            branch_name = request.GET.get('branch', 'HEAD')
            branch = _get_branch(branches, branch_name)
            if branch:
                branch_name = branch['name']
                root_sha1_git = branch['directory']
            else:
                _raise_exception_if_branch_not_found(origin_id, visit_id,
                                                     timestamp, branch_name)

        content_info = service.lookup_directory_with_path(root_sha1_git, path)
        sha1_git = content_info['target']
        query_string = 'sha1_git:' + sha1_git
        content_data = request_content(query_string)

    except Exception as exc:
        return handle_view_exception(request, exc)

    if revision_id:
        query_params = {'revision': revision_id}
    else:
        query_params = {'branch': branch_name}

    content_display_data = prepare_content_for_display(
        content_data['raw_data'], content_data['mimetype'], path)

    filename = None
    path_info = None

    breadcrumbs = []

    split_path = path.split('/')
    filename = split_path[-1]
    path = path.replace(filename, '')
    path_info = gen_path_info(path)
    breadcrumbs.append({'name': root_sha1_git[:7],
                        'url': reverse('browse-origin-directory',
                                       kwargs=url_args,
                                       query_params=query_params)})
    for pi in path_info:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = pi['path']
        breadcrumbs.append({'name': pi['name'],
                            'url': reverse('browse-origin-directory',
                                           kwargs=bc_url_args,
                                           query_params=query_params)})

    breadcrumbs.append({'name': filename,
                        'url': None})

    content_raw_url = reverse('browse-content-raw',
                              kwargs={'query_string': query_string},
                              query_params={'filename': filename})

    content_metadata = {
        'sha1 checksum': content_data['checksums']['sha1'],
        'sha1_git checksum': content_data['checksums']['sha1_git'],
        'sha256 checksum': content_data['checksums']['sha256'],
        'blake2s256 checksum': content_data['checksums']['blake2s256'],
        'mime type': content_data['mimetype'],
        'encoding': content_data['encoding'],
        'size': filesizeformat(content_data['length']),
        'language': content_data['language'],
        'licenses': content_data['licenses'],
        'origin id': origin_info['id'],
        'origin type': origin_info['type'],
        'origin url': origin_info['url'],
        'path': '/' + path,
        'filename': filename
    }

    return render(request, 'content.html',
                  {'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text_left': 'SWH object: Content',
                   'top_panel_text_right': 'Origin: %s' % origin_info['url'],
                   'swh_object_metadata': content_metadata,
                   'main_panel_visible': True,
                   'content': content_display_data['content_data'],
                   'mimetype': content_data['mimetype'],
                   'language': content_display_data['language'],
                   'breadcrumbs': breadcrumbs,
                   'branches': branches,
                   'branch': branch_name,
                   'top_right_link': content_raw_url,
                   'top_right_link_text': 'Raw File'})


def _gen_directory_link(url_args, revision, link_text):
    directory_url = reverse('browse-origin-directory',
                            kwargs=url_args,
                            query_params={'revision': revision})
    return gen_link(directory_url, link_text)


NB_LOG_ENTRIES = 20


@browse_route(r'origin/(?P<origin_id>[0-9]+)/log/',
              r'origin/(?P<origin_id>[0-9]+)/visit/(?P<visit_id>[0-9]+)/log/', # noqa
              r'origin/(?P<origin_id>[0-9]+)/ts/(?P<timestamp>.+)/log/',
              view_name='browse-origin-log')
def origin_log_browse(request, origin_id, visit_id=None, timestamp=None):
    """Django view that produces an HTML display of revisions history (aka
    the commit log) associated to a SWH origin.

    The url scheme that points to it is the following:

        * :http:get:`/browse/origin/(origin_id)/log/`
        * :http:get:`/browse/origin/(origin_id)/visit/(visit_id)/log/`
        * :http:get:`/browse/origin/(origin_id)/ts/(timestamp)/log/`

    Args:
        request: input django http request
        origin_id: id of a swh origin
        visit_id: optionnal visit id parameter
            (the last one will be used by default)
        timestamp: optionnal visit timestamp parameter
            (the last one will be used by default)
        revs_breadcrumb: query parameter used internally to store
            the navigation breadcrumbs (i.e. the list of descendant revisions
            visited so far).
        per_page: optionnal query parameter used to specify the number of
            log entries per page
        branch: optionnal query parameter that specifies the origin branch
            from which to retrieve the content
        revision: optional query parameter to specify the origin revision
            from which to retrieve the directory

    Returns:
        The HTML rendering of revisions history for a given SWH visit.

    """ # noqa
    try:

        if not visit_id and not timestamp:
            origin_visits = get_origin_visits(origin_id)
            if not origin_visits:
                raise NotFoundExc('No SWH visit associated to '
                                  'origin with id %s' % origin_id)
            return origin_log_browse(request, origin_id,
                                     origin_visits[-1]['visit'])

        branches, url_args = _get_origin_branches_and_url_args(origin_id,
                                                               visit_id,
                                                               timestamp)

        for b in branches:
            b['url'] = reverse('browse-origin-log',
                               kwargs=url_args,
                               query_params={'branch': b['name']})

        revision_id = request.GET.get('revision', None)
        revs_breadcrumb = request.GET.get('revs_breadcrumb', None)
        branch_name = request.GET.get('branch', 'HEAD')

        if revision_id:
            revision = service.lookup_revision(revision_id)
            branches.append({'name': revision_id,
                             'revision': revision_id,
                             'directory': revision['directory']})
            revision = revision_id
            branch_name = revision_id
        elif revs_breadcrumb:
            revs = revs_breadcrumb.split('/')
            revision = revs[-1]
        else:
            branch = _get_branch(branches, branch_name)
            if branch:
                branch_name = branch['name']
                revision = branch['revision']
            else:
                _raise_exception_if_branch_not_found(origin_id, visit_id,
                                                     timestamp, branch_name)

        per_page = int(request.GET.get('per_page', NB_LOG_ENTRIES))
        revision_log = service.lookup_revision_log(revision,
                                                   limit=per_page+1)
        revision_log = list(revision_log)

    except Exception as exc:
        return handle_view_exception(request, exc)

    revision_log_display_data = prepare_revision_log_for_display(
        revision_log, per_page, revs_breadcrumb, origin_context=True)

    prev_rev = revision_log_display_data['prev_rev']
    prev_revs_breadcrumb = revision_log_display_data['prev_revs_breadcrumb']
    prev_log_url = None
    if prev_rev:
        prev_log_url = \
            reverse('browse-origin-log',
                    kwargs=url_args,
                    query_params={'revs_breadcrumb': prev_revs_breadcrumb,
                                  'per_page': per_page,
                                  'branch': branch_name})

    next_rev = revision_log_display_data['next_rev']
    next_revs_breadcrumb = revision_log_display_data['next_revs_breadcrumb']
    next_log_url = None
    if next_rev:
        next_log_url = \
            reverse('browse-origin-log',
                    kwargs=url_args,
                    query_params={'revs_breadcrumb': next_revs_breadcrumb,
                                  'per_page': per_page,
                                  'branch': branch_name})

    revision_log_data = revision_log_display_data['revision_log_data']

    for i, log in enumerate(revision_log_data):
        log['directory'] = _gen_directory_link(url_args, revision_log[i]['id'],
                                               'Tree')

    return render(request, 'revision-log.html',
                  {'top_panel_visible': False,
                   'top_panel_collapsible': False,
                   'top_panel_text_left': 'SWH object: Revision history',
                   'top_panel_text_right': 'Sha1 git: ' + revision,
                   'swh_object_metadata': None,
                   'main_panel_visible': True,
                   'revision_log': revision_log_data,
                   'next_log_url': next_log_url,
                   'prev_log_url': prev_log_url,
                   'breadcrumbs': None,
                   'branches': branches,
                   'branch': branch_name,
                   'top_right_link': None,
                   'top_right_link_text': None,
                   'include_top_navigation': True})
