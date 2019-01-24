# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.test import APITestCase
from unittest.mock import patch

from swh.storage.exc import StorageDBError, StorageAPIError

from swh.web.common.utils import reverse
from swh.web.tests.testcase import WebTestCase


class StatApiTestCase(WebTestCase, APITestCase):
    @patch('swh.web.api.views.stat.service')
    def test_api_1_stat_counters_raise_error(self, mock_service):

        mock_service.stat_counters.side_effect = ValueError(
            'voluntary error to check the bad request middleware.')

        url = reverse('api-stat-counters')
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'ValueError',
            'reason': 'voluntary error to check the bad request middleware.'})

    @patch('swh.web.api.views.stat.service')
    def test_api_1_stat_counters_raise_from_db(self, mock_service):

        mock_service.stat_counters.side_effect = StorageDBError(
            'Storage exploded! Will be back online shortly!')

        url = reverse('api-stat-counters')
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 503)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'StorageDBError',
            'reason':
            'An unexpected error occurred in the backend: '
            'Storage exploded! Will be back online shortly!'})

    @patch('swh.web.api.views.stat.service')
    def test_api_1_stat_counters_raise_from_api(self, mock_service):

        mock_service.stat_counters.side_effect = StorageAPIError(
            'Storage API dropped dead! Will resurrect from its ashes asap!'
        )

        url = reverse('api-stat-counters')
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 503)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'StorageAPIError',
            'reason':
            'An unexpected error occurred in the api backend: '
            'Storage API dropped dead! Will resurrect from its ashes asap!'
        })

    def test_api_1_stat_counters(self):

        url = reverse('api-stat-counters')

        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, self.storage.stat_counters())
