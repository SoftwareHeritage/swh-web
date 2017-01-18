# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from nose.tools import istest

from unittest import TestCase
from unittest.mock import patch

from flask import url_for

from swh.web.ui.views import browse
from swh.web.ui.exc import BadInputExc, NotFoundExc
from .. import test_app


class FileMock():

    def __init__(self, filename):
        self.filename = filename


class StaticViews(test_app.SWHViewTestCase):
    render_template = False

    @patch('swh.web.ui.apidoc.APIUrls')
    @istest
    def browse_api_endpoints(self, mock_api_urls):
        # given
        endpoints = {
            '/a/doc/endpoint/': 'relevant documentation',
            '/some/other/endpoint/': 'more docstrings'}
        mock_api_urls.apidoc_routes = endpoints

        # when
        rv = self.client.get('/api/1/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertIsNotNone(
            self.get_context_variable('doc_routes'),
            sorted(endpoints.items())
        )
        self.assert_template_used('api-endpoints.html')

    @istest
    def browse_api_doc(self):
        # given

        # when
        rv = self.client.get('/api/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('api.html')

    @istest
    def browse_archive(self):
        # when
        rv = self.client.get('/browse/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('browse.html')


class SearchRedirectsView(test_app.SWHViewTestCase):
    render_template = False

    @istest
    def search_origin_simple(self):
        # when
        rv = self.client.get('/origin/search/?origin_id=1&meaningless_arg=42')

        # then
        self.assertRedirects(rv, url_for('browse_origin', origin_id=1))

    @istest
    def search_origin_type_url(self):
        # when
        rv = self.client.get('/origin/search/?origin_type=git'
                             '&origin_url=http://cool/project/url'
                             '&meaningless_arg=42')

        # then
        self.assertRedirects(rv, url_for('browse_origin',
                                         origin_type='git',
                                         origin_url='http://cool/project/url'))

    @istest
    def search_directory_dir_sha1(self):
        # when
        rv = self.client.get('/directory/search/?sha1_git=some_sha1'
                             '&path=some/path/in/folder'
                             '&meaningless_arg=gandalf')

        # then
        self.assertRedirects(rv, url_for('browse_directory',
                                         sha1_git='some_sha1',
                                         path='some/path/in/folder'))

    @istest
    def search_directory_dir_sha1_nopath(self):
        # when
        rv = self.client.get('/directory/search/?sha1_git=some_sha1'
                             '&meaningless_arg=gandalf')

        # then
        self.assertRedirects(rv, url_for('browse_directory',
                                         sha1_git='some_sha1'))

    @istest
    def search_directory_rev_sha1(self):
        # when
        rv = self.client.get('/directory/search/?sha1_git=some_sha1'
                             '&dir_path=some/path/in/folder'
                             '&meaningless_arg=gandalf')

        # then
        self.assertRedirects(rv, url_for('browse_revision_directory',
                                         sha1_git='some_sha1',
                                         dir_path='some/path/in/folder'))

    @istest
    def search_directory_rev_sha1_nopath(self):
        # when
        rv = self.client.get('/directory/search/?sha1_git=some_sha1'
                             '&dir_path='
                             '&meaningless_arg=gandalf')

        # then
        self.assertRedirects(rv, url_for('browse_revision_directory',
                                         sha1_git='some_sha1'))

    @istest
    def search_directory_dir_time_place(self):
        # when
        rv = self.client.get('/directory/search/?origin_id=42'
                             '&branch_name=refs/heads/tail'
                             '&meaningless_arg=gandalf'
                             '&path=some/path')

        # then
        self.assertRedirects(rv, url_for(
            'browse_revision_directory_through_origin',
            origin_id=42, branch_name='refs/heads/tail',
            path='some/path', ts=None))

    @istest
    def search_revision_sha1(self):
        # when
        rv = self.client.get('/revision/search/?sha1_git=some_sha1')

        # then
        self.assertRedirects(rv, url_for('browse_revision',
                                         sha1_git='some_sha1'))

    @istest
    def search_revision_time_place(self):
        # when
        rv = self.client.get('/revision/search/?origin_id=42'
                             '&branch_name=big/branch/on/tree'
                             '&ts=meaningful_ts')

        # then
        self.assertRedirects(rv, url_for('browse_revision_with_origin',
                                         origin_id=42,
                                         branch_name='big/branch/on/tree',
                                         ts='meaningful_ts'))


class SearchSymbolView(test_app.SWHViewTestCase):
    render_template = False

    @istest
    def search_symbol(self):
        # when
        rv = self.client.get('/content/symbol/')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('result'), None)
        self.assertEqual(self.get_context_variable('message'), '')
        self.assertEqual(self.get_context_variable('linknext'), None)
        self.assertEqual(self.get_context_variable('linkprev'), None)
        self.assert_template_used('symbols.html')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def search_symbol_with_result(self, mock_api):
        # given
        stub_results = [
            {
                'kind': 'function',
                'name': 'hy',
                'sha1': 'some-hash',
            },
        ]
        mock_api.api_content_symbol.return_value = {
            'results': stub_results,
        }

        # when
        rv = self.client.get('/content/symbol/?q=hy')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('result'), stub_results)

        self.assertEqual(self.get_context_variable('message'), '')
        self.assertEqual(self.get_context_variable('linknext'), None)
        self.assertEqual(self.get_context_variable('linkprev'), None)
        self.assert_template_used('symbols.html')

        mock_api.api_content_symbol.assert_called_once_with('hy')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def search_symbol_with_result_and_pages(self, mock_api):
        # given
        stub_results = [
            {
                'kind': 'function',
                'name': 'hy',
                'sha1': 'some-hash',
            }
        ]
        mock_api.api_content_symbol.return_value = {
            'results': stub_results,
            'headers': {
                'link-next': 'some-link',
            }
        }

        # when
        rv = self.client.get('/content/symbol/?q=hy&per_page=1')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('result'), stub_results)

        self.assertEqual(self.get_context_variable('message'), '')
        self.assertEqual(
            self.get_context_variable('linknext'),
            '/content/symbol/?q=hy&last_sha1=some-hash&per_page=1')
        self.assertEqual(self.get_context_variable('linkprev'), None)
        self.assert_template_used('symbols.html')

        mock_api.api_content_symbol.assert_called_once_with('hy')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def search_symbol_bad_input(self, mock_api):
        # given
        mock_api.api_content_symbol.side_effect = BadInputExc('error msg')

        # when
        rv = self.client.get('/content/symbol/?q=hello|hy')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('message'), 'error msg')
        self.assertEqual(self.get_context_variable('result'), None)
        self.assertEqual(self.get_context_variable('linknext'), None)
        self.assertEqual(self.get_context_variable('linkprev'), None)
        self.assert_template_used('symbols.html')

        mock_api.api_content_symbol.assert_called_once_with('hello|hy')


