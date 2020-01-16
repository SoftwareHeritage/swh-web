# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random
import re

import swh.web.browse.utils

from django.utils.html import escape

from hypothesis import given

from swh.model.hashutil import hash_to_bytes
from swh.web.browse.utils import process_snapshot_branches
from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import (
    reverse, gen_path_info, format_utc_iso_date,
    parse_timestamp, get_swh_persistent_id
)
from swh.web.tests.data import get_content
from swh.web.tests.django_asserts import assert_contains, assert_template_used
from swh.web.tests.strategies import (
    origin, origin_with_multiple_visits, new_origin,
    new_snapshot, visit_dates, revisions, origin_with_releases
)


@given(origin_with_multiple_visits())
def test_origin_visits_browse(client, archive_data, origin):
    url = reverse('browse-origin-visits',
                  url_args={'origin_url': origin['url']})
    resp = client.get(url)

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/origin-visits.html')

    url = reverse('browse-origin-visits',
                  url_args={'origin_url': origin['url']})
    resp = client.get(url)

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/origin-visits.html')

    visits = archive_data.origin_visit_get(origin['url'])

    for v in visits:
        vdate = format_utc_iso_date(v['date'], '%Y-%m-%dT%H:%M:%SZ')
        browse_dir_url = reverse('browse-origin-directory',
                                 url_args={'origin_url': origin['url'],
                                           'timestamp': vdate})
        assert_contains(resp, browse_dir_url)


@given(origin_with_multiple_visits())
def test_origin_content_view(client, archive_data, origin):
    origin_visits = archive_data.origin_visit_get(origin['url'])

    def _get_archive_data(visit_idx):
        snapshot = archive_data.snapshot_get(
            origin_visits[visit_idx]['snapshot'])
        head_rev_id = archive_data.snapshot_get_head(snapshot)
        head_rev = archive_data.revision_get(head_rev_id)
        dir_content = archive_data.directory_ls(head_rev['directory'])
        dir_files = [e for e in dir_content if e['type'] == 'file']
        dir_file = random.choice(dir_files)
        branches, releases = process_snapshot_branches(snapshot)
        return {
            'branches': branches,
            'releases': releases,
            'root_dir_sha1': head_rev['directory'],
            'content': get_content(dir_file['checksums']['sha1']),
            'visit': origin_visits[visit_idx]
        }

    tdata = _get_archive_data(-1)

    _origin_content_view_test_helper(client, origin, origin_visits,
                                     tdata['branches'],
                                     tdata['releases'],
                                     tdata['root_dir_sha1'],
                                     tdata['content'])

    _origin_content_view_test_helper(client, origin, origin_visits,
                                     tdata['branches'],
                                     tdata['releases'],
                                     tdata['root_dir_sha1'],
                                     tdata['content'],
                                     timestamp=tdata['visit']['date'])

    visit_unix_ts = parse_timestamp(tdata['visit']['date']).timestamp()
    visit_unix_ts = int(visit_unix_ts)

    _origin_content_view_test_helper(client, origin, origin_visits,
                                     tdata['branches'],
                                     tdata['releases'],
                                     tdata['root_dir_sha1'],
                                     tdata['content'],
                                     timestamp=visit_unix_ts)

    tdata = _get_archive_data(0)

    _origin_content_view_test_helper(client, origin, origin_visits,
                                     tdata['branches'],
                                     tdata['releases'],
                                     tdata['root_dir_sha1'],
                                     tdata['content'],
                                     visit_id=tdata['visit']['visit'])


@given(origin())
def test_origin_root_directory_view(client, archive_data, origin):
    origin_visits = archive_data.origin_visit_get(origin['url'])

    visit = origin_visits[-1]
    snapshot = archive_data.snapshot_get(visit['snapshot'])
    head_rev_id = archive_data.snapshot_get_head(snapshot)
    head_rev = archive_data.revision_get(head_rev_id)
    root_dir_sha1 = head_rev['directory']
    dir_content = archive_data.directory_ls(root_dir_sha1)
    branches, releases = process_snapshot_branches(snapshot)
    visit_unix_ts = parse_timestamp(visit['date']).timestamp()
    visit_unix_ts = int(visit_unix_ts)

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, dir_content)

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, dir_content,
                                       visit_id=visit['visit'])

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, dir_content,
                                       timestamp=visit_unix_ts)

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, dir_content,
                                       timestamp=visit['date'])

    origin = dict(origin)
    del origin['type']

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, dir_content)

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, dir_content,
                                       visit_id=visit['visit'])

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, dir_content,
                                       timestamp=visit_unix_ts)

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, dir_content,
                                       timestamp=visit['date'])


