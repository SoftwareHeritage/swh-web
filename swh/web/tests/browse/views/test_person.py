# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given

from swh.web.common.utils import reverse
from swh.web.tests.strategies import person, unknown_person
from swh.web.tests.testcase import WebTestCase


class SwhBrowsePersonTest(WebTestCase):

    @given(person())
    def test_person_browse(self, person):
        test_person_data = self.person_get(person)

        url = reverse('browse-person', url_args={'person_id': person})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/person.html')
        self.assertContains(resp, '<pre>%s</pre>' % test_person_data['id'])
        self.assertContains(resp, '<pre>%s</pre>' % test_person_data['name'])
        self.assertContains(resp, '<pre><a href="mailto:%s">%s</a></pre>' %
                                  (test_person_data['email'],
                                   test_person_data['email']))
        self.assertContains(resp, '<pre>%s <<a href="mailto:%s">%s</a>></pre>' % # noqa
                                  (test_person_data['name'],
                                   test_person_data['email'],
                                   test_person_data['email']))

    @given(unknown_person())
    def test_person_request_error(self, unknown_person):
        url = reverse('browse-person', url_args={'person_id': unknown_person})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp,
                            'Person with id %s not found' % unknown_person,
                            status_code=404)
