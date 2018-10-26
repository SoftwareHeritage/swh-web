# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from rest_framework.test import APIRequestFactory

from unittest.mock import patch

from swh.web.api.apiresponse import (
    compute_link_header, transform, make_api_response,
    filter_by_fields
)
from swh.web.tests.testcase import SWHWebTestCase

api_request_factory = APIRequestFactory()


class SWHComputeLinkHeaderTest(SWHWebTestCase):
    def test_compute_link_header(self):
        rv = {
            'headers': {'link-next': 'foo', 'link-prev': 'bar'},
            'results': [1, 2, 3]
        }
        options = {}

        # when
        headers = compute_link_header(
            rv, options)

        self.assertEqual(headers, {
            'Link': '<foo>; rel="next",<bar>; rel="previous"',
        })

    def test_compute_link_header_nothing_changed(self):
        rv = {}
        options = {}

        # when
        headers = compute_link_header(
            rv, options)

        self.assertEqual(headers, {})

    def test_compute_link_header_nothing_changed_2(self):
        rv = {'headers': {}}
        options = {}

        # when
        headers = compute_link_header(
            rv, options)

        self.assertEqual(headers, {})


class SWHTransformProcessorTest(SWHWebTestCase):
    def test_transform_only_return_results_1(self):
        rv = {'results': {'some-key': 'some-value'}}

        self.assertEqual(transform(rv), {'some-key': 'some-value'})

    def test_transform_only_return_results_2(self):
        rv = {'headers': {'something': 'do changes'},
              'results': {'some-key': 'some-value'}}

        self.assertEqual(transform(rv), {'some-key': 'some-value'})

    def test_transform_do_remove_headers(self):
        rv = {'headers': {'something': 'do changes'},
              'some-key': 'some-value'}

        self.assertEqual(transform(rv), {'some-key': 'some-value'})

    def test_transform_do_nothing(self):
        rv = {'some-key': 'some-value'}

        self.assertEqual(transform(rv), {'some-key': 'some-value'})


class RendererTestCase(SWHWebTestCase):

    @patch('swh.web.api.apiresponse.json')
    @patch('swh.web.api.apiresponse.filter_by_fields')
    @patch('swh.web.api.apiresponse.shorten_path')
    def test_swh_multi_response_mimetype(self, mock_shorten_path,
                                         mock_filter, mock_json):
        # given
        data = {
            'data': [12, 34],
            'id': 'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'
        }

        mock_filter.return_value = data
        mock_shorten_path.return_value = 'my_short_path'

        accepted_response_formats = {'html': 'text/html',
                                     'yaml': 'application/yaml',
                                     'json': 'application/json'}

        for format in accepted_response_formats:

            request = api_request_factory.get('/api/test/path/')

            mime_type = accepted_response_formats[format]
            setattr(request, 'accepted_media_type', mime_type)

            if mime_type == 'text/html':

                expected_data = {
                    'response_data': json.dumps(data),
                    'request': {
                        'path': request.path,
                        'method': request.method,
                        'absolute_uri': request.build_absolute_uri()
                    },
                    'headers_data': {},
                    'heading': 'my_short_path',
                    'status_code': 200
                }

                mock_json.dumps.return_value = json.dumps(data)
            else:
                expected_data = data

            # when

            rv = make_api_response(request, data)

            # then
            mock_filter.assert_called_with(request, data)
            self.assertEqual(rv.data, expected_data)
            self.assertEqual(rv.status_code, 200)
            if mime_type == 'text/html':
                self.assertEqual(rv.template_name, 'api/apidoc.html')

    def test_swh_filter_renderer_do_nothing(self):
        # given
        input_data = {'a': 'some-data'}

        request = api_request_factory.get('/api/test/path/', data={})
        setattr(request, 'query_params', request.GET)

        # when
        actual_data = filter_by_fields(request, input_data)

        # then
        self.assertEqual(actual_data, input_data)

    @patch('swh.web.api.apiresponse.utils.filter_field_keys')
    def test_swh_filter_renderer_do_filter(self, mock_ffk):
        # given
        mock_ffk.return_value = {'a': 'some-data'}

        request = api_request_factory.get('/api/test/path/',
                                          data={'fields': 'a,c'})
        setattr(request, 'query_params', request.GET)

        input_data = {'a': 'some-data',
                      'b': 'some-other-data'}

        # when
        actual_data = filter_by_fields(request, input_data)

        # then
        self.assertEqual(actual_data, {'a': 'some-data'})

        mock_ffk.assert_called_once_with(input_data, {'a', 'c'})