@given(origin())
def test_origin_sub_directory_view(client, archive_data, origin):
    origin_visits = archive_data.origin_visit_get(origin['url'])

    visit = origin_visits[-1]
    snapshot = archive_data.snapshot_get(visit['snapshot'])
    head_rev_id = archive_data.snapshot_get_head(snapshot)
    head_rev = archive_data.revision_get(head_rev_id)
    root_dir_sha1 = head_rev['directory']
    subdirs = [e for e in archive_data.directory_ls(root_dir_sha1)
               if e['type'] == 'dir']
    branches, releases = process_snapshot_branches(snapshot)
    visit_unix_ts = parse_timestamp(visit['date']).timestamp()
    visit_unix_ts = int(visit_unix_ts)

    if len(subdirs) == 0:
        return

    subdir = random.choice(subdirs)
    subdir_content = archive_data.directory_ls(subdir['target'])
    subdir_path = subdir['name']

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, subdir_content,
                                       path=subdir_path)

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, subdir_content,
                                       path=subdir_path,
                                       visit_id=visit['visit'])

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, subdir_content,
                                       path=subdir_path,
                                       timestamp=visit_unix_ts)

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, subdir_content,
                                       path=subdir_path,
                                       timestamp=visit['date'])

    origin = dict(origin)
    del origin['type']

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, subdir_content,
                                       path=subdir_path)

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, subdir_content,
                                       path=subdir_path,
                                       visit_id=visit['visit'])

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, subdir_content,
                                       path=subdir_path,
                                       timestamp=visit_unix_ts)

    _origin_directory_view_test_helper(client, origin, origin_visits, branches,
                                       releases, root_dir_sha1, subdir_content,
                                       path=subdir_path,
                                       timestamp=visit['date'])


@given(origin())
def test_origin_branches(client, archive_data, origin):
    origin_visits = archive_data.origin_visit_get(origin['url'])

    visit = origin_visits[-1]
    snapshot = archive_data.snapshot_get(visit['snapshot'])
    snapshot_content = process_snapshot_branches(snapshot)

    _origin_branches_test_helper(client, origin, snapshot_content)

    origin = dict(origin)
    origin['type'] = None

    _origin_branches_test_helper(client, origin, snapshot_content)


@given(origin())
def test_origin_releases(client, archive_data, origin):
    origin_visits = archive_data.origin_visit_get(origin['url'])

    visit = origin_visits[-1]
    snapshot = archive_data.snapshot_get(visit['snapshot'])
    snapshot_content = process_snapshot_branches(snapshot)

    _origin_releases_test_helper(client, origin, snapshot_content)

    origin = dict(origin)
    origin['type'] = None

    _origin_releases_test_helper(client, origin, snapshot_content)


@given(new_origin(), new_snapshot(min_size=4, max_size=4), visit_dates(),
       revisions(min_size=3, max_size=3))
def test_origin_snapshot_null_branch(client, archive_data, new_origin,
                                     new_snapshot, visit_dates, revisions):
    snp_dict = new_snapshot.to_dict()
    new_origin = archive_data.origin_add([new_origin])[0]
    for i, branch in enumerate(snp_dict['branches'].keys()):
        if i == 0:
            snp_dict['branches'][branch] = None
        else:
            snp_dict['branches'][branch] = {
                'target_type': 'revision',
                'target': hash_to_bytes(revisions[i-1]),
            }

    archive_data.snapshot_add([snp_dict])
    visit = archive_data.origin_visit_add(
        new_origin['url'], visit_dates[0], type='git')
    archive_data.origin_visit_update(new_origin['url'], visit['visit'],
                                     status='partial',
                                     snapshot=snp_dict['id'])

    url = reverse('browse-origin-directory',
                  url_args={'origin_url': new_origin['url']})
    rv = client.get(url)
    assert rv.status_code == 200