class SearchView(test_app.SWHViewTestCase):
    render_template = False

    @istest
    def search_default(self):
        # when
        rv = self.client.get('/content/search/')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('message'), '')
        self.assertEqual(self.get_context_variable('search_res'), None)
        self.assert_template_used('search.html')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def search_get_query_hash_not_found(self, mock_api):
        # given
        mock_api.api_check_content_known.return_value = {
            'search_res': [{
                'filename': None,
                'sha1': 'sha1:456',
                'found': False}],
            'search_stats': {'nbfiles': 1, 'pct': 100}}

        # when
        rv = self.client.get('/content/search/?q=sha1:456')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('message'), '')
        self.assertEqual(self.get_context_variable('search_res'), [
            {'filename': None,
             'sha1': 'sha1:456',
             'found': False}])
        self.assert_template_used('search.html')

        mock_api.api_check_content_known.assert_called_once_with('sha1:456')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def search_get_query_hash_bad_input(self, mock_api):
        # given
        mock_api.api_check_content_known.side_effect = BadInputExc('error msg')

        # when
        rv = self.client.get('/content/search/?q=sha1_git:789')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('message'), 'error msg')
        self.assertEqual(self.get_context_variable('search_res'), None)
        self.assert_template_used('search.html')

        mock_api.api_check_content_known.assert_called_once_with(
            'sha1_git:789')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def search_get_query_hash_found(self, mock_api):
        # given
        mock_api.api_check_content_known.return_value = {
            'search_res': [{
                'filename': None,
                'sha1': 'sha1:123',
                'found': True}],
            'search_stats': {'nbfiles': 1, 'pct': 100}}

        # when
        rv = self.client.get('/content/search/?q=sha1:123')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('message'), '')
        self.assertEqual(len(self.get_context_variable('search_res')), 1)
        resp = self.get_context_variable('search_res')[0]
        self.assertTrue(resp is not None)
        self.assertEqual(resp['sha1'], 'sha1:123')
        self.assertEqual(resp['found'], True)
        self.assert_template_used('search.html')

        mock_api.api_check_content_known.assert_called_once_with('sha1:123')

    @patch('swh.web.ui.views.browse.request')
    @patch('swh.web.ui.views.browse.api')
    @istest
    def search_post_hashes_bad_input(self, mock_api, mock_request):
        # given
        mock_request.form = {'a': ['456caf10e9535160d90e874b45aa426de762f19f'],
                             'b': ['745bab676c8f3cec8016e0c39ea61cf57e518865']}
        mock_request.method = 'POST'
        mock_api.api_check_content_known.side_effect = BadInputExc(
            'error bad input')

        # when (mock_request completes the post request)
        rv = self.client.post('/content/search/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('search_stats'),
                         {'nbfiles': 0, 'pct': 0})
        self.assertEqual(self.get_context_variable('search_res'), None)
        self.assertEqual(self.get_context_variable('message'),
                         'error bad input')
        self.assert_template_used('search.html')

    @patch('swh.web.ui.views.browse.request')
    @patch('swh.web.ui.views.browse.api')
    @istest
    def search_post_hashes_none(self, mock_api, mock_request):
        # given
        mock_request.form = {'a': ['456caf10e9535160d90e874b45aa426de762f19f'],
                             'b': ['745bab676c8f3cec8016e0c39ea61cf57e518865']}
        mock_request.method = 'POST'
        mock_api.api_check_content_known.return_value = {
            'search_stats': {'nbfiles': 2, 'pct': 0},
            'search_res': [{'filename': 'a',
                            'sha1': '456caf10e9535160d90e874b45aa426de762f19f',
                            'found': False},
                           {'filename': 'b',
                            'sha1': '745bab676c8f3cec8016e0c39ea61cf57e518865',
                            'found': False}]}

        # when (mock_request completes the post request)
        rv = self.client.post('/content/search/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertIsNotNone(self.get_context_variable('search_res'))
        self.assertTrue(self.get_context_variable('search_stats') is not None)
        self.assertEqual(len(self.get_context_variable('search_res')), 2)

        stats = self.get_context_variable('search_stats')
        self.assertEqual(stats['nbfiles'], 2)
        self.assertEqual(stats['pct'], 0)

        a, b = self.get_context_variable('search_res')
        self.assertEqual(a['found'], False)
        self.assertEqual(b['found'], False)
        self.assertEqual(self.get_context_variable('message'), '')

        self.assert_template_used('search.html')

    @patch('swh.web.ui.views.browse.request')
    @patch('swh.web.ui.views.browse.api')
    @istest
    def search_post_hashes_some(self, mock_api, mock_request):
        # given
        mock_request.form = {'a': '456caf10e9535160d90e874b45aa426de762f19f',
                             'b': '745bab676c8f3cec8016e0c39ea61cf57e518865'}
        mock_request.method = 'POST'
        mock_api.api_check_content_known.return_value = {
            'search_stats': {'nbfiles': 2, 'pct': 50},
            'search_res': [{'filename': 'a',
                            'sha1': '456caf10e9535160d90e874b45aa426de762f19f',
                            'found': False},
                           {'filename': 'b',
                            'sha1': '745bab676c8f3cec8016e0c39ea61cf57e518865',
                            'found': True}]}

        # when (mock_request completes the post request)
        rv = self.client.post('/content/search/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertIsNotNone(self.get_context_variable('search_res'))
        self.assertEqual(len(self.get_context_variable('search_res')), 2)
        self.assertTrue(self.get_context_variable('search_stats') is not None)

        stats = self.get_context_variable('search_stats')
        self.assertEqual(stats['nbfiles'], 2)
        self.assertEqual(stats['pct'], 50)
        self.assertEqual(self.get_context_variable('message'), '')

        a, b = self.get_context_variable('search_res')
        self.assertEqual(a['found'], False)
        self.assertEqual(b['found'], True)
        self.assert_template_used('search.html')


class ContentView(test_app.SWHViewTestCase):
    render_template = False

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_content_ko_not_found(self, mock_api):
        # given
        mock_api.api_content_metadata.side_effect = NotFoundExc(
            'Not found!')

        # when
        rv = self.client.get('/browse/content/sha1:sha1-hash/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('content.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Not found!')
        self.assertIsNone(self.get_context_variable('content'))

        mock_api.api_content_metadata.assert_called_once_with(
            'sha1:sha1-hash')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_content_ko_bad_input(self, mock_api):
        # given
        mock_api.api_content_metadata.side_effect = BadInputExc(
            'Bad input!')

        # when
        rv = self.client.get('/browse/content/sha1:sha1-hash/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('content.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Bad input!')
        self.assertIsNone(self.get_context_variable('content'))

        mock_api.api_content_metadata.assert_called_once_with(
            'sha1:sha1-hash')

    @patch('swh.web.ui.views.browse.service')
    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_content(self, mock_api, mock_service):
        # given
        stub_content = {
            'sha1': 'sha1-hash'
        }
        mock_api.api_content_metadata.return_value = stub_content
        mock_api.api_content_filetype.return_value = {
            'mimetype': 'text/plain',
        }
        mock_api.api_content_language.return_value = {
            'lang': 'Hy',
        }
        mock_api.api_content_license.return_value = {
            'licenses': ['MIT', 'BSD'],
        }
        mock_service.lookup_content_raw.return_value = {
            'data': b'blah'
        }
        mock_api.api_content_ctags.return_value = [
            {
                'line': 12,
            },
            {
                'line': 14,
            }
        ]

        expected_content = {
            'sha1': 'sha1-hash',
            'data': 'blah',
            'encoding': None,
            'mimetype': 'text/plain',
            'language': 'Hy',
            'licenses': "MIT, BSD",
        }

        # when
        rv = self.client.get('/browse/content/sha1:sha1-hash/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('content.html')
        self.assertIsNone(self.get_context_variable('message'))
        actual_content = self.get_context_variable('content')
        actual_content.pop('ctags')
        self.assertEqual(actual_content, expected_content)

        mock_service.lookup_content_raw.assert_called_once_with(
            'sha1:sha1-hash')
        mock_api.api_content_language.assert_called_once_with('sha1:sha1-hash')
        mock_api.api_content_filetype.assert_called_once_with('sha1:sha1-hash')
        mock_api.api_content_license.assert_called_once_with('sha1:sha1-hash')
        mock_api.api_content_metadata.assert_called_once_with('sha1:sha1-hash')
        mock_api.api_content_ctags.assert_called_once_with('sha1:sha1-hash')

    @patch('swh.web.ui.views.browse.service')
    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_content_less_data(self, mock_api, mock_service):
        # given
        stub_content = {
            'sha1': 'ha1',
        }
        mock_api.api_content_metadata.return_value = stub_content
        mock_api.api_content_filetype.return_value = None
        mock_api.api_content_language.return_value = None
        mock_api.api_content_license.return_value = None
        mock_service.lookup_content_raw.return_value = None
        mock_api.api_content_ctags.return_value = []

        expected_content = {
            'sha1': 'ha1',
            'data': None,
            'encoding': None,
            'mimetype': None,
            'language': None,
            'licenses': None,
            'ctags': None,
        }

        # when
        rv = self.client.get('/browse/content/sha1:ha1/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('content.html')
        self.assertIsNone(self.get_context_variable('message'))
        actual_content = self.get_context_variable('content')
        self.assertEqual(actual_content, expected_content)

        mock_service.lookup_content_raw.assert_called_once_with('sha1:ha1')
        mock_api.api_content_language.assert_called_once_with('sha1:ha1')
        mock_api.api_content_filetype.assert_called_once_with('sha1:ha1')
        mock_api.api_content_license.assert_called_once_with('sha1:ha1')
        mock_api.api_content_metadata.assert_called_once_with('sha1:ha1')
        mock_api.api_content_ctags.assert_called_once_with('sha1:ha1')

    @patch('swh.web.ui.views.browse.redirect')
    @patch('swh.web.ui.views.browse.url_for')
    @istest
    def browse_content_raw(self, mock_urlfor, mock_redirect):
        # given
        stub_content_raw = b'some-data'
        mock_urlfor.return_value = '/api/content/sha1:sha1-hash/raw/'
        mock_redirect.return_value = stub_content_raw

        # when
        rv = self.client.get('/browse/content/sha1:sha1-hash/raw/')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data, stub_content_raw)

        mock_urlfor.assert_called_once_with('api_content_raw',
                                            q='sha1:sha1-hash')
        mock_redirect.assert_called_once_with(
            '/api/content/sha1:sha1-hash/raw/')


class DirectoryView(test_app.SWHViewTestCase):
    render_template = False

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_directory_ko_bad_input(self, mock_api):
        # given
        mock_api.api_directory.side_effect = BadInputExc(
            'Invalid hash')

        # when
        rv = self.client.get('/browse/directory/sha2-invalid/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('directory.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Invalid hash')
        self.assertEqual(self.get_context_variable('files'), [])
        mock_api.api_directory.assert_called_once_with(
            'sha2-invalid')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_directory_empty_result(self, mock_api):
        # given
        mock_api.api_directory.return_value = []

        # when
        rv = self.client.get('/browse/directory/some-sha1/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('directory.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Listing for directory some-sha1:')
        self.assertEqual(self.get_context_variable('files'), [])
        mock_api.api_directory.assert_called_once_with(
            'some-sha1')

    @patch('swh.web.ui.views.browse.service')
    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_directory_relative_file(self, mock_api, mock_service):
        # given
        stub_entry = {
            'sha256': '240',
            'type': 'file'
        }
        mock_service.lookup_directory_with_path.return_value = stub_entry
        stub_file = {
            'sha1_git': '123',
            'sha1': '456',
            'status': 'visible',
            'data_url': '/api/1/content/890',
            'length': 42,
            'ctime': 'Thu, 01 Oct 2015 12:13:53 GMT',
            'target': 'file.txt',
            'sha256': '148'
        }
        mock_api.api_content_metadata.return_value = stub_file
        mock_service.lookup_content_raw.return_value = {
            'data': 'this is my file'}

        # when
        rv = self.client.get('/browse/directory/sha1/path/to/file/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('content.html')
        self.assertIsNotNone(self.get_context_variable('content'))
        content = self.get_context_variable('content')
        # change caused by call to prepare_data_for_view
        self.assertEqual(content['data_url'], '/browse/content/890')
        self.assertEqual(content['data'], 'this is my file')
        mock_api.api_content_metadata.assert_called_once_with('sha256:240')
        mock_service.lookup_content_raw.assert_called_once_with('sha256:240')

    @patch('swh.web.ui.views.browse.service')
    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_directory_relative_dir(self, mock_api, mock_service):
        # given
        mock_service.lookup_directory_with_path.return_value = {
            'sha256': '240',
            'target': 'abcd',
            'type': 'dir'
        }

        stub_directory_ls = [
            {'type': 'dir',
             'target': '123',
             'name': 'some-dir-name'},
            {'type': 'file',
             'sha1': '654',
             'name': 'some-filename'},
            {'type': 'dir',
             'target': '987',
             'name': 'some-other-dirname'}
        ]
        mock_api.api_directory.return_value = stub_directory_ls

        # when
        rv = self.client.get('/browse/directory/sha1/path/to/dir/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('directory.html')
        self.assertIsNotNone(self.get_context_variable('files'))
        self.assertEqual(len(self.get_context_variable('files')),
                         len(stub_directory_ls))
        mock_api.api_directory.assert_called_once_with('abcd')

    @patch('swh.web.ui.views.browse.service')
    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_directory_relative_not_found(self, mock_api, mock_service):
        # given
        mock_service.lookup_directory_with_path.side_effect = NotFoundExc(
            'Directory entry not found.')

        # when
        rv = self.client.get('/browse/directory/some-sha1/some/path/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('directory.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Directory entry not found.')

    @patch('swh.web.ui.views.browse.api')
    @patch('swh.web.ui.views.browse.utils')
    @istest
    def browse_directory(self, mock_utils, mock_api):
        # given
        stub_directory_ls = [
            {'type': 'dir',
             'target': '123',
             'name': 'some-dir-name'},
            {'type': 'file',
             'sha1': '654',
             'name': 'some-filename'},
            {'type': 'dir',
             'target': '987',
             'name': 'some-other-dirname'}
        ]
        mock_api.api_directory.return_value = stub_directory_ls
        stub_directory_map = [
            {'link': '/path/to/url/dir/123',
             'name': 'some-dir-name'},
            {'link': '/path/to/url/file/654',
             'name': 'some-filename'},
            {'link': '/path/to/url/dir/987',
             'name': 'some-other-dirname'}
        ]
        mock_utils.prepare_data_for_view.return_value = stub_directory_map

        # when
        rv = self.client.get('/browse/directory/some-sha1/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('directory.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Listing for directory some-sha1:')
        self.assertEqual(self.get_context_variable('files'),
                         stub_directory_map)

        mock_api.api_directory.assert_called_once_with(
            'some-sha1')
        mock_utils.prepare_data_for_view.assert_called_once_with(
            stub_directory_ls)


class ContentWithOriginView(test_app.SWHViewTestCase):
    render_template = False

    @patch('swh.web.ui.views.browse.api')
#    @istest
    def browse_content_with_origin_content_ko_not_found(self, mock_api):
        # given
        mock_api.api_content_checksum_to_origin.side_effect = NotFoundExc(
            'Not found!')

        # when
        rv = self.client.get('/browse/content/sha256:some-sha256/origin/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('content-with-origin.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Not found!')

        mock_api.api_content_checksum_to_origin.assert_called_once_with(
            'sha256:some-sha256')

    @patch('swh.web.ui.views.browse.api')
#    @istest
    def browse_content_with_origin_ko_bad_input(self, mock_api):
        # given
        mock_api.api_content_checksum_to_origin.side_effect = BadInputExc(
            'Invalid hash')

        # when
        rv = self.client.get('/browse/content/sha256:some-sha256/origin/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('content-with-origin.html')
        self.assertEqual(
            self.get_context_variable('message'), 'Invalid hash')

        mock_api.api_content_checksum_to_origin.assert_called_once_with(
            'sha256:some-sha256')

    @patch('swh.web.ui.views.browse.api')
#    @istest
    def browse_content_with_origin(self, mock_api):
        # given
        mock_api.api_content_checksum_to_origin.return_value = {
            'origin_type': 'ftp',
            'origin_url': '/some/url',
            'revision': 'revision-hash',
            'branch': 'master',
            'path': '/path/to',
        }

        # when
        rv = self.client.get('/browse/content/sha256:some-sha256/origin/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('content-with-origin.html')
        self.assertEqual(
            self.get_context_variable('message'),
            "The content with hash sha256:some-sha256 has been seen on " +
            "origin with type 'ftp'\n" +
            "at url '/some/url'. The revision was identified at " +
            "'revision-hash' on branch 'master'.\n" +
            "The file's path referenced was '/path/to'.")

        mock_api.api_content_checksum_to_origin.assert_called_once_with(
            'sha256:some-sha256')


class OriginView(test_app.SWHViewTestCase):
    render_template = False

    def setUp(self):

        def url_for_test(fn, **args):
            if fn == 'browse_revision_with_origin':
                return '/browse/revision/origin/%s/' % args['origin_id']
            elif fn == 'api_origin_visits':
                return '/api/1/stat/visits/%s/' % args['origin_id']

        self.url_for_test = url_for_test

        self.stub_origin = {'type': 'git',
                            'lister': None,
                            'project': None,
                            'url': 'rsync://some/url',
                            'id': 426}

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_origin_ko_not_found(self, mock_api):
        # given
        mock_api.api_origin.side_effect = NotFoundExc('Not found!')

        # when
        rv = self.client.get('/browse/origin/1/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('origin.html')
        self.assertIsNone(self.get_context_variable('origin'))
        self.assertEqual(
            self.get_context_variable('message'),
            'Not found!')

        mock_api.api_origin.assert_called_once_with(1, None, None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_origin_ko_bad_input(self, mock_api):
        # given
        mock_api.api_origin.side_effect = BadInputExc('wrong input')

        # when
        rv = self.client.get('/browse/origin/426/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('origin.html')
        self.assertIsNone(self.get_context_variable('origin'))

        mock_api.api_origin.assert_called_once_with(426, None, None)

    @patch('swh.web.ui.views.browse.api')
    @patch('swh.web.ui.views.browse.url_for')
    @istest
    def browse_origin_found_id(self, mock_url_for, mock_api):
        # given

        mock_url_for.side_effect = self.url_for_test

        mock_api.api_origin.return_value = self.stub_origin

        # when
        rv = self.client.get('/browse/origin/426/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('origin.html')
        self.assertEqual(self.get_context_variable('origin'), self.stub_origin)
        self.assertEqual(self.get_context_variable('browse_url'),
                         '/browse/revision/origin/426/')
        self.assertEqual(self.get_context_variable('visit_url'),
                         '/api/1/stat/visits/426/')

        mock_api.api_origin.assert_called_once_with(426, None, None)

    @patch('swh.web.ui.views.browse.api')
    @patch('swh.web.ui.views.browse.url_for')
    @istest
    def browse_origin_found_url_type(self, mock_url_for, mock_api):
        # given

        mock_url_for.side_effect = self.url_for_test

        mock_api.api_origin.return_value = self.stub_origin

        # when
        rv = self.client.get('/browse/origin/git/url/rsync://some/url/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('origin.html')
        self.assertEqual(self.get_context_variable('origin'), self.stub_origin)
        self.assertEqual(self.get_context_variable('browse_url'),
                         '/browse/revision/origin/426/')
        self.assertEqual(self.get_context_variable('visit_url'),
                         '/api/1/stat/visits/426/')

        mock_api.api_origin.assert_called_once_with(None, 'git',
                                                    'rsync://some/url')


class PersonView(test_app.SWHViewTestCase):
    render_template = False

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_person_ko_not_found(self, mock_api):
        # given
        mock_api.api_person.side_effect = NotFoundExc('not found')

        # when
        rv = self.client.get('/browse/person/1/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('person.html')
        self.assertEqual(self.get_context_variable('person_id'), 1)
        self.assertEqual(
            self.get_context_variable('message'),
            'not found')

        mock_api.api_person.assert_called_once_with(1)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_person_ko_bad_input(self, mock_api):
        # given
        mock_api.api_person.side_effect = BadInputExc('wrong input')

        # when
        rv = self.client.get('/browse/person/426/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('person.html')
        self.assertEqual(self.get_context_variable('person_id'), 426)

        mock_api.api_person.assert_called_once_with(426)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_person(self, mock_api):
        # given
        mock_person = {'type': 'git',
                       'lister': None,
                       'project': None,
                       'url': 'rsync://some/url',
                       'id': 426}
        mock_api.api_person.return_value = mock_person

        # when
        rv = self.client.get('/browse/person/426/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('person.html')
        self.assertEqual(self.get_context_variable('person_id'), 426)
        self.assertEqual(self.get_context_variable('person'), mock_person)

        mock_api.api_person.assert_called_once_with(426)


class ReleaseView(test_app.SWHViewTestCase):
    render_template = False

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_release_ko_not_found(self, mock_api):
        # given
        mock_api.api_release.side_effect = NotFoundExc('not found!')

        # when
        rv = self.client.get('/browse/release/1/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('release.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '1')
        self.assertEqual(
            self.get_context_variable('message'),
            'not found!')

        mock_api.api_release.assert_called_once_with('1')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_release_ko_bad_input(self, mock_api):
        # given
        mock_api.api_release.side_effect = BadInputExc('wrong input')

        # when
        rv = self.client.get('/browse/release/426/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('release.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '426')

        mock_api.api_release.assert_called_once_with('426')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_release(self, mock_api):
        # given
        self.maxDiff = None
        mock_release = {
            "date": "Sun, 05 Jul 2015 18:02:06 GMT",
            "id": "1e951912027ea6873da6985b91e50c47f645ae1a",
            "target": "d770e558e21961ad6cfdf0ff7df0eb5d7d4f0754",
            "target_url": '/browse/revision/d770e558e21961ad6cfdf0ff7df0'
                          'eb5d7d4f0754/',
            "synthetic": False,
            "target_type": "revision",
            "author": {
                "email": "torvalds@linux-foundation.org",
                "name": "Linus Torvalds"
            },
            "message": "Linux 4.2-rc1\n",
            "name": "v4.2-rc1"
        }
        mock_api.api_release.return_value = mock_release

        expected_release = {
            "date": "Sun, 05 Jul 2015 18:02:06 GMT",
            "id": "1e951912027ea6873da6985b91e50c47f645ae1a",
            "target_url": '/browse/revision/d770e558e21961ad6cfdf0ff7df0'
                          'eb5d7d4f0754/',
            "target": 'd770e558e21961ad6cfdf0ff7df0eb5d7d4f0754',
            "synthetic": False,
            "target_type": "revision",
            "author": {
                "email": "torvalds@linux-foundation.org",
                "name": "Linus Torvalds"
            },
            "message": "Linux 4.2-rc1\n",
            "name": "v4.2-rc1"
        }

        # when
        rv = self.client.get('/browse/release/426/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('release.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '426')
        self.assertEqual(self.get_context_variable('release'),
                         expected_release)

        mock_api.api_release.assert_called_once_with('426')


class RevisionView(test_app.SWHViewTestCase):
    render_template = False

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_ko_not_found(self, mock_api):
        # given
        mock_api.api_revision.side_effect = NotFoundExc('Not found!')

        # when
        rv = self.client.get('/browse/revision/1/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '1')
        self.assertEqual(
            self.get_context_variable('message'),
            'Not found!')
        self.assertIsNone(self.get_context_variable('revision'))

        mock_api.api_revision.assert_called_once_with('1', None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_ko_bad_input(self, mock_api):
        # given
        mock_api.api_revision.side_effect = BadInputExc('wrong input!')

        # when
        rv = self.client.get('/browse/revision/426/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '426')
        self.assertEqual(
            self.get_context_variable('message'),
            'wrong input!')
        self.assertIsNone(self.get_context_variable('revision'))

        mock_api.api_revision.assert_called_once_with('426', None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision(self, mock_api):
        # given
        stub_revision = {
            'id': 'd770e558e21961ad6cfdf0ff7df0eb5d7d4f0754',
            'date': 'Sun, 05 Jul 2015 18:01:52 GMT',
            'committer': {
                'email': 'torvalds@linux-foundation.org',
                'name': 'Linus Torvalds'
            },
            'committer_date': 'Sun, 05 Jul 2015 18:01:52 GMT',
            'type': 'git',
            'author': {
                'email': 'torvalds@linux-foundation.org',
                'name': 'Linus Torvalds'
            },
            'message': 'Linux 4.2-rc1\n',
            'synthetic': False,
            'directory_url': '/api/1/directory/'
            '2a1dbabeed4dcf1f4a4c441993b2ffc9d972780b/',
            'parent_url': [
                '/api/1/revision/a585d2b738bfa26326b3f1f40f0f1eda0c067ccf/'
            ],
        }
        mock_api.api_revision.return_value = stub_revision

        expected_revision = {
            'id': 'd770e558e21961ad6cfdf0ff7df0eb5d7d4f0754',
            'date': 'Sun, 05 Jul 2015 18:01:52 GMT',
            'committer': {
                'email': 'torvalds@linux-foundation.org',
                'name': 'Linus Torvalds'
            },
            'committer_date': 'Sun, 05 Jul 2015 18:01:52 GMT',
            'type': 'git',
            'author': {
                'email': 'torvalds@linux-foundation.org',
                'name': 'Linus Torvalds'
            },
            'message': 'Linux 4.2-rc1\n',
            'synthetic': False,
            'parent_url': [
                '/browse/revision/a585d2b738bfa26326b3f1f40f0f1eda0c067ccf/'
            ],
            'directory_url': '/browse/directory/2a1dbabeed4dcf1f4a4c441993b2f'
            'fc9d972780b/',
        }

        # when
        rv = self.client.get('/browse/revision/426/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '426')
        self.assertEqual(self.get_context_variable('revision'),
                         expected_revision)
        self.assertIsNone(self.get_context_variable('message'))

        mock_api.api_revision.assert_called_once_with('426', None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_raw_message(self, mock_api):
        # given
        sha1 = 'd770e558e21961ad6cfdf0ff7df0eb5d7d4f0754'

        # when
        rv = self.client.get('/browse/revision/'
                             'd770e558e21961ad6cfdf0ff7df0eb5d7d4f0754/raw/')

        self.assertRedirects(
            rv, '/api/1/revision/%s/raw/' % sha1)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_log_ko_not_found(self, mock_api):
        # given
        mock_api.api_revision_log.side_effect = NotFoundExc('Not found!')

        # when
        rv = self.client.get('/browse/revision/sha1/log/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-log.html')
        self.assertEqual(self.get_context_variable('sha1_git'), 'sha1')
        self.assertEqual(
            self.get_context_variable('message'),
            'Not found!')
        self.assertEqual(self.get_context_variable('revisions'), [])

        mock_api.api_revision_log.assert_called_once_with('sha1', None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_log_ko_bad_input(self, mock_api):
        # given
        mock_api.api_revision_log.side_effect = BadInputExc('wrong input!')

        # when
        rv = self.client.get('/browse/revision/426/log/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-log.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '426')
        self.assertEqual(
            self.get_context_variable('message'),
            'wrong input!')
        self.assertEqual(self.get_context_variable('revisions'), [])

        mock_api.api_revision_log.assert_called_once_with('426', None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_log(self, mock_api):
        # given
        stub_revisions = {
            'revisions': [{
                'id': 'd770e558e21961ad6cfdf0ff7df0eb5d7d4f0754',
                'date': 'Sun, 05 Jul 2015 18:01:52 GMT',
                'committer': {
                    'email': 'torvalds@linux-foundation.org',
                    'name': 'Linus Torvalds'
                },
                'committer_date': 'Sun, 05 Jul 2015 18:01:52 GMT',
                'type': 'git',
                'author': {
                    'email': 'torvalds@linux-foundation.org',
                    'name': 'Linus Torvalds'
                },
                'message': 'Linux 4.2-rc1\n',
                'synthetic': False,
                'directory_url': '/api/1/directory/'
                '2a1dbabeed4dcf1f4a4c441993b2ffc9d972780b/',
                'parent_url': [
                    '/api/1/revision/a585d2b738bfa26326b3f1f40f0f1eda0c067ccf/'
                ],
            }],
            'next_revs_url': '/api/1/revision/1234/log/'
        }
        mock_api.api_revision_log.return_value = stub_revisions

        # when
        rv = self.client.get('/browse/revision/426/log/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-log.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '426')
        self.assertTrue(
            isinstance(self.get_context_variable('revisions'), map))
        self.assertEqual(
            self.get_context_variable('next_revs_url'),
            '/browse/revision/1234/log/')
        self.assertIsNone(self.get_context_variable('message'))

        mock_api.api_revision_log.assert_called_once_with('426', None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_log_by_ko_not_found(self, mock_api):
        # given
        mock_api.api_revision_log_by.side_effect = NotFoundExc('Not found!')

        # when
        rv = self.client.get('/browse/revision/origin/9/log/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-log.html')
        self.assertEqual(self.get_context_variable('origin_id'), 9)
        self.assertEqual(
            self.get_context_variable('message'),
            'Not found!')
        self.assertEqual(self.get_context_variable('revisions'), [])

        mock_api.api_revision_log_by.assert_called_once_with(
            9, 'refs/heads/master', None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_log_by_ko_bad_input(self, mock_api):
        # given
        mock_api.api_revision_log.side_effect = BadInputExc('wrong input!')

        # when
        rv = self.client.get('/browse/revision/abcd/log/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-log.html')
        self.assertEqual(self.get_context_variable('sha1_git'), 'abcd')
        self.assertEqual(
            self.get_context_variable('message'),
            'wrong input!')
        self.assertEqual(self.get_context_variable('revisions'), [])

        mock_api.api_revision_log.assert_called_once_with('abcd', None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_log_by(self, mock_api):
        # given
        stub_revisions = [{
            'id': 'd770e558e21961ad6cfdf0ff7df0eb5d7d4f0754',
            'date': 'Sun, 05 Jul 2015 18:01:52 GMT',
            'committer': {
                'email': 'torvalds@linux-foundation.org',
                'name': 'Linus Torvalds'
            },
            'committer_date': 'Sun, 05 Jul 2015 18:01:52 GMT',
            'type': 'git',
            'author': {
                'email': 'torvalds@linux-foundation.org',
                'name': 'Linus Torvalds'
            },
            'message': 'Linux 4.2-rc1\n',
            'synthetic': False,
            'directory_url': '/api/1/directory/'
            '2a1dbabeed4dcf1f4a4c441993b2ffc9d972780b/',
            'parent_url': [
                '/api/1/revision/a585d2b738bfa26326b3f1f40f0f1eda0c067ccf/'
            ],
        }]
        mock_api.api_revision_log_by.return_value = stub_revisions

        # when
        rv = self.client.get('/browse/revision/origin/2/log/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-log.html')
        self.assertEqual(self.get_context_variable('origin_id'), 2)
        self.assertTrue(
            isinstance(self.get_context_variable('revisions'), map))
        self.assertIsNone(self.get_context_variable('message'))

        mock_api.api_revision_log_by.assert_called_once_with(
            2, 'refs/heads/master', None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_history_ko_not_found(self, mock_api):
        # given
        mock_api.api_revision_history.side_effect = NotFoundExc(
            'Not found')

        # when
        rv = self.client.get('/browse/revision/1/history/2/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertEqual(self.get_context_variable('sha1_git_root'), '1')
        self.assertEqual(self.get_context_variable('sha1_git'), '2')
        self.assertEqual(
            self.get_context_variable('message'),
            'Not found')

        mock_api.api_revision_history.assert_called_once_with(
            '1', '2')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_history_ko_bad_input(self, mock_api):
        # given
        mock_api.api_revision_history.side_effect = BadInputExc(
            'Input incorrect')

        # when
        rv = self.client.get('/browse/revision/321/history/654/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertEqual(self.get_context_variable('sha1_git_root'), '321')
        self.assertEqual(self.get_context_variable('sha1_git'), '654')
        self.assertEqual(
            self.get_context_variable('message'),
            'Input incorrect')

        mock_api.api_revision_history.assert_called_once_with(
            '321', '654')

    @istest
    def browse_revision_history_ok_same_sha1(self):
        # when
        rv = self.client.get('/browse/revision/10/history/10/')

        # then
        self.assertEqual(rv.status_code, 302)

    @patch('swh.web.ui.views.browse.utils')
    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_history(self, mock_api, mock_utils):
        # given
        stub_revision = {'id': 'some-rev'}
        mock_api.api_revision_history.return_value = stub_revision

        expected_revision = {
            'id': 'some-rev-id',
            'author': {'name': 'foo', 'email': 'bar'},
            'committer': {'name': 'foo', 'email': 'bar'}
        }
        mock_utils.prepare_data_for_view.return_value = expected_revision

        # when
        rv = self.client.get('/browse/revision/426/history/789/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertEqual(self.get_context_variable('sha1_git_root'), '426')
        self.assertEqual(self.get_context_variable('sha1_git'), '789')
        self.assertEqual(self.get_context_variable('revision'),
                         expected_revision)

        mock_api.api_revision_history.assert_called_once_with(
            '426', '789')
        mock_utils.prepare_data_for_view.assert_called_once_with(stub_revision)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_directory_ko_not_found(self, mock_api):
        # given
        mock_api.api_revision_directory.side_effect = NotFoundExc('Not found!')

        # when
        rv = self.client.get('/browse/revision/1/directory/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '1')
        self.assertEqual(self.get_context_variable('path'), '.')
        self.assertIsNone(self.get_context_variable('result'))
        self.assertEqual(
            self.get_context_variable('message'),
            "Not found!")

        mock_api.api_revision_directory.assert_called_once_with(
            '1', None, with_data=True)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_directory_ko_bad_input(self, mock_api):
        # given
        mock_api.api_revision_directory.side_effect = BadInputExc('Bad input!')

        # when
        rv = self.client.get('/browse/revision/10/directory/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '10')
        self.assertEqual(self.get_context_variable('path'), '.')
        self.assertIsNone(self.get_context_variable('result'))
        self.assertEqual(
            self.get_context_variable('message'),
            "Bad input!")

        mock_api.api_revision_directory.assert_called_once_with(
            '10', None, with_data=True)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_directory(self, mock_api):
        # given
        stub_result0 = {
            'type': 'dir',
            'revision': '100',
            'content': [
                {
                    'id': 'some-result',
                    'type': 'file',
                    'name': 'blah',
                },
                {
                    'id': 'some-other-result',
                    'type': 'dir',
                    'name': 'foo',
                }
            ]
        }

        mock_api.api_revision_directory.return_value = stub_result0

        stub_result1 = {
            'type': 'dir',
            'revision': '100',
            'content':
            [
                {
                    'id': 'some-result',
                    'type': 'file',
                    'name': 'blah',
                },
                {
                    'id': 'some-other-result',
                    'type': 'dir',
                    'name': 'foo',
                }
            ]
        }

        # when
        rv = self.client.get('/browse/revision/100/directory/some/path/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '100')
        self.assertEqual(self.get_context_variable('revision'), '100')
        self.assertEqual(self.get_context_variable('path'), 'some/path')
        self.assertIsNone(self.get_context_variable('message'))
        self.assertEqual(self.get_context_variable('result'), stub_result1)

        mock_api.api_revision_directory.assert_called_once_with(
            '100', 'some/path', with_data=True)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_history_directory_ko_not_found(self, mock_api):
        # given
        mock_api.api_revision_history_directory.side_effect = NotFoundExc(
            'not found')

        # when
        rv = self.client.get('/browse/revision/123/history/456/directory/a/b/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertEqual(self.get_context_variable('sha1_git_root'), '123')
        self.assertEqual(self.get_context_variable('sha1_git'), '456')
        self.assertEqual(self.get_context_variable('path'), 'a/b')
        self.assertEqual(self.get_context_variable('message'), 'not found')
        self.assertIsNone(self.get_context_variable('result'))

        mock_api.api_revision_history_directory.assert_called_once_with(
            '123', '456', 'a/b', with_data=True)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_history_directory_ko_bad_input(self, mock_api):
        # given
        mock_api.api_revision_history_directory.side_effect = BadInputExc(
            'bad input')

        # when
        rv = self.client.get('/browse/revision/123/history/456/directory/a/c/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertEqual(self.get_context_variable('sha1_git_root'), '123')
        self.assertEqual(self.get_context_variable('sha1_git'), '456')
        self.assertEqual(self.get_context_variable('path'), 'a/c')
        self.assertEqual(self.get_context_variable('message'), 'bad input')
        self.assertIsNone(self.get_context_variable('result'))

        mock_api.api_revision_history_directory.assert_called_once_with(
            '123', '456', 'a/c', with_data=True)

    @patch('swh.web.ui.views.browse.service')
    @istest
    def browse_revision_history_directory_ok_no_trailing_slash_so_redirect(
            self, mock_service):
        # when
        rv = self.client.get('/browse/revision/1/history/2/directory/path/to')

        # then
        self.assertEqual(rv.status_code, 301)

    @patch('swh.web.ui.views.browse.service')
    @istest
    def browse_revision_history_directory_ok_same_sha1_redirects(
            self, mock_service):
        # when
        rv = self.client.get('/browse/revision/1/history/1/directory/path/to')

        # then
        self.assertEqual(rv.status_code, 301)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_history_directory(self, mock_api):
        # given
        stub_result0 = {
            'type': 'dir',
            'revision': '1000',
            'content': [{
                'id': 'some-result',
                'type': 'file',
                'name': 'blah'
            }]
        }

        mock_api.api_revision_history_directory.return_value = stub_result0

        stub_result1 = {
            'type': 'dir',
            'revision': '1000',
            'content': [{
                'id': 'some-result',
                'type': 'file',
                'name': 'blah'
            }]
        }

        # when
        rv = self.client.get('/browse/revision/100/history/999/directory/'
                             'path/to/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertEqual(self.get_context_variable('sha1_git_root'), '100')
        self.assertEqual(self.get_context_variable('sha1_git'), '999')
        self.assertEqual(self.get_context_variable('revision'), '1000')
        self.assertEqual(self.get_context_variable('path'), 'path/to')
        self.assertIsNone(self.get_context_variable('message'))
        self.assertEqual(self.get_context_variable('result'), stub_result1)

        mock_api.api_revision_history_directory.assert_called_once_with(
            '100', '999', 'path/to', with_data=True)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_history_through_origin_ko_bad_input(self, mock_api):
        # given
        mock_api.api_revision_history_through_origin.side_effect = BadInputExc(
            'Problem input.')  # noqa

        # when
        rv = self.client.get('/browse/revision/origin/99'
                             '/history/123/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertIsNone(self.get_context_variable('revision'))
        self.assertEqual(self.get_context_variable('message'),
                         'Problem input.')

        mock_api.api_revision_history_through_origin.assert_called_once_with(
            99, 'refs/heads/master', None, '123')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_history_through_origin_ko_not_found(self, mock_api):
        # given
        mock_api.api_revision_history_through_origin.side_effect = NotFoundExc(
            'Not found.')

        # when
        rv = self.client.get('/browse/revision/origin/999/'
                             'branch/dev/history/123/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertIsNone(self.get_context_variable('revision'))
        self.assertEqual(self.get_context_variable('message'),
                         'Not found.')

        mock_api.api_revision_history_through_origin.assert_called_once_with(
            999, 'dev', None, '123')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_history_through_origin_ko_other_error(self, mock_api):
        # given
        mock_api.api_revision_history_through_origin.side_effect = ValueError(
            'Other Error.')

        # when
        rv = self.client.get('/browse/revision/origin/438'
                             '/branch/scratch'
                             '/ts/2016'
                             '/history/789/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertIsNone(self.get_context_variable('revision'))
        self.assertEqual(self.get_context_variable('message'),
                         'Other Error.')

        mock_api.api_revision_history_through_origin.assert_called_once_with(
            438, 'scratch', '2016', '789')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_history_through_origin(self, mock_api):
        # given
        stub_rev = {
            'id': 'some-id',
            'author': {},
            'committer': {}
        }
        mock_api.api_revision_history_through_origin.return_value = stub_rev

        # when
        rv = self.client.get('/browse/revision/origin/99/history/123/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertEqual(self.get_context_variable('revision'), stub_rev)
        self.assertIsNone(self.get_context_variable('message'))

        mock_api.api_revision_history_through_origin.assert_called_once_with(
            99, 'refs/heads/master', None, '123')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_with_origin_ko_not_found(self, mock_api):
        # given
        mock_api.api_revision_with_origin.side_effect = NotFoundExc(
            'Not found')

        # when
        rv = self.client.get('/browse/revision/origin/1/')

        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertIsNone(self.get_context_variable('revision'))
        self.assertEqual(self.get_context_variable('message'), 'Not found')

        mock_api.api_revision_with_origin.assert_called_once_with(
            1, 'refs/heads/master', None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_with_origin_ko_bad_input(self, mock_api):
        # given
        mock_api.api_revision_with_origin.side_effect = BadInputExc(
            'Bad Input')

        # when
        rv = self.client.get('/browse/revision/origin/1000/branch/dev/')

        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertIsNone(self.get_context_variable('revision'))
        self.assertEqual(self.get_context_variable('message'), 'Bad Input')

        mock_api.api_revision_with_origin.assert_called_once_with(
            1000, 'dev', None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_with_origin_ko_other(self, mock_api):
        # given
        mock_api.api_revision_with_origin.side_effect = ValueError(
            'Other')

        # when
        rv = self.client.get('/browse/revision/origin/1999'
                             '/branch/scratch/master'
                             '/ts/1990-01-10/')

        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertIsNone(self.get_context_variable('revision'))
        self.assertEqual(self.get_context_variable('message'), 'Other')

        mock_api.api_revision_with_origin.assert_called_once_with(
            1999, 'scratch/master', '1990-01-10')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_with_origin(self, mock_api):
        # given
        stub_rev = {'id': 'some-id',
                    'author': {},
                    'committer': {}}
        mock_api.api_revision_with_origin.return_value = stub_rev

        # when
        rv = self.client.get('/browse/revision/origin/1/')

        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertEqual(self.get_context_variable('revision'), stub_rev)
        self.assertIsNone(self.get_context_variable('message'))

        mock_api.api_revision_with_origin.assert_called_once_with(
            1, 'refs/heads/master', None)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_directory_through_origin_ko_not_found(self, mock_api):
        # given
        mock_api.api_directory_through_revision_origin.side_effect = BadInputExc(  # noqa
            'this is not the robot you are looking for')

        # when
        rv = self.client.get('/browse/revision/origin/2'
                             '/directory/')

        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertIsNone(self.get_context_variable('result'))
        self.assertEqual(self.get_context_variable('message'),
                         'this is not the robot you are looking for')

        mock_api.api_directory_through_revision_origin.assert_called_once_with(  # noqa
            2, 'refs/heads/master', None, None, with_data=True)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_directory_through_origin_ko_bad_input(self, mock_api):
        # given
        mock_api.api_directory_through_revision_origin.side_effect = BadInputExc(  # noqa
            'Bad Robot')

        # when
        rv = self.client.get('/browse/revision/origin/2'
                             '/directory/')

        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertIsNone(self.get_context_variable('result'))
        self.assertEqual(self.get_context_variable('message'), 'Bad Robot')

        mock_api.api_directory_through_revision_origin.assert_called_once_with(
            2, 'refs/heads/master', None, None, with_data=True)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_directory_through_origin_ko_other(self, mock_api):
        # given
        mock_api.api_directory_through_revision_origin.side_effect = ValueError(  # noqa
            'Other bad stuff')

        # when
        rv = self.client.get('/browse/revision/origin/2'
                             '/directory/')

        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertIsNone(self.get_context_variable('result'))
        self.assertEqual(self.get_context_variable('message'),
                         'Other bad stuff')

        mock_api.api_directory_through_revision_origin.assert_called_once_with(
            2, 'refs/heads/master', None, None, with_data=True)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_revision_directory_through_origin(self, mock_api):
        # given
        stub_res = {'id': 'some-id',
                    'revision': 'some-rev-id',
                    'type': 'dir',
                    'content': 'some-content'}
        mock_api.api_directory_through_revision_origin.return_value = stub_res

        # when
        rv = self.client.get('/browse/revision/origin/2'
                             '/branch/dev'
                             '/ts/2013-20-20 10:02'
                             '/directory/some/file/')

        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertEqual(self.get_context_variable('result'), stub_res)
        self.assertIsNone(self.get_context_variable('message'))

        mock_api.api_directory_through_revision_origin.assert_called_once_with(
            2, 'dev', '2013-20-20 10:02', 'some/file', with_data=True)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_directory_through_revision_with_origin_history_ko_not_found(
            self, mock_api):
        mock_api.api_directory_through_revision_with_origin_history.side_effect = NotFoundExc(  # noqa
            'Not found!')

        # when
        rv = self.client.get('/browse/revision/origin/987'
                             '/history/sha1git'
                             '/directory/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertIsNone(self.get_context_variable('result'))
        self.assertEqual(self.get_context_variable('message'), 'Not found!')
        self.assertEqual(self.get_context_variable('path'), '.')

        mock_api.api_directory_through_revision_with_origin_history.assert_called_once_with(  # noqa
            987, 'refs/heads/master', None, 'sha1git', None, with_data=True)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_directory_through_revision_with_origin_history_ko_bad_input(
            self, mock_api):
        mock_api.api_directory_through_revision_with_origin_history.side_effect = BadInputExc(  # noqa
            'Bad input! Bleh!')

        # when
        rv = self.client.get('/browse/revision/origin/798'
                             '/branch/refs/heads/dev'
                             '/ts/2012-11-11'
                             '/history/1234'
                             '/directory/some/path/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertIsNone(self.get_context_variable('result'))
        self.assertEqual(self.get_context_variable('message'),
                         'Bad input! Bleh!')
        self.assertEqual(self.get_context_variable('path'), 'some/path')

        mock_api.api_directory_through_revision_with_origin_history.assert_called_once_with(  # noqa
            798, 'refs/heads/dev', '2012-11-11', '1234', 'some/path',
            with_data=True)

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_directory_through_revision_with_origin_history(
            self, mock_api):
        stub_dir = {'type': 'dir',
                    'content': [],
                    'revision': 'specific-rev-id'}
        mock_api.api_directory_through_revision_with_origin_history.return_value = stub_dir  # noqa

        # when
        rv = self.client.get('/browse/revision/origin/101010'
                             '/ts/1955-11-12'
                             '/history/54628'
                             '/directory/emacs-24.5/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('revision-directory.html')
        self.assertEqual(self.get_context_variable('result'), stub_dir)
        self.assertIsNone(self.get_context_variable('message'))
        self.assertEqual(self.get_context_variable('path'), 'emacs-24.5')

        mock_api.api_directory_through_revision_with_origin_history.assert_called_once_with(  # noqa
            101010, 'refs/heads/master', '1955-11-12', '54628', 'emacs-24.5',
            with_data=True)


class EntityView(test_app.SWHViewTestCase):
    render_template = False

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_entity_ko_not_found(self, mock_api):
        # given
        mock_api.api_entity_by_uuid.side_effect = NotFoundExc('Not found!')

        # when
        rv = self.client.get('/browse/entity/'
                             '5f4d4c51-498a-4e28-88b3-b3e4e8396cba/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('entity.html')
        self.assertEqual(self.get_context_variable('entities'), [])
        self.assertEqual(self.get_context_variable('message'), 'Not found!')

        mock_api.api_entity_by_uuid.assert_called_once_with(
            '5f4d4c51-498a-4e28-88b3-b3e4e8396cba')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_entity_ko_bad_input(self, mock_api):
        # given
        mock_api.api_entity_by_uuid.side_effect = BadInputExc('wrong input!')

        # when
        rv = self.client.get('/browse/entity/blah-blah-uuid/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('entity.html')
        self.assertEqual(self.get_context_variable('entities'), [])
        self.assertEqual(self.get_context_variable('message'), 'wrong input!')

        mock_api.api_entity_by_uuid.assert_called_once_with(
            'blah-blah-uuid')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def browse_entity(self, mock_api):
        # given
        stub_entities = [
            {'id': '5f4d4c51-5a9b-4e28-88b3-b3e4e8396cba'}]
        mock_api.api_entity_by_uuid.return_value = stub_entities

        # when
        rv = self.client.get('/browse/entity/'
                             '5f4d4c51-5a9b-4e28-88b3-b3e4e8396cba/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assert_template_used('entity.html')
        self.assertEqual(self.get_context_variable('entities'), stub_entities)
        self.assertIsNone(self.get_context_variable('message'))

        mock_api.api_entity_by_uuid.assert_called_once_with(
            '5f4d4c51-5a9b-4e28-88b3-b3e4e8396cba')


class Lookup(TestCase):
    @patch('swh.web.ui.views.browse.api')
    @istest
    def api_lookup(self, mock_api):
        # given
        mock_api.api_content_metadata.return_value = {'id': 'blah'}

        # given
        r = browse.api_lookup(mock_api.api_content_metadata, 'sha1:blah')

        # then
        self.assertEquals(r, {'id': 'blah'})
        mock_api.api_content_metadata.assert_called_once_with('sha1:blah')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def api_lookup_not_found(self, mock_api):
        # given
        mock_api.api_content_filetype.side_effect = NotFoundExc

        # given
        r = browse.api_lookup(mock_api.api_content_filetype, 'sha1_git:foo')

        # then
        self.assertIsNone(r)
        mock_api.api_content_filetype.assert_called_once_with('sha1_git:foo')

    @patch('swh.web.ui.views.browse.api')
    @istest
    def api_lookup_bad_input(self, mock_api):
        # given
        mock_api.api_content_license.side_effect = BadInputExc

        # given
        r = browse.api_lookup(mock_api.api_content_license, 'sha1_git:foo')

        # then
        self.assertIsNone(r)
        mock_api.api_content_license.assert_called_once_with('sha1_git:foo')
