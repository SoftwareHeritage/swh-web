# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re

from functools import wraps
from enum import Enum

from flask import request, render_template, url_for
from flask import g

from swh.web.ui.main import app


class argtypes(Enum):  # noqa: N801
    """Class for centralizing argument type descriptions

    """

    ts = 'timestamp'
    int = 'integer'
    str = 'string'
    path = 'path'
    sha1 = 'sha1'
    uuid = 'uuid'
    sha1_git = 'sha1_git'
    algo_and_hash = 'algo_hash:hash'


class rettypes(Enum):  # noqa: N801
    """Class for centralizing return type descriptions

    """
    octet_stream = 'octet stream'
    list = 'list'
    dict = 'dict'


class excs(Enum):  # noqa: N801
    """Class for centralizing exception type descriptions

    """

    badinput = 'BadInputExc'
    notfound = 'NotFoundExc'


class APIUrls(object):
    """
    Class to manage API documentation URLs.
      * Indexes all routes documented using apidoc's decorators.
      * Tracks endpoint/request processing method relationships for use
        in generating related urls in API documentation
    Relies on the load_controllers logic in main.py for initialization.

    """
    apidoc_routes = {}
    method_endpoints = {}

    @classmethod
    def get_app_endpoints(cls):
        return cls.apidoc_routes

    @classmethod
    def get_method_endpoints(cls, fname):
        if len(cls.method_endpoints) == 0:
            cls.method_endpoints = cls.group_routes_by_method()
        return cls.method_endpoints[fname]

    @classmethod
    def group_routes_by_method(cls):
        """
        Group URL endpoints according to their processing method.
        Returns:
            A dict where keys are the processing method names, and values
            are the routes that are bound to the key method.
        """
        endpoints = {}
        for rule in app.url_map.iter_rules():
            rule_dict = {'rule': rule.rule,
                         'methods': rule.methods}
            if rule.endpoint not in endpoints:
                endpoints[rule.endpoint] = [rule_dict]
            else:
                endpoints[rule.endpoint].append(rule_dict)
        return endpoints

    @classmethod
    def index_add_route(cls, route, docstring):
        """
        Add a route to the self-documenting API reference
        """
        if route not in cls.apidoc_routes:
            cls.apidoc_routes[route] = docstring


class route(object):  # noqa: N801
    """
    Decorate an API method to register it in the API doc route index
    and create the corresponding Flask route.
    Caution: decorating a method with this requires to also decorate it
    __at least__ with @returns, or breaks the decorated endpoint
    Args:
        route: the documentation page's route
        noargs: set to True if the route has no arguments, and its result
        should be displayed anytime its documentation is requested
    """
    def __init__(self, route, noargs=False):
        self.route = route
        self.noargs = noargs

    def __call__(self, f):
        APIUrls.index_add_route(self.route, f.__doc__)

        @wraps(f)
        def doc_func(*args, **kwargs):
            return f(call_args=(args, kwargs),
                     doc_route=self.route,
                     noargs=self.noargs)

        if not self.noargs:
            app.add_url_rule(self.route, f.__name__, doc_func)

        return doc_func


class arg(object):  # noqa: N801
    """
    Decorate an API method to display an argument's information on the doc
    page specified by @route above.
    Args:
        name: the argument's name. MUST match the method argument's name to
        create the example request URL.
        default: the argument's default value
        argtype: the argument's type as an Enum value from apidoc.argtypes
        argdoc: the argument's documentation string
    """
    def __init__(self, name, default, argtype, argdoc):
        self.doc_dict = {
            'name': name,
            'type': argtype.value,
            'doc': argdoc,
            'default': default
        }

    def __call__(self, f):
        @wraps(f)
        def arg_fun(*args, **kwargs):
            if 'args' in kwargs:
                kwargs['args'].append(self.doc_dict)
            else:
                kwargs['args'] = [self.doc_dict]
            return f(*args, **kwargs)
        return arg_fun


class raises(object):  # noqa: N801
    """
    Decorate an API method to display information pertaining to an exception
    that can be raised by this method.
    Args:
        exc: the exception name as an Enum value from apidoc.excs
        doc: the exception's documentation string
    """
    def __init__(self, exc, doc):
        self.exc_dict = {
            'exc': exc.value,
            'doc': doc
        }

    def __call__(self, f):
        @wraps(f)
        def exc_fun(*args, **kwargs):
            if 'excs' in kwargs:
                kwargs['excs'].append(self.exc_dict)
            else:
                kwargs['excs'] = [self.exc_dict]
            return f(*args, **kwargs)
        return exc_fun


class returns(object):  # noqa: N801
    """
    Decorate an API method to display information about its return value.
    Caution: this MUST be the last decorator in the apidoc decorator stack,
    or the decorated endpoint breaks
    Args:
        rettype: the return value's type as an Enum value from apidoc.rettypes
        retdoc: the return value's documentation string
    """
    def __init__(self, rettype=None, retdoc=None):
        self.return_dict = {
            'type': rettype.value,
            'doc': retdoc
        }

    def filter_api_url(self, endpoint, route_re, noargs):
        doc_methods = {'GET', 'HEAD', 'OPTIONS'}
        if re.match(route_re, endpoint['rule']):
            if endpoint['methods'] == doc_methods and not noargs:
                return False
        return True

    def __call__(self, f):
        @wraps(f)
        def ret_fun(*args, **kwargs):
            # Build documentation
            env = {
                'docstring': f.__doc__,
                'route': kwargs['doc_route'],
                'return': self.return_dict
            }

            for arg in ['args', 'excs']:
                if arg in kwargs:
                    env[arg] = kwargs[arg]

            route_re = re.compile('.*%s$' % kwargs['doc_route'])
            endpoint_list = APIUrls.get_method_endpoints(f.__name__)
            other_urls = [url for url in endpoint_list if
                          self.filter_api_url(url, route_re, kwargs['noargs'])]
            env['urls'] = other_urls

            # Build example endpoint URL
            if 'args' in env:
                defaults = {arg['name']: arg['default'] for arg in env['args']}
                example = url_for(f.__name__, **defaults)
                env['example'] = re.sub(r'(.*)\?.*', r'\1', example)

            # Prepare and send to mimetype selector if it's not a doc request
            if re.match(route_re, request.url) and not kwargs['noargs'] \
               and request.method == 'GET':
                return app.response_class(
                    render_template('apidoc.html', **env),
                    content_type='text/html')

            cargs, ckwargs = kwargs['call_args']
            g.doc_env = env  # Store for response processing
            return f(*cargs, **ckwargs)
        return ret_fun
