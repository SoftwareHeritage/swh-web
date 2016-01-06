# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import unittest
import yaml

from flask_api.mediatypes import MediaType
from nose.tools import istest
from unittest.mock import patch

from swh.web.ui import renderers


class RendererTestCase(unittest.TestCase):

    @patch('swh.web.ui.renderers.request')
    @istest
    def swh_filter_renderer_do_nothing(self, mock_request):
        # given
        mock_request.args = {}

        swh_filter_renderer = renderers.SWHFilterEnricher()

        input_data = {'a': 'some-data'}

        # when
        actual_data = swh_filter_renderer.filter_by_fields(input_data)

        # then
        self.assertEquals(actual_data, input_data)

    @patch('swh.web.ui.renderers.utils')
    @patch('swh.web.ui.renderers.request')
    @istest
    def swh_filter_renderer_do_filter(self, mock_request, mock_utils):
        # given
        mock_request.args = {'fields': 'a,c'}
        mock_utils.filter_field_keys.return_value = {'a': 'some-data'}

        swh_filter_renderer = renderers.SWHFilterEnricher()

        input_data = {'a': 'some-data',
                      'b': 'some-other-data'}

        # when
        actual_data = swh_filter_renderer.filter_by_fields(input_data)

        # then
        self.assertEquals(actual_data, {'a': 'some-data'})

        mock_utils.filter_field_keys.assert_called_once_with(input_data,
                                                             {'a', 'c'})

    @patch('swh.web.ui.renderers.request')
    @istest
    def yaml_renderer_without_filter(self, mock_request):
        # given
        mock_request.args = {}
        yaml_renderer = renderers.YAMLRenderer()

        input_data = {'target': 'sha1-dir',
                      'type': 'dir',
                      'dir-id': 'dir-id-sha1-git'}

        expected_data = input_data

        # when
        actual_data = yaml_renderer.render(input_data, 'application/yaml')

        # then
        self.assertEqual(yaml.load(actual_data), expected_data)

    @patch('swh.web.ui.renderers.request')
    @istest
    def yaml_renderer(self, mock_request):
        # given
        mock_request.args = {'fields': 'type,target'}
        yaml_renderer = renderers.YAMLRenderer()

        input_data = {'target': 'sha1-dir',
                      'type': 'dir',
                      'dir-id': 'dir-id-sha1-git'}

        expected_data = {'target': 'sha1-dir', 'type': 'dir'}

        # when
        actual_data = yaml_renderer.render(input_data, 'application/yaml')

        # then
        self.assertEqual(yaml.load(actual_data), expected_data)

    @patch('swh.web.ui.renderers.request')
    @istest
    def json_renderer_basic(self, mock_request):
        # given
        mock_request.args = {}
        json_renderer = renderers.SWHJSONRenderer()

        input_data = {'target': 'sha1-dir',
                      'type': 'dir',
                      'dir-id': 'dir-id-sha1-git'}

        expected_data = input_data

        # when
        actual_data = json_renderer.render(input_data, MediaType(
            'application/json'))

        # then
        self.assertEqual(json.loads(actual_data), expected_data)

    @patch('swh.web.ui.renderers.request')
    @istest
    def json_renderer_basic_with_filter(self, mock_request):
        # given
        mock_request.args = {'fields': 'target'}
        json_renderer = renderers.SWHJSONRenderer()

        input_data = {'target': 'sha1-dir',
                      'type': 'dir',
                      'dir-id': 'dir-id-sha1-git'}

        expected_data = {'target': 'sha1-dir'}

        # when
        actual_data = json_renderer.render(input_data, MediaType(
            'application/json'))

        # then
        self.assertEqual(json.loads(actual_data), expected_data)

    @patch('swh.web.ui.renderers.request')
    @istest
    def json_renderer_basic_with_filter_and_jsonp(self, mock_request):
        # given
        mock_request.args = {'fields': 'target',
                             'callback': 'jsonpfn'}
        json_renderer = renderers.SWHJSONRenderer()

        input_data = {'target': 'sha1-dir',
                      'type': 'dir',
                      'dir-id': 'dir-id-sha1-git'}

        # when
        actual_data = json_renderer.render(input_data, MediaType(
            'application/json'))

        # then
        self.assertEqual(actual_data, 'jsonpfn({"target": "sha1-dir"})')

    @patch('swh.web.ui.renderers.request')
    @istest
    def jsonp_enricher_basic_with_filter_and_jsonp(self, mock_request):
        # given
        mock_request.args = {'callback': 'jsonpfn'}
        jsonp_enricher = renderers.JSONPEnricher()

        # when
        actual_output = jsonp_enricher.enrich_with_jsonp({'output': 'test'})

        # then
        self.assertEqual(actual_output, "jsonpfn({'output': 'test'})")

    @patch('swh.web.ui.renderers.request')
    @istest
    def jsonp_enricher_do_nothing(self, mock_request):
        # given
        mock_request.args = {}
        jsonp_enricher = renderers.JSONPEnricher()

        # when
        actual_output = jsonp_enricher.enrich_with_jsonp({'output': 'test'})

        # then
        self.assertEqual(actual_output, {'output': 'test'})

    @istest
    def urlize_api_links(self):
        # update api link with html links content with links
        content = '{"url": "/api/1/abc/"}'
        expected_content = '{"url": "<a href=\"/api/1/abc/\">/api/1/abc/</a>"}'

        self.assertEquals(renderers.urlize_api_links(content),
                          expected_content)

        # will do nothing since it's not an api url
        other_content = '{"url": "/something/api/1/other"}'
        self.assertEquals(renderers.urlize_api_links(other_content),
                          other_content)

    @istest
    def safe_docstring_display(self):
        # update api link with html links content with links
        docstring = """<p>Show all revisions (~git log) starting from
sha1_git.
   The first element returned is the given sha1_git.</p>
<p>Args:
    sha1_git: the revision's hash</p>
<p>Returns:
    Information on the revision if found.</p>
<p>Raises:
    BadInputExc in case of unknown algo_hash or bad hash
    NotFoundExc if the revision is not found.</p>"""
        expected_docstring = """<p>Show all revisions (~git log) starting from
sha1_git.
   The first element returned is the given sha1_git.</p>
<p><strong>Args:</strong><br />&nbsp;&nbsp;
    sha1_git: the revision's hash</p>
<p><strong>Returns:</strong><br />&nbsp;&nbsp;
    Information on the revision if found.</p>
<p><strong>Raises:</strong><br />&nbsp;&nbsp;
    BadInputExc in case of unknown algo_hash or bad hash
    NotFoundExc if the revision is not found.</p>"""

        self.assertEquals(renderers.safe_docstring_display(docstring),
                          expected_docstring)
