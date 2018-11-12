# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta
from django.utils import timezone

from rest_framework.test import APITestCase
from unittest.mock import patch

from swh.web.common.utils import reverse
from swh.web.common.models import (
    SaveUnauthorizedOrigin, SaveOriginRequest,
    SAVE_REQUEST_ACCEPTED, SAVE_REQUEST_REJECTED,
    SAVE_REQUEST_PENDING
)
from swh.web.common.models import (
    SAVE_TASK_NOT_CREATED, SAVE_TASK_NOT_YET_SCHEDULED,
    SAVE_TASK_SCHEDULED, SAVE_TASK_FAILED, SAVE_TASK_SUCCEED
)
from swh.web.tests.testcase import SWHWebTestCase


class SaveApiTestCase(SWHWebTestCase, APITestCase):

    @classmethod
    def setUpTestData(cls):  # noqa: N802
        SaveUnauthorizedOrigin.objects.create(
            url='https://github.com/user/illegal_repo')
        SaveUnauthorizedOrigin.objects.create(
            url='https://gitlab.com/user_to_exclude')

    def test_invalid_origin_type(self):
        url = reverse('api-save-origin',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'https://github.com/torvalds/linux'}) # noqa

        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def test_invalid_origin_url(self):
        url = reverse('api-save-origin',
                      url_args={'origin_type': 'git',
                                'origin_url': 'bar'})

        response = self.client.post(url)
        self.assertEqual(response.status_code, 400)

    def check_created_save_request_status(self, mock_scheduler, origin_url,
                                          scheduler_task_status,
                                          expected_request_status,
                                          expected_task_status=None,
                                          visit_date=None):

        if not scheduler_task_status:
            mock_scheduler.get_tasks.return_value = []
        else:
            mock_scheduler.get_tasks.return_value = \
                [{
                    'priority': 'high',
                    'policy': 'oneshot',
                    'type': 'origin-update-git',
                    'arguments': {
                        'kwargs': {
                            'repo_url': origin_url
                        },
                        'args': []
                    },
                    'status': scheduler_task_status,
                    'id': 1,
                }]

        mock_scheduler.create_tasks.return_value = \
            [{
                'priority': 'high',
                'policy': 'oneshot',
                'type': 'origin-update-git',
                'arguments': {
                    'kwargs': {
                        'repo_url': origin_url
                    },
                    'args': []
                },
                'status': 'next_run_not_scheduled',
                'id': 1,
             }]

        url = reverse('api-save-origin',
                      url_args={'origin_type': 'git',
                                'origin_url': origin_url})

        with patch('swh.web.common.origin_save._get_visit_date_for_save_request') as mock_visit_date: # noqa
            mock_visit_date.return_value = visit_date
            response = self.client.post(url)

            if expected_request_status != SAVE_REQUEST_REJECTED:
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data['save_request_status'],
                                 expected_request_status)
                self.assertEqual(response.data['save_task_status'],
                                 expected_task_status)

            else:
                self.assertEqual(response.status_code, 403)

    def check_save_request_status(self, mock_scheduler, origin_url,
                                  expected_request_status,
                                  expected_task_status,
                                  scheduler_task_status='next_run_not_scheduled', # noqa
                                  visit_date=None):

        mock_scheduler.get_tasks.return_value = \
            [{
                'priority': 'high',
                'policy': 'oneshot',
                'type': 'origin-update-git',
                'arguments': {
                    'kwargs': {
                        'repo_url': origin_url
                    },
                    'args': []
                },
                'status': scheduler_task_status,
                'id': 1,
             }]

        url = reverse('api-save-origin',
                      url_args={'origin_type': 'git',
                                'origin_url': origin_url})

        with patch('swh.web.common.origin_save._get_visit_date_for_save_request') as mock_visit_date: # noqa
            mock_visit_date.return_value = visit_date
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            save_request_data = response.data[0]

            self.assertEqual(save_request_data['save_request_status'],
                             expected_request_status)
            self.assertEqual(save_request_data['save_task_status'],
                             expected_task_status)

            # Check that save task status is still available when
            # the scheduler task has been archived
            mock_scheduler.get_tasks.return_value = []
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            save_request_data = response.data[0]
            self.assertEqual(save_request_data['save_task_status'],
                             expected_task_status)

    @patch('swh.web.common.origin_save.scheduler')
    def test_save_request_rejected(self, mock_scheduler):
        origin_url = 'https://github.com/user/illegal_repo'
        self.check_created_save_request_status(mock_scheduler, origin_url,
                                               None, SAVE_REQUEST_REJECTED)
        self.check_save_request_status(mock_scheduler, origin_url,
                                       SAVE_REQUEST_REJECTED,
                                       SAVE_TASK_NOT_CREATED)

    @patch('swh.web.common.origin_save.scheduler')
    def test_save_request_pending(self, mock_scheduler):
        origin_url = 'https://unkwownforge.com/user/repo'
        self.check_created_save_request_status(mock_scheduler, origin_url,
                                               None, SAVE_REQUEST_PENDING,
                                               SAVE_TASK_NOT_CREATED)
        self.check_save_request_status(mock_scheduler, origin_url,
                                       SAVE_REQUEST_PENDING,
                                       SAVE_TASK_NOT_CREATED)

    @patch('swh.web.common.origin_save.scheduler')
    def test_save_request_succeed(self, mock_scheduler):
        origin_url = 'https://github.com/Kitware/CMake'
        self.check_created_save_request_status(mock_scheduler, origin_url,
                                               None, SAVE_REQUEST_ACCEPTED,
                                               SAVE_TASK_NOT_YET_SCHEDULED)
        self.check_save_request_status(mock_scheduler, origin_url,
                                       SAVE_REQUEST_ACCEPTED,
                                       SAVE_TASK_SCHEDULED,
                                       scheduler_task_status='next_run_scheduled') # noqa
        self.check_save_request_status(mock_scheduler, origin_url,
                                       SAVE_REQUEST_ACCEPTED,
                                       SAVE_TASK_SCHEDULED,
                                       scheduler_task_status='completed',
                                       visit_date=None) # noqa
        visit_date = datetime.now(tz=timezone.utc) + timedelta(hours=1)
        self.check_save_request_status(mock_scheduler, origin_url,
                                       SAVE_REQUEST_ACCEPTED,
                                       SAVE_TASK_SUCCEED,
                                       scheduler_task_status='completed',
                                       visit_date=visit_date) # noqa

    @patch('swh.web.common.origin_save.scheduler')
    def test_save_request_failed(self, mock_scheduler):
        origin_url = 'https://gitlab.com/inkscape/inkscape'
        self.check_created_save_request_status(mock_scheduler, origin_url,
                                               None, SAVE_REQUEST_ACCEPTED,
                                               SAVE_TASK_NOT_YET_SCHEDULED)
        self.check_save_request_status(mock_scheduler, origin_url,
                                       SAVE_REQUEST_ACCEPTED,
                                       SAVE_TASK_SCHEDULED,
                                       scheduler_task_status='next_run_scheduled') # noqa
        self.check_save_request_status(mock_scheduler, origin_url,
                                       SAVE_REQUEST_ACCEPTED,
                                       SAVE_TASK_FAILED,
                                       scheduler_task_status='disabled') # noqa

    @patch('swh.web.common.origin_save.scheduler')
    def test_create_save_request_only_when_needed(self, mock_scheduler):
        origin_url = 'https://gitlab.com/webpack/webpack'
        SaveOriginRequest.objects.create(origin_type='git',
                                         origin_url=origin_url,
                                         status=SAVE_REQUEST_ACCEPTED, # noqa
                                         loading_task_id=56)

        self.check_created_save_request_status(mock_scheduler, origin_url,
                                               'next_run_not_scheduled',
                                               SAVE_REQUEST_ACCEPTED,
                                               SAVE_TASK_NOT_YET_SCHEDULED)
        sors = list(SaveOriginRequest.objects.filter(origin_type='git',
                                                     origin_url=origin_url))
        self.assertEqual(len(sors), 1)

        self.check_created_save_request_status(mock_scheduler, origin_url,
                                               'next_run_scheduled',
                                               SAVE_REQUEST_ACCEPTED,
                                               SAVE_TASK_SCHEDULED)
        sors = list(SaveOriginRequest.objects.filter(origin_type='git',
                                                     origin_url=origin_url))
        self.assertEqual(len(sors), 1)

        visit_date = datetime.now(tz=timezone.utc) + timedelta(hours=1)
        self.check_created_save_request_status(mock_scheduler, origin_url,
                                               'completed',
                                               SAVE_REQUEST_ACCEPTED,
                                               SAVE_TASK_NOT_YET_SCHEDULED,
                                               visit_date=visit_date)
        sors = list(SaveOriginRequest.objects.filter(origin_type='git',
                                                     origin_url=origin_url))
        self.assertEqual(len(sors), 2)

        self.check_created_save_request_status(mock_scheduler, origin_url,
                                               'disabled',
                                               SAVE_REQUEST_ACCEPTED,
                                               SAVE_TASK_NOT_YET_SCHEDULED)
        sors = list(SaveOriginRequest.objects.filter(origin_type='git',
                                                     origin_url=origin_url))
        self.assertEqual(len(sors), 3)
