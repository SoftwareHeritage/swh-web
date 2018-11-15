# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import difflib
import json

from distutils.util import strtobool

from django.http import HttpResponse
from django.shortcuts import render
from django.template.defaultfilters import filesizeformat

from swh.model.hashutil import hash_to_hex

from swh.web.common import query
from swh.web.common.utils import (
    reverse, gen_path_info, swh_object_icons
)
from swh.web.common.exc import NotFoundExc, handle_view_exception
from swh.web.browse.utils import (
    request_content, prepare_content_for_display,
    content_display_max_size, get_snapshot_context,
    get_swh_persistent_ids, gen_link
)
from swh.web.browse.browseurls import browse_route


@browse_route(r'content/(?P<query_string>.+)/raw/',
              view_name='browse-content-raw')
def content_raw(request, query_string):
    """Django view that produces a raw display of a content identified
    by its hash value.

    The url that points to it is :http:get:`/browse/content/[(algo_hash):](hash)/raw/`
    """ # noqa

    try:
        algo, checksum = query.parse_hash(query_string)
        checksum = hash_to_hex(checksum)
        content_data = request_content(query_string, max_size=None,
                                       reencode=False)
    except Exception as exc:
        return handle_view_exception(request, exc)

    filename = request.GET.get('filename', None)
    if not filename:
        filename = '%s_%s' % (algo, checksum)

    if content_data['mimetype'].startswith('text/') or \
       content_data['mimetype'] == 'inode/x-empty':
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
            optional ALGO_HASH can be either ``sha1``, ``sha1_git``,
            ``sha256``, or ``blake2s256`` (default to ``sha1``) and HASH
            the hexadecimal representation of the hash value identifying
            the first content
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
    language = 'nohighlight'

    force = bool(strtobool(force))

    if from_query_string == to_query_string:
        diff_str = 'File renamed without changes'
    else:
        try:
            text_diff = True
            if from_query_string:
                content_from = \
                    request_content(from_query_string, max_size=None)
                content_from_display_data = \
                    prepare_content_for_display(content_from['raw_data'],
                                                content_from['mimetype'], path)
                language = content_from_display_data['language']
                content_from_size = content_from['length']
                if not (content_from['mimetype'].startswith('text/') or
                        content_from['mimetype'] == 'inode/x-empty'):
                    text_diff = False

            if text_diff and to_query_string:
                content_to = request_content(to_query_string, max_size=None)
                content_to_display_data = prepare_content_for_display(
                        content_to['raw_data'], content_to['mimetype'], path)
                language = content_to_display_data['language']
                content_to_size = content_to['length']
                if not (content_to['mimetype'].startswith('text/') or
                        content_to['mimetype'] == 'inode/x-empty'):
                    text_diff = False

            diff_size = abs(content_to_size - content_from_size)

            if not text_diff:
                diff_str = 'Diffs are not generated for non textual content'
                language = 'nohighlight'
            elif not force and diff_size > _auto_diff_size_limit:
                diff_str = 'Large diffs are not automatically computed'
                language = 'nohighlight'
            else:
                if content_from:
                    content_from_lines = \
                        content_from['raw_data'].decode('utf-8')\
                                                .splitlines(True)
                    if content_from_lines and \
                            content_from_lines[-1][-1] != '\n':
                        content_from_lines[-1] += '[swh-no-nl-marker]\n'

                if content_to:
                    content_to_lines = content_to['raw_data'].decode('utf-8')\
                                                            .splitlines(True)
                    if content_to_lines and content_to_lines[-1][-1] != '\n':
                        content_to_lines[-1] += '[swh-no-nl-marker]\n'

                diff_lines = difflib.unified_diff(content_from_lines,
                                                  content_to_lines)
                diff_str = ''.join(list(diff_lines)[2:])
        except Exception as e:
            diff_str = str(e)

    diff_data['diff_str'] = diff_str
    diff_data['language'] = language
    diff_data_json = json.dumps(diff_data, separators=(',', ': '))
    return HttpResponse(diff_data_json, content_type='application/json')


@browse_route(r'content/(?P<query_string>.+)/',
              view_name='browse-content')
