# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import dateutil

from django.shortcuts import render
from swh.web.common import service
from swh.web.common.utils import reverse
from swh.web.common.exc import NotFoundExc, handle_view_exception
from swh.web.browse.utils import (
    get_origin_visits, get_origin_visit_branches,
    gen_path_info, get_directory_entries, request_content,
    prepare_content_for_display
)


def origin_browse(request, origin_id=None, origin_type=None,
                  origin_url=None):
    """Django view that produces an HTML display of a swh origin identified
    by its id or its url.

    See :ref:`Origin browsing URI scheme <browse_origin>` for more details.

    Args:
        request: input django http request
        origin_id: a swh origin id
        origin_type: type of origin (git, svn, ...)
        origin_url: url of the origin (e.g. https://github.com/<user>/<repo>)

    Returns:
        The HMTL rendering for the metadata of the provided origin.
    """
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
        return handle_view_exception(exc)

    origin_info['last swh visit browse url'] = \
        reverse('browse-origin-directory',
                kwargs={'origin_id': origin_id})

    origin_visits_data = []
    for visit in origin_visits:
        visit_date = dateutil.parser.parse(visit['date'])
        visit['date'] = visit_date.strftime('%d %B %Y, %H:%M UTC')
        visit['browse_url'] = reverse('browse-origin-directory',
                                      kwargs={'origin_id': origin_id,
                                              'visit_id': visit['visit']})
        origin_visits_data.append(
            {'date': visit_date.timestamp()})

    return render(request, 'origin.html',
                  {'origin': origin_info,
                   'origin_visits_data': origin_visits_data,
                   'visits': origin_visits,
                   'browse_url_base': '/browse/revision/origin/%s/' %
                   origin_id})


def origin_directory_browse(request, origin_id, visit_id=None,
                            ts=None, path=None):
    """Django view for browsing the content of a swh directory associated
    to an origin for a given visit.

    See :ref:`Origin's directory browsing URI scheme <browse_origin_directory>`
    for more details.

    Args:
        request: input django http request
        origin_id: a swh origin id
        visit_id: optionnal visit id parameter
            (the last one will be used by default)
        ts: optionnal visit timestamp parameter
            (the last one will be used by default)
        path: optionnal path parameter used to navigate in directories
              reachable from the origin root one

    Returns:
        The HTML rendering for the content of the directory associated
        to the provided origin and visit.
    """ # noqa
    try:

        if not visit_id and not ts:
            origin_visits = get_origin_visits(origin_id)
            return origin_directory_browse(request, origin_id,
                                           origin_visits[-1]['visit'],
                                           path=path)

        if not visit_id and ts:
            branches = get_origin_visit_branches(origin_id, visit_ts=ts)
            url_args = {'origin_id': origin_id,
                        'ts': ts}
        else:
            branches = get_origin_visit_branches(origin_id, visit_id)
            url_args = {'origin_id': origin_id,
                        'visit_id': visit_id}

        branch = request.GET.get('branch', 'master')
        filtered_branches = [b for b in branches if branch in b['name']]

        if len(filtered_branches) > 0:
            root_sha1_git = filtered_branches[0]['directory']
            branch = filtered_branches[0]['name']
        else:
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

        sha1_git = root_sha1_git
        if path:
            dir_info = service.lookup_directory_with_path(root_sha1_git, path)
            sha1_git = dir_info['target']

        dirs, files = get_directory_entries(sha1_git)

    except Exception as exc:
        return handle_view_exception(exc)

    for b in branches:
        branch_url_args = dict(url_args)
        if path:
            b['path'] = path
            branch_url_args['path'] = path
        b['url'] = reverse('browse-origin-directory',
                           kwargs=branch_url_args,
                           query_params={'branch': b['name']})

    path_info = gen_path_info(path)

    breadcrumbs = []
    breadcrumbs.append({'name': root_sha1_git[:7],
                        'url': reverse('browse-origin-directory',
                                       kwargs=url_args,
                                       query_params={'branch': branch})})
    for pi in path_info:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = pi['path']
        breadcrumbs.append({'name': pi['name'],
                            'url': reverse('browse-origin-directory',
                                           kwargs=bc_url_args,
                                           query_params={'branch': branch})})

    path = '' if path is None else (path + '/')

    for d in dirs:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = path + d['name']
        d['url'] = reverse('browse-origin-directory',
                           kwargs=bc_url_args,
                           query_params={'branch': branch})

    for f in files:
        bc_url_args = dict(url_args)
        bc_url_args['path'] = path + f['name']
        f['url'] = reverse('browse-origin-content',
                           kwargs=bc_url_args,
                           query_params={'branch': branch})

    return render(request, 'directory.html',
                  {'dir_sha1_git': sha1_git,
                   'dirs': dirs,
                   'files': files,
                   'breadcrumbs': breadcrumbs,
                   'branches': branches,
                   'branch': branch})


