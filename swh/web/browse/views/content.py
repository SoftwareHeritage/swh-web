# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import difflib
import json

from distutils.util import strtobool

from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.shortcuts import render
from django.template.defaultfilters import filesizeformat

from swh.model.hashutil import hash_to_hex

from swh.web.common import query
from swh.web.common.utils import reverse, gen_path_info
from swh.web.common.exc import handle_view_exception
from swh.web.browse.utils import (
    request_content, prepare_content_for_display,
    content_display_max_size
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
        content_data = request_content(query_string, max_size=None)
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


_auto_diff_size_limit = 20000


@browse_route(r'content/(?P<from_query_string>.*)/diff/(?P<to_query_string>.*)', # noqa
              view_name='diff-contents')
def _contents_diff(request, from_query_string, to_query_string):
    """
    Browse endpoint used to compute unified diffs between two contents.

    Diffs are generated only if the two contents are textual.
    By default, diffs whose size are greater than 20 kB will
    not be generated. To force the generation of large diffs,
    the 'force' boolean query parameter must be used.

    Args:
        request: input django http request
        from_query_string: a string of the form "[ALGO_HASH:]HASH" where
            optional ALGO_HASH can be either *sha1*, *sha1_git*, *sha256*,
            or *blake2s256* (default to *sha1*) and HASH the hexadecimal
            representation of the hash value identifying the first content
        to_query_string: same as above for identifying the second content

    Returns:
        A JSON object containing the unified diff.

    """
    diff_data = {}
    content_from = None
    content_to = None
    content_from_size = 0
    content_to_size = 0
    content_from_lines = []
    content_to_lines = []
    force = request.GET.get('force', 'false')
    path = request.GET.get('path', None)
    language = 'nohighlight-swh'

    force = bool(strtobool(force))

    if from_query_string == to_query_string:
        diff_str = 'File renamed without changes'
    else:
        text_diff = True
        if from_query_string:
            content_from = request_content(from_query_string)
            content_from_display_data = prepare_content_for_display(
                    content_from['raw_data'], content_from['mimetype'], path)
            language = content_from_display_data['language']
            content_from_size = content_from['length']
            if not content_from['mimetype'].startswith('text/'):
                text_diff = False

        if text_diff and to_query_string:
            content_to = request_content(to_query_string)
            content_to_display_data = prepare_content_for_display(
                    content_to['raw_data'], content_to['mimetype'], path)
            language = content_to_display_data['language']
            content_to_size = content_to['length']
            if not content_to['mimetype'].startswith('text/'):
                text_diff = False

        diff_size = abs(content_to_size - content_from_size)

        if not text_diff:
            diff_str = 'Diffs are not generated for non textual content'
            language = 'nohighlight-swh'
        elif not force and diff_size > _auto_diff_size_limit:
            diff_str = 'Large diffs are not automatically computed'
            language = 'nohighlight-swh'
        else:
            if content_from:
                content_from_lines = content_from['raw_data'].decode('utf-8')\
                                                             .splitlines(True)
                if content_from_lines[-1][-1] != '\n':
                    content_from_lines[-1] += '[swh-no-nl-marker]\n'

            if content_to:
                content_to_lines = content_to['raw_data'].decode('utf-8')\
                                                         .splitlines(True)
                if content_to_lines[-1][-1] != '\n':
                    content_to_lines[-1] += '[swh-no-nl-marker]\n'

            diff_lines = difflib.unified_diff(content_from_lines,
                                              content_to_lines)
            diff_str = ''.join(list(diff_lines)[2:])

    diff_data['diff_str'] = diff_str
    diff_data['language'] = language
    diff_data_json = json.dumps(diff_data, separators=(',', ': '))
    return HttpResponse(diff_data_json, content_type='application/json')


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

    content = None
    language = None
    if content_data['raw_data'] is not None:
        content_display_data = prepare_content_for_display(
            content_data['raw_data'], content_data['mimetype'], path)
        content = content_display_data['content_data']
        language = content_display_data['language']

    root_dir = None
    filename = None
    path_info = None

    breadcrumbs = []

    if path:
        split_path = path.split('/')
        root_dir = split_path[0]
        filename = split_path[-1]
        path = path.replace(root_dir + '/', '')
        path = path[:-len(filename)]
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
                  {'empty_browse': False,
                   'heading': 'Content information',
                   'top_panel_visible': True,
                   'top_panel_collapsible': True,
                   'top_panel_text': 'SWH object: Content',
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
                   'origin_context': None,
                   'vault_cooking': None
                   })
