# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from unittest.mock import patch
from nose.tools import istest
from django.test import TestCase

from swh.web.common.utils import reverse


class SwhBrowsePersonTest(TestCase):

    @patch('swh.web.browse.views.person.service')
    @istest
    def person_browse(self, mock_service):
        test_person_data = \
            {
                "email": "j.adams440@gmail.com",
                "fullname": "oysterCrusher <j.adams440@gmail.com>",
                "id": 457587,
                "name": "oysterCrusher"
            }

        mock_service.lookup_person.return_value = test_person_data

        url = reverse('browse-person', kwargs={'person_id': 457587})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('person.html')
        self.assertContains(resp, '<td>%s</td>' % test_person_data['id'])
        self.assertContains(resp, '<td>%s</td>' % test_person_data['name'])
        self.assertContains(resp, '<td><a href="mailto:%s">%s</a></td>' %
                                  (test_person_data['email'],
                                   test_person_data['email']))
        self.assertContains(resp, '<td>%s <<a href="mailto:%s">%s</a>></td>' %
                                  (test_person_data['name'],
                                   test_person_data['email'],
                                   test_person_data['email']))
