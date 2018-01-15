# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import dateutil
import json

from distutils.util import strtobool

from django.http import HttpResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe
from django.template.defaultfilters import filesizeformat

from swh.web.common import service
from swh.web.common.utils import (
    gen_path_info, reverse, format_utc_iso_date
)
from swh.web.common.exc import NotFoundExc, handle_view_exception
from swh.web.browse.utils import (
    get_origin_visits, get_origin_visit, get_origin_visit_branches,
    get_directory_entries, request_content,
    prepare_content_for_display, gen_link,
    prepare_revision_log_for_display, gen_origin_link
)
from swh.web.browse.browseurls import browse_route


def _get_origin_branches_and_url_args(origin_info, timestamp, visit_id):
    branches = get_origin_visit_branches(origin_info, timestamp, visit_id)
    url_args = {'origin_type': origin_info['type'],
                'origin_url': origin_info['url']}
    if timestamp:
        url_args['timestamp'] = format_utc_iso_date(timestamp,
                                                    '%Y-%m-%dT%H:%M:%S')

    return branches, url_args


def _raise_exception_if_branch_not_found(origin_info, timestamp,
                                         branch, branches, visit_id=None):
    if visit_id:
        if len(branches) == 0:
            raise NotFoundExc('Origin with type %s and url %s is empty'
                              ' for visit with id %s! No existing branches'
                              ' were found!' % (origin_info['type'],
                                                origin_info['url'], visit_id))
        else:
            raise NotFoundExc('Branch %s associated to visit with'
                              ' id %s for origin with type %s and url %s'
                              ' not found!' % (branch, visit_id,
                                               origin_info['type'],
                                               origin_info['url']))
    else:
        if len(branches) == 0:
            raise NotFoundExc('Origin with type %s and url %s is empty'
                              ' for visit with timestamp %s! No existing'
                              ' branches were found!' % (origin_info['type'],
                                                         origin_info['url'],
                                                         timestamp))
        else:
            raise NotFoundExc('Branch %s associated to visit with'
                              ' timestamp %s for origin with type %s'
                              ' and url %s not found!' % (branch, timestamp,
                                                          origin_info['type'],
                                                          origin_info['url']))


