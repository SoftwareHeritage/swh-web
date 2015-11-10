# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest
import json

from nose.tools import istest
from unittest.mock import patch

from swh.web.ui.tests import test_app


class ApiTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app, _, _ = test_app.init_app()

    @istest
    def info(self):
        # when
        rv = self.app.get('/about')

        self.assertEquals(rv.status_code, 200)
        self.assertIn(b'About', rv.data)

    # @istest
    def search_1(self):
        # when
        rv = self.app.get('/search')

        self.assertEquals(rv.status_code, 200)  # check this api
        self.assertRegexpMatches(rv.data, b'name=q value=>')

    # @istest
    def search_2(self):
        # when
        rv = self.app.get('/search?q=one-hash-to-look-for:another-one')

        self.assertEquals(rv.status_code, 200)  # check this api
        self.assertRegexpMatches(
            rv.data,
            b'name=q value=one-hash-to-look-for:another-one')

    @patch('swh.web.ui.controller.service')
    @istest
    def api_browse(self, mock_service):
        # given
        mock_service.lookup_hash_origin.return_value = {
            'origin': 'some-origin'
        }

        # when
        rv = self.app.get('/api/1/browse/sha1:foo/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {'origin': {'origin': 'some-origin'}})

        mock_service.lookup_hash_origin.assert_called_once_with('sha1:foo')

    @patch('swh.web.ui.controller.service')
    @istest
    def api_search(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = False

        # when
        rv = self.app.get('/api/1/search/sha1:blah/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {'found': False})

        mock_service.lookup_hash.assert_called_once_with('sha1:blah')

    @patch('swh.web.ui.controller.service')
    @istest
    def api_1_stat_counters_raise_error(self, mock_service):
        # given
        mock_service.stat_counters.side_effect = ValueError(
            'voluntary error to check the bad request middleware.')
        # when
        rv = self.app.get('/api/1/stat/counters')
        # then
        self.assertEquals(rv.status_code, 400)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'voluntary error to check the bad request middleware.'})

    @patch('swh.web.ui.controller.service')
    @istest
    def api_1_stat_counters(self, mock_service):
        # given
        mock_service.stat_counters.return_value = {
            "content": 1770830,
            "directory": 211683,
            "directory_entry_dir": 209167,
            "directory_entry_file": 1807094,
            "directory_entry_rev": 0,
            "entity": 0,
            "entity_history": 0,
            "occurrence": 0,
            "occurrence_history": 19600,
            "origin": 1096,
            "person": 0,
            "release": 8584,
            "revision": 7792,
            "revision_history": 0,
            "skipped_content": 0
        }

        # when
        rv = self.app.get('/api/1/stat/counters')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        self.assertEquals(response_data, {
            "content": 1770830,
            "directory": 211683,
            "directory_entry_dir": 209167,
            "directory_entry_file": 1807094,
            "directory_entry_rev": 0,
            "entity": 0,
            "entity_history": 0,
            "occurrence": 0,
            "occurrence_history": 19600,
            "origin": 1096,
            "person": 0,
            "release": 8584,
            "revision": 7792,
            "revision_history": 0,
            "skipped_content": 0
        })

        mock_service.stat_counters.assert_called_once_with()

    @patch('swh.web.ui.controller.service')
    @patch('swh.web.ui.controller.request')
    @istest
    def api_uploadnsearch(self, mock_request, mock_service):
        # given
        mock_request.files = {'filename': 'simple-filename'}
        mock_service.upload_and_search.return_value = (
            'simple-filename', 'some-hex-sha1', False)

        # when
        rv = self.app.post('/api/1/uploadnsearch/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {'filename': 'simple-filename',
                                          'sha1': 'some-hex-sha1',
                                          'found': False})

        mock_service.upload_and_search.assert_called_once_with(
            'simple-filename')
