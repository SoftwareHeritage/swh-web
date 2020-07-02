# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import functools

from typing import Dict

from rest_framework.decorators import api_view

from swh.web.common.urlsindex import UrlsIndex
from swh.web.api import throttling


class APIUrls(UrlsIndex):
    """
    Class to manage API documentation URLs.

    - Indexes all routes documented using apidoc's decorators.
    - Tracks endpoint/request processing method relationships for use in
      generating related urls in API documentation

    """

    _apidoc_routes = {}  # type: Dict[str, Dict[str, str]]
    scope = "api"

    @classmethod
    def get_app_endpoints(cls):
        return cls._apidoc_routes

    @classmethod
    def add_doc_route(cls, route, docstring, noargs=False, api_version="1", **kwargs):
        """
        Add a route to the self-documenting API reference
        """
        route_name = route[1:-1].replace("/", "-")
        if not noargs:
            route_name = "%s-doc" % route_name
        route_view_name = "api-%s-%s" % (api_version, route_name)
        if route not in cls._apidoc_routes:
            d = {
                "docstring": docstring,
                "route": "/api/%s%s" % (api_version, route),
                "route_view_name": route_view_name,
            }
            for k, v in kwargs.items():
                d[k] = v
            cls._apidoc_routes[route] = d


def api_route(
    url_pattern=None,
    view_name=None,
    methods=["GET", "HEAD", "OPTIONS"],
    throttle_scope="swh_api",
    api_version="1",
    checksum_args=None,
):
    """
    Decorator to ease the registration of an API endpoint
    using the Django REST Framework.

    Args:
        url_pattern: the url pattern used by DRF to identify the API route
        view_name: the name of the API view associated to the route used to
           reverse the url
        methods: array of HTTP methods supported by the API route

    """

    url_pattern = "^" + api_version + url_pattern + "$"

    def decorator(f):
        # create a DRF view from the wrapped function
        @api_view(methods)
        @throttling.throttle_scope(throttle_scope)
        @functools.wraps(f)
        def api_view_f(*args, **kwargs):
            return f(*args, **kwargs)

        # small hacks for correctly generating API endpoints index doc
        api_view_f.__name__ = f.__name__
        api_view_f.http_method_names = methods

        # register the route and its view in the endpoints index
        APIUrls.add_url_pattern(url_pattern, api_view_f, view_name)

        if checksum_args:
            APIUrls.add_redirect_for_checksum_args(
                view_name, [url_pattern], checksum_args
            )
        return f

    return decorator
