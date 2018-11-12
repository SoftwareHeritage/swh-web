# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.test import APITestCase
from unittest.mock import patch, MagicMock

from swh.web.tests.testcase import SWHWebTestCase


class ContentApiTestCase(SWHWebTestCase, APITestCase):
    @patch('swh.web.api.views.content.service')
    def test_api_content_filetype(self, mock_service):
        stub_filetype = {
            'accepted_media_type': 'application/xml',
            'encoding': 'ascii',
            'id': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
        }
        mock_service.lookup_content_filetype.return_value = stub_filetype

        # when
        rv = self.client.get(
            '/api/1/content/'
            'sha1_git:b04caf10e9535160d90e874b45aa426de762f19f/filetype/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'accepted_media_type': 'application/xml',
            'encoding': 'ascii',
            'id': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'content_url': '/api/1/content/'
            'sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/',
        })

        mock_service.lookup_content_filetype.assert_called_once_with(
            'sha1_git:b04caf10e9535160d90e874b45aa426de762f19f')

    @patch('swh.web.api.views.content.service')
    def test_api_content_filetype_sha_not_found(self, mock_service):
        # given
        mock_service.lookup_content_filetype.return_value = None

        # when
        rv = self.client.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/'
            'filetype/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'No filetype information found for content '
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03.'
        })

        mock_service.lookup_content_filetype.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.api.views.content.service')
    def test_api_content_language(self, mock_service):
        stub_language = {
            'lang': 'lisp',
            'id': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
        }
        mock_service.lookup_content_language.return_value = stub_language

        # when
        rv = self.client.get(
            '/api/1/content/'
            'sha1_git:b04caf10e9535160d90e874b45aa426de762f19f/language/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'lang': 'lisp',
            'id': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'content_url': '/api/1/content/'
            'sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/',
        })

        mock_service.lookup_content_language.assert_called_once_with(
            'sha1_git:b04caf10e9535160d90e874b45aa426de762f19f')

    @patch('swh.web.api.views.content.service')
    def test_api_content_language_sha_not_found(self, mock_service):
        # given
        mock_service.lookup_content_language.return_value = None

        # when
        rv = self.client.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'
            '/language/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'No language information found for content '
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03.'
        })

        mock_service.lookup_content_language.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.api.views.content.service')
    def test_api_content_symbol(self, mock_service):
        stub_ctag = [{
            'sha1': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'name': 'foobar',
            'kind': 'Haskell',
            'line': 10,
        }]
        mock_service.lookup_expression.return_value = stub_ctag

        # when
        rv = self.client.get('/api/1/content/symbol/foo/?last_sha1=sha1')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, [{
            'sha1': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'name': 'foobar',
            'kind': 'Haskell',
            'line': 10,
            'content_url': '/api/1/content/'
            'sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/',
            'data_url': '/api/1/content/'
            'sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/raw/',
            'license_url': '/api/1/content/'
            'sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/license/',
            'language_url': '/api/1/content/'
            'sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/language/',
            'filetype_url': '/api/1/content/'
            'sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/filetype/',
        }])
        self.assertFalse('Link' in rv)

        mock_service.lookup_expression.assert_called_once_with(
            'foo', 'sha1', 10)

    @patch('swh.web.api.views.content.service')
    def test_api_content_symbol_2(self, mock_service):
        stub_ctag = [{
            'sha1': '12371b8614fcd89ccd17ca2b1d9e66c5b00a6456',
            'name': 'foobar',
            'kind': 'Haskell',
            'line': 10,
        }, {
            'sha1': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6678',
            'name': 'foo',
            'kind': 'Lisp',
            'line': 10,
        }]
        mock_service.lookup_expression.return_value = stub_ctag

        # when
        rv = self.client.get(
            '/api/1/content/symbol/foo/?last_sha1=prev-sha1&per_page=2')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, stub_ctag)
        self.assertTrue(
            rv['Link'] ==  '</api/1/content/symbol/foo/?last_sha1=34571b8614fcd89ccd17ca2b1d9e66c5b00a6678&per_page=2>; rel="next"' or  # noqa
            rv['Link'] ==  '</api/1/content/symbol/foo/?per_page=2&last_sha1=34571b8614fcd89ccd17ca2b1d9e66c5b00a6678>; rel="next"'    # noqa
        )
        mock_service.lookup_expression.assert_called_once_with(
            'foo', 'prev-sha1', 2)

    @patch('swh.web.api.views.content.service')
    def test_api_content_symbol_3(self, mock_service):
        stub_ctag = [{
            'sha1': '67891b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'name': 'foo',
            'kind': 'variable',
            'line': 100,
        }]
        mock_service.lookup_expression.return_value = stub_ctag

        # when
        rv = self.client.get('/api/1/content/symbol/foo/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, [{
            'sha1': '67891b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'name': 'foo',
            'kind': 'variable',
            'line': 100,
            'content_url': '/api/1/content/'
            'sha1:67891b8614fcd89ccd17ca2b1d9e66c5b00a6d03/',
            'data_url': '/api/1/content/'
            'sha1:67891b8614fcd89ccd17ca2b1d9e66c5b00a6d03/raw/',
            'license_url': '/api/1/content/'
            'sha1:67891b8614fcd89ccd17ca2b1d9e66c5b00a6d03/license/',
            'language_url': '/api/1/content/'
            'sha1:67891b8614fcd89ccd17ca2b1d9e66c5b00a6d03/language/',
            'filetype_url': '/api/1/content/'
            'sha1:67891b8614fcd89ccd17ca2b1d9e66c5b00a6d03/filetype/',
        }])
        self.assertFalse(rv.has_header('Link'))

        mock_service.lookup_expression.assert_called_once_with('foo', None, 10)

    @patch('swh.web.api.views.content.service')
    def test_api_content_symbol_not_found(self, mock_service):
        # given
        mock_service.lookup_expression.return_value = []

        # when
        rv = self.client.get('/api/1/content/symbol/bar/?last_sha1=hash')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'No indexed raw content match expression \'bar\'.'
        })
        self.assertFalse('Link' in rv)

        mock_service.lookup_expression.assert_called_once_with(
            'bar', 'hash', 10)

    @patch('swh.web.api.views.content.service')
    def test_api_content_ctags(self, mock_service):
        stub_ctags = {
            'id': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'ctags': []
        }
        mock_service.lookup_content_ctags.return_value = stub_ctags

        # when
        rv = self.client.get(
            '/api/1/content/'
            'sha1_git:b04caf10e9535160d90e874b45aa426de762f19f/ctags/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'id': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'ctags': [],
            'content_url': '/api/1/content/'
            'sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/',
        })

        mock_service.lookup_content_ctags.assert_called_once_with(
            'sha1_git:b04caf10e9535160d90e874b45aa426de762f19f')

    @patch('swh.web.api.views.content.service')
    def test_api_content_license(self, mock_service):
        stub_license = {
            'licenses': ['No_license_found', 'Apache-2.0'],
            'id': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'tool_name': 'nomos',
        }
        mock_service.lookup_content_license.return_value = stub_license

        # when
        rv = self.client.get(
            '/api/1/content/'
            'sha1_git:b04caf10e9535160d90e874b45aa426de762f19f/license/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'licenses': ['No_license_found', 'Apache-2.0'],
            'id': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'tool_name': 'nomos',
            'content_url': '/api/1/content/'
            'sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/',
        })

        mock_service.lookup_content_license.assert_called_once_with(
            'sha1_git:b04caf10e9535160d90e874b45aa426de762f19f')

    @patch('swh.web.api.views.content.service')
    def test_api_content_license_sha_not_found(self, mock_service):
        # given
        mock_service.lookup_content_license.return_value = None

        # when
        rv = self.client.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/'
            'license/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'No license information found for content '
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03.'
        })

        mock_service.lookup_content_license.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.api.views.content.service')
    def test_api_content_provenance(self, mock_service):
        stub_provenances = [{
            'origin': 1,
            'visit': 2,
            'revision': 'b04caf10e9535160d90e874b45aa426de762f19f',
            'content': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'path': 'octavio-3.4.0/octave.html/doc_002dS_005fISREG.html'
        }]
        mock_service.lookup_content_provenance.return_value = stub_provenances

        # when
        rv = self.client.get(
            '/api/1/content/'
            'sha1_git:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/provenance/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, [{
            'origin': 1,
            'visit': 2,
            'origin_url': '/api/1/origin/1/',
            'origin_visits_url': '/api/1/origin/1/visits/',
            'origin_visit_url': '/api/1/origin/1/visit/2/',
            'revision': 'b04caf10e9535160d90e874b45aa426de762f19f',
            'revision_url': '/api/1/revision/'
                            'b04caf10e9535160d90e874b45aa426de762f19f/',
            'content': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'content_url': '/api/1/content/'
            'sha1_git:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/',
            'path': 'octavio-3.4.0/octave.html/doc_002dS_005fISREG.html'
        }])

        mock_service.lookup_content_provenance.assert_called_once_with(
            'sha1_git:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.api.views.content.service')
    def test_api_content_provenance_sha_not_found(self, mock_service):
        # given
        mock_service.lookup_content_provenance.return_value = None

        # when
        rv = self.client.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/'
            'provenance/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Content with sha1:40e71b8614fcd89ccd17ca2b1d9e6'
            '6c5b00a6d03 not found.'
        })

        mock_service.lookup_content_provenance.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.api.views.content.service')
    def test_api_content_metadata(self, mock_service):
        # given
        mock_service.lookup_content.return_value = {
            'checksums': {
                'blake2s256': '685395c5dc57cada459364f0946d3dd45bad5f'
                              'cbabc1048edb44380f1d31d0aa',
                'sha1': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
                'sha1_git': 'b4e8f472ffcb01a03875b26e462eb568739f6882',
                'sha256': '83c0e67cc80f60caf1fcbec2d84b0ccd7968b3be47'
                          '35637006560cde9b067a4f',
            },
            'length': 17,
            'status': 'visible'
        }

        # when
        rv = self.client.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'checksums': {
                'blake2s256': '685395c5dc57cada459364f0946d3dd45bad5f'
                              'cbabc1048edb44380f1d31d0aa',
                'sha1': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
                'sha1_git': 'b4e8f472ffcb01a03875b26e462eb568739f6882',
                'sha256': '83c0e67cc80f60caf1fcbec2d84b0ccd7968b3be47'
                          '35637006560cde9b067a4f',
            },
            'data_url': '/api/1/content/'
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/raw/',
            'filetype_url': '/api/1/content/'
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/filetype/',
            'language_url': '/api/1/content/'
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/language/',
            'license_url': '/api/1/content/'
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/license/',
            'length': 17,
            'status': 'visible'
        })

        mock_service.lookup_content.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.api.views.content.service')
    def test_api_content_not_found_as_json(self, mock_service):
        # given
        mock_service.lookup_content.return_value = None
        mock_service.lookup_content_provenance = MagicMock()

        # when
        rv = self.client.get(
            '/api/1/content/sha256:83c0e67cc80f60caf1fcbec2d84b0ccd7968b3'
            'be4735637006560c/')

        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Content with sha256:83c0e67cc80f60caf1fcbec2d84b0ccd79'
            '68b3be4735637006560c not found.'
        })

        mock_service.lookup_content.assert_called_once_with(
            'sha256:83c0e67cc80f60caf1fcbec2d84b0ccd7968b3'
            'be4735637006560c')
        mock_service.lookup_content_provenance.called = False

    @patch('swh.web.api.views.content.service')
    def test_api_content_not_found_as_yaml(self, mock_service):
        # given
        mock_service.lookup_content.return_value = None
        mock_service.lookup_content_provenance = MagicMock()

        # when
        rv = self.client.get(
            '/api/1/content/sha256:83c0e67cc80f60caf1fcbec2d84b0ccd7968b3'
            'be4735637006560c/',
            HTTP_ACCEPT='application/yaml')

        self.assertEqual(rv.status_code, 404)
        self.assertTrue('application/yaml' in rv['Content-Type'])

        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Content with sha256:83c0e67cc80f60caf1fcbec2d84b0ccd79'
            '68b3be4735637006560c not found.'
        })

        mock_service.lookup_content.assert_called_once_with(
            'sha256:83c0e67cc80f60caf1fcbec2d84b0ccd7968b3'
            'be4735637006560c')
        mock_service.lookup_content_provenance.called = False

    @patch('swh.web.api.views.content.service')
    def test_api_content_raw_ko_not_found(self, mock_service):
        # given
        mock_service.lookup_content_raw.return_value = None

        # when
        rv = self.client.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'
            '/raw/')

        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Content sha1:40e71b8614fcd89ccd17ca2b1d9e6'
            '6c5b00a6d03 is not found.'
        })

        mock_service.lookup_content_raw.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.api.views.content.service')
    def test_api_content_raw_text(self, mock_service):
        # given
        stub_content = {'data': b'some content data'}
        mock_service.lookup_content_raw.return_value = stub_content

        # when
        rv = self.client.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'
            '/raw/')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/octet-stream')
        self.assertEqual(
            rv['Content-disposition'],
            'attachment; filename=content_sha1_'
            '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03_raw')
        self.assertEqual(
            rv['Content-Type'], 'application/octet-stream')
        self.assertEqual(rv.content, stub_content['data'])

        mock_service.lookup_content_raw.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.api.views.content.service')
    def test_api_content_raw_text_with_filename(self, mock_service):
        # given
        stub_content = {'data': b'some content data'}
        mock_service.lookup_content_raw.return_value = stub_content

        # when
        rv = self.client.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'
            '/raw/?filename=filename.txt')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/octet-stream')
        self.assertEqual(
            rv['Content-disposition'],
            'attachment; filename=filename.txt')
        self.assertEqual(
            rv['Content-Type'], 'application/octet-stream')
        self.assertEqual(rv.content, stub_content['data'])

        mock_service.lookup_content_raw.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.api.views.content.service')
    def test_api_check_content_known(self, mock_service):
        # given
        mock_service.lookup_multiple_hashes.return_value = [
            {'found': True,
             'filename': None,
             'sha1': 'sha1:blah'}
        ]

        expected_result = {
            'search_stats': {'nbfiles': 1, 'pct': 100},
            'search_res': [{'sha1': 'sha1:blah',
                            'found': True}]
        }

        # when
        rv = self.client.get('/api/1/content/known/sha1:blah/')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_result)
        mock_service.lookup_multiple_hashes.assert_called_once_with(
            [{'filename': None, 'sha1': 'sha1:blah'}])

    @patch('swh.web.api.views.content.service')
    def test_api_check_content_known_as_yaml(self, mock_service):
        # given
        mock_service.lookup_multiple_hashes.return_value = [
            {'found': True,
             'filename': None,
             'sha1': 'sha1:halb'},
            {'found': False,
             'filename': None,
             'sha1': 'sha1_git:hello'}
        ]

        expected_result = {
            'search_stats': {'nbfiles': 2, 'pct': 50},
            'search_res': [{'sha1': 'sha1:halb',
                            'found': True},
                           {'sha1': 'sha1_git:hello',
                            'found': False}]
        }

        # when
        rv = self.client.get('/api/1/content/known/sha1:halb,sha1_git:hello/',
                             HTTP_ACCEPT='application/yaml')

        self.assertEqual(rv.status_code, 200)
        self.assertTrue('application/yaml' in rv['Content-Type'])
        self.assertEqual(rv.data, expected_result)

        mock_service.lookup_multiple_hashes.assert_called_once_with(
            [{'filename': None, 'sha1': 'sha1:halb'},
             {'filename': None, 'sha1': 'sha1_git:hello'}])

    @patch('swh.web.api.views.content.service')
    def test_api_check_content_known_post_as_yaml(self, mock_service):
        # given
        stub_result = [{'sha1': '7e62b1fe10c88a3eddbba930b156bee2956b2435',
                        'found': True},
                       {'filename': 'filepath',
                        'sha1': '8e62b1fe10c88a3eddbba930b156bee2956b2435',
                        'found': True},
                       {'filename': 'filename',
                        'sha1': '64025b5d1520c615061842a6ce6a456cad962a3f',
                        'found': False}]
        mock_service.lookup_multiple_hashes.return_value = stub_result

        expected_result = {
            'search_stats': {'nbfiles': 3, 'pct': 2/3 * 100},
            'search_res': stub_result
        }

        # when
        rv = self.client.post(
            '/api/1/content/known/search/',
            data=dict(
                q='7e62b1fe10c88a3eddbba930b156bee2956b2435',
                filepath='8e62b1fe10c88a3eddbba930b156bee2956b2435',
                filename='64025b5d1520c615061842a6ce6a456cad962a3f'),
            HTTP_ACCEPT='application/yaml'
        )

        self.assertEqual(rv.status_code, 200)
        self.assertTrue('application/yaml' in rv['Content-Type'])
        self.assertEqual(rv.data, expected_result)

    @patch('swh.web.api.views.content.service')
    def test_api_check_content_known_not_found(self, mock_service):
        # given
        stub_result = [{'sha1': 'sha1:halb',
                        'found': False}]
        mock_service.lookup_multiple_hashes.return_value = stub_result

        expected_result = {
            'search_stats': {'nbfiles': 1, 'pct': 0.0},
            'search_res': stub_result
        }

        # when
        rv = self.client.get('/api/1/content/known/sha1:halb/')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_result)

        mock_service.lookup_multiple_hashes.assert_called_once_with(
            [{'filename': None, 'sha1': 'sha1:halb'}])
