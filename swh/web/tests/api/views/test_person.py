# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.test import APITestCase
from unittest.mock import patch

from swh.web.tests.testcase import SWHWebTestCase


class PersonApiTestCase(SWHWebTestCase, APITestCase):

    @patch('swh.web.api.views.person.service')
    def test_api_person(self, mock_service):
        # given
        stub_person = {
            'id': '198003',
            'name': 'Software Heritage',
            'email': 'robot@softwareheritage.org',
        }
        mock_service.lookup_person.return_value = stub_person

        # when
        rv = self.client.get('/api/1/person/198003/')

        # then
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, stub_person)

    @patch('swh.web.api.views.person.service')
    def test_api_person_not_found(self, mock_service):
        # given
        mock_service.lookup_person.return_value = None

        # when
        rv = self.client.get('/api/1/person/666/')

        # then
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Person with id 666 not found.'})
