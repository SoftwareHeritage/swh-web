# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from datetime import datetime
from hypothesis import given
from unittest.mock import patch

from swh.web.common.origin_save import (
    SAVE_REQUEST_ACCEPTED, SAVE_TASK_NOT_YET_SCHEDULED
)
from swh.web.config import get_config
from swh.web.common.utils import reverse
from swh.web.tests.strategies import origin
from swh.web.tests.testcase import WebTestCase


class SwhBrowseOriginSaveTest(WebTestCase):

    @given(origin())
    def test_recaptcha_activation_in_gui(self, origin):

        swh_web_config = get_config()

        for captcha_activated in (True, False):

            swh_web_config.update({
                'grecaptcha': {
                    'activated': captcha_activated,
                    'site_key': ''
                }
            })

            url = reverse('browse-origin-save')
            resp = self.client.get(url)

            captcha_script_url = 'https://www.google.com/recaptcha/api.js'
            captcha_dom_elt = '<div class="g-recaptcha"'

            if captcha_activated:
                self.assertContains(resp, captcha_script_url)
                self.assertContains(resp, captcha_dom_elt)
            else:
                self.assertNotContains(resp, captcha_script_url)
                self.assertNotContains(resp, captcha_dom_elt)

            url = reverse('browse-origin-directory',
                          url_args={'origin_type': origin['type'],
                                    'origin_url': origin['url']})

            resp = self.client.get(url)

            if captcha_activated:
                self.assertContains(resp, captcha_script_url)
                self.assertContains(resp, captcha_dom_elt)
            else:
                self.assertNotContains(resp, captcha_script_url)
                self.assertNotContains(resp, captcha_dom_elt)

    @patch('swh.web.browse.views.origin_save.create_save_origin_request')
    def test_recaptcha_not_activated_server_side(
            self, mock_create_save_origin_request):

        swh_web_config = get_config()

        swh_web_config.update({
            'grecaptcha': {
                'activated': False,
                'site_key': ''
            }
        })

        origin_type = 'git'
        origin_url = 'https://github.com/python/cpython'

        expected_data = {
            'origin_type': origin_type,
            'origin_url': origin_url,
            'save_request_date': datetime.now().isoformat(),
            'save_request_status': SAVE_REQUEST_ACCEPTED,
            'save_task_status': SAVE_TASK_NOT_YET_SCHEDULED,
            'visit_date': None
        }

        mock_create_save_origin_request.return_value = expected_data

        url = reverse('browse-origin-save-request',
                      url_args={'origin_type': origin_type,
                                'origin_url': origin_url})
        resp = self.client.post(
            url, data={}, content_type='application/json')

        save_request_data = json.loads(resp.content.decode('utf-8'))

        self.assertEqual(save_request_data, expected_data)

    @patch('swh.web.browse.views.origin_save.is_recaptcha_valid')
    @patch('swh.web.browse.views.origin_save.create_save_origin_request')
    def test_recaptcha_activated_server_side(
            self, mock_create_save_origin_request,
            mock_is_recaptcha_valid):

        swh_web_config = get_config()

        swh_web_config.update({
            'grecaptcha': {
                'activated': True,
                'site_key': ''
            }
        })

        origin_type = 'git'
        origin_url = 'https://github.com/python/cpython'

        expected_data = {
            'origin_type': origin_type,
            'origin_url': origin_url,
            'save_request_date': datetime.now().isoformat(),
            'save_request_status': SAVE_REQUEST_ACCEPTED,
            'save_task_status': SAVE_TASK_NOT_YET_SCHEDULED,
            'visit_date': None
        }

        mock_create_save_origin_request.return_value = expected_data

        for captcha_valid in (False, True):

            mock_is_recaptcha_valid.return_value = captcha_valid

            url = reverse('browse-origin-save-request',
                          url_args={'origin_type': origin_type,
                                    'origin_url': origin_url})
            resp = self.client.post(
                url, data={}, content_type='application/json')

            if captcha_valid is False:
                self.assertEqual(resp.status_code, 403)
            else:
                save_request_data = json.loads(resp.content.decode('utf-8'))
                self.assertEqual(save_request_data, expected_data)
