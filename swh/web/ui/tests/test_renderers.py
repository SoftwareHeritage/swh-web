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
    def SWHFilterRenderer_do_nothing(self, mock_request):
        # given
        mock_request.args = {}

        swhFilterRenderer = renderers.SWHFilterEnricher()

        input_data = {'a': 'some-data'}

        # when
        actual_data = swhFilterRenderer.filter_by_fields(input_data)

        # then
        self.assertEquals(actual_data, input_data)

    @patch('swh.web.ui.renderers.utils')
    @patch('swh.web.ui.renderers.request')
    @istest
    def SWHFilterRenderer_do_filter(self, mock_request, mock_utils):
        # given
        mock_request.args = {'fields': 'a,c'}
        mock_utils.filter_field_keys.return_value = {'a': 'some-data'}

        swhFilterRenderer = renderers.SWHFilterEnricher()

        input_data = {'a': 'some-data',
                      'b': 'some-other-data'}

        # when
        actual_data = swhFilterRenderer.filter_by_fields(input_data)

        # then
        self.assertEquals(actual_data, {'a': 'some-data'})

        mock_utils.filter_field_keys.assert_called_once_with(input_data,
                                                             {'a', 'c'})

    @istest
    def doNothingRenderer(self):
        # given
        doNothingRenderer = renderers.DoNothingRenderer()
        input_data = 'some data'

        # when
        actual_data = doNothingRenderer.render(input_data, 'some-media-type')

        # then
        self.assertEqual(actual_data, input_data)  # do nothing on data

    @istest
    def plainRenderer(self):
        # given
        plainRenderer = renderers.PlainRenderer()
        input_data = 'some data'

        # when
        actual_data = plainRenderer.render(input_data, 'some-media-type')

        # then
        self.assertEqual(actual_data, input_data)  # do nothing on data

    @istest
    def bytesRenderer(self):
        # given
        bytesRenderer = renderers.BytesRenderer()
        input_data = b'some data'

        # when
        actual_data = bytesRenderer.render(input_data, 'some-media-type')

        # then
        self.assertEqual('application/octet-stream', bytesRenderer.media_type)
        self.assertEqual(actual_data, input_data)  # do nothing on data

    @patch('swh.web.ui.renderers.request')
    @istest
    def yamlRenderer_without_filter(self, mock_request):
        # given
        mock_request.args = {}
        yamlRenderer = renderers.YAMLRenderer()

        input_data = {'target': 'sha1-dir',
                      'type': 'dir',
                      'dir-id': 'dir-id-sha1-git'}

        expected_data = input_data

        # when
        actual_data = yamlRenderer.render(input_data, 'application/yaml')

        # then
        self.assertEqual(yaml.load(actual_data), expected_data)

    @patch('swh.web.ui.renderers.request')
    @istest
    def yamlRenderer(self, mock_request):
        # given
        mock_request.args = {'fields': 'type,target'}
        yamlRenderer = renderers.YAMLRenderer()

        input_data = {'target': 'sha1-dir',
                      'type': 'dir',
                      'dir-id': 'dir-id-sha1-git'}

        expected_data = {'target': 'sha1-dir', 'type': 'dir'}

        # when
        actual_data = yamlRenderer.render(input_data, 'application/yaml')

        # then
        self.assertEqual(yaml.load(actual_data), expected_data)

    @patch('swh.web.ui.renderers.request')
    @istest
    def jsonRenderer_basic(self, mock_request):
        # given
        mock_request.args = {}
        jsonRenderer = renderers.SWHJSONRenderer()

        input_data = {'target': 'sha1-dir',
                      'type': 'dir',
                      'dir-id': 'dir-id-sha1-git'}

        expected_data = input_data

        # when
        actual_data = jsonRenderer.render(input_data, MediaType(
            'application/json'))

        # then
        self.assertEqual(json.loads(actual_data), expected_data)

    @patch('swh.web.ui.renderers.request')
    @istest
    def jsonRenderer_basic_with_filter(self, mock_request):
        # given
        mock_request.args = {'fields': 'target'}
        jsonRenderer = renderers.SWHJSONRenderer()

        input_data = {'target': 'sha1-dir',
                      'type': 'dir',
                      'dir-id': 'dir-id-sha1-git'}

        expected_data = {'target': 'sha1-dir'}

        # when
        actual_data = jsonRenderer.render(input_data, MediaType(
            'application/json'))

        # then
        self.assertEqual(json.loads(actual_data), expected_data)

    @patch('swh.web.ui.renderers.request')
    @istest
    def jsonRenderer_basic_with_filter_and_jsonp(self, mock_request):
        # given
        mock_request.args = {'fields': 'target',
                             'callback': 'jsonpfn'}
        jsonRenderer = renderers.SWHJSONRenderer()

        input_data = {'target': 'sha1-dir',
                      'type': 'dir',
                      'dir-id': 'dir-id-sha1-git'}

        # when
        actual_data = jsonRenderer.render(input_data, MediaType(
            'application/json'))

        # then
        self.assertEqual(actual_data, 'jsonpfn({"target": "sha1-dir"})')

    @patch('swh.web.ui.renderers.request')
    @istest
    def jsonpEnricher_basic_with_filter_and_jsonp(self, mock_request):
        # given
        mock_request.args = {'callback': 'jsonpfn'}
        jsonpEnricher = renderers.JSONPEnricher()

        # when
        actual_output = jsonpEnricher.enrich_with_jsonp({'output': 'test'})

        # then
        self.assertEqual(actual_output, "jsonpfn({'output': 'test'})")

    @patch('swh.web.ui.renderers.request')
    @istest
    def jsonpEnricher_do_nothing(self, mock_request):
        # given
        mock_request.args = {}
        jsonpEnricher = renderers.JSONPEnricher()

        # when
        actual_output = jsonpEnricher.enrich_with_jsonp({'output': 'test'})

        # then
        self.assertEqual(actual_output, {'output': 'test'})
