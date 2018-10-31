# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.test import APITestCase
from unittest.mock import patch

from swh.web.tests.testcase import SWHWebTestCase


class DirectoryApiTestCase(SWHWebTestCase, APITestCase):

    @patch('swh.web.api.views.directory.service')
    def test_api_directory(self, mock_service):
        # given
        stub_directories = [
            {
                'sha1_git': '18d8be353ed3480476f032475e7c233eff7371d5',
                'type': 'file',
                'target': '4568be353ed3480476f032475e7c233eff737123',
            },
            {
                'sha1_git': '1d518d8be353ed3480476f032475e7c233eff737',
                'type': 'dir',
                'target': '8be353ed3480476f032475e7c233eff737123456',
            }]

        expected_directories = [
            {
                'sha1_git': '18d8be353ed3480476f032475e7c233eff7371d5',
                'type': 'file',
                'target': '4568be353ed3480476f032475e7c233eff737123',
                'target_url': '/api/1/content/'
                'sha1_git:4568be353ed3480476f032475e7c233eff737123/',
            },
            {
                'sha1_git': '1d518d8be353ed3480476f032475e7c233eff737',
                'type': 'dir',
                'target': '8be353ed3480476f032475e7c233eff737123456',
                'target_url':
                '/api/1/directory/8be353ed3480476f032475e7c233eff737123456/',
            }]

        mock_service.lookup_directory.return_value = stub_directories

        # when
        rv = self.client.get('/api/1/directory/'
                             '18d8be353ed3480476f032475e7c233eff7371d5/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_directories)

        mock_service.lookup_directory.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5')

    @patch('swh.web.api.views.directory.service')
    def test_api_directory_not_found(self, mock_service):
        # given
        mock_service.lookup_directory.return_value = []

        # when
        rv = self.client.get('/api/1/directory/'
                             '66618d8be353ed3480476f032475e7c233eff737/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Directory with sha1_git '
            '66618d8be353ed3480476f032475e7c233eff737 not found.'})

    @patch('swh.web.api.views.directory.service')
    def test_api_directory_with_path_found(self, mock_service):
        # given
        expected_dir = {
                'sha1_git': '18d8be353ed3480476f032475e7c233eff7371d5',
                'type': 'file',
                'name': 'bla',
                'target': '4568be353ed3480476f032475e7c233eff737123',
                'target_url': '/api/1/content/'
                'sha1_git:4568be353ed3480476f032475e7c233eff737123/',
            }

        mock_service.lookup_directory_with_path.return_value = expected_dir

        # when
        rv = self.client.get('/api/1/directory/'
                             '18d8be353ed3480476f032475e7c233eff7371d5/bla/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_dir)

        mock_service.lookup_directory_with_path.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5', 'bla')

    @patch('swh.web.api.views.directory.service')
    def test_api_directory_with_path_not_found(self, mock_service):
        # given
        mock_service.lookup_directory_with_path.return_value = None
        path = 'some/path/to/dir/'

        # when
        rv = self.client.get(('/api/1/directory/'
                              '66618d8be353ed3480476f032475e7c233eff737/%s')
                             % path)
        path = path.strip('/')  # Path stripped of lead/trail separators

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': (('Entry with path %s relative to '
                        'directory with sha1_git '
                        '66618d8be353ed3480476f032475e7c233eff737 not found.')
                       % path)})
