# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import docutils.nodes
import docutils.parsers.rst
import docutils.utils
import functools
import os
import re
import textwrap

from functools import wraps
from rest_framework.decorators import api_view

from swh.web.common.utils import parse_rst
from swh.web.api.apiurls import APIUrls
from swh.web.api.apiresponse import make_api_response, error_response


class _HTTPDomainDocVisitor(docutils.nodes.NodeVisitor):
    """
    docutils visitor for walking on a parsed rst document containing sphinx
    httpdomain roles. Its purpose is to extract relevant info regarding swh
    api endpoints (for instance url arguments) from their docstring written
    using sphinx httpdomain.
    """

    # httpdomain roles we want to parse (based on sphinxcontrib.httpdomain 1.6)
    parameter_roles = ('param', 'parameter', 'arg', 'argument')

    response_json_object_roles = ('resjsonobj', 'resjson', '>jsonobj', '>json')

    response_json_array_roles = ('resjsonarr', '>jsonarr')

    query_parameter_roles = ('queryparameter', 'queryparam', 'qparam', 'query')

    request_header_roles = ('<header', 'reqheader', 'requestheader')

    response_header_roles = ('>header', 'resheader', 'responseheader')

    status_code_roles = ('statuscode', 'status', 'code')

    def __init__(self, document, urls, data):
        super().__init__(document)
        self.urls = urls
        self.url_idx = 0
        self.data = data
        self.args_set = set()
        self.params_set = set()
        self.returns_set = set()
        self.status_codes_set = set()
        self.reqheaders_set = set()
        self.resheaders_set = set()
        self.field_list_visited = False

    def process_paragraph(self, par):
        """
        Process extracted paragraph text before display.
        Cleanup document model markups and transform the
        paragraph into a valid raw rst string (as the apidoc
        documentation transform rst to html when rendering).
        """
        par = par.replace('\n', ' ')
        # keep emphasized, strong and literal text
        par = par.replace('<emphasis>', '*')
        par = par.replace('</emphasis>', '*')
        par = par.replace('<strong>', '**')
        par = par.replace('</strong>', '**')
        par = par.replace('<literal>', '``')
        par = par.replace('</literal>', '``')
        # remove parsed document markups
        par = re.sub('<[^<]+?>', '', par)
        # api urls cleanup to generate valid links afterwards
        par = re.sub('\(\w+\)', '', par) # noqa
        par = re.sub('\[.*\]', '', par) # noqa
        par = par.replace('//', '/')
        # transform references to api endpoints into valid rst links
        par = re.sub(':http:get:`(.*)`', r'`<\1>`_', par)
        # transform references to some elements into bold text
        par = re.sub(':http:header:`(.*)`', r'**\1**', par)
        par = re.sub(':func:`(.*)`', r'**\1**', par)
        return par

    def visit_field_list(self, node):
        """
        Visit parsed rst field lists to extract relevant info
        regarding api endpoint.
        """
        self.field_list_visited = True
        for child in node.traverse():
            # get the parsed field name
            if isinstance(child, docutils.nodes.field_name):
                field_name = child.astext()
            # parse field text
            elif isinstance(child, docutils.nodes.paragraph):
                text = self.process_paragraph(str(child))
                field_data = field_name.split(' ')
                # Parameters
                if field_data[0] in self.parameter_roles:
                    if field_data[2] not in self.args_set:
                        self.data['args'].append({'name': field_data[2],
                                                  'type': field_data[1],
                                                  'doc': text})
                        self.args_set.add(field_data[2])
                # Query Parameters
                if field_data[0] in self.query_parameter_roles:
                    if field_data[2] not in self.params_set:
                        self.data['params'].append({'name': field_data[2],
                                                    'type': field_data[1],
                                                    'doc': text})
                        self.params_set.add(field_data[2])
                # Response type
                if field_data[0] in self.response_json_array_roles or \
                        field_data[0] in self.response_json_object_roles:
                    # array
                    if field_data[0] in self.response_json_array_roles:
                        self.data['return_type'] = 'array'
                    # object
                    else:
                        self.data['return_type'] = 'object'
                    # returned object field
                    if field_data[2] not in self.returns_set:
                        self.data['returns'].append({'name': field_data[2],
                                                     'type': field_data[1],
                                                     'doc': text})
                        self.returns_set.add(field_data[2])
                # Status Codes
                if field_data[0] in self.status_code_roles:
                    if field_data[1] not in self.status_codes_set:
                        self.data['status_codes'].append({'code': field_data[1], # noqa
                                                          'doc': text})
                        self.status_codes_set.add(field_data[1])
                # Request Headers
                if field_data[0] in self.request_header_roles:
                    if field_data[1] not in self.reqheaders_set:
                        self.data['reqheaders'].append({'name': field_data[1],
                                                        'doc': text})
                        self.reqheaders_set.add(field_data[1])
                # Response Headers
                if field_data[0] in self.response_header_roles:
                    if field_data[1] not in self.resheaders_set:
                        resheader = {'name': field_data[1],
                                     'doc': text}
                        self.data['resheaders'].append(resheader)
                        self.resheaders_set.add(field_data[1])
                        if resheader['name'] == 'Content-Type' and \
                                resheader['doc'] == 'application/octet-stream':
                            self.data['return_type'] = 'octet stream'

    def visit_paragraph(self, node):
        """
        Visit relevant paragraphs to parse
        """
        # only parsed top level paragraphs
        if isinstance(node.parent, docutils.nodes.block_quote):
            text = self.process_paragraph(str(node))
            # endpoint description
            if not text.startswith('**') and self.data['description'] != text:
                self.data['description'] += '\n\n' if self.data['description'] else '' # noqa
                self.data['description'] += text
            # http methods
            elif text.startswith('**Allowed HTTP Methods:**'):
                text = text.replace('**Allowed HTTP Methods:**', '')
                http_methods = text.strip().split(',')
                http_methods = [m[m.find('`')+1:-1].upper()
                                for m in http_methods]
                self.data['urls'].append({'rule': self.urls[self.url_idx],
                                          'methods': http_methods})
                self.url_idx += 1

    def visit_literal_block(self, node):
        """
        Visit literal blocks
        """
        text = node.astext()
        # literal block in endpoint description
        if not self.field_list_visited:
            self.data['description'] += \
                ':\n\n%s\n' % textwrap.indent(text, '\t')
        # extract example url
        if ':swh_web_api:' in text:
            self.data['examples'].append(
                '/api/1/' + re.sub('.*`(.*)`.*', r'\1', text))

    def visit_bullet_list(self, node):
        # bullet list in endpoint description
        if not self.field_list_visited:
            self.data['description'] += '\n\n'
            for child in node.traverse():
                # process list item
                if isinstance(child, docutils.nodes.paragraph):
                    line_text = self.process_paragraph(str(child))
                    self.data['description'] += '\t* %s\n' % line_text

    def unknown_visit(self, node):
        pass

    def depart_document(self, node):
        """
        End of parsing extra processing
        """
        default_methods = ['GET', 'HEAD', 'OPTIONS']
        # ensure urls info is present and set default http methods
        if not self.data['urls']:
            for url in self.urls:
                self.data['urls'].append({'rule': url,
                                          'methods': default_methods})

    def unknown_departure(self, node):
        pass


