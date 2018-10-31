# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.test import APITestCase
from unittest.mock import patch

from swh.web.common.exc import NotFoundExc
from swh.web.api.views.revision import (
    _revision_directory_by
)

from swh.web.tests.testcase import SWHWebTestCase


class ReleaseApiTestCase(SWHWebTestCase, APITestCase):

    @patch('swh.web.api.views.revision.service')
    def test_api_revision(self, mock_service):
        # given
        stub_revision = {
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'author_name': 'Software Heritage',
            'author_email': 'robot@softwareheritage.org',
            'committer_name': 'Software Heritage',
            'committer_email': 'robot@softwareheritage.org',
            'message': 'synthetic revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': ['8734ef7e7c357ce2af928115c6c6a42b7e2a44e7'],
            'type': 'tar',
            'synthetic': True,
            'metadata': {
                'original_artifact': [{
                    'archive_type': 'tar',
                    'name': 'webbase-5.7.0.tar.gz',
                    'sha1': '147f73f369733d088b7a6fa9c4e0273dcd3c7ccd',
                    'sha1_git': '6a15ea8b881069adedf11feceec35588f2cfe8f1',
                    'sha256': '401d0df797110bea805d358b85bcc1ced29549d3d73f'
                    '309d36484e7edf7bb912'
                }]
            },
        }
        mock_service.lookup_revision.return_value = stub_revision

        expected_revision = {
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'url': '/api/1/revision/18d8be353ed3480476f032475e7c233eff7371d5/',
            'history_url': '/api/1/revision/18d8be353ed3480476f032475e7c233e'
                           'ff7371d5/log/',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'directory_url': '/api/1/directory/7834ef7e7c357ce2af928115c6c6'
                             'a42b7e2a44e6/',
            'author_name': 'Software Heritage',
            'author_email': 'robot@softwareheritage.org',
            'committer_name': 'Software Heritage',
            'committer_email': 'robot@softwareheritage.org',
            'message': 'synthetic revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': [{
                'id': '8734ef7e7c357ce2af928115c6c6a42b7e2a44e7',
                 'url': '/api/1/revision/8734ef7e7c357ce2af928115c6c6a42b7e2a44e7/'  # noqa
            }],
            'type': 'tar',
            'synthetic': True,
            'metadata': {
                'original_artifact': [{
                    'archive_type': 'tar',
                    'name': 'webbase-5.7.0.tar.gz',
                    'sha1': '147f73f369733d088b7a6fa9c4e0273dcd3c7ccd',
                    'sha1_git': '6a15ea8b881069adedf11feceec35588f2cfe8f1',
                    'sha256': '401d0df797110bea805d358b85bcc1ced29549d3d73f'
                    '309d36484e7edf7bb912'
                }]
            },
        }

        # when
        rv = self.client.get('/api/1/revision/'
                             '18d8be353ed3480476f032475e7c233eff7371d5/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(expected_revision, rv.data)

        mock_service.lookup_revision.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5')

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_not_found(self, mock_service):
        # given
        mock_service.lookup_revision.return_value = None

        # when
        rv = self.client.get('/api/1/revision/12345/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Revision with sha1_git 12345 not found.'})

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_raw_ok(self, mock_service):
        # given
        stub_revision = {'message': 'synthetic revision message'}

        mock_service.lookup_revision_message.return_value = stub_revision

        # when
        rv = self.client.get('/api/1/revision/18d8be353ed3480476f032475e7c2'
                             '33eff7371d5/raw/')
        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/octet-stream')
        self.assertEqual(rv.content, b'synthetic revision message')

        mock_service.lookup_revision_message.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5')

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_raw_ok_no_msg(self, mock_service):
        # given
        mock_service.lookup_revision_message.side_effect = NotFoundExc(
            'No message for revision')

        # when
        rv = self.client.get('/api/1/revision/'
                             '18d8be353ed3480476f032475e7c233eff7371d5/raw/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'No message for revision'})

        self.assertEqual
        mock_service.lookup_revision_message.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5')

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_raw_ko_no_rev(self, mock_service):
        # given
        mock_service.lookup_revision_message.side_effect = NotFoundExc(
            'No revision found')

        # when
        rv = self.client.get('/api/1/revision/'
                             '18d8be353ed3480476f032475e7c233eff7371d5/raw/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'No revision found'})

        mock_service.lookup_revision_message.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5')

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_with_origin_not_found(self, mock_service):
        mock_service.lookup_revision_by.return_value = None

        rv = self.client.get('/api/1/revision/origin/123/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertIn('Revision with (origin_id: 123', rv.data['reason'])
        self.assertIn('not found', rv.data['reason'])
        self.assertEqual('NotFoundExc', rv.data['exception'])

        mock_service.lookup_revision_by.assert_called_once_with(
            '123',
            'refs/heads/master',
            None)

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_with_origin(self, mock_service):
        mock_revision = {
            'id': '32',
            'directory': '21',
            'message': 'message 1',
            'type': 'deb',
        }
        expected_revision = {
            'id': '32',
            'url': '/api/1/revision/32/',
            'history_url': '/api/1/revision/32/log/',
            'directory': '21',
            'directory_url': '/api/1/directory/21/',
            'message': 'message 1',
            'type': 'deb',
        }
        mock_service.lookup_revision_by.return_value = mock_revision

        rv = self.client.get('/api/1/revision/origin/1/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_revision)

        mock_service.lookup_revision_by.assert_called_once_with(
            '1',
            'refs/heads/master',
            None)

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_with_origin_and_branch_name(self, mock_service):
        mock_revision = {
            'id': '12',
            'directory': '23',
            'message': 'message 2',
            'type': 'tar',
        }
        mock_service.lookup_revision_by.return_value = mock_revision

        expected_revision = {
            'id': '12',
            'url': '/api/1/revision/12/',
            'history_url': '/api/1/revision/12/log/',
            'directory': '23',
            'directory_url': '/api/1/directory/23/',
            'message': 'message 2',
            'type': 'tar',
        }

        rv = self.client.get('/api/1/revision/origin/1'
                             '/branch/refs/origin/dev/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_revision)

        mock_service.lookup_revision_by.assert_called_once_with(
            '1',
            'refs/origin/dev',
            None)

    @patch('swh.web.api.views.revision.parse_timestamp')
    @patch('swh.web.api.views.revision.service')
    @patch('swh.web.api.views.revision.utils')
    def test_api_revision_with_origin_and_branch_name_and_timestamp(self,
                                                               mock_utils,
                                                               mock_service,
                                                               mock_parse_timestamp): # noqa
        mock_revision = {
            'id': '123',
            'directory': '456',
            'message': 'message 3',
            'type': 'tar',
        }
        mock_service.lookup_revision_by.return_value = mock_revision

        expected_revision = {
            'id': '123',
            'url': '/api/1/revision/123/',
            'history_url': '/api/1/revision/123/log/',
            'directory': '456',
            'directory_url': '/api/1/directory/456/',
            'message': 'message 3',
            'type': 'tar',
        }

        mock_parse_timestamp.return_value = 'parsed-date'
        mock_utils.enrich_revision.return_value = expected_revision

        rv = self.client.get('/api/1/revision'
                             '/origin/1'
                             '/branch/refs/origin/dev'
                             '/ts/1452591542/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_revision)

        mock_service.lookup_revision_by.assert_called_once_with(
            '1',
            'refs/origin/dev',
            'parsed-date')
        mock_parse_timestamp.assert_called_once_with('1452591542')
        mock_utils.enrich_revision.assert_called_once_with(
            mock_revision)

    @patch('swh.web.api.views.revision.parse_timestamp')
    @patch('swh.web.api.views.revision.service')
    @patch('swh.web.api.views.revision.utils')
    def test_api_revision_with_origin_and_branch_name_and_timestamp_escapes(
            self,
            mock_utils,
            mock_service,
            mock_parse_timestamp):
        mock_revision = {
            'id': '999',
        }
        mock_service.lookup_revision_by.return_value = mock_revision

        expected_revision = {
            'id': '999',
            'url': '/api/1/revision/999/',
            'history_url': '/api/1/revision/999/log/',
        }

        mock_parse_timestamp.return_value = 'parsed-date'
        mock_utils.enrich_revision.return_value = expected_revision

        rv = self.client.get('/api/1/revision'
                             '/origin/1'
                             '/branch/refs%2Forigin%2Fdev'
                             '/ts/Today%20is%20'
                             'January%201,%202047%20at%208:21:00AM/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_revision)

        mock_service.lookup_revision_by.assert_called_once_with(
            '1',
            'refs/origin/dev',
            'parsed-date')
        mock_parse_timestamp.assert_called_once_with(
            'Today is January 1, 2047 at 8:21:00AM')
        mock_utils.enrich_revision.assert_called_once_with(
            mock_revision)

    @patch('swh.web.api.views.revision.service')
    def test_revision_directory_by_ko_raise(self, mock_service):
        # given
        mock_service.lookup_directory_through_revision.side_effect = NotFoundExc('not')  # noqa

        # when
        with self.assertRaises(NotFoundExc):
            _revision_directory_by(
                {'sha1_git': 'id'},
                None,
                '/api/1/revision/sha1/directory/')

        # then
        mock_service.lookup_directory_through_revision.assert_called_once_with(
            {'sha1_git': 'id'},
            None, limit=100, with_data=False)

    @patch('swh.web.api.views.revision.service')
    def test_revision_directory_by_type_dir(self, mock_service):
        # given
        mock_service.lookup_directory_through_revision.return_value = (
            'rev-id',
            {
                'type': 'dir',
                'revision': 'rev-id',
                'path': 'some/path',
                'content': []
            })
        # when
        actual_dir_content = _revision_directory_by(
            {'sha1_git': 'blah-id'},
            'some/path', '/api/1/revision/sha1/directory/')

        # then
        self.assertEqual(actual_dir_content, {
            'type': 'dir',
            'revision': 'rev-id',
            'path': 'some/path',
            'content': []
        })

        mock_service.lookup_directory_through_revision.assert_called_once_with(
            {'sha1_git': 'blah-id'},
            'some/path', limit=100, with_data=False)

    @patch('swh.web.api.views.revision.service')
    def test_revision_directory_by_type_file(self, mock_service):
        # given
        mock_service.lookup_directory_through_revision.return_value = (
            'rev-id',
            {
                'type': 'file',
                'revision': 'rev-id',
                'path': 'some/path',
                'content': {'blah': 'blah'}
            })
        # when
        actual_dir_content = _revision_directory_by(
            {'sha1_git': 'sha1'},
            'some/path',
            '/api/1/revision/origin/2/directory/',
            limit=1000, with_data=True)

        # then
        self.assertEqual(actual_dir_content, {
                'type': 'file',
                'revision': 'rev-id',
                'path': 'some/path',
                'content': {'blah': 'blah'}
            })

        mock_service.lookup_directory_through_revision.assert_called_once_with(
            {'sha1_git': 'sha1'},
            'some/path', limit=1000, with_data=True)

    @patch('swh.web.api.views.revision.parse_timestamp')
    @patch('swh.web.api.views.revision._revision_directory_by')
    @patch('swh.web.api.views.revision.utils')
    def test_api_directory_through_revision_origin_ko_not_found(self,
                                                           mock_utils,
                                                           mock_rev_dir,
                                                           mock_parse_timestamp): # noqa
        mock_rev_dir.side_effect = NotFoundExc('not found')
        mock_parse_timestamp.return_value = '2012-10-20 00:00:00'

        rv = self.client.get('/api/1/revision'
                             '/origin/10'
                             '/branch/refs/remote/origin/dev'
                             '/ts/2012-10-20'
                             '/directory/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'not found'})

        mock_rev_dir.assert_called_once_with(
            {'origin_id': '10',
             'branch_name': 'refs/remote/origin/dev',
             'ts': '2012-10-20 00:00:00'}, None,
            '/api/1/revision'
            '/origin/10'
            '/branch/refs/remote/origin/dev'
            '/ts/2012-10-20'
            '/directory/',
            with_data=False)

    @patch('swh.web.api.views.revision._revision_directory_by')
    def test_api_directory_through_revision_origin(self,
                                                   mock_revision_dir):
        expected_res = [{
            'id': '123'
        }]
        mock_revision_dir.return_value = expected_res

        rv = self.client.get('/api/1/revision/origin/3/directory/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_res)

        mock_revision_dir.assert_called_once_with({
            'origin_id': '3',
            'branch_name': 'refs/heads/master',
            'ts': None}, None, '/api/1/revision/origin/3/directory/',
                                                  with_data=False)

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_log(self, mock_service):
        # given
        stub_revisions = [{
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'author_name': 'Software Heritage',
            'author_email': 'robot@softwareheritage.org',
            'committer_name': 'Software Heritage',
            'committer_email': 'robot@softwareheritage.org',
            'message': 'synthetic revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': ['7834ef7e7c357ce2af928115c6c6a42b7e2a4345'],
            'type': 'tar',
            'synthetic': True,
        }]
        mock_service.lookup_revision_log.return_value = stub_revisions

        expected_revisions = [{
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'url': '/api/1/revision/18d8be353ed3480476f032475e7c233eff7371d5/',
            'history_url': '/api/1/revision/18d8be353ed3480476f032475e7c233ef'
            'f7371d5/log/',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'directory_url': '/api/1/directory/7834ef7e7c357ce2af928115c6c6a'
            '42b7e2a44e6/',
            'author_name': 'Software Heritage',
            'author_email': 'robot@softwareheritage.org',
            'committer_name': 'Software Heritage',
            'committer_email': 'robot@softwareheritage.org',
            'message': 'synthetic revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': [{
                'id': '7834ef7e7c357ce2af928115c6c6a42b7e2a4345',
                'url': '/api/1/revision/7834ef7e7c357ce2af928115c6c6a42b7e2a4345/',  # noqa
            }],
            'type': 'tar',
            'synthetic': True,
        }]

        # when
        rv = self.client.get('/api/1/revision/8834ef7e7c357ce2af928115c6c6a42'
                             'b7e2a44e6/log/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')

        self.assertEqual(rv.data, expected_revisions)
        self.assertFalse(rv.has_header('Link'))

        mock_service.lookup_revision_log.assert_called_once_with(
            '8834ef7e7c357ce2af928115c6c6a42b7e2a44e6', 11)

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_log_with_next(self, mock_service):
        # given
        stub_revisions = []
        for i in range(27):
            stub_revisions.append({'id': str(i)})

        mock_service.lookup_revision_log.return_value = stub_revisions[:26]

        expected_revisions = [x for x in stub_revisions if int(x['id']) < 25]
        for e in expected_revisions:
            e['url'] = '/api/1/revision/%s/' % e['id']
            e['history_url'] = '/api/1/revision/%s/log/' % e['id']

        # when
        rv = self.client.get('/api/1/revision/8834ef7e7c357ce2af928115c6c6a42'
                             'b7e2a44e6/log/?per_page=25')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_revisions)
        self.assertEqual(rv['Link'],
                         '</api/1/revision/25/log/?per_page=25>; rel="next"')

        mock_service.lookup_revision_log.assert_called_once_with(
            '8834ef7e7c357ce2af928115c6c6a42b7e2a44e6', 26)

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_log_not_found(self, mock_service):
        # given
        mock_service.lookup_revision_log.return_value = None

        # when
        rv = self.client.get('/api/1/revision/8834ef7e7c357ce2af928115c6c6'
                             'a42b7e2a44e6/log/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Revision with sha1_git'
            ' 8834ef7e7c357ce2af928115c6c6a42b7e2a44e6 not found.'})
        self.assertFalse(rv.has_header('Link'))

        mock_service.lookup_revision_log.assert_called_once_with(
            '8834ef7e7c357ce2af928115c6c6a42b7e2a44e6', 11)

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_log_context(self, mock_service):
        # given
        stub_revisions = [{
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'author_name': 'Software Heritage',
            'author_email': 'robot@softwareheritage.org',
            'committer_name': 'Software Heritage',
            'committer_email': 'robot@softwareheritage.org',
            'message': 'synthetic revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': ['7834ef7e7c357ce2af928115c6c6a42b7e2a4345'],
            'type': 'tar',
            'synthetic': True,
        }]

        mock_service.lookup_revision_log.return_value = stub_revisions
        mock_service.lookup_revision_multiple.return_value = [{
            'id': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'directory': '18d8be353ed3480476f032475e7c233eff7371d5',
            'author_name': 'Name Surname',
            'author_email': 'name@surname.com',
            'committer_name': 'Name Surname',
            'committer_email': 'name@surname.com',
            'message': 'amazing revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': ['adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'],
            'type': 'tar',
            'synthetic': True,
        }]

        expected_revisions = [
            {
                'url': '/api/1/revision/'
                '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6/',
                'history_url': '/api/1/revision/'
                '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6/log/',
                'id': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
                'directory': '18d8be353ed3480476f032475e7c233eff7371d5',
                'directory_url': '/api/1/directory/'
                '18d8be353ed3480476f032475e7c233eff7371d5/',
                'author_name': 'Name Surname',
                'author_email': 'name@surname.com',
                'committer_name': 'Name Surname',
                'committer_email': 'name@surname.com',
                'message': 'amazing revision message',
                'date_offset': 0,
                'committer_date_offset': 0,
                'parents': [{
                    'id': 'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
                    'url': '/api/1/revision/adc83b19e793491b1c6ea0fd8b46cd9f32e592fc/',  # noqa
                }],
                'type': 'tar',
                'synthetic': True,
            },
            {
                'url': '/api/1/revision/'
                '18d8be353ed3480476f032475e7c233eff7371d5/',
                'history_url': '/api/1/revision/'
                '18d8be353ed3480476f032475e7c233eff7371d5/log/',
                'id': '18d8be353ed3480476f032475e7c233eff7371d5',
                'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
                'directory_url': '/api/1/directory/'
                '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6/',
                'author_name': 'Software Heritage',
                'author_email': 'robot@softwareheritage.org',
                'committer_name': 'Software Heritage',
                'committer_email': 'robot@softwareheritage.org',
                'message': 'synthetic revision message',
                'date_offset': 0,
                'committer_date_offset': 0,
                'parents': [{
                    'id': '7834ef7e7c357ce2af928115c6c6a42b7e2a4345',
                    'url': '/api/1/revision/7834ef7e7c357ce2af928115c6c6a42b7e2a4345/',  # noqa
                }],
                'type': 'tar',
                'synthetic': True,
            }]

        # when
        rv = self.client.get('/api/1/revision/18d8be353ed3480476f0'
                             '32475e7c233eff7371d5/prev/21145781e2'
                             '6ad1f978e/log/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(expected_revisions, rv.data)
        self.assertFalse(rv.has_header('Link'))

        mock_service.lookup_revision_log.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5', 11)
        mock_service.lookup_revision_multiple.assert_called_once_with(
            ['21145781e26ad1f978e'])

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_log_by(self, mock_service):
        # given
        stub_revisions = [{
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'author_name': 'Software Heritage',
            'author_email': 'robot@softwareheritage.org',
            'committer_name': 'Software Heritage',
            'committer_email': 'robot@softwareheritage.org',
            'message': 'synthetic revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': ['7834ef7e7c357ce2af928115c6c6a42b7e2a4345'],
            'type': 'tar',
            'synthetic': True,
        }]
        mock_service.lookup_revision_log_by.return_value = stub_revisions

        expected_revisions = [{
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'url': '/api/1/revision/18d8be353ed3480476f032475e7c233eff7371d5/',
            'history_url': '/api/1/revision/18d8be353ed3480476f032475e7c233ef'
                           'f7371d5/log/',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'directory_url': '/api/1/directory/7834ef7e7c357ce2af928115c6c6a'
                             '42b7e2a44e6/',
            'author_name': 'Software Heritage',
            'author_email': 'robot@softwareheritage.org',
            'committer_name': 'Software Heritage',
            'committer_email': 'robot@softwareheritage.org',
            'message': 'synthetic revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': [{
                'id': '7834ef7e7c357ce2af928115c6c6a42b7e2a4345',
                 'url': '/api/1/revision/7834ef7e7c357ce2af928115c6c6a42b7e2a4345/'  # noqa
            }],
            'type': 'tar',
            'synthetic': True,
        }]

        # when
        rv = self.client.get('/api/1/revision/origin/1/log/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_revisions)
        self.assertFalse(rv.has_header('Link'))

        mock_service.lookup_revision_log_by.assert_called_once_with(
            '1', 'refs/heads/master', None, 11)

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_log_by_with_next(self, mock_service):
        # given
        stub_revisions = []
        for i in range(27):
            stub_revisions.append({'id': str(i)})

        mock_service.lookup_revision_log_by.return_value = stub_revisions[:26]

        expected_revisions = [x for x in stub_revisions if int(x['id']) < 25]
        for e in expected_revisions:
            e['url'] = '/api/1/revision/%s/' % e['id']
            e['history_url'] = '/api/1/revision/%s/log/' % e['id']

        # when
        rv = self.client.get('/api/1/revision/origin/1/log/?per_page=25')

        # then
        self.assertEqual(rv.status_code, 200)

        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertIsNotNone(rv['Link'])
        self.assertEqual(rv.data, expected_revisions)

        mock_service.lookup_revision_log_by.assert_called_once_with(
            '1', 'refs/heads/master', None, 26)

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_log_by_norev(self, mock_service):
        # given
        mock_service.lookup_revision_log_by.side_effect = NotFoundExc(
            'No revision')

        # when
        rv = self.client.get('/api/1/revision/origin/1/log/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertFalse(rv.has_header('Link'))
        self.assertEqual(rv.data, {'exception': 'NotFoundExc',
                                   'reason': 'No revision'})

        mock_service.lookup_revision_log_by.assert_called_once_with(
            '1', 'refs/heads/master', None, 11)

    @patch('swh.web.api.views.revision.service')
    def test_api_revision_history(self, mock_service):
        # for readability purposes, we use:
        # - sha1 as 3 letters (url are way too long otherwise to respect pep8)
        # - only keys with modification steps (all other keys are kept as is)

        # given
        stub_revision = {
            'id': '883',
            'children': ['777', '999'],
            'parents': [],
            'directory': '272'
        }

        mock_service.lookup_revision.return_value = stub_revision

        # then
        rv = self.client.get('/api/1/revision/883/prev/999/')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'id': '883',
            'url': '/api/1/revision/883/',
            'history_url': '/api/1/revision/883/log/',
            'history_context_url': '/api/1/revision/883/prev/999/log/',
            'children': ['777', '999'],
            'children_urls': ['/api/1/revision/777/',
                              '/api/1/revision/999/'],
            'parents': [],
            'directory': '272',
            'directory_url': '/api/1/directory/272/'
        })

        mock_service.lookup_revision.assert_called_once_with('883')

    @patch('swh.web.api.views.revision._revision_directory_by')
    def test_api_revision_directory_ko_not_found(self, mock_rev_dir):
        # given
        mock_rev_dir.side_effect = NotFoundExc('Not found')

        # then
        rv = self.client.get('/api/1/revision/999/directory/some/path/to/dir/')

        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Not found'})

        mock_rev_dir.assert_called_once_with(
            {'sha1_git': '999'},
            'some/path/to/dir',
            '/api/1/revision/999/directory/some/path/to/dir/',
            with_data=False)

    @patch('swh.web.api.views.revision._revision_directory_by')
    def test_api_revision_directory_ok_returns_dir_entries(self, mock_rev_dir):
        stub_dir = {
            'type': 'dir',
            'revision': '999',
            'content': [
                {
                    'sha1_git': '789',
                    'type': 'file',
                    'target': '101',
                    'target_url': '/api/1/content/sha1_git:101/',
                    'name': 'somefile',
                    'file_url': '/api/1/revision/999/directory/some/path/'
                    'somefile/'
                },
                {
                    'sha1_git': '123',
                    'type': 'dir',
                    'target': '456',
                    'target_url': '/api/1/directory/456/',
                    'name': 'to-subdir',
                    'dir_url': '/api/1/revision/999/directory/some/path/'
                    'to-subdir/',
                }]
        }

        # given
        mock_rev_dir.return_value = stub_dir

        # then
        rv = self.client.get('/api/1/revision/999/directory/some/path/')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, stub_dir)

        mock_rev_dir.assert_called_once_with(
            {'sha1_git': '999'},
            'some/path',
            '/api/1/revision/999/directory/some/path/',
            with_data=False)

    @patch('swh.web.api.views.revision._revision_directory_by')
    def test_api_revision_directory_ok_returns_content(self, mock_rev_dir):
        stub_content = {
            'type': 'file',
            'revision': '999',
            'content': {
                'sha1_git': '789',
                'sha1': '101',
                'data_url': '/api/1/content/101/raw/',
            }
        }

        # given
        mock_rev_dir.return_value = stub_content

        # then
        url = '/api/1/revision/666/directory/some/other/path/'
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, stub_content)

        mock_rev_dir.assert_called_once_with(
            {'sha1_git': '666'}, 'some/other/path', url, with_data=False)
