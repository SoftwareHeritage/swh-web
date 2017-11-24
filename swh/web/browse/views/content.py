# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import HttpResponse

from django.shortcuts import render
from django.template.defaultfilters import filesizeformat

from swh.model.hashutil import hash_to_hex

from swh.web.common import query
from swh.web.common.utils import reverse
from swh.web.common.exc import handle_view_exception
from swh.web.browse.utils import (
    gen_path_info, request_content,
    prepare_content_for_display
)
from swh.web.browse.browseurls import browse_route


@browse_route(r'content/(?P<query_string>.+)/raw/',
              view_name='browse-content-raw')
def content_raw(request, query_string):
    """Django view that produces a raw display of a SWH content identified
    by its hash value.

    The url that points to it is :http:get:`/browse/content/[(algo_hash):](hash)/raw/`

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
        content_data = request_content(query_string)
    except Exception as exc:
        return handle_view_exception(request, exc)

    filename = request.GET.get('filename', None)
    if not filename:
        filename = '%s_%s' % (algo, checksum)

    if content_data['mimetype'].startswith('text/'):
        response = HttpResponse(content_data['raw_data'],
                                content_type="text/plain")
        response['Content-disposition'] = 'filename=%s' % filename
    else:
        response = HttpResponse(content_data['raw_data'],
                                content_type='application/octet-stream')
        response['Content-disposition'] = 'attachment; filename=%s' % filename
    return response


@browse_route(r'content/(?P<query_string>.+)/',
              view_name='browse-content')
def content_display(request, query_string):
    """Django view that produces an HTML display of a SWH content identified
    by its hash value.

    The url that points to it is :http:get:`/browse/content/[(algo_hash):](hash)/`

    Args:
        request: input django http request
        query_string: a string of the form "[ALGO_HASH:]HASH" where
            optional ALGO_HASH can be either *sha1*, *sha1_git*, *sha256*,
            or *blake2s256* (default to *sha1*) and HASH the hexadecimal
            representation of the hash value

    Returns:
        The HTML rendering of the requested content.

    """ # noqa
    try:
        algo, checksum = query.parse_hash(query_string)
        checksum = hash_to_hex(checksum)
        content_data = request_content(query_string)
    except Exception as exc:
        return handle_view_exception(request, exc)

    path = request.GET.get('path', None)

    content_display_data = prepare_content_for_display(
        content_data['raw_data'], content_data['mimetype'], path)

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

    content_metadata = {
        'sha1 checksum': content_data['checksums']['sha1'],
        'sha1_git checksum': content_data['checksums']['sha1_git'],
        'sha256 checksum': content_data['checksums']['sha256'],
        'blake2s256 checksum': content_data['checksums']['blake2s256'],
        'mime type': content_data['mimetype'],
        'encoding': content_data['encoding'],
        'size': filesizeformat(content_data['length']),
        'language': content_data['language'],
        'licenses': content_data['licenses']
    }

    return render(request, 'content.html',
                  {'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text_left': 'SWH object: Content',
                   'top_panel_text_right': '%s: %s' % (algo, checksum),
                   'swh_object_metadata': content_metadata,
                   'main_panel_visible': True,
                   'content': content_display_data['content_data'],
                   'mimetype': content_data['mimetype'],
                   'language': content_display_data['language'],
                   'breadcrumbs': breadcrumbs,
                   'branches': None,
                   'branch': None,
                   'top_right_link': content_raw_url,
                   'top_right_link_text': 'Raw File'})
