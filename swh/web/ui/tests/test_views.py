# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from nose.tools import istest

from swh.web.ui.tests import test_app
from unittest.mock import patch, MagicMock
from swh.web.ui.exc import BadInputExc


class ViewTestCase(test_app.SWHViewTestCase):
    render_template = False

    @istest
    def info(self):
        # when
        rv = self.client.get('/about')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('about.html')
        self.assertIn(b'About', rv.data)

    @istest
    def search_default(self):
        # when
        rv = self.client.get('/search')

        self.assertEquals(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('q'), '')
        self.assertEqual(self.get_context_variable('message'), '')
        self.assert_template_used('search.html')

    @patch('swh.web.ui.views.service')
    @istest
    def search_content_found(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {
            'found': True,
            'algo': 'sha1'
        }

        # when
        rv = self.client.get('/search?q=sha1:123')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('search.html')
        self.assertEqual(self.get_context_variable('q'), 'sha1:123')
        self.assertEqual(self.get_context_variable('message'),
                         'Content with hash sha1:123 found!')

        mock_service.lookup_hash.assert_called_once_with('sha1:123')

    @patch('swh.web.ui.views.service')
    @istest
    def search_content_not_found(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {
            'found': False,
            'algo': 'sha1'
        }

        # when
        rv = self.client.get('/search?q=sha1:456')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('search.html')
        self.assertEqual(self.get_context_variable('q'), 'sha1:456')
        self.assertEqual(self.get_context_variable('message'),
                         'Content with hash sha1:456 not found!')

        mock_service.lookup_hash.assert_called_once_with('sha1:456')

    @patch('swh.web.ui.views.service')
    @istest
    def search_content_invalid_query(self, mock_service):
        # given
        mock_service.lookup_hash = MagicMock(
            side_effect=BadInputExc('Invalid query!')
        )

        # when
        rv = self.client.get('/search?q=sha1:invalid-hash')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('search.html')
        self.assertEqual(self.get_context_variable('q'), 'sha1:invalid-hash')
        self.assertEqual(self.get_context_variable('message'),
                         'Invalid query!')

        mock_service.lookup_hash.assert_called_once_with('sha1:invalid-hash')

    @patch('swh.web.ui.views.service')
    @istest
    def show_content(self, mock_service):
        # given
        stub_content_raw = {
            'sha1': 'sha1-hash',
            'data': 'some-data'
        }
        mock_service.lookup_content_raw.return_value = stub_content_raw

        # when
        rv = self.client.get('/browse/content/sha1:sha1-hash/raw')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('display_content.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Content sha1-hash')
        self.assertEqual(self.get_context_variable('content'),
                         stub_content_raw)

        mock_service.lookup_content_raw.assert_called_once_with(
            'sha1:sha1-hash')

    @patch('swh.web.ui.views.service')
    @istest
    def show_content_not_found(self, mock_service):
        # given
        mock_service.lookup_content_raw.return_value = None

        # when
        rv = self.client.get('/browse/content/sha1:sha1-unknown/raw')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('display_content.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Content with sha1:sha1-unknown not found.')
        self.assertEqual(self.get_context_variable('content'), None)
        mock_service.lookup_content_raw.assert_called_once_with(
            'sha1:sha1-unknown')

    @patch('swh.web.ui.views.service')
    @istest
    def show_content_invalid_hash(self, mock_service):
        # given
        mock_service.lookup_content_raw.side_effect = BadInputExc(
            'Invalid hash')

        # when
        rv = self.client.get('/browse/content/sha2:sha1-invalid/raw')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('display_content.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Invalid hash')
        self.assertEqual(self.get_context_variable('content'), None)
        mock_service.lookup_content_raw.assert_called_once_with(
            'sha2:sha1-invalid')

    @patch('swh.web.ui.views.service')
    @patch('swh.web.ui.utils')
    @istest
    def browse_directory_bad_input(self, mock_utils, mock_service):
        # given
        mock_service.lookup_directory.side_effect = BadInputExc('Invalid hash')

        # when
        rv = self.client.get('/browse/directory/sha2-invalid')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('directory.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Invalid hash')
        self.assertEqual(self.get_context_variable('files'), [])
        mock_service.lookup_directory.assert_called_once_with(
            'sha2-invalid')

    @patch('swh.web.ui.views.service')
    @patch('swh.web.ui.utils')
    @istest
    def browse_directory_empty_result(self, mock_utils, mock_service):
        # given
        mock_service.lookup_directory.return_value = None

        # when
        rv = self.client.get('/browse/directory/some-sha1')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('directory.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Directory some-sha1 not found.')
        self.assertEqual(self.get_context_variable('files'), [])
        mock_service.lookup_directory.assert_called_once_with(
            'some-sha1')

    @patch('swh.web.ui.views.service')
    @patch('swh.web.ui.views.utils')
    @istest
    def browse_directory(self, mock_utils, mock_service):
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
        mock_service.lookup_directory.return_value = stub_directory_ls
        stub_directory_map = [
            {'link': '/path/to/url/dir/123',
             'name': 'some-dir-name'},
            {'link': '/path/to/url/file/654',
             'name': 'some-filename'},
            {'link': '/path/to/url/dir/987',
             'name': 'some-other-dirname'}
        ]
        mock_utils.prepare_directory_listing.return_value = stub_directory_map

        # when
        rv = self.client.get('/browse/directory/some-sha1')

        # then
        print(self.templates)
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('directory.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Listing for directory some-sha1:')
        self.assertEqual(self.get_context_variable('files'),
                         stub_directory_map)

        mock_service.lookup_directory.assert_called_once_with(
            'some-sha1')
        mock_utils.prepare_directory_listing.assert_called_once_with(
            stub_directory_ls)
