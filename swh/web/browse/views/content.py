# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import base64

from django.http import HttpResponse

from django.shortcuts import render

from swh.model.hashutil import hash_to_hex

from swh.web.common import service, highlightjs, query
from swh.web.common.utils import reverse
from swh.web.common.exc import NotFoundExc, handle_view_exception
from swh.web.browse.utils import (
    gen_path_info, get_mimetype_for_content,
    get_origin_visit_branches, get_origin_visits
)


_browsers_supported_image_mimes = set(['image/gif', 'image/png',
                                       'image/jpeg', 'image/bmp',
                                       'image/webp'])


def _request_content(query_string):
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


def content_display(request, query_string):
    """Django view that produces an HTML display of a SWH content identified
    by its hash value.

    See :ref:`Content browsing URI scheme <browse_content>` for more details.

    Args:
        request: input django http request
        query_string: a string of the form "[ALGO_HASH:]HASH" where
            optional ALGO_HASH can be either *sha1*, *sha1_git*, *sha256*,
            or *blake2s256* (default to *sha1*) and HASH the hexadecimal
            representation of the hash value

    Returns:
        The HTML rendering of the requested content.

    """

    try:
        algo, checksum = query.parse_hash(query_string)
        checksum = hash_to_hex(checksum)
        content_data, mime_type = _request_content(query_string)
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

    query_params = None
    if filename:
        query_params = {'filename': filename}

    content_raw_url = reverse('browse-content-raw',
                              kwargs={'query_string': query_string},
                              query_params=query_params)

    return render(request, 'content.html',
                  {'content_hash_algo': algo,
                   'content_checksum': checksum,
                   'content': content_display_data['content_data'],
                   'content_raw_url': content_raw_url,
                   'mime_type': content_display_data['mime_type'],
                   'language': content_display_data['language'],
                   'breadcrumbs': breadcrumbs,
                   'branches': None,
                   'branch': None})


def content_raw(request, query_string):
    """Django view that produces a raw display of a SWH content identified
    by its hash value.

    See :ref:`Raw content browsing URI scheme <browse_content_raw>` for more details.

    Args:
        request: input django http request
        query_string: a string of the form "[ALGO_HASH:]HASH" where
            optional ALGO_HASH can be either *sha1*, *sha1_git*, *sha256*,
            or *blake2s256* (default to *sha1*) and HASH the hexadecimal
            representation of the hash value

    Returns:
        The raw bytes of the content.


    """ # noqa

    try:
        algo, checksum = query.parse_hash(query_string)
        checksum = hash_to_hex(checksum)
        content_data, mime_type = _request_content(query_string)
    except Exception as exc:
        return handle_view_exception(exc)

    filename = request.GET.get('filename', None)
    if not filename:
        filename = '%s_%s' % (algo, checksum)

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

    See :ref:`Origin content browsing URI scheme <browse_origin_content>` for more details.

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
        content_data, mime_type = _request_content(query_string)

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
                              kwargs={'query_string': query_string},
                              query_params={'filename': filename})

    return render(request, 'content.html',
                  {'content_hash_algo': 'sha1_git',
                   'content_checksum': sha1_git,
                   'content': content_display_data['content_data'],
                   'content_raw_url': content_raw_url,
                   'mime_type': content_display_data['mime_type'],
                   'language': content_display_data['language'],
                   'breadcrumbs': breadcrumbs,
                   'branches': branches,
                   'branch': branch})
