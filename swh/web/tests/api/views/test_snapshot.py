# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.test import APITestCase
from unittest.mock import patch

from swh.web.common.exc import BadInputExc, NotFoundExc
from swh.web.common.utils import reverse
from swh.web.tests.testcase import SWHWebTestCase

_snapshot_id = '36ce36946fcd0f39bdfc40727af4acfce81f67af'

_snapshot_branches = [
    {
        'name': 'gh-pages',
        'target': 'refs/heads/gh-pages',
        'target_type': 'alias',
    },
    {
        'name': 'latest',
        'target': 'refs/tags/v1.3.0',
        'target_type': 'alias',
    },
    {
        'name': 'refs/heads/andresgalante-dismissable-badges',
        'target': '3af57e6db525015a25b4f3abb29263432e4af7b1',
        'target_type': 'revision',
    },
    {
        'name': 'refs/heads/boom-toasted',
        'target': 'e3f4957facfbdc25fdc4c6d3f7fcf1c488f06cea',
        'target_type': 'revision',
    },
    {
        'name': 'refs/heads/flex-checks',
        'target': '1b08ea1630a987d6f56f0c99e869896485bf230b',
        'target_type': 'revision',
    },
    {
        'name': 'refs/heads/gh-pages',
        'target': 'ea4129886adec992483aa592db717f908b4be355',
        'target_type': 'revision',
    },
    {
        'name': 'refs/heads/grid-vertical-align-height',
        'target': 'ba23eea651f483b88b78bee1084d7d0f61161e8d',
        'target_type': 'revision',
    },
    {
        'name': 'refs/tags/v1.0.0',
        'target': 'd28343dc3ad53a411ae3685e7d6a7866c8c22d6b',
        'target_type': 'release',
    },
    {
        'name': 'refs/tags/v1.1.0',
        'target': '0f11410b77140852f835ad456e5fbcf28760846c',
        'target_type': 'release',
    },
    {
        'name': 'refs/tags/v1.1.1',
        'target': '4ca26e76ee4867bfcd65ecf81039f183fc1d3b4d',
        'target_type': 'release',
    },
    {
        'name': 'refs/tags/v1.2.0',
        'target': 'cabae13db21e0e1db686f5628d1725c6191062ef',
        'target_type': 'release',
    },
    {
        'name': 'refs/tags/v1.3.0',
        'target': '3c3d596d94501509bec1959a4cfb44b20bfa8606',
        'target_type': 'release',
    }
]


def _lookup_snapshot(snapshot_id, branches_from='',
                     branches_count=None, target_types=None):
    ret = {'id': snapshot_id, 'branches': {}}
    count = 0
    for branch in _snapshot_branches:
        if branches_count and count == branches_count:
            break
        if branch['name'] >= branches_from:
            if not target_types or branch['target_type'] in target_types: # noqa
                ret['branches'][branch['name']] = {
                    'target': branch['target'],
                    'target_type': branch['target_type']
                }
                count += 1
    return ret


def _get_branch_url(target_type, target):
    url = None
    if target_type == 'revision':
        url = reverse('api-revision', url_args={'sha1_git': target})
    if target_type == 'release':
        url = reverse('api-release', url_args={'sha1_git': target})
    return url


def _enrich_snapshot_data(snapshot_data):
    for branch in snapshot_data['branches'].keys():
        target = snapshot_data['branches'][branch]['target']
        target_type = snapshot_data['branches'][branch]['target_type']
        snapshot_data['branches'][branch]['target_url'] = \
            _get_branch_url(target_type, target)
    for branch in snapshot_data['branches'].keys():
        target = snapshot_data['branches'][branch]['target']
        target_type = snapshot_data['branches'][branch]['target_type']
        if target_type == 'alias':
            if target in snapshot_data['branches']:
                snapshot_data['branches'][branch]['target_url'] = \
                    snapshot_data['branches'][target]['target_url']
            else:
                snp = _lookup_snapshot(snapshot_data['id'],
                                       branches_from=target,
                                       branches_count=1)
                alias_target = snp['branches'][target]['target']
                alias_target_type = snp['branches'][target]['target_type']
                snapshot_data['branches'][branch]['target_url'] = \
                    _get_branch_url(alias_target_type, alias_target)

    return snapshot_data


@patch('swh.web.api.views.snapshot.service')
class SnapshotApiTestCase(SWHWebTestCase, APITestCase):

    def test_api_snapshot(self, mock_service):
        mock_service.lookup_snapshot.side_effect = _lookup_snapshot

        url = reverse('api-snapshot',
                      url_args={'snapshot_id': _snapshot_id})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        expected_data = _lookup_snapshot(_snapshot_id)
        expected_data = _enrich_snapshot_data(expected_data)
        self.assertEqual(rv.data, expected_data)

    def test_api_snapshot_paginated(self, mock_service):
        mock_service.lookup_snapshot.side_effect = _lookup_snapshot

        branches_offset = 0
        branches_count = 2

        whole_snapshot = {'id': _snapshot_id, 'branches': {}}

        while branches_offset < len(_snapshot_branches):
            branches_from = _snapshot_branches[branches_offset]['name']
            url = reverse('api-snapshot',
                          url_args={'snapshot_id': _snapshot_id},
                          query_params={'branches_from': branches_from,
                                        'branches_count': branches_count})
            rv = self.client.get(url)
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv['Content-Type'], 'application/json')
            expected_data = _lookup_snapshot(_snapshot_id, branches_from,
                                             branches_count)
            expected_data = _enrich_snapshot_data(expected_data)
            self.assertEqual(rv.data, expected_data)
            whole_snapshot['branches'].update(expected_data['branches'])
            branches_offset += branches_count

            if branches_offset < len(_snapshot_branches):
                next_branch = _snapshot_branches[branches_offset]['name'] # noqa
                next_url = reverse('api-snapshot',
                                   url_args={'snapshot_id': _snapshot_id},
                                   query_params={'branches_from': next_branch,
                                                 'branches_count': branches_count}) # noqa
                self.assertEqual(rv['Link'], '<%s>; rel="next"' % next_url)
            else:
                self.assertFalse(rv.has_header('Link'))

        url = reverse('api-snapshot',
                      url_args={'snapshot_id': _snapshot_id})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, whole_snapshot)

    def test_api_snapshot_filtered(self, mock_service):
        mock_service.lookup_snapshot.side_effect = _lookup_snapshot

        target_types = 'release'

        url = reverse('api-snapshot',
                      url_args={'snapshot_id': _snapshot_id},
                      query_params={'target_types': target_types})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        expected_data = _lookup_snapshot(_snapshot_id,
                                         target_types=target_types.split(','))
        expected_data = _enrich_snapshot_data(expected_data)
        self.assertEqual(rv.data, expected_data)

    def test_api_snapshot_errors(self, mock_service):
        mock_service.lookup_snapshot.side_effect = \
            BadInputExc('Invalid snapshot id!')

        url = reverse('api-snapshot',
                      url_args={'snapshot_id': '63ce369'})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 400)

        mock_service.lookup_snapshot.side_effect = \
            NotFoundExc('Snapshot not found!')

        snapshot_inexistent = '63ce36946fcd0f79bdfc40727af4acfce81f67fa'
        url = reverse('api-snapshot',
                      url_args={'snapshot_id': snapshot_inexistent})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 404)
