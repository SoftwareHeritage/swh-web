# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from unittest.mock import patch

from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import reverse
from swh.web.tests.testcase import SWHWebTestCase


class SwhBrowsePersonTest(SWHWebTestCase):

    @patch('swh.web.browse.views.person.service')
    def test_person_browse(self, mock_service):
        test_person_data = \
            {
                "email": "j.adams440@gmail.com",
                "fullname": "oysterCrusher <j.adams440@gmail.com>",
                "id": 457587,
                "name": "oysterCrusher"
            }

        mock_service.lookup_person.return_value = test_person_data

        url = reverse('browse-person', url_args={'person_id': 457587})

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

    @patch('swh.web.browse.views.person.service')
    def test_person_request_error(self, mock_service):
        mock_service.lookup_person.side_effect = \
            NotFoundExc('Person not found')

        url = reverse('browse-person', url_args={'person_id': 457587})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'Person not found', status_code=404)
