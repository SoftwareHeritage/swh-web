# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import unittest
import yaml

from flask import Response
from flask_api.mediatypes import MediaType
from nose.tools import istest
from unittest.mock import patch, MagicMock

from swh.web.ui import renderers


class RendererTestCase(unittest.TestCase):

    @patch('swh.web.ui.renderers.g')
    @patch('swh.web.ui.renderers.json')
    @patch('swh.web.ui.renderers.request')
    @patch('swh.web.ui.renderers.render_template')
    @patch('swh.web.ui.renderers.SWHMultiResponse.filter_by_fields')
    @istest
    def swh_multi_response_mimetype_html(self, mock_filter, mock_render,
                                         mock_request, mock_json, mock_g):
        # given
        data = {'data': [12, 34],
                'id': 'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'}
        mock_g.get.return_value = {'my_key': 'my_display_value'}
        mock_filter.return_value = data
        expected_env = {
            'my_key': 'my_display_value',
            'response_data': json.dumps(data),
            'request': mock_request
        }

        def mock_mimetypes(key):
            mimetypes = {
                'text/html': 10,
                'application/json': 0.1,
                'application/yaml': 0.1
            }
            return mimetypes[key]
        accept_mimetypes = MagicMock()
        accept_mimetypes.__getitem__.side_effect = mock_mimetypes
        accept_mimetypes.best_match = MagicMock(return_value='text/html')
        mock_request.accept_mimetypes = accept_mimetypes
        mock_json.dumps.return_value = json.dumps(data)

        # when
        rv = renderers.SWHMultiResponse.make_response_from_mimetype(data)

        # then
        mock_filter.assert_called_once_with(renderers.SWHMultiResponse, data)
        mock_render.assert_called_with('apidoc.html', **expected_env)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.mimetype, 'text/html')

    @patch('swh.web.ui.renderers.g')
    @patch('swh.web.ui.renderers.yaml')
    @patch('swh.web.ui.renderers.request')
    @patch('swh.web.ui.renderers.SWHMultiResponse.filter_by_fields')
    @istest
    def swh_multi_response_mimetype_yaml(self, mock_filter,
                                         mock_request, mock_yaml, mock_g):
        # given
        data = {'data': [12, 34],
                'id': 'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'}

        def mock_mimetypes(key):
            mimetypes = {
                'application/yaml': 10,
                'application/json': 0.1,
                'text/html': 0.1
            }
            return mimetypes[key]
        accept_mimetypes = MagicMock()
        accept_mimetypes.__getitem__.side_effect = mock_mimetypes
        accept_mimetypes.best_match = MagicMock(
            return_value='application/yaml')
        mock_request.accept_mimetypes = accept_mimetypes
        mock_yaml.dump.return_value = yaml.dump(data)
        mock_filter.return_value = data

        # when
        rv = renderers.SWHMultiResponse.make_response_from_mimetype(data)

        # then
        mock_filter.assert_called_once_with(renderers.SWHMultiResponse, data)
        mock_yaml.dump.assert_called_once_with(data)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.mimetype, 'application/yaml')
        self.assertEqual(data, yaml.load(rv.data.decode('utf-8')))

    @patch('swh.web.ui.renderers.g')
    @patch('swh.web.ui.renderers.json')
    @patch('swh.web.ui.renderers.request')
    @patch('swh.web.ui.renderers.SWHMultiResponse.filter_by_fields')
    @istest
    def swh_multi_response_mimetype_json(self, mock_filter,
                                         mock_request, mock_json, mock_g):
        # given
        data = {'data': [12, 34],
                'id': 'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'}

        def mock_mimetypes(key):
            mimetypes = {
                'application/json': 10,
                'text/html': 0.1,
                'application/yaml': 0.1
            }
            return mimetypes[key]
        accept_mimetypes = MagicMock()
        accept_mimetypes.__getitem__.side_effect = mock_mimetypes
        accept_mimetypes.best_match = MagicMock(
            return_value='application/json')
        mock_request.accept_mimetypes = accept_mimetypes
        mock_json.dumps.return_value = json.dumps(data)
        mock_filter.return_value = data

        # when
        rv = renderers.SWHMultiResponse.make_response_from_mimetype(data)

        # then
        mock_filter.assert_called_once_with(renderers.SWHMultiResponse, data)
        mock_json.dumps.assert_called_once_with(data)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.mimetype, 'application/json')
        self.assertEqual(data, json.loads(rv.data.decode('utf-8')))

    @istest
    def apidoc_make_response_not_list_dict(self):
        # given
        incoming = Response()

        # when
        rv = renderers.SWHMultiResponse.make_response_from_mimetype(incoming)

        # then
        self.assertEqual(rv, incoming)

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

        # update /browse link with html links content with links
        content = '{"url": "/browse/def/"}'
        expected_content = '{"url": "<a href=\"/browse/def/\">' \
                           '/browse/def/</a>"}'

        self.assertEquals(renderers.urlize_api_links(content),
                          expected_content)

        # will do nothing since it's not an api url
        other_content = '{"url": "/something/api/1/other"}'
        self.assertEquals(renderers.urlize_api_links(other_content),
                          other_content)

    @istest
    def revision_id_from_url(self):
        url = ('/browse/revision/9ba4bcb645898d562498ea66a0df958ef0e7a68c/'
               'prev/9ba4bcb645898d562498ea66a0df958ef0e7aaaa/')

        expected_id = '9ba4bcb645898d562498ea66a0df958ef0e7a68c'
        self.assertEqual(renderers.revision_id_from_url(url), expected_id)

    @istest
    def safe_docstring_display(self):
        # update api link with html links content with links
        docstring = """This is my list header:

         - Here is item 1, with a continuation
           line right here
         - Here is item 2

        Here is something that is not part of the list"""

        expected_docstring = """<p>This is my list header:</p>
<ul class="docstring">
<li>Here is item 1, with a continuation
line right here</li>
<li>Here is item 2</li>
</ul>
<p>Here is something that is not part of the list</p>
"""

        self.assertEquals(renderers.safe_docstring_display(docstring),
                          expected_docstring)
