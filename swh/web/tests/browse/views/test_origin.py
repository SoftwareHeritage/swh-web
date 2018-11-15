# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# flake8: noqa

from unittest.mock import patch

from django.utils.html import escape

from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import (
    reverse, gen_path_info, format_utc_iso_date,
    parse_timestamp, get_swh_persistent_id
)
from swh.web.tests.testcase import SWHWebTestCase

from .data.origin_test_data import (
    origin_info_test_data,
    origin_visits_test_data,
    stub_content_origin_info, stub_content_origin_visit_id,
    stub_content_origin_visit_unix_ts, stub_content_origin_visit_iso_date,
    stub_content_origin_branch,
    stub_content_origin_visits, stub_content_origin_snapshot,
    stub_origin_info, stub_visit_id,
    stub_origin_visits, stub_origin_snapshot,
    stub_origin_root_directory_entries, stub_origin_master_branch,
    stub_origin_root_directory_sha1, stub_origin_sub_directory_path,
    stub_origin_sub_directory_entries, stub_visit_unix_ts, stub_visit_iso_date
)

from .data.content_test_data import (
    stub_content_root_dir,
    stub_content_text_data,
    stub_content_text_path
)

stub_origin_info_no_type = dict(stub_origin_info)
stub_origin_info_no_type['type'] = None

def _to_snapshot_dict(branches=None, releases=None):
    snp = {'branches': {}}
    if branches:
        for b in branches:
            snp['branches'][b['name']] = {
                'target': b['revision'],
                'target_type': 'revision'
            }
    if releases:
        for r in releases:
            snp['branches'][r['branch_name']] =  {
                'target': r['id'],
                'target_type': 'release'
            }
    return snp