@given(new_origin(), new_snapshot(min_size=4, max_size=4), visit_dates(),
       revisions(min_size=4, max_size=4))
def test_origin_snapshot_invalid_branch(client, archive_data, new_origin,
                                        new_snapshot, visit_dates, revisions):
    snp_dict = new_snapshot.to_dict()
    new_origin = archive_data.origin_add([new_origin])[0]
    for i, branch in enumerate(snp_dict['branches'].keys()):
        snp_dict['branches'][branch] = {
            'target_type': 'revision',
            'target': hash_to_bytes(revisions[i]),
        }

    archive_data.snapshot_add([snp_dict])
    visit = archive_data.origin_visit_add(
        new_origin['url'], visit_dates[0], type='git')
    archive_data.origin_visit_update(new_origin['url'], visit['visit'],
                                     status='full',
                                     snapshot=snp_dict['id'])

    url = reverse('browse-origin-directory',
                  url_args={'origin_url': new_origin['url']},
                  query_params={'branch': 'invalid_branch'})
    rv = client.get(url)
    assert rv.status_code == 404


def test_origin_request_errors(client, archive_data, mocker):
    mock_snapshot_service = mocker.patch(
        'swh.web.browse.views.utils.snapshot_context.service')
    mock_origin_service = mocker.patch('swh.web.browse.views.origin.service')
    mock_utils_service = mocker.patch('swh.web.browse.utils.service')
    mock_get_origin_visit_snapshot = mocker.patch(
        'swh.web.browse.utils.get_origin_visit_snapshot')
    mock_get_origin_visits = mocker.patch(
        'swh.web.common.origin_visits.get_origin_visits')
    mock_request_content = mocker.patch(
        'swh.web.browse.views.utils.snapshot_context.request_content')
    mock_origin_service.lookup_origin.side_effect = NotFoundExc(
        'origin not found')
    url = reverse('browse-origin-visits',
                  url_args={'origin_url': 'bar'})
    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, 'error.html')
    assert_contains(resp, 'origin not found', status_code=404)

    mock_origin_service.lookup_origin.side_effect = None
    mock_origin_service.lookup_origin.return_value = {'type': 'foo',
                                                      'url': 'bar',
                                                      'id': 457}
    mock_get_origin_visits.return_value = []
    url = reverse('browse-origin-directory',
                  url_args={'origin_url': 'bar'})
    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, 'error.html')
    assert_contains(resp, "No visit", status_code=404)

    mock_get_origin_visits.return_value = [{'visit': 1}]
    mock_get_origin_visit_snapshot.side_effect = NotFoundExc('visit not found')
    url = reverse('browse-origin-directory',
                  url_args={'origin_url': 'bar'},
                  query_params={'visit_id': 2})
    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, 'error.html')
    assert re.search('Visit.*not found', resp.content.decode('utf-8'))

    mock_get_origin_visits.return_value = [{
        'date': '2015-09-26T09:30:52.373449+00:00',
        'metadata': {},
        'origin': 457,
        'snapshot': 'bdaf9ac436488a8c6cda927a0f44e172934d3f65',
        'status': 'full',
        'visit': 1
    }]
    mock_get_origin_visit_snapshot.side_effect = None
    mock_get_origin_visit_snapshot.return_value = (
        [{'directory': 'ae59ceecf46367e8e4ad800e231fc76adc3afffb',
            'name': 'HEAD',
            'revision': '7bc08e1aa0b08cb23e18715a32aa38517ad34672',
            'date': '04 May 2017, 13:27 UTC',
            'message': ''}],
        []
    )
    mock_utils_service.lookup_snapshot_sizes.return_value = {
        'revision': 1,
        'release': 0
    }
    mock_lookup_directory = mock_utils_service.lookup_directory
    mock_lookup_directory.side_effect = NotFoundExc('Directory not found')
    url = reverse('browse-origin-directory',
                  url_args={'origin_url': 'bar'})
    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, 'error.html')
    assert_contains(resp, 'Directory not found', status_code=404)

    mock_origin_service.lookup_origin.side_effect = None
    mock_origin_service.lookup_origin.return_value = {'type': 'foo',
                                                      'url': 'bar',
                                                      'id': 457}
    mock_get_origin_visits.return_value = []
    url = reverse('browse-origin-content',
                  url_args={'origin_url': 'bar',
                            'path': 'foo'})
    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, 'error.html')
    assert_contains(resp, "No visit", status_code=404)

    mock_get_origin_visits.return_value = [{'visit': 1}]
    mock_get_origin_visit_snapshot.side_effect = NotFoundExc('visit not found')
    url = reverse('browse-origin-content',
                  url_args={'origin_url': 'bar',
                            'path': 'foo'},
                  query_params={'visit_id': 2})
    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, 'error.html')
    assert re.search('Visit.*not found', resp.content.decode('utf-8'))

    mock_get_origin_visits.return_value = [{
        'date': '2015-09-26T09:30:52.373449+00:00',
        'metadata': {},
        'origin': 457,
        'snapshot': 'bdaf9ac436488a8c6cda927a0f44e172934d3f65',
        'status': 'full',
        'type': 'git',
        'visit': 1
    }]
    mock_get_origin_visit_snapshot.side_effect = None
    mock_get_origin_visit_snapshot.return_value = ([], [])
    mock_utils_service.lookup_snapshot_sizes.return_value = {
        'revision': 0,
        'release': 0
    }
    mock_utils_service.lookup_origin.return_value = {'type': 'foo',
                                                     'url': 'bar',
                                                     'id': 457}
    url = reverse('browse-origin-content',
                  url_args={'origin_url': 'bar',
                            'path': 'baz'})
    resp = client.get(url)
    assert resp.status_code == 200
    assert_template_used(resp, 'browse/content.html')
    assert re.search('snapshot.*is empty', resp.content.decode('utf-8'))

    mock_get_origin_visit_snapshot.return_value = (
        [{'directory': 'ae59ceecf46367e8e4ad800e231fc76adc3afffb',
            'name': 'HEAD',
            'revision': '7bc08e1aa0b08cb23e18715a32aa38517ad34672',
            'date': '04 May 2017, 13:27 UTC',
            'message': ''}],
        []
    )
    mock_utils_service.lookup_snapshot_sizes.return_value = {
        'revision': 1,
        'release': 0
    }
    mock_snapshot_service.lookup_directory_with_path.return_value = {
        'target': '5ecd9f37b7a2d2e9980d201acd6286116f2ba1f1'
    }
    mock_request_content.side_effect = NotFoundExc('Content not found')
    url = reverse('browse-origin-content',
                  url_args={'origin_url': 'bar',
                            'path': 'baz'})
    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, 'error.html')
    assert_contains(resp, 'Content not found', status_code=404)

    mock_get_snapshot_context = mocker.patch(
        'swh.web.browse.views.utils.snapshot_context.get_snapshot_context')

    mock_get_snapshot_context.side_effect = NotFoundExc('Snapshot not found')
    url = reverse('browse-origin-directory',
                  url_args={'origin_url': 'bar'})
    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, 'error.html')
    assert_contains(resp, 'Snapshot not found', status_code=404)


