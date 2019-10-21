# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import os

from datetime import datetime, timedelta, timezone

import pytest
import requests_mock

from swh.web.common.models import (
    SaveOriginRequest
)
from swh.web.common.origin_save import get_save_origin_task_info
from swh.web.config import get_config


_RESOURCES_PATH = os.path.join(os.path.dirname(__file__), '../resources')

_es_url = 'http://esnode1.internal.softwareheritage.org:9200'
_es_workers_index_url = '%s/swh_workers-*' % _es_url


def _get_save_origin_task_info_test(mocker, task_archived=False,
                                    es_available=True):

    swh_web_config = get_config()

    if es_available:
        swh_web_config.update({'es_workers_index_url': _es_workers_index_url})
    else:
        swh_web_config.update({'es_workers_index_url': ''})

    sor_id = 4473

    SaveOriginRequest.objects.create(
        id=sor_id,
        request_date=datetime(2019, 8, 30, 23, 7, 3, 474294,
                              tzinfo=timezone.utc),
        visit_type='git',
        origin_url='https://gitlab.com/inkscape/inkscape',
        status='accepted',
        loading_task_id=203525448,
        visit_date=datetime(2019, 8, 30, 23, 18, 11, 54341,
                            tzinfo=timezone.utc)
    )

    mock_scheduler = mocker.patch('swh.web.common.origin_save.scheduler')
    task = {
        'arguments': {
            'args': [],
            'kwargs': {
                'repo_url': 'https://gitlab.com/inkscape/inkscape'
            }
        },
        'current_interval': timedelta(days=64),
        'id': 203525448,
        'next_run': datetime(2019, 8, 30, 23, 7, 1, 614823),
        'policy': 'oneshot',
        'priority': 'high',
        'retries_left': 0,
        'status': 'disabled',
        'type': 'load-git'
    } if not task_archived else None
    mock_scheduler.get_tasks.return_value = [task]

    task_run = {
        'backend_id': 'f00c712c-e820-41ce-a07c-9bf8df914205',
        'ended': datetime(2019, 8, 30, 23, 18, 13, 770800),
        'id': 654270631,
        'metadata': {},
        'scheduled': datetime(2019, 8, 30, 23, 8, 34, 282021),
        'started': None,
        'status': 'failed',
        'task': 203525448
    }
    mock_scheduler.get_task_runs.return_value = [task_run]

    es_response = os.path.join(_RESOURCES_PATH,
                               'json/es_task_info_response.json')
    with open(es_response) as json_fd:
        es_response = json.load(json_fd)

    task_exec_data = es_response['hits']['hits'][-1]['_source']

    with requests_mock.Mocker() as requests_mocker:
        requests_mocker.register_uri('POST', _es_workers_index_url+'/_search',
                                     json=es_response)

        sor_task_info = get_save_origin_task_info(sor_id)

    expected_result = {
        'type': task['type'],
        'arguments': task['arguments'],
        'id': task['id'],
        'backend_id': task_run['backend_id'],
        'scheduled': task_run['scheduled'],
        'ended': task_run['ended'],
        'status': task_run['status'],
    } if not task_archived else {}

    if es_available and not task_archived:
        expected_result.update({
            'message': task_exec_data['message'],
            'name': task_exec_data['swh_task_name'],
            'worker': task_exec_data['hostname']
        })

    assert sor_task_info == expected_result


@pytest.mark.django_db
def test_get_save_origin_archived_task_info(mocker):
    _get_save_origin_task_info_test(mocker, task_archived=True)


@pytest.mark.django_db
def test_get_save_origin_task_info_with_es(mocker):
    _get_save_origin_task_info_test(mocker, es_available=True)


@pytest.mark.django_db
def test_get_save_origin_task_info_without_es(mocker):
    _get_save_origin_task_info_test(mocker, es_available=False)
