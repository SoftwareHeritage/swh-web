# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from unittest.mock import patch
from nose.tools import istest

from django.test import TestCase

from swh.web.common.utils import reverse

from .data.origin_test_data import (
    origin_info_test_data,
    origin_visits_test_data
)


class SwhBrowseOriginViewTest(TestCase):

    @patch('swh.web.browse.views.origin.get_origin_visits')
    @patch('swh.web.browse.views.origin.service')
    @istest
    def test_origin_browse(self, mock_service, mock_get_origin_visits):
        mock_service.lookup_origin.return_value = origin_info_test_data
        mock_get_origin_visits.return_value = origin_visits_test_data

        url = reverse('browse-origin',
                      kwargs={'origin_id': origin_info_test_data['id']})
        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('origin.html')
        self.assertContains(resp, '<td>%s</td>' % origin_info_test_data['id'])
        self.assertContains(resp, '<td>%s</td>' % origin_info_test_data['type']) # noqa
        self.assertContains(resp, '<td><a href="%s">%s</a></td>' %
                                  (origin_info_test_data['url'],
                                   origin_info_test_data['url']))

        self.assertContains(resp, '<tr class="swh-origin-visit">',
                            count=len(origin_visits_test_data))

        for visit in origin_visits_test_data:
            browse_url = reverse('browse-origin-directory',
                                 kwargs={'origin_id': visit['origin'],
                                         'visit_id': visit['visit']})
            self.assertContains(resp, '<td><a href="%s">%s</a></td>' %
                                (browse_url, browse_url))
