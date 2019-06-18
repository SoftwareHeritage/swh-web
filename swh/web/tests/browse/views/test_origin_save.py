# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from datetime import datetime
from unittest.mock import patch

from rest_framework.test import APITestCase, APIClient

from swh.web.common.origin_save import (
    SAVE_REQUEST_ACCEPTED, SAVE_TASK_NOT_YET_SCHEDULED
)
from swh.web.common.utils import reverse
from swh.web.settings.tests import save_origin_rate_post
from swh.web.tests.testcase import WebTestCase


class SwhBrowseOriginSaveTest(WebTestCase, APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.origin = {
            'type': 'git',
            'url': 'https://github.com/python/cpython'
        }

    @patch('swh.web.browse.views.origin_save.create_save_origin_request')
    def test_save_request_form_csrf_token(
            self, mock_create_save_origin_request):

        self._mock_create_save_origin_request(mock_create_save_origin_request)

        url = reverse('browse-origin-save-request',
                      url_args={'origin_type': self.origin['type'],
                                'origin_url':  self.origin['url']})

        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 403)

        data = self._get_csrf_token(reverse('browse-origin-save'))
        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 200)

    @patch('swh.web.browse.views.origin_save.create_save_origin_request')
    def test_save_request_form_rate_limit(
            self, mock_create_save_origin_request):

        self._mock_create_save_origin_request(mock_create_save_origin_request)

        url = reverse('browse-origin-save-request',
                      url_args={'origin_type': self.origin['type'],
                                'origin_url':  self.origin['url']})

        data = self._get_csrf_token(reverse('browse-origin-save'))
        for _ in range(save_origin_rate_post):
            resp = self.client.post(url, data=data)
            self.assertEqual(resp.status_code, 200)

        resp = self.client.post(url, data=data)
        self.assertEqual(resp.status_code, 429)

    def _get_csrf_token(self, url):
        resp = self.client.get(url)
        return {
            'csrfmiddlewaretoken': resp.cookies['csrftoken'].value
        }

    def _mock_create_save_origin_request(self, mock):
        expected_data = {
            'origin_type': self.origin['type'],
            'origin_url': self.origin['url'],
            'save_request_date': datetime.now().isoformat(),
            'save_request_status': SAVE_REQUEST_ACCEPTED,
            'save_task_status': SAVE_TASK_NOT_YET_SCHEDULED,
            'visit_date': None
        }
        mock.return_value = expected_data
