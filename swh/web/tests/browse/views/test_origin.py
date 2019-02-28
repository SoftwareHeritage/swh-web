# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from unittest.mock import patch

from django.utils.html import escape

from hypothesis import given

from swh.web.browse.utils import process_snapshot_branches
from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import (
    reverse, gen_path_info, format_utc_iso_date,
    parse_timestamp, get_swh_persistent_id
)
from swh.web.tests.data import get_content
from swh.web.tests.strategies import (
    origin, origin_with_multiple_visits
)
from swh.web.tests.testcase import WebTestCase


class SwhBrowseOriginTest(WebTestCase):

    @given(origin_with_multiple_visits())
    def test_origin_visits_browse(self, origin):

        url = reverse('browse-origin-visits',
                      url_args={'origin_type': origin['type'],
                                'origin_url': origin['url']})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('origin-visits.html')

        url = reverse('browse-origin-visits',
                      url_args={'origin_url': origin['url']})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('origin-visits.html')

        visits = self.origin_visit_get(origin['id'])

        for v in visits:
            vdate = format_utc_iso_date(v['date'], '%Y-%m-%dT%H:%M:%SZ')
            browse_dir_url = reverse('browse-origin-directory',
                                     url_args={'origin_url': origin['url'],
                                               'timestamp': vdate})
            self.assertContains(resp, browse_dir_url)

    def origin_content_view_helper(self, origin_info, origin_visits,
                                   origin_branches, origin_releases,
                                   root_dir_sha1, content,
                                   visit_id=None, timestamp=None):

        content_path = '/'.join(content['path'].split('/')[1:])

        url_args = {'origin_type': origin_info['type'],
                    'origin_url': origin_info['url'],
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

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('content.html')

        self.assertContains(resp, '<code class="%s">' %
                                  content['hljs_language'])
        self.assertContains(resp, escape(content['data']))

        split_path = content_path.split('/')

        filename = split_path[-1]
        path = content_path.replace(filename, '')[:-1]

        path_info = gen_path_info(path)

        del url_args['path']

        if timestamp:
            url_args['timestamp'] = \
                format_utc_iso_date(parse_timestamp(timestamp).isoformat(),
                                    '%Y-%m-%dT%H:%M:%S')

        root_dir_url = reverse('browse-origin-directory',
                               url_args=url_args,
                               query_params=query_params)

        self.assertContains(resp, '<li class="swh-path">',
                            count=len(path_info)+1)

        self.assertContains(resp, '<a href="%s">%s</a>' %
                            (root_dir_url, root_dir_sha1[:7]))

        for p in path_info:
            url_args['path'] = p['path']
            dir_url = reverse('browse-origin-directory',
                              url_args=url_args,
                              query_params=query_params)
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (dir_url, p['name']))

        self.assertContains(resp, '<li>%s</li>' % filename)

        query_string = 'sha1_git:' + content['sha1_git']

        url_raw = reverse('browse-content-raw',
                          url_args={'query_string': query_string},
                          query_params={'filename': filename})
        self.assertContains(resp, url_raw)

        if 'args' in url_args:
            del url_args['path']

        origin_branches_url = reverse('browse-origin-branches',
                                      url_args=url_args,
                                      query_params=query_params)

        self.assertContains(resp, '<a href="%s">Branches (%s)</a>' %
                                  (origin_branches_url, len(origin_branches)))

        origin_releases_url = reverse('browse-origin-releases',
                                      url_args=url_args,
                                      query_params=query_params)

        self.assertContains(resp, '<a href="%s">Releases (%s)</a>' %
                                  (origin_releases_url, len(origin_releases)))

        self.assertContains(resp, '<li class="swh-branch">',
                            count=len(origin_branches))

        url_args['path'] = content_path

        for branch in origin_branches:
            query_params['branch'] = branch['name']
            root_dir_branch_url = reverse('browse-origin-content',
                                          url_args=url_args,
                                          query_params=query_params)

        self.assertContains(resp, '<a href="%s">' % root_dir_branch_url)

        self.assertContains(resp, '<li class="swh-release">',
                            count=len(origin_releases))

        query_params['branch'] = None
        for release in origin_releases:
            query_params['release'] = release['name']
            root_dir_release_url = reverse('browse-origin-content',
                                           url_args=url_args,
                                           query_params=query_params)

            self.assertContains(resp, '<a href="%s">' % root_dir_release_url)

        del url_args['origin_type']

        url = reverse('browse-origin-content',
                      url_args=url_args,
                      query_params=query_params)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('content.html')

        swh_cnt_id = get_swh_persistent_id('content', content['sha1_git'])
        swh_cnt_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_cnt_id})
        self.assertContains(resp, swh_cnt_id)
        self.assertContains(resp, swh_cnt_id_url)

        self.assertContains(resp, 'swh-take-new-snapshot')

    @given(origin_with_multiple_visits())
    def test_origin_content_view(self, origin):

        origin_visits = self.origin_visit_get(origin['id'])

        def _get_test_data(visit_idx):
            snapshot = self.snapshot_get(origin_visits[visit_idx]['snapshot'])
            head_rev_id = snapshot['branches']['HEAD']['target']
            head_rev = self.revision_get(head_rev_id)
            dir_content = self.directory_ls(head_rev['directory'])
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

        test_data = _get_test_data(-1)

        self.origin_content_view_helper(origin,
                                        origin_visits,
                                        test_data['branches'],
                                        test_data['releases'],
                                        test_data['root_dir_sha1'],
                                        test_data['content'])

        self.origin_content_view_helper(origin,
                                        origin_visits,
                                        test_data['branches'],
                                        test_data['releases'],
                                        test_data['root_dir_sha1'],
                                        test_data['content'],
                                        timestamp=test_data['visit']['date'])

        visit_unix_ts = parse_timestamp(test_data['visit']['date']).timestamp()
        visit_unix_ts = int(visit_unix_ts)

        self.origin_content_view_helper(origin,
                                        origin_visits,
                                        test_data['branches'],
                                        test_data['releases'],
                                        test_data['root_dir_sha1'],
                                        test_data['content'],
                                        timestamp=visit_unix_ts)

        test_data = _get_test_data(0)

        self.origin_content_view_helper(origin,
                                        origin_visits,
                                        test_data['branches'],
                                        test_data['releases'],
                                        test_data['root_dir_sha1'],
                                        test_data['content'],
                                        visit_id=test_data['visit']['visit'])

    def origin_directory_view_helper(self, origin_info, origin_visits,
                                     origin_branches, origin_releases,
                                     root_directory_sha1, directory_entries,
                                     visit_id=None, timestamp=None, path=None):

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

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('directory.html')

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('directory.html')

        self.assertContains(resp, '<td class="swh-directory">',
                            count=len(dirs))
        self.assertContains(resp, '<td class="swh-content">',
                            count=len(files))

        if timestamp:
            url_args['timestamp'] = \
                format_utc_iso_date(parse_timestamp(timestamp).isoformat(),
                                    '%Y-%m-%dT%H:%M:%S')

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
            self.assertContains(resp, dir_url)

        for f in files:
            file_path = f['name']
            if path:
                file_path = "%s/%s" % (path, f['name'])
            file_url_args = dict(url_args)
            file_url_args['path'] = file_path
            file_url = reverse('browse-origin-content',
                               url_args=file_url_args,
                               query_params=query_params)
            self.assertContains(resp, file_url)

        if 'path' in url_args:
            del url_args['path']

        root_dir_branch_url = \
            reverse('browse-origin-directory',
                    url_args=url_args,
                    query_params=query_params)

        nb_bc_paths = 1
        if path:
            nb_bc_paths = len(path.split('/')) + 1

        self.assertContains(resp, '<li class="swh-path">', count=nb_bc_paths)
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (root_dir_branch_url,
                                   root_directory_sha1[:7]))

        origin_branches_url = reverse('browse-origin-branches',
                                      url_args=url_args,
                                      query_params=query_params)

        self.assertContains(resp, '<a href="%s">Branches (%s)</a>' %
                                  (origin_branches_url, len(origin_branches)))

        origin_releases_url = reverse('browse-origin-releases',
                                      url_args=url_args,
                                      query_params=query_params)

        nb_releases = len(origin_releases)
        if nb_releases > 0:
            self.assertContains(resp, '<a href="%s">Releases (%s)</a>' %
                                      (origin_releases_url, nb_releases))

        if path:
            url_args['path'] = path

        self.assertContains(resp, '<li class="swh-branch">',
                            count=len(origin_branches))

        for branch in origin_branches:
            query_params['branch'] = branch['name']
            root_dir_branch_url = \
                reverse('browse-origin-directory',
                        url_args=url_args,
                        query_params=query_params)

            self.assertContains(resp, '<a href="%s">' % root_dir_branch_url)

        self.assertContains(resp, '<li class="swh-release">',
                            count=len(origin_releases))

        query_params['branch'] = None
        for release in origin_releases:
            query_params['release'] = release['name']
            root_dir_release_url = \
                reverse('browse-origin-directory',
                        url_args=url_args,
                        query_params=query_params)

            self.assertContains(resp, '<a href="%s">' % root_dir_release_url)

        self.assertContains(resp, 'vault-cook-directory')
        self.assertContains(resp, 'vault-cook-revision')

        swh_dir_id = get_swh_persistent_id('directory', directory_entries[0]['dir_id']) # noqa
        swh_dir_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_dir_id})
        self.assertContains(resp, swh_dir_id)
        self.assertContains(resp, swh_dir_id_url)

        self.assertContains(resp, 'swh-take-new-snapshot')

    @given(origin())
    def test_origin_root_directory_view(self, origin):

        origin_visits = self.origin_visit_get(origin['id'])

        visit = origin_visits[-1]
        snapshot = self.snapshot_get(visit['snapshot'])
        head_rev_id = snapshot['branches']['HEAD']['target']
        head_rev = self.revision_get(head_rev_id)
        root_dir_sha1 = head_rev['directory']
        dir_content = self.directory_ls(root_dir_sha1)
        branches, releases = process_snapshot_branches(snapshot)
        visit_unix_ts = parse_timestamp(visit['date']).timestamp()
        visit_unix_ts = int(visit_unix_ts)

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          dir_content)

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          dir_content,
                                          visit_id=visit['visit'])

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          dir_content,
                                          timestamp=visit_unix_ts)

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          dir_content,
                                          timestamp=visit['date'])

        origin = dict(origin)
        del origin['type']

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          dir_content)

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          dir_content,
                                          visit_id=visit['visit'])

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          dir_content,
                                          timestamp=visit_unix_ts)

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          dir_content,
                                          timestamp=visit['date'])

    @given(origin())
    def test_origin_sub_directory_view(self, origin):

        origin_visits = self.origin_visit_get(origin['id'])

        visit = origin_visits[-1]
        snapshot = self.snapshot_get(visit['snapshot'])
        head_rev_id = snapshot['branches']['HEAD']['target']
        head_rev = self.revision_get(head_rev_id)
        root_dir_sha1 = head_rev['directory']
        subdirs = [e for e in self.directory_ls(root_dir_sha1)
                   if e['type'] == 'dir']
        branches, releases = process_snapshot_branches(snapshot)
        visit_unix_ts = parse_timestamp(visit['date']).timestamp()
        visit_unix_ts = int(visit_unix_ts)

        if len(subdirs) == 0:
            return

        subdir = random.choice(subdirs)
        subdir_content = self.directory_ls(subdir['target'])
        subdir_path = subdir['name']

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          subdir_content,
                                          path=subdir_path)

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          subdir_content,
                                          path=subdir_path,
                                          visit_id=visit['visit'])

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          subdir_content,
                                          path=subdir_path,
                                          timestamp=visit_unix_ts)

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          subdir_content,
                                          path=subdir_path,
                                          timestamp=visit['date'])

        origin = dict(origin)
        del origin['type']

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          subdir_content,
                                          path=subdir_path)

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          subdir_content,
                                          path=subdir_path,
                                          visit_id=visit['visit'])

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          subdir_content,
                                          path=subdir_path,
                                          timestamp=visit_unix_ts)

        self.origin_directory_view_helper(origin, origin_visits,
                                          branches,
                                          releases,
                                          root_dir_sha1,
                                          subdir_content,
                                          path=subdir_path,
                                          timestamp=visit['date'])

    def origin_branches_helper(self, origin_info, origin_snapshot):
        url_args = {'origin_type': origin_info['type'],
                    'origin_url': origin_info['url']}

        url = reverse('browse-origin-branches',
                      url_args=url_args)

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('branches.html')

        origin_branches = origin_snapshot[0]
        origin_releases = origin_snapshot[1]

        origin_branches_url = reverse('browse-origin-branches',
                                      url_args=url_args)

        self.assertContains(resp, '<a href="%s">Branches (%s)</a>' %
                                  (origin_branches_url, len(origin_branches)))

        origin_releases_url = reverse('browse-origin-releases',
                                      url_args=url_args)

        nb_releases = len(origin_releases)
        if nb_releases > 0:
            self.assertContains(resp, '<a href="%s">Releases (%s)</a>' %
                                      (origin_releases_url, nb_releases))

        self.assertContains(resp, '<tr class="swh-branch-entry',
                            count=len(origin_branches))

        for branch in origin_branches:
            browse_branch_url = reverse(
                'browse-origin-directory',
                url_args={'origin_type': origin_info['type'],
                          'origin_url': origin_info['url']},
                query_params={'branch': branch['name']})
            self.assertContains(resp, '<a href="%s">' %
                                      escape(browse_branch_url))

            browse_revision_url = reverse(
                'browse-revision',
                url_args={'sha1_git': branch['revision']},
                query_params={'origin_type': origin_info['type'],
                              'origin': origin_info['url']})
            self.assertContains(resp, '<a href="%s">' %
                                      escape(browse_revision_url))

    @given(origin())
    def test_origin_branches(self, origin):

        origin_visits = self.origin_visit_get(origin['id'])

        visit = origin_visits[-1]
        snapshot = self.snapshot_get(visit['snapshot'])
        snapshot_content = process_snapshot_branches(snapshot)

        self.origin_branches_helper(origin, snapshot_content)

        origin = dict(origin)
        origin['type'] = None

        self.origin_branches_helper(origin, snapshot_content)

    def origin_releases_helper(self, origin_info, origin_snapshot):
        url_args = {'origin_type': origin_info['type'],
                    'origin_url': origin_info['url']}

        url = reverse('browse-origin-releases',
                      url_args=url_args)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('releases.html')

        origin_branches = origin_snapshot[0]
        origin_releases = origin_snapshot[1]

        origin_branches_url = reverse('browse-origin-branches',
                                      url_args=url_args)

        self.assertContains(resp, '<a href="%s">Branches (%s)</a>' %
                                  (origin_branches_url, len(origin_branches)))

        origin_releases_url = reverse('browse-origin-releases',
                                      url_args=url_args)

        nb_releases = len(origin_releases)
        if nb_releases > 0:
            self.assertContains(resp, '<a href="%s">Releases (%s)</a>' %
                                      (origin_releases_url, nb_releases))

        self.assertContains(resp, '<tr class="swh-release-entry',
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

            self.assertContains(resp, '<a href="%s">' %
                                      escape(browse_release_url))
            self.assertContains(resp, '<a href="%s">' %
                                      escape(browse_revision_url))

    @given(origin())
    def test_origin_releases(self, origin):

        origin_visits = self.origin_visit_get(origin['id'])

        visit = origin_visits[-1]
        snapshot = self.snapshot_get(visit['snapshot'])
        snapshot_content = process_snapshot_branches(snapshot)

        self.origin_releases_helper(origin, snapshot_content)

        origin = dict(origin)
        origin['type'] = None

        self.origin_releases_helper(origin, snapshot_content)

    @patch('swh.web.browse.views.utils.snapshot_context.request_content')
    @patch('swh.web.common.origin_visits.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.origin.service')
    @patch('swh.web.browse.views.utils.snapshot_context.service')
    @patch('swh.web.browse.views.origin.get_origin_info')
    def test_origin_request_errors(self, mock_get_origin_info,
                                   mock_snapshot_service,
                                   mock_origin_service,
                                   mock_utils_service,
                                   mock_get_origin_visit_snapshot,
                                   mock_get_origin_visits,
                                   mock_request_content):

        mock_get_origin_info.side_effect = \
            NotFoundExc('origin not found')
        url = reverse('browse-origin-visits',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'origin not found', status_code=404)

        mock_utils_service.lookup_origin.side_effect = None
        mock_utils_service.lookup_origin.return_value = {'type': 'foo',
                                                         'url': 'bar',
                                                         'id': 457}
        mock_get_origin_visits.return_value = []
        url = reverse('browse-origin-directory',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, "No visit", status_code=404)

        mock_get_origin_visits.return_value = [{'visit': 1}]
        mock_get_origin_visit_snapshot.side_effect = \
            NotFoundExc('visit not found')
        url = reverse('browse-origin-directory',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar'},
                      query_params={'visit_id': 2})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertRegex(resp.content.decode('utf-8'), 'Visit.*not found')

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
        mock_utils_service.lookup_snapshot_size.return_value = {
            'revision': 1,
            'release': 0
        }
        mock_utils_service.lookup_directory.side_effect = \
            NotFoundExc('Directory not found')
        url = reverse('browse-origin-directory',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'Directory not found', status_code=404)

        with patch('swh.web.browse.views.utils.snapshot_context.'
                   'get_snapshot_context') as mock_get_snapshot_context:
            mock_get_snapshot_context.side_effect = \
                NotFoundExc('Snapshot not found')
            url = reverse('browse-origin-directory',
                          url_args={'origin_type': 'foo',
                                    'origin_url': 'bar'})
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 404)
            self.assertTemplateUsed('error.html')
            self.assertContains(resp, 'Snapshot not found', status_code=404)

        mock_origin_service.lookup_origin.side_effect = None
        mock_origin_service.lookup_origin.return_value = {'type': 'foo',
                                                          'url': 'bar',
                                                          'id': 457}
        mock_get_origin_visits.return_value = []
        url = reverse('browse-origin-content',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar',
                                'path': 'foo'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, "No visit", status_code=404)

        mock_get_origin_visits.return_value = [{'visit': 1}]
        mock_get_origin_visit_snapshot.side_effect = \
            NotFoundExc('visit not found')
        url = reverse('browse-origin-content',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar',
                                'path': 'foo'},
                      query_params={'visit_id': 2})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertRegex(resp.content.decode('utf-8'), 'Visit.*not found')

        mock_get_origin_visits.return_value = [{
            'date': '2015-09-26T09:30:52.373449+00:00',
            'metadata': {},
            'origin': 457,
            'snapshot': 'bdaf9ac436488a8c6cda927a0f44e172934d3f65',
            'status': 'full',
            'visit': 1
        }]
        mock_get_origin_visit_snapshot.side_effect = None
        mock_get_origin_visit_snapshot.return_value = ([], [])
        url = reverse('browse-origin-content',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar',
                                'path': 'baz'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertRegex(resp.content.decode('utf-8'),
                         'Origin.*has an empty list of branches')

        mock_get_origin_visit_snapshot.return_value = (
            [{'directory': 'ae59ceecf46367e8e4ad800e231fc76adc3afffb',
              'name': 'HEAD',
              'revision': '7bc08e1aa0b08cb23e18715a32aa38517ad34672',
              'date': '04 May 2017, 13:27 UTC',
              'message': ''}],
            []
        )
        mock_snapshot_service.lookup_directory_with_path.return_value = \
            {'target': '5ecd9f37b7a2d2e9980d201acd6286116f2ba1f1'}
        mock_request_content.side_effect = \
            NotFoundExc('Content not found')
        url = reverse('browse-origin-content',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar',
                                'path': 'baz'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'Content not found', status_code=404)

    @patch('swh.web.common.origin_visits.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.service')
    def test_origin_empty_snapshot(self, mock_utils_service,
                                   mock_get_origin_visit_snapshot,
                                   mock_get_origin_visits):

        mock_get_origin_visits.return_value = [{
            'date': '2015-09-26T09:30:52.373449+00:00',
            'metadata': {},
            'origin': 457,
            'snapshot': 'bdaf9ac436488a8c6cda927a0f44e172934d3f65',
            'status': 'full',
            'visit': 1
        }]
        mock_get_origin_visit_snapshot.return_value = ([], [])
        mock_utils_service.lookup_snapshot_size.return_value = {
            'revision': 0,
            'release': 0
        }
        url = reverse('browse-origin-directory',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('content.html')
        self.assertRegex(resp.content.decode('utf-8'), 'snapshot.*is empty')
