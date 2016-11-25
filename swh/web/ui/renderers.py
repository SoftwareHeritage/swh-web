# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re
import yaml
import json

from docutils.core import publish_parts
from docutils.writers.html4css1 import Writer, HTMLTranslator
from inspect import cleandoc
from jinja2 import Markup
from flask import request, Response, render_template
from flask import g
from pygments import highlight
from pygments.lexers import guess_lexer
from pygments.formatters import HtmlFormatter

from swh.web.ui import utils


class SWHFilterEnricher():
    """Global filter on fields.

    """
    @classmethod
    def filter_by_fields(cls, data):
        """Extract a request parameter 'fields' if it exists to permit the
           filtering on the data dict's keys.

           If such field is not provided, returns the data as is.

        """
        fields = request.args.get('fields')
        if fields:
            fields = set(fields.split(','))
            data = utils.filter_field_keys(data, fields)

        return data


class SWHAddLinkHeaderEnricher:
    """Add link header to response.

    Mixin intended to be used for example in SWHMultiResponse

    """
    @classmethod
    def add_link_header(cls, rv, options):
        """Add Link header in returned value results.

        Args:
            rv (dict): with keys:
                - 'headers': potential headers with 'link-next'
                  and 'link-prev' keys
                - 'results': containing the result to return

        Returns:
            tuple rv, options:

            If link-headers are present, rv is the returned value
            present in the 'results' key. Also, options is updated
            with headers 'Link' containing the 'link-next' and
            'link-prev' headers.

            Otherwise, rv, options stays the same as the input.

        """
        link_headers = []

        if 'headers' not in rv:
            return rv, options

        rv_headers = rv['headers']

        if 'link-next' in rv_headers:
            link_headers.append('<%s>; rel="next"' % (
                rv_headers['link-next']))
        if 'link-prev' in rv_headers:
            link_headers.append('<%s>; rel="previous"' % (
                rv_headers['link-prev']))

        if link_headers:
            link_header_str = ','.join(link_headers)
            headers = options.get('headers', {})
            headers.update({
                'Link': link_header_str
            })
            options['headers'] = headers
            rv.pop('headers')
            return rv['results'], options

        return rv, options


class SWHMultiResponse(Response, SWHFilterEnricher, SWHAddLinkHeaderEnricher):
    """
    A Flask Response subclass.
    Override force_type to transform dict/list responses into callable Flask
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

        rv = cls.filter_by_fields(rv)
        acc_mime = ['application/json', 'application/yaml', 'text/html']
        best_match = request.accept_mimetypes.best_match(acc_mime)

        rv, options = cls.add_link_header(rv, options)

        if wants_html(best_match):
            data = json.dumps(rv, sort_keys=True,
                              indent=4, separators=(',', ': '))
            env = g.get('doc_env', {})
            env['response_data'] = data
            env['request'] = request
            rv = Response(render_template('apidoc.html', **env),
                          content_type='text/html',
                          **options)
        elif wants_yaml(best_match):
            rv = Response(
                yaml.dump(rv),
                content_type='application/yaml',
                **options)
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
    docstring = cleandoc(docstring)
    return publish_parts(docstring, writer=DOCSTRING_WRITER)['html_body']


def revision_id_from_url(url):
    """Utility function to obtain a revision's ID from its browsing URL."""
    return re.sub(r'/browse/revision/([0-9a-f]{40}|[0-9a-f]{64})/.*',
                  r'\1', url)


def highlight_source(source_code_as_text):
    """Leverage pygments to guess and highlight source code.

    Args
        source_code_as_text (str): source code in plain text

    Returns:
        Highlighted text if possible or plain text otherwise

    """
    try:
        maybe_lexer = guess_lexer(source_code_as_text)
        if maybe_lexer:
            r = highlight(
                source_code_as_text, maybe_lexer,
                HtmlFormatter(linenos=True,
                              lineanchors='l',
                              anchorlinenos=True))
        else:
            r = '<pre>%s</pre>' % source_code_as_text
    except:
        r = '<pre>%s</pre>' % source_code_as_text

    return Markup(r)
