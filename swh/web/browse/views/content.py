# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import base64

from django.http import (
    HttpResponse, HttpResponseBadRequest
)
from django.shortcuts import render

from swh.web.common import service, highlightjs
from swh.web.browse.utils import (
    gen_path_info, get_mimetype_for_content
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
    return content_raw, mime_type


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
        content_raw, mime_type = _request_content(sha1_git)
    except Exception as exc:
        return HttpResponseBadRequest(str(exc))

    path = request.GET.get('path', None)
    content_data = content_raw['data']

    if not mime_type:
        mime_type = get_mimetype_for_content(content_data)

    language = highlightjs.get_hljs_language_from_filename(path)

    if not language:
        language = highlightjs.get_hljs_language_from_mime_type(mime_type)

    if not language:
        language = 'nohighlight'
    elif mime_type.startswith('application/'):
        mime_type = mime_type.replace('application/', 'text/')

    root_dir = None
    filename = None
    path_info = None
    if path:
        split_path = path.split('/')
        root_dir = split_path[0]
        filename = split_path[-1]
        path = path.replace(root_dir + '/', '').replace(filename, '')
        path_info = gen_path_info(path)

    if mime_type.startswith('image/'):
        if mime_type in _browsers_supported_image_mimes:
            content_data = base64.b64encode(content_data)
        else:
            content_data = None

    return render(request, 'content.html', {'content': content_data,
                                            'mime_type': mime_type,
                                            'language': language,
                                            'content_sha1': sha1_git,
                                            'root_dir': root_dir,
                                            'filename': filename,
                                            'path_info': path_info})


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
        content_raw, mime_type = _request_content(sha1_git)
    except Exception as exc:
        return HttpResponseBadRequest(str(exc))

    filename = request.GET.get('filename', None)
    if not filename:
        filename = sha1_git

    content_data = content_raw['data']
    mime_type = get_mimetype_for_content(content_data)
    if mime_type.startswith('text/'):
        response = HttpResponse(content_data, content_type="text/plain")
        response['Content-disposition'] = 'filename=%s' % filename
    else:
        response = HttpResponse(content_data,
                                content_type='application/octet-stream')
        response['Content-disposition'] = 'attachment; filename=%s' % filename
    return response