def test_origin_empty_snapshot(client, mocker):
    mock_utils_service = mocker.patch('swh.web.browse.utils.service')
    mock_get_origin_visit_snapshot = mocker.patch(
        'swh.web.browse.utils.get_origin_visit_snapshot')
    mock_get_origin_visits = mocker.patch(
        'swh.web.common.origin_visits.get_origin_visits')
    mock_get_origin_visits.return_value = [{
        'date': '2015-09-26T09:30:52.373449+00:00',
        'metadata': {},
        'origin': 457,
        'snapshot': 'bdaf9ac436488a8c6cda927a0f44e172934d3f65',
        'status': 'full',
        'type': 'git',
        'visit': 1
    }]
    mock_get_origin_visit_snapshot.return_value = ([], [])
    mock_utils_service.lookup_snapshot_sizes.return_value = {
        'revision': 0,
        'release': 0
    }
    mock_utils_service.lookup_origin.return_value = {
        'id': 457,
        'url': 'https://github.com/foo/bar'
    }
    url = reverse('browse-origin-directory',
                  url_args={'origin_url': 'bar'})
    resp = client.get(url)
    assert resp.status_code == 200
    assert_template_used(resp, 'browse/directory.html')
    resp_content = resp.content.decode('utf-8')
    assert re.search('snapshot.*is empty', resp_content)
    assert not re.search('swh-tr-link', resp_content)


