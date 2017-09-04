# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from nose.tools import istest
from unittest.mock import patch

from swh.web.api.exc import BadInputExc

from ..swh_api_testcase import SWHApiTestCase


class EntityApiTestCase(SWHApiTestCase):

    @patch('swh.web.api.views.entity.service')
    @istest
    def api_lookup_entity_by_uuid_not_found(self, mock_service):
        # when
        mock_service.lookup_entity_by_uuid.return_value = []

        # when
        rv = self.client.get('/api/1/entity/'
                             '5f4d4c51-498a-4e28-88b3-b3e4e8396cba/')

        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv['Content-Type'], 'application/json')
        self.assertEquals(rv.data, {
            'exception': 'NotFoundExc',
            'reason':
            "Entity with uuid '5f4d4c51-498a-4e28-88b3-b3e4e8396cba' not " +
            "found."})

        mock_service.lookup_entity_by_uuid.assert_called_once_with(
            '5f4d4c51-498a-4e28-88b3-b3e4e8396cba')

    @patch('swh.web.api.views.entity.service')
    @istest
    def api_lookup_entity_by_uuid_bad_request(self, mock_service):
        # when
        mock_service.lookup_entity_by_uuid.side_effect = BadInputExc(
            'bad input: uuid malformed!')

        # when
        rv = self.client.get('/api/1/entity/uuid malformed/')

        self.assertEquals(rv.status_code, 400)
        self.assertEquals(rv['Content-Type'], 'application/json')
        self.assertEquals(rv.data, {
            'exception': 'BadInputExc',
            'reason': 'bad input: uuid malformed!'})
        mock_service.lookup_entity_by_uuid.assert_called_once_with(
            'uuid malformed')

    @patch('swh.web.api.views.entity.service')
    @istest
    def api_lookup_entity_by_uuid(self, mock_service):
        # when
        stub_entities = [
            {
                'uuid': '34bd6b1b-463f-43e5-a697-785107f598e4',
                'parent': 'aee991a0-f8d7-4295-a201-d1ce2efc9fb2'
            },
            {
                'uuid': 'aee991a0-f8d7-4295-a201-d1ce2efc9fb2'
            }
        ]
        mock_service.lookup_entity_by_uuid.return_value = stub_entities

        expected_entities = [
            {
                'uuid': '34bd6b1b-463f-43e5-a697-785107f598e4',
                'uuid_url': '/api/1/entity/34bd6b1b-463f-43e5-a697-'
                            '785107f598e4/',
                'parent': 'aee991a0-f8d7-4295-a201-d1ce2efc9fb2',
                'parent_url': '/api/1/entity/aee991a0-f8d7-4295-a201-'
                              'd1ce2efc9fb2/'
            },
            {
                'uuid': 'aee991a0-f8d7-4295-a201-d1ce2efc9fb2',
                'uuid_url': '/api/1/entity/aee991a0-f8d7-4295-a201-'
                            'd1ce2efc9fb2/'
            }
        ]

        # when
        rv = self.client.get('/api/1/entity'
                             '/34bd6b1b-463f-43e5-a697-785107f598e4/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv['Content-Type'], 'application/json')
        self.assertEquals(rv.data, expected_entities)
        mock_service.lookup_entity_by_uuid.assert_called_once_with(
            '34bd6b1b-463f-43e5-a697-785107f598e4')
