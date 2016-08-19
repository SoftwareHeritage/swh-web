# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re
import yaml
import json
import sys

from docutils.core import publish_parts
from docutils.writers.html4css1 import Writer, HTMLTranslator

from flask import request, Response, render_template
from flask import g

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


class SWHMultiResponse(Response, SWHFilterEnricher):
    """
    A Flask Response subclass.
    Override force_type to transform dict responses into callable Flask
    response objects whose mimetype matches the request's Accept header: HTML
    template render, YAML dump or default to a JSON dump.
    """

    @classmethod
    def make_response_from_mimetype(cls, rv, options={}):
        if not (isinstance(rv, list) or isinstance(rv, dict)):
            return rv

        def wants_html(best_match):
            return best_match == 'text/html' and \
                request.accept_mimetypes[best_match] > \
                request.accept_mimetypes['application/json']

        def wants_yaml(best_match):
            return best_match == 'application/yaml' and \
                request.accept_mimetypes[best_match] > \
                request.accept_mimetypes['application/json']

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
                          content_type='text/html',
                          **options)
        # return formatted yaml
        elif wants_yaml(best_match):
            rv = Response(
                yaml.dump(rv),
                content_type='application/yaml',
                **options)
        # return formatted json
        else:
            # jsonify is unhappy with lists in Flask 0.10.1, use json.dumps
            rv = Response(
                json.dumps(rv),
                content_type='application/json',
                **options)
        return rv

    @classmethod
    def force_type(cls, rv, environ=None):
        if isinstance(rv, dict) or isinstance(rv, list):
            rv = cls.make_response_from_mimetype(rv)
        return super().force_type(rv, environ)


def error_response(error_code, error):
    """Private function to create a custom error response.

    """
    error_opts = {'status': error_code}
    error_data = {'error': str(error)}

    return SWHMultiResponse.make_response_from_mimetype(error_data,
                                                        options=error_opts)


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

    def trim(docstring):
        """Correctly trim triple-quoted docstrings, taking into account
        first-line indentation inconsistency.
        Source: https://www.python.org/dev/peps/pep-0257/#handling-docstring-indentation  # noqa
        """
        if not docstring:
            return ''
        lines = docstring.expandtabs().splitlines()
        indent = sys.maxsize
        for line in lines[1:]:
            stripped = line.lstrip()
            if stripped:
                indent = min(indent, len(line) - len(stripped))
        trimmed = [lines[0].strip()]
        if indent < sys.maxsize:
            for line in lines[1:]:
                trimmed.append(line[indent:].rstrip())
        while trimmed and not trimmed[-1]:
            trimmed.pop()
        while trimmed and not trimmed[0]:
            trimmed.pop(0)
        return '\n'.join(trimmed)

    docstring = trim(docstring)
    return publish_parts(docstring, writer=DOCSTRING_WRITER)['html_body']


def revision_id_from_url(url):
    """Utility function to obtain a revision's ID from its browsing URL."""
    return re.sub(r'/browse/revision/([0-9a-f]{40}|[0-9a-f]{64})/.*',
                  r'\1', url)