@given(origin_with_releases())
def test_origin_release_browse(client, archive_data, origin):
    # for swh.web.browse.utils.get_snapshot_content to only return one branch
    snapshot_max_size = swh.web.browse.utils.snapshot_content_max_size
    swh.web.browse.utils.snapshot_content_max_size = 1
    try:
        snapshot = archive_data.snapshot_get_latest(origin['url'])
        release = [b for b in snapshot['branches'].values()
                   if b['target_type'] == 'release'][-1]
        release_data = archive_data.release_get(release['target'])
        url = reverse('browse-origin-directory',
                      url_args={'origin_url': origin['url']},
                      query_params={'release': release_data['name']})

        resp = client.get(url)
        assert resp.status_code == 200
        assert_contains(resp, release_data['name'])
        assert_contains(resp, release['target'])
    finally:
        swh.web.browse.utils.snapshot_content_max_size = snapshot_max_size


@given(origin_with_releases())
def test_origin_release_browse_not_found(client, archive_data, origin):

    invalid_release_name = 'swh-foo-bar'
    url = reverse('browse-origin-directory',
                  url_args={'origin_url': origin['url']},
                  query_params={'release': invalid_release_name})

    resp = client.get(url)
    assert resp.status_code == 404
    assert re.search(f'Release {invalid_release_name}.*not found',
                     resp.content.decode('utf-8'))


def _origin_content_view_test_helper(client, origin_info, origin_visits,
                                     origin_branches, origin_releases,
                                     root_dir_sha1, content,
                                     visit_id=None, timestamp=None):
    content_path = '/'.join(content['path'].split('/')[1:])

    url_args = {'origin_url': origin_info['url'],
                'path': content_path}

    if not visit_id:
        visit_id = origin_visits[-1]['visit']

    query_params = {}

    if timestamp:
        url_args['timestamp'] = timestamp

    if visit_id:
        query_params['visit_id'] = visit_id

    url = reverse('browse-origin-content',
                  url_args=url_args,
                  query_params=query_params)

    resp = client.get(url)

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/content.html')

    assert type(content['data']) == str

    assert_contains(resp, '<code class="%s">' %
                    content['hljs_language'])
    assert_contains(resp, escape(content['data']))

    split_path = content_path.split('/')

    filename = split_path[-1]
    path = content_path.replace(filename, '')[:-1]

    path_info = gen_path_info(path)

    del url_args['path']

    if timestamp:
        url_args['timestamp'] = format_utc_iso_date(
            parse_timestamp(timestamp).isoformat(), '%Y-%m-%dT%H:%M:%S')

    root_dir_url = reverse('browse-origin-directory',
                           url_args=url_args,
                           query_params=query_params)

    assert_contains(resp, '<li class="swh-path">',
                    count=len(path_info)+1)

    assert_contains(resp, '<a href="%s">%s</a>' %
                    (root_dir_url, root_dir_sha1[:7]))

    for p in path_info:
        url_args['path'] = p['path']
        dir_url = reverse('browse-origin-directory',
                          url_args=url_args,
                          query_params=query_params)
        assert_contains(resp, '<a href="%s">%s</a>' %
                        (dir_url, p['name']))

    assert_contains(resp, '<li>%s</li>' % filename)

    query_string = 'sha1_git:' + content['sha1_git']

    url_raw = reverse('browse-content-raw',
                      url_args={'query_string': query_string},
                      query_params={'filename': filename})
    assert_contains(resp, url_raw)

    if 'args' in url_args:
        del url_args['path']

    origin_branches_url = reverse('browse-origin-branches',
                                  url_args=url_args,
                                  query_params=query_params)

    assert_contains(resp, '<a href="%s">Branches (%s)</a>' %
                    (origin_branches_url, len(origin_branches)))

    origin_releases_url = reverse('browse-origin-releases',
                                  url_args=url_args,
                                  query_params=query_params)

    assert_contains(resp, '<a href="%s">Releases (%s)</a>' %
                    (origin_releases_url, len(origin_releases)))

    assert_contains(resp, '<li class="swh-branch">',
                    count=len(origin_branches))

    url_args['path'] = content_path

    for branch in origin_branches:
        query_params['branch'] = branch['name']
        root_dir_branch_url = reverse('browse-origin-content',
                                      url_args=url_args,
                                      query_params=query_params)

        assert_contains(resp, '<a href="%s">' % root_dir_branch_url)

    assert_contains(resp, '<li class="swh-release">',
                    count=len(origin_releases))

    query_params['branch'] = None
    for release in origin_releases:
        query_params['release'] = release['name']
        root_dir_release_url = reverse('browse-origin-content',
                                       url_args=url_args,
                                       query_params=query_params)

        assert_contains(resp, '<a href="%s">' % root_dir_release_url)

    url = reverse('browse-origin-content',
                  url_args=url_args,
                  query_params=query_params)

    resp = client.get(url)
    assert resp.status_code == 200
    assert_template_used(resp, 'browse/content.html')

    swh_cnt_id = get_swh_persistent_id('content', content['sha1_git'])
    swh_cnt_id_url = reverse('browse-swh-id',
                             url_args={'swh_id': swh_cnt_id})
    assert_contains(resp, swh_cnt_id)
    assert_contains(resp, swh_cnt_id_url)

    assert_contains(resp, 'swh-take-new-snapshot')


