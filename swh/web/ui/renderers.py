# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re
import yaml
import json

from docutils.core import publish_parts
from docutils.writers.html4css1 import Writer, HTMLTranslator

from flask import make_response, request, Response, render_template
from flask import g
from flask.ext.api import renderers, parsers
from flask_api.mediatypes import MediaType

from swh.web.ui import utils


class SWHFilterEnricher():
    """Global filter on fields.

    """
    def filter_by_fields(self, data):
        """Extract a request parameter 'fields' if it exists to permit the
           filtering on the data dict's keys.

           If such field is not provided, returns the data as is.

        """
        fields = request.args.get('fields')
        if fields:
            fields = set(fields.split(','))
            data = utils.filter_field_keys(data, fields)

        return data


class YAMLRenderer(renderers.BaseRenderer, SWHFilterEnricher):
    """Renderer for application/yaml.
    Orchestrate from python data structure to yaml.

    """
    media_type = 'application/yaml'

    def render(self, data, media_type, **options):
        data = self.filter_by_fields(data)
        return yaml.dump(data, encoding=self.charset)


class JSONPEnricher():
    """JSONP rendering.

    """
    def enrich_with_jsonp(self, data):
        """Defines a jsonp function that extracts a potential 'callback'
           request parameter holding the function name and wraps the data
           inside a call to such function

           e.g:
           GET /blah/foo/bar renders: {'output': 'wrapped'}
           GET /blah/foo/bar?callback=fn renders: fn({'output': 'wrapped'})
        """
        jsonp = request.args.get('callback')
        if jsonp:
            return '%s(%s)' % (jsonp, data)

        return data


class SWHJSONRenderer(renderers.JSONRenderer,
                      SWHFilterEnricher,
                      JSONPEnricher):
    """Renderer for application/json.
    Serializes in json the data and returns it.

    Also deals with jsonp.  If callback is found in request parameter,
    wrap the result as a function with name the value of the parameter
    query 'callback'.

    """
    def render(self, data, media_type, **options):
        data = self.filter_by_fields(data)
        res = super().render(data, media_type, **options)
        return self.enrich_with_jsonp(res)


class SWHMultiResponse(Response, SWHFilterEnricher):
    """
    A Flask Response subclass.
    Override force_type to transform dict responses into callable Flask
    response objects whose mimetype matches the request's Accept header: HTML
    template render, YAML dump or default to a JSON dump.
    """

    @classmethod
    def make_response_from_mimetype(cls, rv):

        def wants_html(best_match):
            return best_match == 'text/html' and \
                request.accept_mimetypes[best_match] > \
                request.accept_mimetypes['application/json']

        def wants_yaml(best_match):
            return best_match == 'application/yaml' and \
                request.accept_mimetypes[best_match] > \
                request.accept_mimetypes['application/json']

        if isinstance(rv, dict) or isinstance(rv, list):
            rv = cls.filter_by_fields(cls, rv)
            acc_mime = ['application/json', 'application/yaml', 'text/html']
            best_match = request.accept_mimetypes.best_match(acc_mime)
            # return a template render
            if wants_html(best_match):
                data = json.dumps(rv, sort_keys=True,
                                  indent=4, separators=(',', ': '))
                env = g.get('doc_env', {})
                env['response_data'] = data
                env['request'] = request
                rv = Response(render_template('apidoc.html', **env),
                              content_type='text/html')
            # return formatted yaml
            elif wants_yaml(best_match):
                rv = Response(
                    yaml.dump(rv),
                    content_type='application/yaml')
            # return formatted json
            else:
                # jsonify is unhappy with lists in Flask 0.10.1, use json.dumps
                rv = Response(
                    json.dumps(rv),
                    content_type='application/json')
        return rv

    @classmethod
    def force_type(cls, rv, environ=None):
        # Data from apidoc
        if isinstance(rv, dict) or isinstance(rv, list):
            rv = cls.make_response_from_mimetype(rv)
        return super().force_type(rv, environ)


def urlize_api_links(content):
    """Utility function for decorating api links in browsable api."""
    return re.sub(r'"(/api/.*|/browse/.*)"', r'"<a href="\1">\1</a>"', content)


class NoHeaderHTMLTranslator(HTMLTranslator):
    """
    Docutils translator subclass to customize the generation of HTML
    from reST-formatted docstrings
    """
    def __init__(self, document):
        super().__init__(document)
        self.body_prefix = []
        self.body_suffix = []

    # disable blockquotes to ignore indentation issue with docstrings
    def visit_block_quote(self, node):
        pass

    def depart_block_quote(self, node):
        pass

    def visit_bullet_list(self, node):
        self.context.append((self.compact_simple, self.compact_p))
        self.compact_p = None
        self.compact_simple = self.is_compactable(node)
        self.body.append(self.starttag(node, 'ul', CLASS='docstring'))

DOCSTRING_WRITER = Writer()
DOCSTRING_WRITER.translator_class = NoHeaderHTMLTranslator


def safe_docstring_display(docstring):
    """
    Utility function to htmlize reST-formatted documentation in browsable
    api.
    """
    return publish_parts(docstring, writer=DOCSTRING_WRITER)['html_body']


def revision_id_from_url(url):
    """Utility function to obtain a revision's ID from its browsing URL."""
    return re.sub(r'/browse/revision/([0-9a-f]{40}|[0-9a-f]{64})/.*',
                  r'\1', url)


class SWHBrowsableAPIRenderer(renderers.BrowsableAPIRenderer):
    """SWH's browsable api renderer.

    """
    template = "api.html"


RENDERERS = [
    'swh.web.ui.renderers.SWHJSONRenderer',
    'swh.web.ui.renderers.SWHBrowsableAPIRenderer',
    'flask.ext.api.parsers.URLEncodedParser',
    'swh.web.ui.renderers.YAMLRenderer',
]


RENDERERS_INSTANCE = [
    SWHJSONRenderer(),
    SWHBrowsableAPIRenderer(),
    parsers.URLEncodedParser(),
    YAMLRenderer(),
]


RENDERERS_BY_TYPE = {
    r.media_type: r
    for r in RENDERERS_INSTANCE
}


def error_response(default_error_msg, error_code, error):
    """Private function to create a custom error response.

    """
    # if nothing is requested by client, use json
    default_application_type = 'application/json'
    accept_type = request.headers.get('Accept', default_application_type)
    renderer = RENDERERS_BY_TYPE.get(
        accept_type,
        RENDERERS_BY_TYPE[default_application_type])

    # for edge cases, use the elected renderer's media type
    accept_type = renderer.media_type
    response = make_response(default_error_msg, error_code)
    response.headers['Content-Type'] = accept_type
    response.data = renderer.render({"error": str(error)},
                                    media_type=MediaType(accept_type),
                                    status=error_code,
                                    headers={'Content-Type': accept_type})

    return response
