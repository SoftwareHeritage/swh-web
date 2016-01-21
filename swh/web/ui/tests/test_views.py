# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from nose.tools import istest

from swh.web.ui.tests import test_app
from unittest.mock import patch
from swh.web.ui.exc import BadInputExc


class FileMock():
    def __init__(self, filename):
        self.filename = filename


class ViewTestCase(test_app.SWHViewTestCase):
    render_template = False

    @istest
    def info(self):
        # when
        rv = self.client.get('/about/')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('about.html')
        self.assertIn(b'About', rv.data)

    @istest
    def search_default(self):
        # when
        rv = self.client.get('/search/')

        self.assertEquals(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('q'), '')
        self.assertEqual(self.get_context_variable('messages'), [])
        self.assertEqual(self.get_context_variable('filename'), None)
        self.assertEqual(self.get_context_variable('file'), None)
        self.assert_template_used('upload_and_search.html')

    @patch('swh.web.ui.views.service')
    @istest
    def search_get_query_hash_not_found(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {'found': None}

        # when
        rv = self.client.get('/search/?q=sha1:456')

        self.assertEquals(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('q'), 'sha1:456')
        self.assertEqual(self.get_context_variable('messages'),
                         ['Content with hash sha1:456 not found!'])
        self.assertEqual(self.get_context_variable('filename'), None)
        self.assertEqual(self.get_context_variable('file'), None)
        self.assert_template_used('upload_and_search.html')

        mock_service.lookup_hash.assert_called_once_with('sha1:456')

    @patch('swh.web.ui.views.service')
    @istest
    def search_get_query_hash_bad_input(self, mock_service):
        # given
        mock_service.lookup_hash.side_effect = BadInputExc('error msg')

        # when
        rv = self.client.get('/search/?q=sha1_git:789')

        self.assertEquals(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('q'), 'sha1_git:789')
        self.assertEqual(self.get_context_variable('messages'),
                         ['error msg'])
        self.assertEqual(self.get_context_variable('filename'), None)
        self.assertEqual(self.get_context_variable('file'), None)
        self.assert_template_used('upload_and_search.html')

        mock_service.lookup_hash.assert_called_once_with('sha1_git:789')

    @patch('swh.web.ui.views.service')
    @istest
    def search_get_query_hash_found(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {'found': True}

        # when
        rv = self.client.get('/search/?q=sha1:123')

        self.assertEquals(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('q'), 'sha1:123')
        self.assertEqual(self.get_context_variable('messages'),
                         ['Content with hash sha1:123 found!'])
        self.assertEqual(self.get_context_variable('filename'), None)
        self.assertEqual(self.get_context_variable('file'), None)
        self.assert_template_used('upload_and_search.html')

        mock_service.lookup_hash.assert_called_once_with('sha1:123')

    @patch('swh.web.ui.views.service')
    @istest
    def search_post_query_hash_not_found(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {'found': None}

        # when
        rv = self.client.get('/search/?q=sha1:456')

        self.assertEquals(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('q'), 'sha1:456')
        self.assertEqual(self.get_context_variable('messages'),
                         ['Content with hash sha1:456 not found!'])
        self.assertEqual(self.get_context_variable('filename'), None)
        self.assertEqual(self.get_context_variable('file'), None)
        self.assert_template_used('upload_and_search.html')

        mock_service.lookup_hash.assert_called_once_with('sha1:456')

    @patch('swh.web.ui.views.service')
    @istest
    def search_post_query_hash_bad_input(self, mock_service):
        # given
        mock_service.lookup_hash.side_effect = BadInputExc('error msg!')

        # when
        rv = self.client.post('/search/', data=dict(q='sha1_git:987'))

        self.assertEquals(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('q'), 'sha1_git:987')
        self.assertEqual(self.get_context_variable('messages'),
                         ['error msg!'])
        self.assertEqual(self.get_context_variable('filename'), None)
        self.assertEqual(self.get_context_variable('file'), None)
        self.assert_template_used('upload_and_search.html')

        mock_service.lookup_hash.assert_called_once_with('sha1_git:987')

    @patch('swh.web.ui.views.service')
    @istest
    def search_post_query_hash_found(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {'found': True}

        # when
        rv = self.client.post('/search/', data=dict(q='sha1:321'))

        self.assertEquals(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('q'), 'sha1:321')
        self.assertEqual(self.get_context_variable('messages'),
                         ['Content with hash sha1:321 found!'])
        self.assertEqual(self.get_context_variable('filename'), None)
        self.assertEqual(self.get_context_variable('file'), None)
        self.assert_template_used('upload_and_search.html')

        mock_service.lookup_hash.assert_called_once_with('sha1:321')

    @patch('swh.web.ui.views.service')
    @patch('swh.web.ui.views.request')
    @istest
    def search_post_upload_and_hash_bad_input(self, mock_request,
                                              mock_service):
        # given
        mock_request.data = {}
        mock_request.method = 'POST'
        mock_request.files = dict(filename=FileMock('foobar'))
        mock_service.upload_and_search.side_effect = BadInputExc(
            'error bad input')

        # when (mock_request completes the post request)
        rv = self.client.post('/search/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('messages'),
                         ['error bad input'])
        self.assert_template_used('upload_and_search.html')

        mock_service.upload_and_search.called = True

    @patch('swh.web.ui.views.service')
    @patch('swh.web.ui.views.request')
    @istest
    def search_post_upload_and_hash_not_found(self, mock_request,
                                              mock_service):
        # given
        mock_request.data = {}
        mock_request.method = 'POST'
        mock_request.files = dict(filename=FileMock('foobar'))
        mock_service.upload_and_search.return_value = {'filename': 'foobar',
                                                       'sha1': 'blahhash',
                                                       'found': False}

        # when (mock_request completes the post request)
        rv = self.client.post('/search/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('messages'),
                         ["File foobar with hash blahhash not found!"])
        self.assertEqual(self.get_context_variable('filename'), 'foobar')
        self.assertEqual(self.get_context_variable('sha1'), 'blahhash')
        self.assert_template_used('upload_and_search.html')

        mock_service.upload_and_search.called = True

    @patch('swh.web.ui.views.service')
    @patch('swh.web.ui.views.request')
    @istest
    def search_post_upload_and_hash_found(self, mock_request, mock_service):
        # given
        mock_request.data = {}
        mock_request.method = 'POST'
        mock_request.files = dict(filename=FileMock('foobar'))
        mock_service.upload_and_search.return_value = {'filename': 'foobar',
                                                       'sha1': '123456789',
                                                       'found': True}

        # when (mock_request completes the post request)
        rv = self.client.post('/search/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEqual(self.get_context_variable('messages'),
                         ["File foobar with hash 123456789 found!"])
        self.assertEqual(self.get_context_variable('filename'), 'foobar')
        self.assertEqual(self.get_context_variable('sha1'), '123456789')
        self.assert_template_used('upload_and_search.html')

        mock_service.upload_and_search.called = True

    @patch('swh.web.ui.views.service')
    @istest
    def browse_content_detail_not_found(self, mock_service):
        # given
        mock_service.lookup_content.return_value = None

        # when
        rv = self.client.get('/browse/content/sha1:sha1-hash/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('content.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Content with sha1:sha1-hash not found.')
        self.assertEqual(self.get_context_variable('content'),
                         None)

        mock_service.lookup_content.assert_called_once_with(
            'sha1:sha1-hash')

    @patch('swh.web.ui.views.service')
    @istest
    def browse_content_detail_bad_input(self, mock_service):
        # given
        mock_service.lookup_content.side_effect = BadInputExc('Bad input!')

        # when
        rv = self.client.get('/browse/content/sha1:sha1-hash/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('content.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Bad input!')
        self.assertIsNone(self.get_context_variable('content'))

        mock_service.lookup_content.assert_called_once_with(
            'sha1:sha1-hash')

    @patch('swh.web.ui.views.service')
    @istest
    def browse_content_detail(self, mock_service):
        # given
        stub_content = {'sha1': 'sha1_hash'}
        mock_service.lookup_content.return_value = stub_content

        # when
        rv = self.client.get('/browse/content/sha1:sha1-hash/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('content.html')
        self.assertIsNone(self.get_context_variable('message'))
        self.assertEqual(self.get_context_variable('content'),
                         {'sha1': 'sha1_hash'})

        mock_service.lookup_content.assert_called_once_with(
            'sha1:sha1-hash')

    @patch('swh.web.ui.views.service')
    @istest
    def browse_content_data(self, mock_service):
        # given
        stub_content_raw = {
            'sha1': 'sha1-hash',
            'data': b'some-data'
        }
        mock_service.lookup_content_raw.return_value = stub_content_raw

        # when
        rv = self.client.get('/browse/content/sha1:sha1-hash/raw/')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('content-data.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Content sha1-hash')
        self.assertEqual(self.get_context_variable('content'),
                         stub_content_raw)

        mock_service.lookup_content_raw.assert_called_once_with(
            'sha1:sha1-hash')

    @patch('swh.web.ui.views.service')
    @istest
    def browse_content_data_not_found(self, mock_service):
        # given
        mock_service.lookup_content_raw.return_value = None

        # when
        rv = self.client.get('/browse/content/sha1:sha1-unknown/raw/')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('content-data.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Content with sha1:sha1-unknown not found.')
        self.assertEqual(self.get_context_variable('content'), None)
        mock_service.lookup_content_raw.assert_called_once_with(
            'sha1:sha1-unknown')

    @patch('swh.web.ui.views.service')
    @istest
    def browse_content_data_invalid_hash(self, mock_service):
        # given
        mock_service.lookup_content_raw.side_effect = BadInputExc(
            'Invalid hash')

        # when
        rv = self.client.get('/browse/content/sha2:sha1-invalid/raw/')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('content-data.html')
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
        rv = self.client.get('/browse/directory/sha2-invalid/')

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
        rv = self.client.get('/browse/directory/some-sha1/')

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
        rv = self.client.get('/browse/directory/some-sha1/')

        # then
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

    @patch('swh.web.ui.views.service')
#    @istest
    def browse_content_with_origin_content_not_found(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {'found': False}

        # when
        rv = self.client.get('/browse/content/sha256:some-sha256/origin/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('content-with-origin.html')
        self.assertEqual(self.get_context_variable('message'),
                         'Hash sha256:some-sha256 was not found.')

        mock_service.lookup_hash.assert_called_once_with(
            'sha256:some-sha256')
        mock_service.lookup_hash_origin.called = False

    @patch('swh.web.ui.views.service')
#    @istest
    def browse_content_with_origin_bad_input(self, mock_service):
        # given
        mock_service.lookup_hash.side_effect = BadInputExc('Invalid hash')

        # when
        rv = self.client.get('/browse/content/sha256:some-sha256/origin/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('content-with-origin.html')
        self.assertEqual(
            self.get_context_variable('message'), 'Invalid hash')

        mock_service.lookup_hash.assert_called_once_with(
            'sha256:some-sha256')
        mock_service.lookup_hash_origin.called = False

    @patch('swh.web.ui.views.service')
#    @istest
    def browse_content_with_origin(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {'found': True}
        mock_service.lookup_hash_origin.return_value = {
            'origin_type': 'ftp',
            'origin_url': '/some/url',
            'revision': 'revision-hash',
            'branch': 'master',
            'path': '/path/to',
        }

        # when
        rv = self.client.get('/browse/content/sha256:some-sha256/origin/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('content-with-origin.html')
        self.assertEqual(
            self.get_context_variable('message'),
            "The content with hash sha256:some-sha256 has been seen on " +
            "origin with type 'ftp'\n" +
            "at url '/some/url'. The revision was identified at " +
            "'revision-hash' on branch 'master'.\n" +
            "The file's path referenced was '/path/to'.")

        mock_service.lookup_hash.assert_called_once_with(
            'sha256:some-sha256')
        mock_service.lookup_hash_origin.assert_called_once_with(
            'sha256:some-sha256')

    @patch('swh.web.ui.views.service')
    @istest
    def browse_origin_not_found(self, mock_service):
        # given
        mock_service.lookup_origin.return_value = None

        # when
        rv = self.client.get('/browse/origin/1/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('origin.html')
        self.assertEqual(self.get_context_variable('origin_id'), 1)
        self.assertEqual(
            self.get_context_variable('message'),
            'Origin 1 not found!')

        mock_service.lookup_origin.assert_called_once_with(1)

    @patch('swh.web.ui.views.service')
    @istest
    def browse_origin_found(self, mock_service):
        # given
        mock_origin = {'type': 'git',
                       'lister': None,
                       'project': None,
                       'url': 'rsync://some/url',
                       'id': 426}
        mock_service.lookup_origin.return_value = mock_origin

        # when
        rv = self.client.get('/browse/origin/426/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('origin.html')
        self.assertEqual(self.get_context_variable('origin_id'), 426)
        self.assertEqual(self.get_context_variable('origin'), mock_origin)

        mock_service.lookup_origin.assert_called_once_with(426)

    @patch('swh.web.ui.views.service')
    @istest
    def browse_origin_bad_input(self, mock_service):
        # given
        mock_service.lookup_origin.side_effect = BadInputExc('wrong input')

        # when
        rv = self.client.get('/browse/origin/426/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('origin.html')
        self.assertEqual(self.get_context_variable('origin_id'), 426)

        mock_service.lookup_origin.assert_called_once_with(426)

    @patch('swh.web.ui.views.service')
    @istest
    def browse_person_not_found(self, mock_service):
        # given
        mock_service.lookup_person.return_value = None

        # when
        rv = self.client.get('/browse/person/1/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('person.html')
        self.assertEqual(self.get_context_variable('person_id'), 1)
        self.assertEqual(
            self.get_context_variable('message'),
            'Person 1 not found!')

        mock_service.lookup_person.assert_called_once_with(1)

    @patch('swh.web.ui.views.service')
    @istest
    def browse_person_found(self, mock_service):
        # given
        mock_person = {'type': 'git',
                       'lister': None,
                       'project': None,
                       'url': 'rsync://some/url',
                       'id': 426}
        mock_service.lookup_person.return_value = mock_person

        # when
        rv = self.client.get('/browse/person/426/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('person.html')
        self.assertEqual(self.get_context_variable('person_id'), 426)
        self.assertEqual(self.get_context_variable('person'), mock_person)

        mock_service.lookup_person.assert_called_once_with(426)

    @patch('swh.web.ui.views.service')
    @istest
    def browse_person_bad_input(self, mock_service):
        # given
        mock_service.lookup_person.side_effect = BadInputExc('wrong input')

        # when
        rv = self.client.get('/browse/person/426/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('person.html')
        self.assertEqual(self.get_context_variable('person_id'), 426)

        mock_service.lookup_person.assert_called_once_with(426)

    @patch('swh.web.ui.views.service')
    @istest
    def browse_release_not_found(self, mock_service):
        # given
        mock_service.lookup_release.return_value = None

        # when
        rv = self.client.get('/browse/release/1/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('release.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '1')
        self.assertEqual(
            self.get_context_variable('message'),
            'Release 1 not found!')

        mock_service.lookup_release.assert_called_once_with('1')

    @patch('swh.web.ui.views.service')
    @istest
    def browse_release_bad_input(self, mock_service):
        # given
        mock_service.lookup_release.side_effect = BadInputExc('wrong input')

        # when
        rv = self.client.get('/browse/release/426/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('release.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '426')

        mock_service.lookup_release.assert_called_once_with('426')

    @patch('swh.web.ui.views.service')
    @istest
    def browse_release_found(self, mock_service):
        # given
        mock_release = {
            "date": "Sun, 05 Jul 2015 18:02:06 GMT",
            "id": "1e951912027ea6873da6985b91e50c47f645ae1a",
            "target": "d770e558e21961ad6cfdf0ff7df0eb5d7d4f0754",
            "synthetic": False,
            "target_type": "revision",
            "author": {
                "email": "torvalds@linux-foundation.org",
                "name": "Linus Torvalds"
            },
            "message": "Linux 4.2-rc1\n",
            "name": "v4.2-rc1"
        }
        mock_service.lookup_release.return_value = mock_release

        expected_release = {
            "date": "Sun, 05 Jul 2015 18:02:06 GMT",
            "id": "1e951912027ea6873da6985b91e50c47f645ae1a",
            "target": '/browse/revision/d770e558e21961ad6cfdf0ff7df0'
                      'eb5d7d4f0754/',
            "synthetic": False,
            "target_type": "revision",
            "author": "Linus Torvalds <torvalds@linux-foundation.org>",
            "message": "Linux 4.2-rc1\n",
            "name": "v4.2-rc1"
        }

        # when
        rv = self.client.get('/browse/release/426/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('release.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '426')
        self.assertEqual(self.get_context_variable('release'),
                         expected_release)
        self.assertEqual(self.get_context_variable('keys'), [
            'id', 'name', 'date', 'message', 'author', 'target',
            'target_type'])

        mock_service.lookup_release.assert_called_once_with('426')

    @patch('swh.web.ui.views.service')
    @istest
    def browse_revision_not_found(self, mock_service):
        # given
        mock_service.lookup_revision.return_value = None

        # when
        rv = self.client.get('/browse/revision/1/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '1')
        self.assertEqual(
            self.get_context_variable('message'),
            'Revision 1 not found!')

        mock_service.lookup_revision.assert_called_once_with('1')

    @patch('swh.web.ui.views.service')
    @istest
    def browse_revision_bad_input(self, mock_service):
        # given
        mock_service.lookup_revision.side_effect = BadInputExc('wrong input')

        # when
        rv = self.client.get('/browse/revision/426/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '426')

        mock_service.lookup_revision.assert_called_once_with('426')

    @patch('swh.web.ui.views.service')
    @istest
    def browse_revision_found(self, mock_service):
        # given
        mock_revision = {
            'id': 'd770e558e21961ad6cfdf0ff7df0eb5d7d4f0754',
            'date': 'Sun, 05 Jul 2015 18:01:52 GMT',
            'committer': {
                'email': 'torvalds@linux-foundation.org',
                'name': 'Linus Torvalds'
            },
            'committer_date': 'Sun, 05 Jul 2015 18:01:52 GMT',
            'metadata': None,
            'type': 'git',
            'author': {
                'email': 'torvalds@linux-foundation.org',
                'name': 'Linus Torvalds'
            },
            'message': 'Linux 4.2-rc1\n',
            'synthetic': False,
            'directory': '2a1dbabeed4dcf1f4a4c441993b2ffc9d972780b',
            'parents': [
                'a585d2b738bfa26326b3f1f40f0f1eda0c067ccf'
            ],
        }
        mock_service.lookup_revision.return_value = mock_revision

        expected_revision = {
            'id': 'd770e558e21961ad6cfdf0ff7df0eb5d7d4f0754',
            'date': 'Sun, 05 Jul 2015 18:01:52 GMT',
            'committer': 'Linus Torvalds <torvalds@linux-foundation.org>',
            'committer_date': 'Sun, 05 Jul 2015 18:01:52 GMT',
            'type': 'git',
            'author': 'Linus Torvalds <torvalds@linux-foundation.org>',
            'message': 'Linux 4.2-rc1\n',
            'synthetic': False,
            'metadata': None,
            'parents': [
                '/browse/revision/a585d2b738bfa26326b3f1f40f0f1eda0c067ccf/'
            ],
            'directory': '/browse/directory/2a1dbabeed4dcf1f4a4c441993b2f'
            'fc9d972780b/',
        }

        # when
        rv = self.client.get('/browse/revision/426/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('revision.html')
        self.assertEqual(self.get_context_variable('sha1_git'), '426')
        self.assertEqual(self.get_context_variable('revision'),
                         expected_revision)
        self.assertEqual(self.get_context_variable('keys'),
                         ['id', 'message',
                          'date', 'author',
                          'committer', 'committer_date',
                          'synthetic'])

        mock_service.lookup_revision.assert_called_once_with('426')
