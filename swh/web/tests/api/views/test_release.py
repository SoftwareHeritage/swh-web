# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.test import APITestCase
from unittest.mock import patch

from swh.web.tests.testcase import SWHWebTestCase


class ReleaseApiTestCase(SWHWebTestCase, APITestCase):

    @patch('swh.web.api.views.release.service')
    def test_api_release(self, mock_service):
        release_id = '7045404f3d1c54e6473'
        target_id = '6072557b6c10cd9a211'
        # given
        stub_release = {
            'id': release_id,
            'target_type': 'revision',
            'target': target_id,
            "date": "Mon, 10 Mar 1997 08:00:00 GMT",
            "synthetic": True,
            'author': {
                'id': 10,
                'name': 'author release name',
                'email': 'author@email',
            },
        }

        expected_release = {
            'id': release_id,
            'target_type': 'revision',
            'target': target_id,
            'target_url': '/api/1/revision/%s/' % target_id,
            "date": "Mon, 10 Mar 1997 08:00:00 GMT",
            "synthetic": True,
            'author_url': '/api/1/person/10/',
            'author': {
                'id': 10,
                'name': 'author release name',
                'email': 'author@email',
            },
        }

        mock_service.lookup_release.return_value = stub_release

        # when
        rv = self.client.get('/api/1/release/%s/' % release_id)

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_release)

        mock_service.lookup_release.assert_called_once_with(release_id)

    @patch('swh.web.api.views.release.service')
    def test_api_release_target_type_not_a_revision(self, mock_service):
        release = '8d56a78'
        target = '9a5c3f'
        # given
        stub_release = {
            'id': release,
            'target_type': 'other-stuff',
            'target': target,
            "date": "Mon, 10 Mar 1997 08:00:00 GMT",
            "synthetic": True,
            'author': {
                'id': 9,
                'name': 'author release name',
                'email': 'author@email',
            },
        }

        expected_release = {
            'id': release,
            'target_type': 'other-stuff',
            'target': target,
            "date": "Mon, 10 Mar 1997 08:00:00 GMT",
            "synthetic": True,
            'author_url': '/api/1/person/9/',
            'author': {
                'id': 9,
                'name': 'author release name',
                'email': 'author@email',
            },
        }

        mock_service.lookup_release.return_value = stub_release

        # when
        rv = self.client.get('/api/1/release/%s/' % release)

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_release)

        mock_service.lookup_release.assert_called_once_with(release)

    @patch('swh.web.api.views.release.service')
    def test_api_release_not_found(self, mock_service):
        # given
        mock_service.lookup_release.return_value = None

        # when
        rv = self.client.get('/api/1/release/c54e6473c71bbb716529/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Release with sha1_git c54e6473c71bbb716529 not found.'
        })