def _get_branch(branches, branch_name):
    """
    Utility function to get a specific branch from an origin branches list.
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


@browse_route(r'origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/directory/', # noqa
              r'origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/directory/(?P<path>.+)/', # noqa
              r'origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/directory/', # noqa
              r'origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/directory/(?P<path>.+)/', # noqa
              view_name='browse-origin-directory')
def origin_directory_browse(request, origin_type, origin_url,
                            timestamp=None, path=None):
    """Django view for browsing the content of a swh directory associated
    to an origin for a given visit.

    The url scheme that points to it is the following:

        * :http:get:`/browse/origin/(origin_type)/url/(origin_url)/directory/[(path)/]`
        * :http:get:`/browse/origin/(origin_type)/url/(origin_type)/visit/(timestamp)/directory/[(path)/]`

    Args:
        request: input django http request
        origin_type: the type of swh origin (git, svn, hg, ...)
        origin_url: the url of the swh origin
        timestamp: optional swh visit timestamp parameter
            (the last one will be used by default)
        path: optional path parameter used to navigate in directories
              reachable from the origin root one
        branch: optional query parameter that specifies the origin branch
            from which to retrieve the directory
        revision: optional query parameter to specify the origin revision
            from which to retrieve the directory

    Returns:
        The HTML rendering for the content of the directory associated
        to the provided origin and visit.
    """ # noqa
    try:

        origin_info = service.lookup_origin({
            'type': origin_type,
            'url': origin_url
        })

        visit_id = request.GET.get('visit_id', None)

        visit_info = get_origin_visit(origin_info, timestamp, visit_id)

        if timestamp:
            timestamp = visit_info['date']

        branches, url_args = \
            _get_origin_branches_and_url_args(origin_info, timestamp, visit_id)

        for b in branches:
            branch_url_args = dict(url_args)
            if path:
                b['path'] = path
                branch_url_args['path'] = path
            b['url'] = reverse('browse-origin-directory',
                               kwargs=branch_url_args,
                               query_params={'branch': b['name'],
                                             'visit_id': visit_id})

        query_params = {'visit_id': visit_id}

        revision_id = request.GET.get('revision', None)

        if revision_id:
            revision = service.lookup_revision(revision_id)
            root_sha1_git = revision['directory']
            branches.append({'name': revision_id,
                             'revision': revision_id,
                             'directory': root_sha1_git,
                             'url': None})
            branch_name = revision_id
            query_params['revision'] = revision_id
        else:
            branch_name = request.GET.get('branch', 'HEAD')
            branch = _get_branch(branches, branch_name)
            if branch:
                branch_name = branch['name']
                root_sha1_git = branch['directory']
                query_params['branch'] = branch_name
                revision_id = branch['revision']
            else:
                _raise_exception_if_branch_not_found(origin_info, timestamp,
                                                     branch_name, branches,
                                                     visit_id)

        sha1_git = root_sha1_git
        if path:
            dir_info = service.lookup_directory_with_path(root_sha1_git, path)
            sha1_git = dir_info['target']

        dirs, files = get_directory_entries(sha1_git)

    except Exception as exc:
        return handle_view_exception(request, exc)

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

    readme_name = None
    readme_url = None

    for f in files:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = path + f['name']
        f['url'] = reverse('browse-origin-content',
                           kwargs=bc_url_args,
                           query_params=query_params)
        sum_file_sizes += f['length']
        f['length'] = filesizeformat(f['length'])
        if f['name'].lower().startswith('readme'):
            readme_name = f['name']
            readme_sha1 = f['checksums']['sha1']
            readme_url = reverse('browse-content-raw',
                                 kwargs={'query_string': readme_sha1})

    history_url = reverse('browse-origin-log',
                          kwargs=url_args,
                          query_params=query_params)

    sum_file_sizes = filesizeformat(sum_file_sizes)

    browse_dir_url = reverse('browse-directory',
                             kwargs={'sha1_git': sha1_git})

    browse_rev_url = reverse('browse-revision',
                             kwargs={'sha1_git': revision_id},
                             query_params={'origin_type': origin_info['type'],
                                           'origin_url': origin_info['url']})

    dir_metadata = {'id': sha1_git,
                    'browse directory url': browse_dir_url,
                    'number of regular files': len(files),
                    'number of subdirectories': len(dirs),
                    'sum of regular file sizes': sum_file_sizes,
                    'origin id': origin_info['id'],
                    'origin type': origin_info['type'],
                    'origin url': origin_info['url'],
                    'origin visit date': format_utc_iso_date(visit_info['date']), # noqa
                    'origin visit id': visit_info['visit'],
                    'path': '/' + path,
                    'revision id': revision_id,
                    'browse revision url': browse_rev_url}

    return render(request, 'directory.html',
                  {'empty_browse': False,
                   'heading': 'Directory information',
                   'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text_left': 'SWH object: Directory',
                   'top_panel_text_right': gen_origin_link(origin_info),
                   'swh_object_metadata': dir_metadata,
                   'main_panel_visible': True,
                   'dirs': dirs,
                   'files': files,
                   'breadcrumbs': breadcrumbs,
                   'branches': branches,
                   'branch': branch_name,
                   'top_right_link': history_url,
                   'top_right_link_text': mark_safe(
                       '<i class="fa fa-history fa-fw" aria-hidden="true"></i>'
                       'History'
                    ),
                   'readme_name': readme_name,
                   'readme_url': readme_url})


@browse_route(r'origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/content/(?P<path>.+)/', # noqa
              r'origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/content/(?P<path>.+)/', # noqa
              view_name='browse-origin-content')
def origin_content_display(request, origin_type, origin_url, path,
                           timestamp=None):
    """Django view that produces an HTML display of a swh content
    associated to an origin for a given visit.

    The url scheme that points to it is the following:

        * :http:get:`/browse/origin/(origin_type)/url/(origin_url)/content/(path)/`
        * :http:get:`/browse/origin/(origin_type)/url/(origin_url)/visit/(timestamp)/content/(path)/`

    Args:
        request: input django http request
        origin_type: the type of swh origin (git, svn, hg, ...)
        origin_url: the url of the swh origin
        path: path of the content relative to the origin root directory
        timestamp: optional swh visit timestamp parameter
            (the last one will be used by default)
        branch: optional query parameter that specifies the origin branch
            from which to retrieve the content
        revision: optional query parameter to specify the origin revision
            from which to retrieve the content

    Returns:
        The HTML rendering of the requested content associated to
        the provided origin and visit.

    """ # noqa
    try:

        origin_info = service.lookup_origin({
            'type': origin_type,
            'url': origin_url
        })

        visit_id = request.GET.get('visit_id', None)

        visit_info = get_origin_visit(origin_info, timestamp, visit_id)
        if timestamp:
            timestamp = visit_info['date']

        branches, url_args = \
            _get_origin_branches_and_url_args(origin_info, timestamp, visit_id)

        for b in branches:
            bc_url_args = dict(url_args)
            bc_url_args['path'] = path
            b['url'] = reverse('browse-origin-content',
                               kwargs=bc_url_args,
                               query_params={'branch': b['name'],
                                             'visit_id': visit_id})

        query_params = {'visit_id': visit_id}

        revision_id = request.GET.get('revision', None)

        if revision_id:
            revision = service.lookup_revision(revision_id)
            root_sha1_git = revision['directory']
            branches.append({'name': revision_id,
                             'revision': revision_id,
                             'directory': root_sha1_git,
                             'url': None})
            branch_name = revision_id
            query_params['revision'] = revision_id
        else:
            branch_name = request.GET.get('branch', 'HEAD')
            branch = _get_branch(branches, branch_name)
            if branch:
                branch_name = branch['name']
                root_sha1_git = branch['directory']
                query_params['branch'] = branch_name
                revision_id = branch['revision']
            else:
                _raise_exception_if_branch_not_found(origin_info, timestamp,
                                                     branch_name, branches,
                                                     visit_id)

        content_info = service.lookup_directory_with_path(root_sha1_git, path)
        sha1_git = content_info['target']
        query_string = 'sha1_git:' + sha1_git
        content_data = request_content(query_string)

    except Exception as exc:
        return handle_view_exception(request, exc)

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

    browse_content_url = reverse('browse-content',
                                 kwargs={'query_string': query_string})

    content_raw_url = reverse('browse-content-raw',
                              kwargs={'query_string': query_string},
                              query_params={'filename': filename})

    browse_rev_url = reverse('browse-revision',
                             kwargs={'sha1_git': revision_id},
                             query_params={'origin_type': origin_info['type'],
                                           'origin_url': origin_info['url']})

    content_metadata = {
        'browse content url': browse_content_url,
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
        'origin visit date': format_utc_iso_date(visit_info['date']),
        'origin visit id': visit_info['visit'],
        'path': '/' + path,
        'filename': filename,
        'revision id': revision_id,
        'browse revision url': browse_rev_url
    }

    return render(request, 'content.html',
                  {'empty_browse': False,
                   'heading': 'Content information',
                   'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text_left': 'SWH object: Content',
                   'top_panel_text_right': gen_origin_link(origin_info),
                   'swh_object_metadata': content_metadata,
                   'main_panel_visible': True,
                   'content': content_display_data['content_data'],
                   'mimetype': content_data['mimetype'],
                   'language': content_display_data['language'],
                   'breadcrumbs': breadcrumbs,
                   'branches': branches,
                   'branch': branch_name,
                   'top_right_link': content_raw_url,
                   'top_right_link_text': mark_safe(
                       '<i class="fa fa-file-text fa-fw" aria-hidden="true">'
                       '</i>Raw File')
                   })


def _gen_directory_link(url_args, query_params, link_text):
    directory_url = reverse('browse-origin-directory',
                            kwargs=url_args,
                            query_params=query_params)
    return gen_link(directory_url, link_text)


NB_LOG_ENTRIES = 20


@browse_route(r'origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/log/', # noqa
              r'origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/log/',
              view_name='browse-origin-log')
def origin_log_browse(request, origin_type, origin_url, timestamp=None):
    """Django view that produces an HTML display of revisions history (aka
    the commit log) associated to a SWH origin.

    The url scheme that points to it is the following:

        * :http:get:`/browse/origin/(origin_type)/url/(origin_url)/log/`
        * :http:get:`/browse/origin/(origin_type)/url/(origin_url)/visit/(timestamp)/log/`

    Args:
        request: input django http request
        origin_type: the type of swh origin (git, svn, hg, ...)
        origin_url: the url of the swh origin
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

        origin_info = service.lookup_origin({
            'type': origin_type,
            'url': origin_url
        })

        visit_id = request.GET.get('visit_id', None)

        visit_info = get_origin_visit(origin_info, timestamp, visit_id)
        if timestamp:
            timestamp = visit_info['date']

        branches, url_args = \
            _get_origin_branches_and_url_args(origin_info, timestamp, visit_id)

        for b in branches:
            b['url'] = reverse('browse-origin-log',
                               kwargs=url_args,
                               query_params={'branch': b['name'],
                                             'visit_id': visit_id})

        revision_id = request.GET.get('revision', None)
        revs_breadcrumb = request.GET.get('revs_breadcrumb', None)
        branch_name = request.GET.get('branch', 'HEAD')

        if revision_id:
            revision = service.lookup_revision(revision_id)
            branches.append({'name': revision_id,
                             'revision': revision_id,
                             'directory': revision['directory'],
                             'url': None})
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
                _raise_exception_if_branch_not_found(origin_info, timestamp,
                                                     branch_name, branches,
                                                     visit_id)

        per_page = int(request.GET.get('per_page', NB_LOG_ENTRIES))
        revision_log = service.lookup_revision_log(revision,
                                                   limit=per_page+1)
        revision_log = list(revision_log)

    except Exception as exc:
        return handle_view_exception(request, exc)

    revision_log_display_data = prepare_revision_log_for_display(
        revision_log, per_page, revs_breadcrumb, origin_context=True,
        origin_info=origin_info)

    prev_rev = revision_log_display_data['prev_rev']
    prev_revs_breadcrumb = revision_log_display_data['prev_revs_breadcrumb']
    prev_log_url = None
    if prev_rev:
        prev_log_url = \
            reverse('browse-origin-log',
                    kwargs=url_args,
                    query_params={'revs_breadcrumb': prev_revs_breadcrumb,
                                  'per_page': per_page,
                                  'branch': branch_name,
                                  'visit_id': visit_id})

    next_rev = revision_log_display_data['next_rev']
    next_revs_breadcrumb = revision_log_display_data['next_revs_breadcrumb']
    next_log_url = None
    if next_rev:
        next_log_url = \
            reverse('browse-origin-log',
                    kwargs=url_args,
                    query_params={'revs_breadcrumb': next_revs_breadcrumb,
                                  'per_page': per_page,
                                  'branch': branch_name,
                                  'visit_id': visit_id})

    revision_log_data = revision_log_display_data['revision_log_data']

    for i, log in enumerate(revision_log_data):
        query_params = {
            'revision': revision_log[i]['id'],
            'visit_id': visit_id
        }
        log['directory'] = _gen_directory_link(url_args, query_params, 'Tree')

    browse_log_url = reverse('browse-revision-log',
                             kwargs={'sha1_git': revision})

    revision_metadata = {
        'browse revision history url': browse_log_url,
        'origin id': origin_info['id'],
        'origin type': origin_info['type'],
        'origin url': origin_info['url'],
        'origin visit date': format_utc_iso_date(visit_info['date']),
        'origin visit id': visit_info['visit']
    }

    return render(request, 'revision-log.html',
                  {'empty_browse': False,
                   'heading': 'Revision history information',
                   'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text_left': 'SWH object: Revision history',
                   'top_panel_text_right': gen_origin_link(origin_info),
                   'swh_object_metadata': revision_metadata,
                   'main_panel_visible': True,
                   'revision_log': revision_log_data,
                   'next_log_url': next_log_url,
                   'prev_log_url': prev_log_url,
                   'breadcrumbs': None,
                   'branches': branches,
                   'branch': branch_name,
                   'top_right_link': None,
                   'top_right_link_text': None,
                   'include_top_navigation': True,
                   'no_origin_context': False})