def _parse_httpdomain_doc(doc, data):
    doc_lines = doc.split('\n')
    doc_lines_filtered = []
    urls = []
    # httpdomain is a sphinx extension that is unknown to docutils but
    # fortunately we can still parse its directives' content,
    # so remove lines with httpdomain directives before executing the
    # rst parser from docutils
    for doc_line in doc_lines:
        if '.. http' not in doc_line:
            doc_lines_filtered.append(doc_line)
        else:
            url = doc_line[doc_line.find('/'):]
            # emphasize url arguments for html rendering
            url = re.sub(r'\((\w+)\)', r' **\(\1\)** ', url)
            urls.append(url)
    # parse the rst docstring and do not print system messages about
    # unknown httpdomain roles
    document = parse_rst('\n'.join(doc_lines_filtered), report_level=5)
    # remove the system_message nodes from the parsed document
    for node in document.traverse(docutils.nodes.system_message):
        node.parent.remove(node)
    # visit the document nodes to extract relevant endpoint info
    visitor = _HTTPDomainDocVisitor(document, urls, data)
    document.walkabout(visitor)


class APIDocException(Exception):
    """
    Custom exception to signal errors in the use of the APIDoc decorators
    """


class api_doc(object):  # noqa: N801
    """
    Decorate an API function to register it in the API doc route index
    and create the corresponding DRF route.

    Args:
        route (str): documentation page's route
        noargs (boolean): set to True if the route has no arguments, and its
            result should be displayed anytime its documentation
            is requested. Default to False
        tags (list): Further information on api endpoints. Two values are
            possibly expected:

                * hidden: remove the entry points from the listing
                * upcoming: display the entry point but it is not followable

        handle_response (boolean): indicate if the decorated function takes
            care of creating the HTTP response or delegates that task to the
            apiresponse module
        api_version (str): api version string

    """
    def __init__(self, route, noargs=False, tags=[], handle_response=False,
                 api_version='1'):
        super().__init__()
        self.route = route
        self.urlpattern = '^' + api_version + route + '$'
        self.noargs = noargs
        self.tags = set(tags)
        self.handle_response = handle_response

    # @api_doc() Decorator call
    def __call__(self, f):

        # If the route is not hidden, add it to the index
        if 'hidden' not in self.tags:
            doc_data = self.get_doc_data(f)
            doc_desc = doc_data['description']
            first_dot_pos = doc_desc.find('.')
            APIUrls.add_route(self.route, doc_desc[:first_dot_pos+1],
                              tags=self.tags)

        # If the decorated route has arguments, we create a specific
        # documentation view
        if not self.noargs:

            @api_view(['GET', 'HEAD'])
            def doc_view(request):
                doc_data = self.get_doc_data(f)
                return make_api_response(request, None, doc_data)

            view_name = 'api-%s' % self.route[1:-1].replace('/', '-')
            APIUrls.add_url_pattern(self.urlpattern, doc_view, view_name)

        @wraps(f)
        def documented_view(request, **kwargs):
            doc_data = self.get_doc_data(f)

            try:
                response = f(request, **kwargs)
            except Exception as exc:
                return error_response(request, exc, doc_data)

            if self.handle_response:
                return response
            else:
                return make_api_response(request, response, doc_data)

        return documented_view

    @functools.lru_cache(maxsize=32)
    def get_doc_data(self, f):
        """
        Build documentation data for the decorated api endpoint function
        """
        data = {
            'description': '',
            'response_data': None,
            'urls': [],
            'args': [],
            'params': [],
            'resheaders': [],
            'reqheaders': [],
            'return_type': '',
            'returns': [],
            'status_codes': [],
            'examples': [],
            'route': self.route,
            'noargs': self.noargs
        }

        if not f.__doc__:
            raise APIDocException('apidoc %s: expected a docstring'
                                  ' for function %s'
                                  % (self.__class__.__name__, f.__name__))

        # use raw docstring as endpoint documentation if sphinx
        # httpdomain is not used
        if '.. http' not in f.__doc__:
            data['description'] = f.__doc__
        # else parse the sphinx httpdomain docstring with docutils
        # (except when building the swh-web documentation through autodoc
        # sphinx extension, not needed and raise errors with sphinx >= 1.7)
        elif 'SWH_WEB_DOC_BUILD' not in os.environ:
            _parse_httpdomain_doc(f.__doc__, data)
            # process returned object info for nicer html display
            returns_list = ''
            for ret in data['returns']:
                returns_list += '\t* **%s (%s)**: %s\n' %\
                    (ret['name'], ret['type'], ret['doc'])
            data['returns_list'] = returns_list

        return data