def content_display(request, query_string):
    """Django view that produces an HTML display of a content identified
    by its hash value.

    The url that points to it is :http:get:`/browse/content/[(algo_hash):](hash)/`
    """ # noqa
    try:
        algo, checksum = query.parse_hash(query_string)
        checksum = hash_to_hex(checksum)
        content_data = request_content(query_string,
                                       raise_if_unavailable=False)
        origin_type = request.GET.get('origin_type', None)
        origin_url = request.GET.get('origin_url', None)
        if not origin_url:
            origin_url = request.GET.get('origin', None)
        snapshot_context = None
        if origin_url:
            try:
                snapshot_context = get_snapshot_context(None, origin_type,
                                                        origin_url)
            except Exception:
                raw_cnt_url = reverse('browse-content',
                                      url_args={'query_string': query_string})
                error_message = \
                    ('The Software Heritage archive has a content '
                     'with the hash you provided but the origin '
                     'mentioned in your request appears broken: %s. '
                     'Please check the URL and try again.\n\n'
                     'Nevertheless, you can still browse the content '
                     'without origin information: %s'
                        % (gen_link(origin_url), gen_link(raw_cnt_url)))

                raise NotFoundExc(error_message)
        if snapshot_context:
            snapshot_context['visit_info'] = None
    except Exception as exc:
        return handle_view_exception(request, exc)

    path = request.GET.get('path', None)

    content = None
    language = None
    mimetype = None
    if content_data['raw_data'] is not None:
        content_display_data = prepare_content_for_display(
            content_data['raw_data'], content_data['mimetype'], path)
        content = content_display_data['content_data']
        language = content_display_data['language']
        mimetype = content_display_data['mimetype']

    root_dir = None
    filename = None
    path_info = None

    query_params = {'origin': origin_url}

    breadcrumbs = []

    if path:
        split_path = path.split('/')
        root_dir = split_path[0]
        filename = split_path[-1]
        if root_dir != path:
            path = path.replace(root_dir + '/', '')
            path = path[:-len(filename)]
            path_info = gen_path_info(path)
            dir_url = reverse('browse-directory',
                              url_args={'sha1_git': root_dir},
                              query_params=query_params)
            breadcrumbs.append({'name': root_dir[:7],
                                'url': dir_url})
            for pi in path_info:
                dir_url = reverse('browse-directory',
                                  url_args={'sha1_git': root_dir,
                                            'path': pi['path']},
                                  query_params=query_params)
                breadcrumbs.append({'name': pi['name'],
                                    'url': dir_url})
        breadcrumbs.append({'name': filename,
                            'url': None})

    query_params = {'filename': filename}

    content_raw_url = reverse('browse-content-raw',
                              url_args={'query_string': query_string},
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
        'licenses': content_data['licenses'],
        'filename': filename
    }

    if filename:
        content_metadata['filename'] = filename

    sha1_git = content_data['checksums']['sha1_git']
    swh_ids = get_swh_persistent_ids([{'type': 'content',
                                       'id': sha1_git}])

    heading = 'Content - %s' % sha1_git
    if breadcrumbs:
        content_path = '/'.join([bc['name'] for bc in breadcrumbs])
        heading += ' - %s' % content_path

    return render(request, 'browse/content.html',
                  {'heading': heading,
                   'swh_object_id': swh_ids[0]['swh_id'],
                   'swh_object_name': 'Content',
                   'swh_object_metadata': content_metadata,
                   'content': content,
                   'content_size': content_data['length'],
                   'max_content_size': content_display_max_size,
                   'mimetype': mimetype,
                   'language': language,
                   'breadcrumbs': breadcrumbs,
                   'top_right_link': {
                        'url': content_raw_url,
                        'icon': swh_object_icons['content'],
                        'text': 'Raw File'
                   },
                   'snapshot_context': snapshot_context,
                   'vault_cooking': None,
                   'show_actions_menu': True,
                   'swh_ids': swh_ids,
                   'error_code': content_data['error_code'],
                   'error_message': content_data['error_message'],
                   'error_description': content_data['error_description']},
                  status=content_data['error_code'])