@browse_route(r'origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/',
              view_name='browse-origin')
def origin_browse(request, origin_type=None, origin_url=None):
    """Django view that produces an HTML display of a swh origin identified
    by its id or its url.

    The url scheme that points to it is :http:get:`/browse/origin/(origin_type)/url/(origin_url)/`.

    Args:
        request: input django http request
        origin_type: type of origin (git, svn, ...)
        origin_url: url of the origin (e.g. https://github.com/<user>/<repo>)

    Returns:
        The HMTL rendering for the metadata of the provided origin.
    """ # noqa
    try:
        origin_info = service.lookup_origin({
            'type': origin_type,
            'url': origin_url
        })
        origin_visits = get_origin_visits(origin_info)
        origin_visits.reverse()
    except Exception as exc:
        return handle_view_exception(request, exc)

    origin_info['last swh visit browse url'] = \
        reverse('browse-origin-directory',
                kwargs={'origin_type': origin_type,
                        'origin_url': origin_url})

    origin_visits_data = []
    visits_splitted = []
    visits_by_year = {}
    for i, visit in enumerate(origin_visits):
        visit_date = dateutil.parser.parse(visit['date'])
        visit_year = str(visit_date.year)
        url_date = format_utc_iso_date(visit['date'], '%Y-%m-%dT%H:%M:%S')
        visit['fmt_date'] = format_utc_iso_date(visit['date'])
        query_params = {}
        if i < len(origin_visits) - 1:
            if visit['date'] == origin_visits[i+1]['date']:
                query_params = {'visit_id': visit['visit']}
        if i > 0:
            if visit['date'] == origin_visits[i-1]['date']:
                query_params = {'visit_id': visit['visit']}

        visit['browse_url'] = reverse('browse-origin-directory',
                                      kwargs={'origin_type': origin_type,
                                              'origin_url': origin_url,
                                              'timestamp': url_date},
                                      query_params=query_params)
        origin_visits_data.insert(0, {'date': visit_date.timestamp()})
        if visit_year not in visits_by_year:
            # display 3 years by row in visits list view
            if len(visits_by_year) == 3:
                visits_splitted.insert(0, visits_by_year)
                visits_by_year = {}
            visits_by_year[visit_year] = []
        visits_by_year[visit_year].append(visit)

    if len(visits_by_year) > 0:
        visits_splitted.insert(0, visits_by_year)

    return render(request, 'origin.html',
                  {'empty_browse': False,
                   'heading': 'Origin information',
                   'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text_left': 'SWH object: Origin',
                   'top_panel_text_right': 'Url: ' + origin_info['url'],
                   'swh_object_metadata': origin_info,
                   'main_panel_visible': True,
                   'origin_visits_data': origin_visits_data,
                   'visits_splitted': visits_splitted,
                   'browse_url_base': '/browse/origin/%s/url/%s/' %
                   (origin_type, origin_url)})


@browse_route(r'origin/search/(?P<url_pattern>.+)/',
              view_name='browse-origin-search')
def origin_search(request, url_pattern):
    """Search for origins whose urls contain a provided string pattern
    or match a provided regular expression.
    The search is performed in a case insensitive way.

    """

    offset = int(request.GET.get('offset', '0'))
    limit = int(request.GET.get('limit', '50'))
    regexp = request.GET.get('regexp', 'false')

    results = service.search_origin(url_pattern, offset, limit,
                                    bool(strtobool(regexp)))

    results = json.dumps(list(results), sort_keys=True, indent=4,
                         separators=(',', ': '))

    return HttpResponse(results, content_type='application/json')
