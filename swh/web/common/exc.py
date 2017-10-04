# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import traceback

from django.http import (
    HttpResponseBadRequest, HttpResponseNotFound
)

from swh.web.config import get_config


class BadInputExc(ValueError):
    """Wrong request to the api.

    Example: Asking a content with the wrong identifier format.

    """
    pass


class NotFoundExc(Exception):
    """Good request to the api but no result were found.

    Example: Asking a content with the right identifier format but
    that content does not exist.

    """
    pass


class ForbiddenExc(Exception):
    """Good request to the api, forbidden result to return due to enforce
       policy.

    Example: Asking for a raw content which exists but whose mimetype
    is not text.

    """
    pass


def handle_view_exception(exc):
    content_type = None
    content = str(exc)
    if get_config()['debug']:
        content_type = 'text/plain'
        content = traceback.format_exc()
    if isinstance(exc, NotFoundExc):
        return HttpResponseNotFound(content, content_type=content_type)
    else:
        return HttpResponseBadRequest(content, content_type=content_type)
