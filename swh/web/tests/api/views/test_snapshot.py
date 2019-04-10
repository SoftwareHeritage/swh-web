# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from hypothesis import given
from rest_framework.test import APITestCase

from swh.web.common.utils import reverse
from swh.web.tests.strategies import snapshot, unknown_snapshot
from swh.web.tests.testcase import WebTestCase


class SnapshotApiTestCase(WebTestCase, APITestCase):

    @given(snapshot())
    def test_api_snapshot(self, snapshot):

        url = reverse('api-snapshot',
                      url_args={'snapshot_id': snapshot})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        expected_data = self.snapshot_get(snapshot)
        expected_data = self._enrich_snapshot(expected_data)
        self.assertEqual(rv.data, expected_data)

    @given(snapshot())
    def test_api_snapshot_paginated(self, snapshot):

        branches_offset = 0
        branches_count = 2

        snapshot_branches = []

        for k, v in sorted(self.snapshot_get(snapshot)['branches'].items()):
            snapshot_branches.append({
                'name': k,
                'target_type': v['target_type'],
                'target': v['target']
            })

        whole_snapshot = {'id': snapshot, 'branches': {}, 'next_branch': None}

        while branches_offset < len(snapshot_branches):
            branches_from = snapshot_branches[branches_offset]['name']
            url = reverse('api-snapshot',
                          url_args={'snapshot_id': snapshot},
                          query_params={'branches_from': branches_from,
                                        'branches_count': branches_count})
            rv = self.client.get(url)
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv['Content-Type'], 'application/json')
            expected_data = self.snapshot_get_branches(snapshot, branches_from,
                                                       branches_count)

            expected_data = self._enrich_snapshot(expected_data)

            branches_offset += branches_count
            if branches_offset < len(snapshot_branches):
                next_branch = snapshot_branches[branches_offset]['name']
                expected_data['next_branch'] = next_branch
            else:
                expected_data['next_branch'] = None

            self.assertEqual(rv.data, expected_data)
            whole_snapshot['branches'].update(expected_data['branches'])

            if branches_offset < len(snapshot_branches):
                next_url = reverse(
                    'api-snapshot',
                    url_args={'snapshot_id': snapshot},
                    query_params={'branches_from': next_branch,
                                  'branches_count': branches_count})
                self.assertEqual(rv['Link'], '<%s>; rel="next"' % next_url)
            else:
                self.assertFalse(rv.has_header('Link'))

        url = reverse('api-snapshot',
                      url_args={'snapshot_id': snapshot})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, whole_snapshot)

    @given(snapshot())
    def test_api_snapshot_filtered(self, snapshot):

        snapshot_branches = []

        for k, v in sorted(self.snapshot_get(snapshot)['branches'].items()):
            snapshot_branches.append({
                'name': k,
                'target_type': v['target_type'],
                'target': v['target']
            })

        target_type = random.choice(snapshot_branches)['target_type']

        url = reverse('api-snapshot',
                      url_args={'snapshot_id': snapshot},
                      query_params={'target_types': target_type})
        rv = self.client.get(url)

        expected_data = self.snapshot_get_branches(
            snapshot, target_types=target_type)
        expected_data = self._enrich_snapshot(expected_data)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_data)

    @given(unknown_snapshot())
    def test_api_snapshot_errors(self, unknown_snapshot):

        url = reverse('api-snapshot',
                      url_args={'snapshot_id': '63ce369'})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 400)

        url = reverse('api-snapshot',
                      url_args={'snapshot_id': unknown_snapshot})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 404)

    def _enrich_snapshot(self, snapshot):
        def _get_branch_url(target_type, target):
            url = None
            if target_type == 'revision':
                url = reverse('api-revision', url_args={'sha1_git': target})
            if target_type == 'release':
                url = reverse('api-release', url_args={'sha1_git': target})
            return url

        for branch in snapshot['branches'].keys():
            target = snapshot['branches'][branch]['target']
            target_type = snapshot['branches'][branch]['target_type']
            snapshot['branches'][branch]['target_url'] = \
                _get_branch_url(target_type, target)
        for branch in snapshot['branches'].keys():
            target = snapshot['branches'][branch]['target']
            target_type = snapshot['branches'][branch]['target_type']
            if target_type == 'alias':
                if target in snapshot['branches']:
                    snapshot['branches'][branch]['target_url'] = \
                        snapshot['branches'][target]['target_url']
                else:
                    snp = self.snapshot_get_branches(snapshot['id'],
                                                     branches_from=target,
                                                     branches_count=1)
                    alias_target = snp['branches'][target]['target']
                    alias_target_type = snp['branches'][target]['target_type']
                    snapshot['branches'][branch]['target_url'] = \
                        _get_branch_url(alias_target_type, alias_target)

        return snapshot

    @given(snapshot())
    def test_api_snapshot_uppercase(self, snapshot):
        url = reverse('api-snapshot-uppercase-checksum',
                      url_args={'snapshot_id': snapshot.upper()})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        redirect_url = reverse('api-snapshot-uppercase-checksum',
                               url_args={'snapshot_id': snapshot})

        self.assertEqual(resp['location'], redirect_url)
