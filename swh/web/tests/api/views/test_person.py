# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given
from rest_framework.test import APITestCase

from swh.web.common.utils import reverse
from swh.web.tests.strategies import person, unknown_person
from swh.web.tests.testcase import WebTestCase


class PersonApiTestCase(WebTestCase, APITestCase):

    @given(person())
    def test_api_person(self, person):

        url = reverse('api-person', url_args={'person_id': person})

        rv = self.client.get(url)

        expected_person = self.person_get(person)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_person)

    @given(unknown_person())
    def test_api_person_not_found(self, unknown_person):

        url = reverse('api-person', url_args={'person_id': unknown_person})

        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Person with id %s not found' % unknown_person})
