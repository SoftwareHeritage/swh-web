# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.shortcuts import render

from swh.web.common import service
from swh.web.common.utils import reverse
from swh.web.common.exc import NotFoundExc, handle_view_exception
from swh.web.browse.utils import (
    gen_path_info, get_origin_visit_branches,
    get_origin_visits
)


def _get_directory_entries(sha1_git):
    entries = list(service.lookup_directory(sha1_git))
    entries = sorted(entries, key=lambda e: e['name'])
    dirs = [e for e in entries if e['type'] == 'dir']
    files = [e for e in entries if e['type'] == 'file']
    return dirs, files


def directory_browse(request, sha1_git, path=None):
    """Django view for browsing the content of a swh directory identified
    by its sha1_git value.

    The url scheme that points to that view is the following:

        * /browse/directory/<sha1_git>/

        * /browse/directory/<sha1_git>/<path>/

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the provided root directory to
    directories reachable from it in a recursive way.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    Args:
        request: input django http request
        sha1_git: swh sha1_git identifer of the directory to browse
        path: optionnal path parameter used to navigate in directories
              reachable from the provided root one

    Returns:
        The HTML rendering for the content of the provided directory.
    """
    root_sha1_git = sha1_git
    try:
        if path:
            dir_info = service.lookup_directory_with_path(sha1_git, path)
            sha1_git = dir_info['target']

        dirs, files = _get_directory_entries(sha1_git)
    except Exception as exc:
        return handle_view_exception(exc)

    path_info = gen_path_info(path)

    breadcrumbs = []
    breadcrumbs.append({'name': root_sha1_git[:7],
                        'url': reverse('browse-directory',
                                       kwargs={'sha1_git': root_sha1_git})})
    for pi in path_info:
        breadcrumbs.append({'name': pi['name'],
                            'url': reverse('browse-directory',
                                           kwargs={'sha1_git': root_sha1_git,
                                                   'path': pi['path']})})

    path = '' if path is None else (path + '/')

    for d in dirs:
        d['url'] = reverse('browse-directory',
                           kwargs={'sha1_git': root_sha1_git,
                                   'path': path + d['name']})

    for f in files:
        f['url'] = reverse('browse-content',
                           kwargs={'sha1_git': f['target']},
                           query_params={'path': root_sha1_git + '/' +
                                         path + f['name']})

    return render(request, 'directory.html',
                  {'dir_sha1_git': sha1_git,
                   'dirs': dirs,
                   'files': files,
                   'breadcrumbs': breadcrumbs,
                   'branches': None,
                   'branch': None})


def origin_directory_browse(request, origin_id, visit_id=None, ts=None,
                            path=None):
    """Django view for browsing the content of a swh directory associated
    to an origin for a given visit.

    The url scheme that points to that view is the following:

        * /browse/origin/<origin_id>/directory/[?branch=<branch_name>]

        * /browse/origin/<origin_id>/directory/<path>/[?branch=<branch_name>]

        * /browse/origin/<origin_id>/visit/<visit_id>/directory/[?branch=<branch_name>]

        * /browse/origin/<origin_id>/visit/<visit_id>/directory/<path>/[?branch=<branch_name>]

        * /browse/origin/<origin_id>/ts/<ts>/directory/[?branch=<branch_name>]

        * /browse/origin/<origin_id>/ts/<ts>/directory/<path>/[?branch=<branch_name>]

    For the first two urls, the displayed directory will correspond to
    the one associated to the latest swh visit.

    The content of the directory is first sorted in lexicographical order
    and the sub-directories are displayed before the regular files.

    The view enables to navigate from the origin root directory to
    directories reachable from it in a recursive way.
    A breadcrumb located in the top part of the view allows
    to keep track of the paths navigated so far.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the directory 
    content can also be specified by using the branch query parameter.

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

        dirs, files = _get_directory_entries(sha1_git)

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
