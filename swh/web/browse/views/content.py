# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import base64

from django.http import HttpResponse

from django.shortcuts import render

from swh.web.common import service, highlightjs
from swh.web.common.utils import reverse
from swh.web.common.exc import NotFoundExc, handle_view_exception
from swh.web.browse.utils import (
    gen_path_info, get_mimetype_for_content,
    get_origin_visit_branches, get_origin_visits
)


_browsers_supported_image_mimes = set(['image/gif', 'image/png',
                                       'image/jpeg', 'image/bmp',
                                       'image/webp'])


def _request_content(sha1_git):
    query_string = 'sha1_git:' + sha1_git
    content_raw = service.lookup_content_raw(query_string)
    mime_type = service.lookup_content_filetype(query_string)
    if mime_type:
        mime_type = mime_type['mimetype']
    return content_raw['data'], mime_type


def _prepare_content_for_display(content_data, mime_type, path):
    if not mime_type:
        mime_type = get_mimetype_for_content(content_data)

    language = highlightjs.get_hljs_language_from_filename(path)

    if not language:
        language = highlightjs.get_hljs_language_from_mime_type(mime_type)

    if not language:
        language = 'nohighlight-swh'
    elif mime_type.startswith('application/'):
        mime_type = mime_type.replace('application/', 'text/')

    if mime_type.startswith('image/'):
        if mime_type in _browsers_supported_image_mimes:
            content_data = base64.b64encode(content_data)
        else:
            content_data = None

    return {'content_data': content_data,
            'language': language,
            'mime_type': mime_type}


def content_display(request, sha1_git):
    """Django view that produces an HTML display of a swh content identified
    by its sha1_git value.

    The url that points to it is /browse/content/<sha1_git>/[?path=<path>]

    In the context of a navigation coming from a directory view,
    the path query parameter will be used and filled with the path
    of the file relative to a root directory.

    If the content to display is textual, it will be highlighted client-side
    if possible using highlight.js. In order for that operation to be
    performed, a programming language must first be associated to the content.
    The following procedure is used in order to find the language:

        1) First try to find a language from the content's filename
           (provided as query parameter when navigating from a directory view).

        2) If no language has been found from the filename,
           try to find one from the content's mime type.
           The mime type is retrieved from the content metadata stored
           in the swh archive or is computed server-side using Python
           magic module.

    When that view is called in the context of a navigation coming from
    a directory view, a breadcrumb will be displayed on top of the rendered
    content in order to easily navigate up to the associated root directory.

    Args:
        request: input django http request
        sha1_git: swh sha1_git identifier of the content to display

    Returns:
        The HTML rendering of the requested content.

    """

    try:
        content_data, mime_type = _request_content(sha1_git)
    except Exception as exc:
        return handle_view_exception(exc)

    path = request.GET.get('path', None)

    content_display_data = _prepare_content_for_display(content_data,
                                                        mime_type, path)

    root_dir = None
    filename = None
    path_info = None

    breadcrumbs = []

    if path:
        split_path = path.split('/')
        root_dir = split_path[0]
        filename = split_path[-1]
        path = path.replace(root_dir + '/', '')
        path = path.replace(filename, '')
        path_info = gen_path_info(path)
        breadcrumbs.append({'name': root_dir[:7],
                            'url': reverse('browse-directory',
                                           kwargs={'sha1_git': root_dir})})
        for pi in path_info:
            breadcrumbs.append({'name': pi['name'],
                                'url': reverse('browse-directory',
                                               kwargs={'sha1_git': root_dir,
                                                       'path': pi['path']})})
        breadcrumbs.append({'name': filename,
                            'url': None})

    content_raw_url = reverse('browse-content-raw',
                              kwargs={'sha1_git': sha1_git},
                              query_params={'filename': filename})

    return render(request, 'content.html',
                  {'content_sha1_git': sha1_git,
                   'content': content_display_data['content_data'],
                   'content_raw_url': content_raw_url,
                   'mime_type': content_display_data['mime_type'],
                   'language': content_display_data['language'],
                   'breadcrumbs': breadcrumbs,
                   'branches': None,
                   'branch': None})


def content_raw(request, sha1_git):
    """Django view that produces a raw display of a swh content identified
    by its sha1_git value.

    The url that points to it is /browse/content/<sha1_git>/raw/[?filename=<filename>]

    The behaviour of that view depends on the mime type of the requested content.
    If the mime type is from the text family, the view will return a response whose
    content type is 'text/plain' that will be rendered by the browser. Otherwise,
    the view will return a response whose content type is 'application/octet-stream'
    and the browser will then offer to download the file.

    In the context of a navigation coming from a directory view, the filename query
    parameter will be used in order to provide the real name of the file when
    one wants to save it locally.

    Args:
        request: input django http request
        sha1_git: swh sha1_git identifier of the requested content

    Returns:
        The raw bytes of the content.


    """ # noqa

    try:
        content_data, mime_type = _request_content(sha1_git)
    except Exception as exc:
        return handle_view_exception(exc)

    filename = request.GET.get('filename', None)
    if not filename:
        filename = sha1_git

    mime_type = get_mimetype_for_content(content_data)
    if mime_type.startswith('text/'):
        response = HttpResponse(content_data, content_type="text/plain")
        response['Content-disposition'] = 'filename=%s' % filename
    else:
        response = HttpResponse(content_data,
                                content_type='application/octet-stream')
        response['Content-disposition'] = 'attachment; filename=%s' % filename
    return response


def origin_content_display(request, origin_id, path, visit_id=None, ts=None):
    """Django view that produces an HTML display of a swh content
    associated to an origin for a given visit.

    The url scheme that points to it is:

        * /browse/origin/<origin_id>/content/<path>/[?branch=<branch_name>]

        * /browse/origin/<origin_id>/visit/<visit_id>/content/<path>/[?branch=<branch_name>]

        * /browse/origin/<origin_id>/ts/<ts>/content/<path>/[?branch=<branch_name>]

    If the content to display is textual, it will be highlighted client-side
    if possible using highlight.js. In order for that operation to be
    performed, a programming language must first be associated to the content.
    The following procedure is used in order to find the language:

        1) First try to find a language from the content's filename
           (provided as query parameter when navigating from a directory view).

        2) If no language has been found from the filename,
           try to find one from the content's mime type.
           The mime type is retrieved from the content metadata stored
           in the swh archive or is computed server-side using Python
           magic module.

    The view displays a breadcrumb on top of the rendered
    content in order to easily navigate up to the origin root directory.

    The view also enables to easily switch between the origin branches
    through a dropdown menu.

    The origin branch (default to master) from which to retrieve the content
    can also be specified by using the branch query parameter.

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
        content_data, mime_type = _request_content(sha1_git)

    except Exception as exc:
        return handle_view_exception(exc)

    content_display_data = _prepare_content_for_display(content_data,
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
                              kwargs={'sha1_git': sha1_git},
                              query_params={'filename': filename})

    return render(request, 'content.html',
                  {'content_sha1_git': sha1_git,
                   'content': content_display_data['content_data'],
                   'content_raw_url': content_raw_url,
                   'mime_type': content_display_data['mime_type'],
                   'language': content_display_data['language'],
                   'breadcrumbs': breadcrumbs,
                   'branches': branches,
                   'branch': branch})
