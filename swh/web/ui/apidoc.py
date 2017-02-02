# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re

from collections import defaultdict
from functools import wraps
from enum import Enum

from flask import render_template, url_for
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
    algo_and_hash = 'hash_type:hash'


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
    def index_add_route(cls, route, docstring, **kwargs):
        """
        Add a route to the self-documenting API reference
        """
        if route not in cls.apidoc_routes:
            d = {'docstring': docstring}
            for k, v in kwargs.items():
                d[k] = v
            cls.apidoc_routes[route] = d


class APIDocException(Exception):
    """
    Custom exception to signal errors in the use of the APIDoc decorators
    """


class route(object):  # noqa: N801
    """Decorate an API method to register it in the API doc route index
    and create the corresponding Flask route.

    This decorator is responsible for bootstrapping the linking of subsequent
    decorators, as well as traversing the decorator stack to obtain the
    documentation data from it.

    Args:
        route: documentation page's route
        noargs: set to True if the route has no arguments, and its
                result should be displayed anytime its documentation
                is requested. Default to False
        hidden: set to True to remove the endpoint from being listed
                in the /api endpoints. Default to False.
        tags: Further information on api endpoints. Two values are
              possibly expected:
              - hidden: remove the entry points from the listing
              - upcoming: display the entry point but it is not followable

    """
    def __init__(self, route, noargs=False, tags=[]):
        super().__init__()
        self.route = route
        self.noargs = noargs
        self.tags = set(tags)

    # @apidoc.route() Decorator call
    def __call__(self, f):
        # If the route is not hidden, add it to the index
        if 'hidden' not in self.tags:
            APIUrls.index_add_route(self.route, f.__doc__, tags=self.tags)

        # If the decorated route has arguments, we create a specific
        # documentation view
        if not self.noargs:
            doc_route_name = 'doc_for_%s' % f.__name__

            def doc_view():
                doc_data = self.get_doc_data(f)
                return app.response_class(
                    render_template('apidoc.html', **doc_data),
                    content_type='text/html')

            app.add_url_rule(self.route, doc_route_name, doc_view,
                             methods=['GET'])

        # The documented view only adds the documentation data to the global
        # context
        @wraps(f)
        def documented_view(*args, **kwargs):
            g.doc_env = self.get_doc_data(f)  # Store for response processing
            rv = f(*args, **kwargs)
            return rv

        return documented_view

    def filter_api_url(self, endpoint, route_re, noargs):
        doc_methods = {'GET', 'HEAD', 'OPTIONS'}
        if re.match(route_re, endpoint['rule']):
            if endpoint['methods'] == doc_methods and not noargs:
                return False
        return True

    def build_examples(self, f, urls, args):
        """Build example documentation.

        Args:
            f: function
            urls: information relative to url for that function
            args: information relative to arguments for that function

        Yields:
            example based on default parameter value if any

        """
        s = set()
        r = []
        for data_url in urls:
            url = data_url['rule']
            defaults = {arg['name']: arg['default']
                        for arg in args
                        if arg['name'] in url}
            if defaults:
                url = url_for(f.__name__, **defaults)
                if url in s:
                    continue
                s.add(url)
                r.append(url)

        return r

    def get_doc_data(self, f):
        """Build documentation data for the decorated function"""
        data = {
            'route': self.route,
            'noargs': self.noargs,
        }

        data.update(getattr(f, 'doc_data', {}))

        if not f.__doc__:
            raise APIDocException('Apidoc %s: expected a docstring'
                                  ' for function %s'
                                  % (self.__class__.__name__, f.__name__))
        data['docstring'] = f.__doc__

        route_re = re.compile('.*%s$' % data['route'])
        endpoint_list = APIUrls.get_method_endpoints(f.__name__)
        data['urls'] = [url for url in endpoint_list if
                        self.filter_api_url(url, route_re, data['noargs'])]

        if 'args' in data:
            data['examples'] = self.build_examples(
                f, data['urls'], data['args'])

        data['heading'] = '%s Documentation' % data['route']

        return data


class DocData(object):
    """Base description of optional input/output setup for a route.

    """
    destination = None

    def __init__(self):
        self.doc_data = {}

    def __call__(self, f):
        if not hasattr(f, 'doc_data'):
            f.doc_data = defaultdict(list)

        f.doc_data[self.destination].append(self.doc_data)

        return f


class arg(DocData):  # noqa: N801
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
    destination = 'args'

    def __init__(self, name, default, argtype, argdoc):
        super().__init__()
        self.doc_data = {
            'name': name,
            'type': argtype.value,
            'doc': argdoc,
            'default': default
        }


class header(DocData):  # noqa: N801
    """
    Decorate an API method to display header information the api can
    potentially return in the response.

    Args:
        name: the header name
        doc: the information about that header

    """
    destination = 'headers'

    def __init__(self, name, doc):
        super().__init__()
        self.doc_data = {
            'name': name,
            'doc': doc,
        }


class param(DocData):  # noqa: N801
    """Decorate an API method to display query parameter information the
    api can potentially accept.

    Args:
        name: parameter's name
        default: parameter's default value
        argtype: parameter's type as an Enum value from apidoc.argtypes
        doc: the information about that header

    """
    destination = 'params'

    def __init__(self, name, default, argtype, doc):
        super().__init__()
        self.doc_data = {
            'name': name,
            'type': argtype.value,
            'default': default,
            'doc': doc,
        }


class raises(DocData):  # noqa: N801
    """Decorate an API method to display information pertaining to an exception
    that can be raised by this method.

    Args:
        exc: the exception name as an Enum value from apidoc.excs
        doc: the exception's documentation string

    """
    destination = 'excs'

    def __init__(self, exc, doc):
        super().__init__()
        self.doc_data = {
            'exc': exc.value,
            'doc': doc
        }


class returns(DocData):  # noqa: N801
    """Decorate an API method to display information about its return value.

    Args:
        rettype: the return value's type as an Enum value from
        apidoc.rettypes retdoc: the return value's documentation
        string

    """
    destination = 'returns'

    def __init__(self, rettype=None, retdoc=None):
        super().__init__()
        self.doc_data = {
            'type': rettype.value,
            'doc': retdoc
        }