def origin_content_display(request, origin_id, path, visit_id=None, ts=None):
    """Django view that produces an HTML display of a swh content
    associated to an origin for a given visit.

    See :ref:`Origin content browsing URI scheme <browse_origin_content>` 
    for more details.

    Args:
        request: input django http request
        origin_id: id of a swh origin
        path: path of the content relative to the origin root directory
        visit_id: optionnal visit id parameter
            (the last one will be used by default)
        ts: optionnal visit timestamp parameter
            (the last one will be used by default)
        branch: optionnal query parameter that specifies the origin branch
            from which to retrieve the content

    Returns:
        The HTML rendering of the requested content associated to
        the provided origin and visit.

    """ # noqa
    try:

        if not visit_id and not ts:
            origin_visits = get_origin_visits(origin_id)
            return origin_content_display(request, origin_id, path,
                                          origin_visits[-1]['visit'])

        if not visit_id and ts:
            branches = get_origin_visit_branches(origin_id, visit_ts=ts)
            kwargs = {'origin_id': origin_id,
                      'ts': ts}
        else:
            branches = get_origin_visit_branches(origin_id, visit_id)
            kwargs = {'origin_id': origin_id,
                      'visit_id': visit_id}

        for b in branches:
            bc_kwargs = dict(kwargs)
            bc_kwargs['path'] = path
            b['url'] = reverse('browse-origin-content',
                               kwargs=bc_kwargs,
                               query_params={'branch': b['name']})

        branch = request.GET.get('branch', 'master')
        filtered_branches = [b for b in branches if branch in b['name']]

        if len(filtered_branches) > 0:
            root_sha1_git = filtered_branches[0]['directory']
            branch = filtered_branches[0]['name']
        else:
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

        content_info = service.lookup_directory_with_path(root_sha1_git, path)
        sha1_git = content_info['target']
        query_string = 'sha1_git:' + sha1_git
        content_data, mime_type = request_content(query_string)

    except Exception as exc:
        return handle_view_exception(exc)

    content_display_data = prepare_content_for_display(content_data,
                                                       mime_type, path)

    filename = None
    path_info = None

    breadcrumbs = []

    split_path = path.split('/')
    filename = split_path[-1]
    path = path.replace(filename, '')
    path_info = gen_path_info(path)
    breadcrumbs.append({'name': root_sha1_git[:7],
                        'url': reverse('browse-origin-directory',
                                       kwargs=kwargs,
                                       query_params={'branch': branch})})
    for pi in path_info:
        bc_kwargs = dict(kwargs)
        bc_kwargs['path'] = pi['path']
        breadcrumbs.append({'name': pi['name'],
                            'url': reverse('browse-origin-directory',
                                           kwargs=bc_kwargs,
                                           query_params={'branch': branch})})

    breadcrumbs.append({'name': filename,
                        'url': None})

    content_raw_url = reverse('browse-content-raw',
                              kwargs={'query_string': query_string},
                              query_params={'filename': filename})

    return render(request, 'content.html',
                  {'content_hash_algo': 'sha1_git',
                   'content_checksum': sha1_git,
                   'content': content_display_data['content_data'],
                   'content_raw_url': content_raw_url,
                   'mime_type': mime_type,
                   'language': content_display_data['language'],
                   'breadcrumbs': breadcrumbs,
                   'branches': branches,
                   'branch': branch})
