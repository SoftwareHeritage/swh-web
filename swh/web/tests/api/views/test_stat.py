# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.test import APITestCase
from unittest.mock import patch

from swh.storage.exc import StorageDBError, StorageAPIError

from swh.web.tests.testcase import SWHWebTestCase


class StatApiTestCase(SWHWebTestCase, APITestCase):
    @patch('swh.web.api.views.stat.service')
    def test_api_1_stat_counters_raise_error(self, mock_service):
        # given
        mock_service.stat_counters.side_effect = ValueError(
            'voluntary error to check the bad request middleware.')
        # when
        rv = self.client.get('/api/1/stat/counters/')
        # then
        self.assertEqual(rv.status_code, 400)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'ValueError',
            'reason': 'voluntary error to check the bad request middleware.'})

    @patch('swh.web.api.views.stat.service')
    def test_api_1_stat_counters_raise_from_db(self, mock_service):
        # given
        mock_service.stat_counters.side_effect = StorageDBError(
            'Storage exploded! Will be back online shortly!')
        # when
        rv = self.client.get('/api/1/stat/counters/')
        # then
        self.assertEqual(rv.status_code, 503)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'StorageDBError',
            'reason':
            'An unexpected error occurred in the backend: '
            'Storage exploded! Will be back online shortly!'})

    @patch('swh.web.api.views.stat.service')
    def test_api_1_stat_counters_raise_from_api(self, mock_service):
        # given
        mock_service.stat_counters.side_effect = StorageAPIError(
            'Storage API dropped dead! Will resurrect from its ashes asap!'
        )
        # when
        rv = self.client.get('/api/1/stat/counters/')
        # then
        self.assertEqual(rv.status_code, 503)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'StorageAPIError',
            'reason':
            'An unexpected error occurred in the api backend: '
            'Storage API dropped dead! Will resurrect from its ashes asap!'
        })

    @patch('swh.web.api.views.stat.service')
    def test_api_1_stat_counters(self, mock_service):
        # given
        stub_stats = {
            "content": 1770830,
            "directory": 211683,
            "directory_entry_dir": 209167,
            "directory_entry_file": 1807094,
            "directory_entry_rev": 0,
            "entity": 0,
            "entity_history": 0,
            "origin": 1096,
            "person": 0,
            "release": 8584,
            "revision": 7792,
            "revision_history": 0,
            "skipped_content": 0
        }
        mock_service.stat_counters.return_value = stub_stats

        # when
        rv = self.client.get('/api/1/stat/counters/')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, stub_stats)

        mock_service.stat_counters.assert_called_once_with()
