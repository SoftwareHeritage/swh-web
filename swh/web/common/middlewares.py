# Copyright (C) 2018-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from htmlmin import minify
import sentry_sdk

from swh.web.common.exc import handle_view_exception
from swh.web.common.utils import prettify_html


class HtmlPrettifyMiddleware(object):
    """
    Django middleware for prettifying generated HTML in
    development mode.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if "text/html" in response.get("Content-Type", ""):
            if hasattr(response, "content"):
                content = response.content
                response.content = prettify_html(content)
            elif hasattr(response, "streaming_content"):
                content = b"".join(response.streaming_content)
                response.streaming_content = prettify_html(content)

        return response


class HtmlMinifyMiddleware(object):
    """
    Django middleware for minifying generated HTML in
    production mode.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if "text/html" in response.get("Content-Type", ""):
            try:
                minified_html = minify(
                    response.content.decode("utf-8"), convert_charrefs=False
                )
                response.content = minified_html.encode("utf-8")
            except Exception as exc:
                sentry_sdk.capture_exception(exc)
        return response


class ThrottlingHeadersMiddleware(object):
    """
    Django middleware for inserting rate limiting related
    headers in HTTP response.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        resp = self.get_response(request)
        if "RateLimit-Limit" in request.META:
            resp["X-RateLimit-Limit"] = request.META["RateLimit-Limit"]
        if "RateLimit-Remaining" in request.META:
            resp["X-RateLimit-Remaining"] = request.META["RateLimit-Remaining"]
        if "RateLimit-Reset" in request.META:
            resp["X-RateLimit-Reset"] = request.META["RateLimit-Reset"]
        return resp


class ExceptionMiddleware(object):
    """
    Django middleware for handling uncaught exception raised when
    processing a view.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        return handle_view_exception(request, exception)
