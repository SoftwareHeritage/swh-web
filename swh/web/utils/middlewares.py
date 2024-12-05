# Copyright (C) 2018-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.web.utils.exc import handle_view_exception


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
