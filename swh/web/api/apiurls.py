# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.decorators import api_view

from swh.web.common.urlsindex import UrlsIndex
from swh.web.common.throttling import throttle_scope


class APIUrls(UrlsIndex):
    """
    Class to manage API documentation URLs.

    - Indexes all routes documented using apidoc's decorators.
    - Tracks endpoint/request processing method relationships for use in
      generating related urls in API documentation

    """
    _apidoc_routes = {}
    _method_endpoints = {}
    scope = 'api'

    @classmethod
    def get_app_endpoints(cls):
        return cls._apidoc_routes

    @classmethod
    def add_route(cls, route, docstring, **kwargs):
        """
        Add a route to the self-documenting API reference
        """
        route_view_name = 'api-%s' % route[1:-1].replace('/', '-')
        if route not in cls._apidoc_routes:
            d = {'docstring': docstring,
                 'route_view_name': route_view_name}
            for k, v in kwargs.items():
                d[k] = v
            cls._apidoc_routes[route] = d


class api_route(object):  # noqa: N801
    """
    Decorator to ease the registration of an API endpoint
    using the Django REST Framework.

    Args:
        url_pattern: the url pattern used by DRF to identify the API route
        view_name: the name of the API view associated to the route used to
           reverse the url
        methods: array of HTTP methods supported by the API route

    """

    def __init__(self, url_pattern=None, view_name=None,
                 methods=['GET', 'HEAD', 'OPTIONS'],
                 throttle_scope='swh_api',
                 api_version='1'):
        super().__init__()
        self.url_pattern = '^' + api_version + url_pattern + '$'
        self.view_name = view_name
        self.methods = methods
        self.throttle_scope = throttle_scope

    def __call__(self, f):
        # create a DRF view from the wrapped function
        @api_view(self.methods)
        @throttle_scope(self.throttle_scope)
        def api_view_f(*args, **kwargs):
            return f(*args, **kwargs)
        # small hacks for correctly generating API endpoints index doc
        api_view_f.__name__ = f.__name__
        api_view_f.http_method_names = self.methods

        # register the route and its view in the endpoints index
        APIUrls.add_url_pattern(self.url_pattern, api_view_f,
                                self.view_name)
        return f
