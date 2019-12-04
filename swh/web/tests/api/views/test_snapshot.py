# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from hypothesis import given

from swh.model.hashutil import hash_to_hex
from swh.web.common.utils import reverse
from swh.web.tests.data import random_sha1
from swh.web.tests.strategies import (
    snapshot, new_snapshot
)


@given(snapshot())
def test_api_snapshot(api_client, archive_data, snapshot):

    url = reverse('api-1-snapshot',
                  url_args={'snapshot_id': snapshot})
    rv = api_client.get(url)

    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    expected_data = archive_data.snapshot_get(snapshot)
    expected_data = _enrich_snapshot(archive_data, expected_data)
    assert rv.data == expected_data


@given(snapshot())
def test_api_snapshot_paginated(api_client, archive_data, snapshot):

    branches_offset = 0
    branches_count = 2

    snapshot_branches = []

    for k, v in sorted(
            archive_data.snapshot_get(snapshot)['branches'].items()):
        snapshot_branches.append({
            'name': k,
            'target_type': v['target_type'],
            'target': v['target']
        })

    whole_snapshot = {'id': snapshot, 'branches': {}, 'next_branch': None}

    while branches_offset < len(snapshot_branches):
        branches_from = snapshot_branches[branches_offset]['name']
        url = reverse('api-1-snapshot',
                      url_args={'snapshot_id': snapshot},
                      query_params={'branches_from': branches_from,
                                    'branches_count': branches_count})
        rv = api_client.get(url)
        assert rv.status_code == 200, rv.data
        assert rv['Content-Type'] == 'application/json'
        expected_data = archive_data.snapshot_get_branches(
            snapshot, branches_from, branches_count)

        expected_data = _enrich_snapshot(archive_data, expected_data)

        branches_offset += branches_count
        if branches_offset < len(snapshot_branches):
            next_branch = snapshot_branches[branches_offset]['name']
            expected_data['next_branch'] = next_branch
        else:
            expected_data['next_branch'] = None

        assert rv.data == expected_data
        whole_snapshot['branches'].update(expected_data['branches'])

        if branches_offset < len(snapshot_branches):
            next_url = reverse(
                'api-1-snapshot',
                url_args={'snapshot_id': snapshot},
                query_params={'branches_from': next_branch,
                              'branches_count': branches_count})
            assert rv['Link'] == '<%s>; rel="next"' % next_url
        else:
            assert not rv.has_header('Link')

    url = reverse('api-1-snapshot',
                  url_args={'snapshot_id': snapshot})
    rv = api_client.get(url)

    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == whole_snapshot


@given(snapshot())
def test_api_snapshot_filtered(api_client, archive_data, snapshot):

    snapshot_branches = []

    for k, v in sorted(
            archive_data.snapshot_get(snapshot)['branches'].items()):
        snapshot_branches.append({
            'name': k,
            'target_type': v['target_type'],
            'target': v['target']
        })

    target_type = random.choice(snapshot_branches)['target_type']

    url = reverse('api-1-snapshot',
                  url_args={'snapshot_id': snapshot},
                  query_params={'target_types': target_type})
    rv = api_client.get(url)

    expected_data = archive_data.snapshot_get_branches(
        snapshot, target_types=target_type)
    expected_data = _enrich_snapshot(archive_data, expected_data)

    assert rv.status_code == 200, rv.data
    assert rv['Content-Type'] == 'application/json'
    assert rv.data == expected_data


def test_api_snapshot_errors(api_client):
    unknown_snapshot_ = random_sha1()

    url = reverse('api-1-snapshot',
                  url_args={'snapshot_id': '63ce369'})
    rv = api_client.get(url)
    assert rv.status_code == 400, rv.data

    url = reverse('api-1-snapshot',
                  url_args={'snapshot_id': unknown_snapshot_})
    rv = api_client.get(url)
    assert rv.status_code == 404, rv.data


@given(snapshot())
def test_api_snapshot_uppercase(api_client, snapshot):
    url = reverse('api-1-snapshot-uppercase-checksum',
                  url_args={'snapshot_id': snapshot.upper()})

    resp = api_client.get(url)
    assert resp.status_code == 302

    redirect_url = reverse('api-1-snapshot-uppercase-checksum',
                           url_args={'snapshot_id': snapshot})

    assert resp['location'] == redirect_url


@given(new_snapshot(min_size=4))
def test_api_snapshot_null_branch(api_client, archive_data, new_snapshot):
    snp_dict = new_snapshot.to_dict()
    snp_id = hash_to_hex(snp_dict['id'])
    for branch in snp_dict['branches'].keys():
        snp_dict['branches'][branch] = None
        break
    archive_data.snapshot_add([snp_dict])
    url = reverse('api-1-snapshot',
                  url_args={'snapshot_id': snp_id})
    rv = api_client.get(url)
    assert rv.status_code == 200, rv.data


def _enrich_snapshot(archive_data, snapshot):
    def _get_branch_url(target_type, target):
        url = None
        if target_type == 'revision':
            url = reverse('api-1-revision', url_args={'sha1_git': target})
        if target_type == 'release':
            url = reverse('api-1-release', url_args={'sha1_git': target})
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
                snp = archive_data.snapshot_get_branches(snapshot['id'],
                                                         branches_from=target,
                                                         branches_count=1)
                alias_target = snp['branches'][target]['target']
                alias_target_type = snp['branches'][target]['target_type']
                snapshot['branches'][branch]['target_url'] = \
                    _get_branch_url(alias_target_type, alias_target)

    return snapshot
