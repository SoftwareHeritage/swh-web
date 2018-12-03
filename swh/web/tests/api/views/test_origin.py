# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.test import APITestCase
from unittest.mock import patch

from swh.storage.exc import StorageDBError, StorageAPIError

from swh.web.tests.testcase import SWHWebTestCase


class OriginApiTestCase(SWHWebTestCase, APITestCase):

    def setUp(self):
        self.origin_visit1 = {
            'date': 1104616800.0,
            'origin': 10,
            'visit': 100,
            'metadata': None,
            'status': 'full',
        }

        self.origin1 = {
            'id': 1234,
            'url': 'ftp://some/url/to/origin/0',
            'type': 'ftp'
        }

    @patch('swh.web.api.views.origin.get_origin_visits')
    def test_api_1_lookup_origin_visits_raise_error(
        self, mock_get_origin_visits,
    ):
        # given
        mock_get_origin_visits.side_effect = ValueError(
            'voluntary error to check the bad request middleware.')
        # when
        rv = self.client.get('/api/1/origin/2/visits/')
        # then
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'ValueError',
            'reason': 'voluntary error to check the bad request middleware.'})

    @patch('swh.web.common.utils.service')
    def test_api_1_lookup_origin_visits_raise_swh_storage_error_db(
            self, mock_service):
        # given
        mock_service.lookup_origin_visits.side_effect = StorageDBError(
            'Storage exploded! Will be back online shortly!')
        # when
        rv = self.client.get('/api/1/origin/2/visits/')
        # then
        self.assertEqual(rv.status_code, 503)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'StorageDBError',
            'reason':
            'An unexpected error occurred in the backend: '
            'Storage exploded! Will be back online shortly!'})

    @patch('swh.web.common.utils.service')
    def test_api_1_lookup_origin_visits_raise_swh_storage_error_api(
            self, mock_service):
        # given
        mock_service.lookup_origin_visits.side_effect = StorageAPIError(
            'Storage API dropped dead! Will resurrect from its ashes asap!'
        )
        # when
        rv = self.client.get('/api/1/origin/2/visits/')
        # then
        self.assertEqual(rv.status_code, 503)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'StorageAPIError',
            'reason':
            'An unexpected error occurred in the api backend: '
            'Storage API dropped dead! Will resurrect from its ashes asap!'
        })

    @patch('swh.web.api.views.origin.get_origin_visits')
    def test_api_1_lookup_origin_visits(self, mock_get_origin_visits):
        # given
        stub_visits = [
            {
                'date': 1293919200.0,
                'origin': 2,
                'snapshot': '1234',
                'visit': 1
            },
            {
                'date': 1293919200.0,
                'origin': 2,
                'snapshot': '1234',
                'visit': 2
            },
            {
                'date': 1420149600.0,
                'origin': 2,
                'snapshot': '5678',
                'visit': 3
            },
            {
                'date': 1420149600.0,
                'origin': 2,
                'snapshot': '5678',
                'visit': 4
            }
        ]

        mock_get_origin_visits.return_value = stub_visits

        # when
        rv = self.client.get('/api/1/origin/2/visits/?per_page=2&last_visit=3')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, [
            {
                'date': 1293919200.0,
                'origin': 2,
                'snapshot': '1234',
                'visit': 2,
                'origin_visit_url': '/api/1/origin/2/visit/2/',
                'snapshot_url': '/api/1/snapshot/1234/'
            },
            {
                'date': 1293919200.0,
                'origin': 2,
                'snapshot': '1234',
                'visit': 1,
                'origin_visit_url': '/api/1/origin/2/visit/1/',
                'snapshot_url': '/api/1/snapshot/1234/'
            },

        ])

    @patch('swh.web.api.views.origin.service')
    def test_api_1_lookup_origin_visit(self, mock_service):
        # given
        origin_visit = self.origin_visit1.copy()
        origin_visit.update({
            'snapshot': '57478754'
        })

        mock_service.lookup_origin_visit.return_value = origin_visit

        expected_origin_visit = self.origin_visit1.copy()
        expected_origin_visit.update({
            'origin_url': '/api/1/origin/10/',
            'snapshot': '57478754',
            'snapshot_url': '/api/1/snapshot/57478754/'
        })

        # when
        rv = self.client.get('/api/1/origin/10/visit/100/')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_origin_visit)

        mock_service.lookup_origin_visit.assert_called_once_with('10', '100')

    @patch('swh.web.api.views.origin.service')
    def test_api_1_lookup_origin_visit_not_found(self, mock_service):
        # given
        mock_service.lookup_origin_visit.return_value = None

        # when
        rv = self.client.get('/api/1/origin/1/visit/1000/')

        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'No visit 1000 for origin 1 found'
        })

        mock_service.lookup_origin_visit.assert_called_once_with('1', '1000')

    @patch('swh.web.api.views.origin.service')
    def test_api_origin_by_id(self, mock_service):
        # given
        mock_service.lookup_origin.return_value = self.origin1

        expected_origin = self.origin1.copy()
        expected_origin.update({
            'origin_visits_url': '/api/1/origin/1234/visits/'
        })

        # when
        rv = self.client.get('/api/1/origin/1234/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_origin)

        mock_service.lookup_origin.assert_called_with({'id': '1234'})

    @patch('swh.web.api.views.origin.service')
    def test_api_origin_by_type_url(self, mock_service):
        # given
        stub_origin = self.origin1.copy()
        stub_origin.update({
            'id': 987
        })
        mock_service.lookup_origin.return_value = stub_origin

        expected_origin = stub_origin.copy()
        expected_origin.update({
            'origin_visits_url': '/api/1/origin/987/visits/'
        })

        # when
        rv = self.client.get('/api/1/origin/ftp/url'
                             '/ftp://some/url/to/origin/0/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_origin)

        mock_service.lookup_origin.assert_called_with(
            {'url': 'ftp://some/url/to/origin/0',
             'type': 'ftp'})

    @patch('swh.web.api.views.origin.service')
    def test_api_origin_not_found(self, mock_service):
        # given
        mock_service.lookup_origin.return_value = None

        # when
        rv = self.client.get('/api/1/origin/4321/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Origin with id 4321 not found.'
        })

        mock_service.lookup_origin.assert_called_with({'id': '4321'})

    @patch('swh.web.common.service.idx_storage')
    def test_api_origin_metadata_search(self, mock_idx_storage):
        # given
        mock_idx_storage.origin_intrinsic_metadata_search_fulltext \
            .return_value = [{
                'from_revision':
                b'p&\xb7\xc1\xa2\xafVR\x1e\x95\x1c\x01\xed \xf2U\xfa\x05B8',
                'metadata': {'author': 'Jane Doe'},
                'origin_id': 54974445,
                'tool': {
                    'configuration': {
                        'context': ['NpmMapping', 'CodemetaMapping'],
                        'type': 'local'
                    },
                    'id': 3,
                    'name': 'swh-metadata-detector',
                    'version': '0.0.1'
                }
            }]

        # when
        rv = self.client.get(
            '/api/1/origin/metadata-search/?fulltext=Jane%20Doe')

        # then
        self.assertEqual(rv.status_code, 200, rv.content)
        self.assertEqual(rv['Content-Type'], 'application/json')
        expected_data = [{
            'origin_id': 54974445,
            'metadata': {'author': 'Jane Doe'},
            'from_revision': '7026b7c1a2af56521e951c01ed20f255fa054238',
            'tool': {
                'configuration': {
                    'context': ['NpmMapping', 'CodemetaMapping'],
                    'type': 'local'
                },
                'id': 3,
                'name': 'swh-metadata-detector',
                'version': '0.0.1',
            }
        }]
        self.assertEqual(rv.data, expected_data)
        mock_idx_storage.origin_intrinsic_metadata_search_fulltext \
            .assert_called_with(conjunction=['Jane Doe'], limit=70)

    @patch('swh.web.common.service.idx_storage')
    def test_api_origin_metadata_search_limit(self, mock_idx_storage):
        # given
        mock_idx_storage.origin_intrinsic_metadata_search_fulltext \
            .return_value = [{
                'from_revision':
                b'p&\xb7\xc1\xa2\xafVR\x1e\x95\x1c\x01\xed \xf2U\xfa\x05B8',
                'metadata': {'author': 'Jane Doe'},
                'origin_id': 54974445,
                'tool': {
                    'configuration': {
                        'context': ['NpmMapping', 'CodemetaMapping'],
                        'type': 'local'
                    },
                    'id': 3,
                    'name': 'swh-metadata-detector',
                    'version': '0.0.1'
                }
            }]

        # when
        rv = self.client.get(
            '/api/1/origin/metadata-search/?fulltext=Jane%20Doe')

        # then
        self.assertEqual(rv.status_code, 200, rv.content)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(len(rv.data), 1)
        mock_idx_storage.origin_intrinsic_metadata_search_fulltext \
            .assert_called_with(conjunction=['Jane Doe'], limit=70)

        # when
        rv = self.client.get(
            '/api/1/origin/metadata-search/?fulltext=Jane%20Doe&limit=10')

        # then
        self.assertEqual(rv.status_code, 200, rv.content)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(len(rv.data), 1)
        mock_idx_storage.origin_intrinsic_metadata_search_fulltext \
            .assert_called_with(conjunction=['Jane Doe'], limit=10)

        # when
        rv = self.client.get(
            '/api/1/origin/metadata-search/?fulltext=Jane%20Doe&limit=987')

        # then
        self.assertEqual(rv.status_code, 200, rv.content)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(len(rv.data), 1)
        mock_idx_storage.origin_intrinsic_metadata_search_fulltext \
            .assert_called_with(conjunction=['Jane Doe'], limit=100)

    @patch('swh.web.common.service.idx_storage')
    def test_api_origin_metadata_search_invalid(self, mock_idx_storage):
        rv = self.client.get('/api/1/origin/metadata-search/')

        # then
        self.assertEqual(rv.status_code, 400, rv.content)
        mock_idx_storage.assert_not_called()
