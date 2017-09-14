# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re

from django.conf.urls import url
from rest_framework.decorators import api_view

from swh.web.common.throttling import throttle_scope


class APIUrls(object):
    """
    Class to manage API documentation URLs.

    - Indexes all routes documented using apidoc's decorators.
    - Tracks endpoint/request processing method relationships for use in
      generating related urls in API documentation

    """
    apidoc_routes = {}
    method_endpoints = {}
    urlpatterns = []

    @classmethod
    def get_app_endpoints(cls):
        return cls.apidoc_routes

    @classmethod
    def get_method_endpoints(cls, f):
        if f.__name__ not in cls.method_endpoints:
            cls.method_endpoints[f.__name__] = cls.group_routes_by_method(f)
        return cls.method_endpoints[f.__name__]

    @classmethod
    def group_routes_by_method(cls, f):
        """
        Group URL endpoints according to their processing method.

        Returns:
            A dict where keys are the processing method names, and values are
            the routes that are bound to the key method.

        """
        rules = []
        for urlp in cls.urlpatterns:
            endpoint = urlp.callback.__name__
            if endpoint != f.__name__:
                continue
            method_names = urlp.callback.http_method_names
            url_rule = urlp.regex.pattern.replace('^', '/').replace('$', '')
            url_rule_params = re.findall('\([^)]+\)', url_rule)
            for param in url_rule_params:
                param_name = re.findall('<(.*)>', param)
                param_name = param_name[0] if len(param_name) > 0 else None
                if param_name and hasattr(f, 'doc_data') and f.doc_data['args']: # noqa
                    param_index = \
                        next(i for (i, d) in enumerate(f.doc_data['args'])
                             if d['name'] == param_name)
                    if param_index is not None:
                        url_rule = url_rule.replace(
                            param, '<' +
                            f.doc_data['args'][param_index]['name'] +
                            ': ' + f.doc_data['args'][param_index]['type'] +
                            '>').replace('.*', '')
            rule_dict = {'rule': '/api' + url_rule,
                         'name': urlp.name,
                         'methods': {method.upper() for method in method_names}
                         }
            rules.append(rule_dict)

        return rules

    @classmethod
    def index_add_route(cls, route, docstring, **kwargs):
        """
        Add a route to the self-documenting API reference
        """
        route_view_name = route[1:-1].replace('/', '-')
        if route not in cls.apidoc_routes:
            d = {'docstring': docstring,
                 'route_view_name': route_view_name}
            for k, v in kwargs.items():
                d[k] = v
            cls.apidoc_routes[route] = d

    @classmethod
    def index_add_url_pattern(cls, url_pattern, view, view_name):
        cls.urlpatterns.append(url(url_pattern, view, name=view_name))

    @classmethod
    def get_url_patterns(cls):
        return cls.urlpatterns


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
                 methods=['GET', 'HEAD', 'OPTIONS'], api_version='1'):
        super().__init__()
        self.url_pattern = '^' + api_version + url_pattern + '$'
        self.view_name = view_name
        self.methods = methods

    def __call__(self, f):

        # create a DRF view from the wrapped function
        @api_view(self.methods)
        @throttle_scope('swh_api')
        def api_view_f(*args, **kwargs):
            return f(*args, **kwargs)
        # small hacks for correctly generating API endpoints index doc
        api_view_f.__name__ = f.__name__
        api_view_f.http_method_names = self.methods

        # register the route and its view in the endpoints index
        APIUrls.index_add_url_pattern(self.url_pattern, api_view_f,
                                      self.view_name)
        return f