def _origin_directory_view_test_helper(client, origin_info, origin_visits,
                                       origin_branches, origin_releases,
                                       root_directory_sha1, directory_entries,
                                       visit_id=None, timestamp=None,
                                       path=None):
    dirs = [e for e in directory_entries
            if e['type'] in ('dir', 'rev')]
    files = [e for e in directory_entries
             if e['type'] == 'file']

    if not visit_id:
        visit_id = origin_visits[-1]['visit']

    url_args = {'origin_url': origin_info['url']}

    query_params = {}

    if timestamp:
        url_args['timestamp'] = timestamp
    else:
        query_params['visit_id'] = visit_id

    if path:
        url_args['path'] = path

    url = reverse('browse-origin-directory',
                  url_args=url_args,
                  query_params=query_params)

    resp = client.get(url)

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/directory.html')

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/directory.html')

    assert_contains(resp, '<td class="swh-directory">',
                    count=len(dirs))
    assert_contains(resp, '<td class="swh-content">',
                    count=len(files))

    if timestamp:
        url_args['timestamp'] = format_utc_iso_date(
            parse_timestamp(timestamp).isoformat(), '%Y-%m-%dT%H:%M:%S')

    for d in dirs:
        if d['type'] == 'rev':
            dir_url = reverse('browse-revision',
                              url_args={'sha1_git': d['target']})
        else:
            dir_path = d['name']
            if path:
                dir_path = "%s/%s" % (path, d['name'])
            dir_url_args = dict(url_args)
            dir_url_args['path'] = dir_path
            dir_url = reverse('browse-origin-directory',
                              url_args=dir_url_args,
                              query_params=query_params)
        assert_contains(resp, dir_url)

    for f in files:
        file_path = f['name']
        if path:
            file_path = "%s/%s" % (path, f['name'])
        file_url_args = dict(url_args)
        file_url_args['path'] = file_path
        file_url = reverse('browse-origin-content',
                           url_args=file_url_args,
                           query_params=query_params)
        assert_contains(resp, file_url)

    if 'path' in url_args:
        del url_args['path']

    root_dir_branch_url = reverse('browse-origin-directory',
                                  url_args=url_args,
                                  query_params=query_params)

    nb_bc_paths = 1
    if path:
        nb_bc_paths = len(path.split('/')) + 1

    assert_contains(resp, '<li class="swh-path">', count=nb_bc_paths)
    assert_contains(resp, '<a href="%s">%s</a>' %
                    (root_dir_branch_url,
                     root_directory_sha1[:7]))

    origin_branches_url = reverse('browse-origin-branches',
                                  url_args=url_args,
                                  query_params=query_params)

    assert_contains(resp, '<a href="%s">Branches (%s)</a>' %
                    (origin_branches_url, len(origin_branches)))

    origin_releases_url = reverse('browse-origin-releases',
                                  url_args=url_args,
                                  query_params=query_params)

    nb_releases = len(origin_releases)
    if nb_releases > 0:
        assert_contains(resp, '<a href="%s">Releases (%s)</a>' %
                        (origin_releases_url, nb_releases))

    if path:
        url_args['path'] = path

    assert_contains(resp, '<li class="swh-branch">',
                    count=len(origin_branches))

    for branch in origin_branches:
        query_params['branch'] = branch['name']
        root_dir_branch_url = reverse('browse-origin-directory',
                                      url_args=url_args,
                                      query_params=query_params)

        assert_contains(resp, '<a href="%s">' % root_dir_branch_url)

    assert_contains(resp, '<li class="swh-release">',
                    count=len(origin_releases))

    query_params['branch'] = None
    for release in origin_releases:
        query_params['release'] = release['name']
        root_dir_release_url = reverse('browse-origin-directory',
                                       url_args=url_args,
                                       query_params=query_params)

        assert_contains(resp, '<a href="%s">' % root_dir_release_url)

    assert_contains(resp, 'vault-cook-directory')
    assert_contains(resp, 'vault-cook-revision')

    swh_dir_id = get_swh_persistent_id('directory', directory_entries[0]['dir_id'])  # noqa
    swh_dir_id_url = reverse('browse-swh-id',
                             url_args={'swh_id': swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)

    assert_contains(resp, 'swh-take-new-snapshot')


def _origin_branches_test_helper(client, origin_info, origin_snapshot):
    url_args = {'origin_url': origin_info['url']}

    url = reverse('browse-origin-branches',
                  url_args=url_args)

    resp = client.get(url)

    assert resp.status_code == 200
    assert_template_used(resp, 'browse/branches.html')

    origin_branches = origin_snapshot[0]
    origin_releases = origin_snapshot[1]

    origin_branches_url = reverse('browse-origin-branches',
                                  url_args=url_args)

    assert_contains(resp, '<a href="%s">Branches (%s)</a>' %
                    (origin_branches_url, len(origin_branches)))

    origin_releases_url = reverse('browse-origin-releases',
                                  url_args=url_args)

    nb_releases = len(origin_releases)
    if nb_releases > 0:
        assert_contains(resp, '<a href="%s">Releases (%s)</a>' %
                        (origin_releases_url, nb_releases))

    assert_contains(resp, '<tr class="swh-branch-entry',
                    count=len(origin_branches))

    for branch in origin_branches:
        browse_branch_url = reverse(
            'browse-origin-directory',
            url_args={'origin_url': origin_info['url']},
            query_params={'branch': branch['name']})
        assert_contains(resp, '<a href="%s">' %
                        escape(browse_branch_url))

        browse_revision_url = reverse(
            'browse-revision',
            url_args={'sha1_git': branch['revision']},
            query_params={'origin': origin_info['url']})
        assert_contains(resp, '<a href="%s">' %
                        escape(browse_revision_url))


def _origin_releases_test_helper(client, origin_info, origin_snapshot):
    url_args = {'origin_url': origin_info['url']}

    url = reverse('browse-origin-releases',
                  url_args=url_args)

    resp = client.get(url)
    assert resp.status_code == 200
    assert_template_used(resp, 'browse/releases.html')

    origin_branches = origin_snapshot[0]
    origin_releases = origin_snapshot[1]

    origin_branches_url = reverse('browse-origin-branches',
                                  url_args=url_args)

    assert_contains(resp, '<a href="%s">Branches (%s)</a>' %
                    (origin_branches_url, len(origin_branches)))

    origin_releases_url = reverse('browse-origin-releases',
                                  url_args=url_args)

    nb_releases = len(origin_releases)
    if nb_releases > 0:
        assert_contains(resp, '<a href="%s">Releases (%s)</a>' %
                        (origin_releases_url, nb_releases))

    assert_contains(resp, '<tr class="swh-release-entry',
                    count=nb_releases)

    for release in origin_releases:
        browse_release_url = reverse(
            'browse-release',
            url_args={'sha1_git': release['id']},
            query_params={'origin': origin_info['url']})
        browse_revision_url = reverse(
            'browse-revision',
            url_args={'sha1_git': release['target']},
            query_params={'origin': origin_info['url']})

        assert_contains(resp, '<a href="%s">' %
                        escape(browse_release_url))
        assert_contains(resp, '<a href="%s">' %
                        escape(browse_revision_url))
