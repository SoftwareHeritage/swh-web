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


class APIDocException(Exception):
    """
    Custom exception to signal errors in the use of the APIDoc decorators
    """


class APIDocBase(object):
    """
    The API documentation decorator base class, responsible for the
    operations that link the decorator stack together:

    * manages the _inner_dec property, which represents the
      decorator directly below self in the decorator tower
    * contains the logic used to return appropriately if self is the last
      decorator to be applied to the API function
    """

    def __init__(self):
        self._inner_dec = None

    @property
    def inner_dec(self):
        return self._inner_dec

    @inner_dec.setter
    def inner_dec(self, instance):
        self._inner_dec = instance

    @property
    def data(self):
        raise NotImplementedError

    def process_rv(self, f, args, kwargs):
        """
        From the arguments f has, determine whether or not it is the last
        decorator in the stack, and return the appropriate call to f.
        """

        rv = None
        if 'outer_decorator' in f.__code__.co_varnames:
            rv = f(*args, **kwargs)
        else:
            nargs = {k: v for k, v in kwargs.items() if k != 'outer_decorator'}
            try:
                rv = f(*args, **nargs)
            except (TypeError, KeyError):  # documentation call
                rv = None
        return rv

    def maintain_stack(self, f, args, kwargs):
        """
        From the arguments f is called with, determine whether or not the
        stack link was made by @apidoc.route, and maintain the linking for
        the next call to f.
        """

        if 'outer_decorator' not in kwargs:
            raise APIDocException('Apidoc %s: expected an apidoc'
                                  ' route decorator first'
                                  % self.__class__.__name__)
        kwargs['outer_decorator'].inner_dec = self
        kwargs['outer_decorator'] = self

        return self.process_rv(f, args, kwargs)


class route(APIDocBase):  # noqa: N801
    """
    Decorate an API method to register it in the API doc route index
    and create the corresponding Flask route.

    This decorator is responsible for bootstrapping the linking of subsequent
    decorators, as well as traversing the decorator stack to obtain the
    documentation data from it.

    Args:
        route: the documentation page's route
        noargs: set to True if the route has no arguments, and its result
        should be displayed anytime its documentation is requested
    """
    def __init__(self, route, noargs=False):
        super().__init__()
        self.route = route
        self.noargs = noargs

    def __call__(self, f):
        APIUrls.index_add_route(self.route, f.__doc__)

        @wraps(f)
        def doc_func(*args, **kwargs):
            kwargs['outer_decorator'] = self
            rv = self.process_rv(f, args, kwargs)
            return self.compute_return(f, rv)

        if not self.noargs:
            app.add_url_rule(self.route, f.__name__, doc_func)

        return doc_func

    def filter_api_url(self, endpoint, route_re, noargs):
        doc_methods = {'GET', 'HEAD', 'OPTIONS'}
        if re.match(route_re, endpoint['rule']):
            if endpoint['methods'] == doc_methods and not noargs:
                return False
        return True

    def compute_return(self, f, rv):
        """Build documentation"""
        data = self.data
        if not f.__doc__:
            raise APIDocException('Apidoc %s: expected a docstring'
                                  ' for function %s'
                                  % (self.__class__.__name__, f.__name__))
        data['docstring'] = f.__doc__

        route_re = re.compile('.*%s$' % data['route'])
        endpoint_list = APIUrls.get_method_endpoints(f.__name__)
        other_urls = [url for url in endpoint_list if
                      self.filter_api_url(url, route_re, data['noargs'])]
        data['urls'] = other_urls

        # Build example endpoint URL
        if 'args' in data:
            defaults = {arg['name']: arg['default'] for arg in data['args']}
            example = url_for(f.__name__, **defaults)
            data['example'] = re.sub(r'(.*)\?.*', r'\1', example)

        # Prepare and send to mimetype selector if it's not a doc request
        if re.match(route_re, request.url) and not data['noargs'] \
           and request.method == 'GET':
            return app.response_class(
                render_template('apidoc.html', **data),
                content_type='text/html')

        g.doc_env = data  # Store for response processing
        return rv

    @property
    def data(self):
        data = {'route': self.route, 'noargs': self.noargs}

        doc_instance = self.inner_dec
        while doc_instance:
            if isinstance(doc_instance, arg):
                if 'args' not in data:
                    data['args'] = []
                    data['args'].append(doc_instance.data)
            elif isinstance(doc_instance, raises):
                if 'excs' not in data:
                    data['excs'] = []
                    data['excs'].append(doc_instance.data)
            elif isinstance(doc_instance, returns):
                data['return'] = doc_instance.data
            else:
                raise APIDocException('Unknown API documentation decorator')
            doc_instance = doc_instance.inner_dec

        return data


class arg(APIDocBase):  # noqa: N801
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
        super().__init__()
        self.doc_dict = {
            'name': name,
            'type': argtype.value,
            'doc': argdoc,
            'default': default
        }
        self.inner_dec = None

    def __call__(self, f):
        @wraps(f)
        def arg_fun(*args, outer_decorator=None, **kwargs):
            kwargs['outer_decorator'] = outer_decorator
            return self.maintain_stack(f, args, kwargs)
        return arg_fun

    @property
    def data(self):
        return self.doc_dict


class raises(APIDocBase):  # noqa: N801
    """
    Decorate an API method to display information pertaining to an exception
    that can be raised by this method.
    Args:
        exc: the exception name as an Enum value from apidoc.excs
        doc: the exception's documentation string
    """
    def __init__(self, exc, doc):
        super().__init__()
        self.exc_dict = {
            'exc': exc.value,
            'doc': doc
        }

    def __call__(self, f):
        @wraps(f)
        def exc_fun(*args, outer_decorator=None, **kwargs):
            kwargs['outer_decorator'] = outer_decorator
            return self.maintain_stack(f, args, kwargs)
        return exc_fun

    @property
    def data(self):
        return self.exc_dict


class returns(APIDocBase):  # noqa: N801
    """
    Decorate an API method to display information about its return value.
    Args:
        rettype: the return value's type as an Enum value from apidoc.rettypes
        retdoc: the return value's documentation string
    """
    def __init__(self, rettype=None, retdoc=None):
        super().__init__()
        self.return_dict = {
            'type': rettype.value,
            'doc': retdoc
        }

    def __call__(self, f):
        @wraps(f)
        def ret_fun(*args, outer_decorator=None, **kwargs):
            kwargs['outer_decorator'] = outer_decorator
            return self.maintain_stack(f, args, kwargs)
        return ret_fun

    @property
    def data(self):
        return self.return_dict