class SwhBrowseOriginTest(SWHWebTestCase):

    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_info')
    @patch('swh.web.browse.views.origin.get_origin_info')
    @patch('swh.web.browse.views.origin.get_origin_visits')
    @patch('swh.web.browse.views.origin.service')
    def test_origin_visits_browse(self, mock_service, mock_get_origin_visits,
                                  mock_get_origin_info, mock_get_origin_info_utils,
                                  mock_get_origin_visits_utils,
                                  mock_get_origin_visit_snapshot,
                                  mock_utils_service):
        mock_service.lookup_origin.return_value = origin_info_test_data
        mock_get_origin_info.return_value = origin_info_test_data
        mock_get_origin_info_utils.return_value = origin_info_test_data
        mock_get_origin_visits.return_value = origin_visits_test_data
        mock_get_origin_visits_utils.return_value = origin_visits_test_data
        mock_get_origin_visit_snapshot.return_value = stub_content_origin_snapshot
        mock_utils_service.lookup_snapshot_size.return_value = {
            'revision': len(stub_content_origin_snapshot[0]),
            'release': len(stub_content_origin_snapshot[1])
        }

        url = reverse('browse-origin-visits',
                      url_args={'origin_type': origin_info_test_data['type'],
                              'origin_url': origin_info_test_data['url']})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('origin-visits.html')

        url = reverse('browse-origin-visits',
                      url_args={'origin_url': origin_info_test_data['url']})
        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('origin-visits.html')

    def origin_content_view_helper(self, origin_info, origin_visits,
                                   origin_branches, origin_releases,
                                   origin_branch,
                                   root_dir_sha1, content_sha1, content_sha1_git,
                                   content_path, content_data,
                                   content_language,
                                   visit_id=None, timestamp=None):

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

        self.assertContains(resp, '<code class="%s">' % content_language)
        self.assertContains(resp, escape(content_data))

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

        query_string = 'sha1_git:' + content_sha1

        url_raw = reverse('browse-content-raw',
                          url_args={'query_string': query_string},
                          query_params={'filename': filename})
        self.assertContains(resp, url_raw)

        del url_args['path']

        origin_branches_url = \
                reverse('browse-origin-branches',
                        url_args=url_args,
                        query_params=query_params)

        self.assertContains(resp, '<a href="%s">Branches (%s)</a>' %
            (origin_branches_url, len(origin_branches)))

        origin_releases_url = \
                reverse('browse-origin-releases',
                        url_args=url_args,
                        query_params=query_params)

        self.assertContains(resp, '<a href="%s">Releases (%s)</a>' %
            (origin_releases_url, len(origin_releases)))

        self.assertContains(resp, '<li class="swh-branch">',
                            count=len(origin_branches))

        url_args['path'] = content_path

        for branch in origin_branches:
            query_params['branch'] = branch['name']
            root_dir_branch_url = \
                reverse('browse-origin-content',
                        url_args=url_args,
                        query_params=query_params)

        self.assertContains(resp, '<a href="%s">' % root_dir_branch_url)

        self.assertContains(resp, '<li class="swh-release">',
                            count=len(origin_releases))

        query_params['branch'] = None
        for release in origin_releases:
            query_params['release'] = release['name']
            root_dir_release_url = \
                reverse('browse-origin-content',
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

        swh_cnt_id = get_swh_persistent_id('content', content_sha1_git)
        swh_cnt_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_cnt_id})
        self.assertContains(resp, swh_cnt_id)
        self.assertContains(resp, swh_cnt_id_url)

    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.views.utils.snapshot_context.service')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.utils.snapshot_context.request_content')
    def test_origin_content_view(self, mock_request_content, mock_utils_service,
                                 mock_service, mock_get_origin_visit_snapshot,
                                 mock_get_origin_visits):

        stub_content_text_sha1 = stub_content_text_data['checksums']['sha1']
        stub_content_text_sha1_git = stub_content_text_data['checksums']['sha1_git']
        mock_get_origin_visits.return_value = stub_content_origin_visits
        mock_get_origin_visit_snapshot.return_value = stub_content_origin_snapshot
        mock_service.lookup_directory_with_path.return_value = \
            {'target': stub_content_text_sha1}
        mock_request_content.return_value = stub_content_text_data
        mock_utils_service.lookup_origin.return_value = stub_content_origin_info
        mock_utils_service.lookup_snapshot_size.return_value = {
            'revision': len(stub_content_origin_snapshot[0]),
            'release': len(stub_content_origin_snapshot[1])
        }

        self.origin_content_view_helper(stub_content_origin_info,
                                        stub_content_origin_visits,
                                        stub_content_origin_snapshot[0],
                                        stub_content_origin_snapshot[1],
                                        stub_content_origin_branch,
                                        stub_content_root_dir,
                                        stub_content_text_sha1,
                                        stub_content_text_sha1_git,
                                        stub_content_text_path,
                                        stub_content_text_data['raw_data'],
                                        'cpp')

        self.origin_content_view_helper(stub_content_origin_info,
                                        stub_content_origin_visits,
                                        stub_content_origin_snapshot[0],
                                        stub_content_origin_snapshot[1],
                                        stub_content_origin_branch,
                                        stub_content_root_dir,
                                        stub_content_text_sha1,
                                        stub_content_text_sha1_git,
                                        stub_content_text_path,
                                        stub_content_text_data['raw_data'],
                                        'cpp',
                                        visit_id=stub_content_origin_visit_id)

        self.origin_content_view_helper(stub_content_origin_info,
                                        stub_content_origin_visits,
                                        stub_content_origin_snapshot[0],
                                        stub_content_origin_snapshot[1],
                                        stub_content_origin_branch,
                                        stub_content_root_dir,
                                        stub_content_text_sha1,
                                        stub_content_text_sha1_git,
                                        stub_content_text_path,
                                        stub_content_text_data['raw_data'],
                                        'cpp',
                                        timestamp=stub_content_origin_visit_unix_ts)

        self.origin_content_view_helper(stub_content_origin_info,
                                        stub_content_origin_visits,
                                        stub_content_origin_snapshot[0],
                                        stub_content_origin_snapshot[1],
                                        stub_content_origin_branch,
                                        stub_content_root_dir,
                                        stub_content_text_sha1,
                                        stub_content_text_sha1_git,
                                        stub_content_text_path,
                                        stub_content_text_data['raw_data'],
                                        'cpp',
                                        timestamp=stub_content_origin_visit_iso_date)

    def origin_directory_view_helper(self, origin_info, origin_visits,
                                     origin_branches, origin_releases, origin_branch,
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

        origin_branches_url = \
                reverse('browse-origin-branches',
                        url_args=url_args,
                        query_params=query_params)

        self.assertContains(resp, '<a href="%s">Branches (%s)</a>' %
            (origin_branches_url, len(origin_branches)))

        origin_releases_url = \
                reverse('browse-origin-releases',
                        url_args=url_args,
                        query_params=query_params)

        self.assertContains(resp, '<a href="%s">Releases (%s)</a>' %
            (origin_releases_url, len(origin_releases)))

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


    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.origin.service')
    def test_origin_root_directory_view(self, mock_origin_service,
                                        mock_utils_service,
                                        mock_get_origin_visit_snapshot,
                                        mock_get_origin_visits):

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_utils_service.lookup_directory.return_value = \
            stub_origin_root_directory_entries
        mock_utils_service.lookup_origin.return_value = stub_origin_info
        mock_utils_service.lookup_snapshot_size.return_value = {
            'revision': len(stub_origin_snapshot[0]),
            'release': len(stub_origin_snapshot[1])
        }

        self.origin_directory_view_helper(stub_origin_info, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_root_directory_entries)

        self.origin_directory_view_helper(stub_origin_info, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_root_directory_entries,
                                          visit_id=stub_visit_id)

        self.origin_directory_view_helper(stub_origin_info, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_root_directory_entries,
                                          timestamp=stub_visit_unix_ts)

        self.origin_directory_view_helper(stub_origin_info, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_root_directory_entries,
                                          timestamp=stub_visit_iso_date)

        self.origin_directory_view_helper(stub_origin_info_no_type, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_root_directory_entries)

        self.origin_directory_view_helper(stub_origin_info_no_type, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_root_directory_entries,
                                          visit_id=stub_visit_id)

        self.origin_directory_view_helper(stub_origin_info_no_type, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_root_directory_entries,
                                          timestamp=stub_visit_unix_ts)

        self.origin_directory_view_helper(stub_origin_info_no_type, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_root_directory_entries,
                                          timestamp=stub_visit_iso_date)

    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.utils.snapshot_context.service')
    def test_origin_sub_directory_view(self, mock_origin_service,
                                       mock_utils_service,
                                       mock_get_origin_visit_snapshot,
                                       mock_get_origin_visits):

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_utils_service.lookup_directory.return_value = \
            stub_origin_sub_directory_entries
        mock_origin_service.lookup_directory_with_path.return_value = \
            {'target': stub_origin_sub_directory_entries[0]['dir_id'],
             'type' : 'dir'}
        mock_utils_service.lookup_origin.return_value = stub_origin_info
        mock_utils_service.lookup_snapshot_size.return_value = {
            'revision': len(stub_origin_snapshot[0]),
            'release': len(stub_origin_snapshot[1])
        }

        self.origin_directory_view_helper(stub_origin_info, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_sub_directory_entries,
                                          path=stub_origin_sub_directory_path)

        self.origin_directory_view_helper(stub_origin_info, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_sub_directory_entries,
                                          visit_id=stub_visit_id,
                                          path=stub_origin_sub_directory_path)

        self.origin_directory_view_helper(stub_origin_info, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_sub_directory_entries,
                                          timestamp=stub_visit_unix_ts,
                                          path=stub_origin_sub_directory_path)

        self.origin_directory_view_helper(stub_origin_info, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_sub_directory_entries,
                                          timestamp=stub_visit_iso_date,
                                          path=stub_origin_sub_directory_path)

        self.origin_directory_view_helper(stub_origin_info_no_type, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_sub_directory_entries,
                                          path=stub_origin_sub_directory_path)

        self.origin_directory_view_helper(stub_origin_info_no_type, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_sub_directory_entries,
                                          visit_id=stub_visit_id,
                                          path=stub_origin_sub_directory_path)

        self.origin_directory_view_helper(stub_origin_info_no_type, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_sub_directory_entries,
                                          timestamp=stub_visit_unix_ts,
                                          path=stub_origin_sub_directory_path)

        self.origin_directory_view_helper(stub_origin_info_no_type, stub_origin_visits,
                                          stub_origin_snapshot[0],
                                          stub_origin_snapshot[1],
                                          stub_origin_master_branch,
                                          stub_origin_root_directory_sha1,
                                          stub_origin_sub_directory_entries,
                                          timestamp=stub_visit_iso_date,
                                          path=stub_origin_sub_directory_path)

    @patch('swh.web.browse.views.utils.snapshot_context.request_content')
    @patch('swh.web.browse.utils.get_origin_visits')
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
        mock_utils_service.lookup_origin.return_value = origin_info_test_data
        mock_get_origin_visits.return_value = []
        url = reverse('browse-origin-directory',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, "No visit", status_code=404)

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.side_effect = \
            NotFoundExc('visit not found')
        url = reverse('browse-origin-directory',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar'},
                      query_params={'visit_id': len(stub_origin_visits)+1})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertRegex(resp.content.decode('utf-8'), 'Visit.*not found')

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.side_effect = None
        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_utils_service.lookup_snapshot_size.return_value = {
            'revision': len(stub_origin_snapshot[0]),
            'release': len(stub_origin_snapshot[1])
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

        with patch('swh.web.browse.views.utils.snapshot_context.get_snapshot_context') \
                as mock_get_snapshot_context:
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
        mock_origin_service.lookup_origin.return_value = origin_info_test_data
        mock_get_origin_visits.return_value = []
        url = reverse('browse-origin-content',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar',
                                'path': 'foo'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, "No visit", status_code=404)

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.side_effect = \
            NotFoundExc('visit not found')
        url = reverse('browse-origin-content',
                      url_args={'origin_type': 'foo',
                                'origin_url': 'bar',
                                'path': 'foo'},
                      query_params={'visit_id': len(stub_origin_visits)+1})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertRegex(resp.content.decode('utf-8'), 'Visit.*not found')

        mock_get_origin_visits.return_value = stub_origin_visits
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

        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_snapshot_service.lookup_directory_with_path.return_value = \
            {'target': stub_content_text_data['checksums']['sha1']}
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


    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.service')
    def test_origin_empty_snapshot(self, mock_utils_service,
                                   mock_get_origin_visit_snapshot,
                                   mock_get_origin_visits):

        mock_get_origin_visits.return_value = stub_origin_visits
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

        origin_branches_url = \
                reverse('browse-origin-branches',
                        url_args=url_args)

        self.assertContains(resp, '<a href="%s">Branches (%s)</a>' %
            (origin_branches_url, len(origin_branches)))

        origin_releases_url = \
                reverse('browse-origin-releases',
                        url_args=url_args)

        self.assertContains(resp, '<a href="%s">Releases (%s)</a>' %
            (origin_releases_url, len(origin_releases)))

        self.assertContains(resp, '<tr class="swh-branch-entry',
                            count=len(origin_branches))

        for branch in origin_branches:
            browse_branch_url = reverse('browse-origin-directory',
                                        url_args={'origin_type': origin_info['type'],
                                                'origin_url': origin_info['url']},
                                        query_params={'branch': branch['name']})
            self.assertContains(resp, '<a href="%s">' % escape(browse_branch_url))

            browse_revision_url = reverse('browse-revision',
                                          url_args={'sha1_git': branch['revision']},
                                          query_params={'origin_type': origin_info['type'],
                                                        'origin': origin_info['url']})
            self.assertContains(resp, '<a href="%s">' % escape(browse_revision_url))


    @patch('swh.web.browse.views.utils.snapshot_context.process_snapshot_branches')
    @patch('swh.web.browse.views.utils.snapshot_context.service')
    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.origin.service')
    def test_origin_branches(self, mock_origin_service,
                             mock_utils_service,
                             mock_get_origin_visit_snapshot,
                             mock_get_origin_visits,
                             mock_snp_ctx_service,
                             mock_snp_ctx_process_branches):
        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_utils_service.lookup_origin.return_value = stub_origin_info
        mock_utils_service.lookup_snapshot_size.return_value = \
            {'revision': len(stub_origin_snapshot[0]), 'release': len(stub_origin_snapshot[1])}
        mock_snp_ctx_service.lookup_snapshot.return_value = \
            _to_snapshot_dict(branches=stub_origin_snapshot[0])
        mock_snp_ctx_process_branches.return_value = stub_origin_snapshot

        self.origin_branches_helper(stub_origin_info, stub_origin_snapshot)

        self.origin_branches_helper(stub_origin_info_no_type, stub_origin_snapshot)


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

        origin_branches_url = \
                reverse('browse-origin-branches',
                        url_args=url_args)

        self.assertContains(resp, '<a href="%s">Branches (%s)</a>' %
            (origin_branches_url, len(origin_branches)))

        origin_releases_url = \
                reverse('browse-origin-releases',
                        url_args=url_args)

        self.assertContains(resp, '<a href="%s">Releases (%s)</a>' %
            (origin_releases_url, len(origin_releases)))

        self.assertContains(resp, '<tr class="swh-release-entry',
                            count=len(origin_releases))

        for release in origin_releases:
            browse_release_url = reverse('browse-release',
                                         url_args={'sha1_git': release['id']},
                                         query_params={'origin': origin_info['url']})
            browse_revision_url = reverse('browse-revision',
                                          url_args={'sha1_git': release['target']},
                                          query_params={'origin': origin_info['url']})

            self.assertContains(resp, '<a href="%s">' % escape(browse_release_url))
            self.assertContains(resp, '<a href="%s">' % escape(browse_revision_url))


    @patch('swh.web.browse.views.utils.snapshot_context.process_snapshot_branches')
    @patch('swh.web.browse.views.utils.snapshot_context.service')
    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.origin.service')
    def test_origin_releases(self, mock_origin_service,
                             mock_utils_service,
                             mock_get_origin_visit_snapshot,
                             mock_get_origin_visits,
                             mock_snp_ctx_service,
                             mock_snp_ctx_process_branches):
        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_utils_service.lookup_origin.return_value = stub_origin_info
        mock_utils_service.lookup_snapshot_size.return_value = \
            {'revision': len(stub_origin_snapshot[0]), 'release': len(stub_origin_snapshot[1])}
        mock_snp_ctx_service.lookup_snapshot.return_value = \
            _to_snapshot_dict(releases=stub_origin_snapshot[1])
        mock_snp_ctx_process_branches.return_value = stub_origin_snapshot

        self.origin_releases_helper(stub_origin_info, stub_origin_snapshot)
        self.origin_releases_helper(stub_origin_info_no_type, stub_origin_snapshot)

