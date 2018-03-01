# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

# flake8: noqa

from unittest.mock import patch
from nose.tools import istest, nottest

from django.test import TestCase
from django.utils.html import escape

from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import (
    reverse, gen_path_info, format_utc_iso_date,
    parse_timestamp
)
from swh.web.tests.testbase import SWHWebTestBase

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


class SwhBrowseOriginTest(SWHWebTestBase, TestCase):

    @patch('swh.web.browse.views.origin.get_origin_visits')
    @patch('swh.web.browse.views.origin.service')
    @istest
    def origin_browse(self, mock_service, mock_get_origin_visits):
        mock_service.lookup_origin.return_value = origin_info_test_data
        mock_get_origin_visits.return_value = origin_visits_test_data

        url = reverse('browse-origin',
                      kwargs={'origin_type': origin_info_test_data['type'],
                              'origin_url': origin_info_test_data['url']})
        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('origin.html')
        self.assertContains(resp, '<pre>%s</pre>' % origin_info_test_data['type'])
        self.assertContains(resp, '<pre><a href="%s">%s</a></pre>' %
                                  (origin_info_test_data['url'],
                                   origin_info_test_data['url']))

        self.assertContains(resp, '<td class="swh-origin-visit">',
                            count=len(origin_visits_test_data))

        for visit in origin_visits_test_data:
            visit_date_iso = format_utc_iso_date(visit['date'], '%Y-%m-%dT%H:%M:%SZ')
            visit_date = format_utc_iso_date(visit['date'])
            browse_url = reverse('browse-origin-directory',
                                 kwargs={'origin_type': origin_info_test_data['type'],
                                         'origin_url': origin_info_test_data['url'],
                                         'timestamp': visit_date_iso})
            self.assertContains(resp, 'href="%s">%s</a>' %
                                (browse_url, visit_date))

    @nottest
    def origin_content_view_test(self, origin_info, origin_visits,
                                 origin_branches, origin_releases,
                                 origin_branch,
                                 root_dir_sha1, content_sha1,
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
                      kwargs=url_args,
                      query_params=query_params)

        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
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
                               kwargs=url_args,
                               query_params=query_params)

        self.assertContains(resp, '<li class="swh-path">',
                            count=len(path_info)+1)


        self.assertContains(resp, '<a href="%s">%s</a>' %
                            (root_dir_url, root_dir_sha1[:7]))

        for p in path_info:
            url_args['path'] = p['path']
            dir_url = reverse('browse-origin-directory',
                              kwargs=url_args,
                              query_params=query_params)
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (dir_url, p['name']))

        self.assertContains(resp, '<li>%s</li>' % filename)

        query_string = 'sha1_git:' + content_sha1

        url_raw = reverse('browse-content-raw',
                          kwargs={'query_string': query_string},
                          query_params={'filename': filename})
        self.assertContains(resp, url_raw)

        del url_args['path']

        origin_branches_url = \
                reverse('browse-origin-branches',
                        kwargs=url_args,
                        query_params=query_params)

        self.assertContains(resp, '<a href="%s">Branches (%s)</a>' %
            (origin_branches_url, len(origin_branches)))

        origin_releases_url = \
                reverse('browse-origin-releases',
                        kwargs=url_args,
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
                        kwargs=url_args,
                        query_params=query_params)

        self.assertContains(resp, '<a href="%s">' % root_dir_branch_url)

        self.assertContains(resp, '<li class="swh-release">',
                            count=len(origin_releases))

        query_params['branch'] = None
        for release in origin_releases:
            query_params['release'] = release['name']
            root_dir_release_url = \
                reverse('browse-origin-content',
                        kwargs=url_args,
                        query_params=query_params)

            self.assertContains(resp, '<a href="%s">' % root_dir_release_url)

    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.views.origin.service')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.origin.request_content')
    @istest
    def origin_content_view(self, mock_request_content, mock_utils_service,
                            mock_service, mock_get_origin_visit_snapshot,
                            mock_get_origin_visits):

        stub_content_text_sha1 = stub_content_text_data['checksums']['sha1']
        mock_get_origin_visits.return_value = stub_content_origin_visits
        mock_get_origin_visit_snapshot.return_value = stub_content_origin_snapshot
        mock_service.lookup_directory_with_path.return_value = \
            {'target': stub_content_text_sha1}
        mock_request_content.return_value = stub_content_text_data
        mock_utils_service.lookup_origin.return_value = stub_content_origin_info

        self.origin_content_view_test(stub_content_origin_info,
                                      stub_content_origin_visits,
                                      stub_content_origin_snapshot[0],
                                      stub_content_origin_snapshot[1],
                                      stub_content_origin_branch,
                                      stub_content_root_dir,
                                      stub_content_text_sha1,
                                      stub_content_text_path,
                                      stub_content_text_data['raw_data'],
                                      'cpp')

        self.origin_content_view_test(stub_content_origin_info,
                                      stub_content_origin_visits,
                                      stub_content_origin_snapshot[0],
                                      stub_content_origin_snapshot[1],
                                      stub_content_origin_branch,
                                      stub_content_root_dir,
                                      stub_content_text_sha1,
                                      stub_content_text_path,
                                      stub_content_text_data['raw_data'],
                                      'cpp',
                                      visit_id=stub_content_origin_visit_id)

        self.origin_content_view_test(stub_content_origin_info,
                                      stub_content_origin_visits,
                                      stub_content_origin_snapshot[0],
                                      stub_content_origin_snapshot[1],
                                      stub_content_origin_branch,
                                      stub_content_root_dir,
                                      stub_content_text_sha1,
                                      stub_content_text_path,
                                      stub_content_text_data['raw_data'],
                                      'cpp',
                                      timestamp=stub_content_origin_visit_unix_ts)

        self.origin_content_view_test(stub_content_origin_info,
                                      stub_content_origin_visits,
                                      stub_content_origin_snapshot[0],
                                      stub_content_origin_snapshot[1],
                                      stub_content_origin_branch,
                                      stub_content_root_dir,
                                      stub_content_text_sha1,
                                      stub_content_text_path,
                                      stub_content_text_data['raw_data'],
                                      'cpp',
                                      timestamp=stub_content_origin_visit_iso_date)

    @nottest
    def origin_directory_view(self, origin_info, origin_visits,
                              origin_branches, origin_releases, origin_branch,
                              root_directory_sha1, directory_entries,
                              visit_id=None, timestamp=None, path=None):

        dirs = [e for e in directory_entries
                if e['type'] == 'dir']
        files = [e for e in directory_entries
                 if e['type'] == 'file']

        if not visit_id:
            visit_id = origin_visits[-1]['visit']

        url_args = {'origin_type': origin_info['type'],
                    'origin_url': origin_info['url']}

        query_params = {}

        if timestamp:
            url_args['timestamp'] = timestamp
        else:
            query_params['visit_id'] = visit_id

        if path:
            url_args['path'] = path

        url = reverse('browse-origin-directory',
                      kwargs=url_args,
                      query_params=query_params)

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
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
            dir_path = d['name']
            if path:
                dir_path = "%s/%s" % (path, d['name'])
            dir_url_args = dict(url_args)
            dir_url_args['path'] = dir_path
            dir_url = reverse('browse-origin-directory',
                              kwargs=dir_url_args,
                              query_params=query_params)
            self.assertContains(resp, dir_url)

        for f in files:
            file_path = f['name']
            if path:
                file_path = "%s/%s" % (path, f['name'])
            file_url_args = dict(url_args)
            file_url_args['path'] = file_path
            file_url = reverse('browse-origin-content',
                               kwargs=file_url_args,
                               query_params=query_params)
            self.assertContains(resp, file_url)

        if 'path' in url_args:
            del url_args['path']

        root_dir_branch_url = \
            reverse('browse-origin-directory',
                    kwargs=url_args,
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
                        kwargs=url_args,
                        query_params=query_params)

        self.assertContains(resp, '<a href="%s">Branches (%s)</a>' %
            (origin_branches_url, len(origin_branches)))

        origin_releases_url = \
                reverse('browse-origin-releases',
                        kwargs=url_args,
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
                        kwargs=url_args,
                        query_params=query_params)

            self.assertContains(resp, '<a href="%s">' % root_dir_branch_url)

        self.assertContains(resp, '<li class="swh-release">',
                            count=len(origin_releases))

        query_params['branch'] = None
        for release in origin_releases:
            query_params['release'] = release['name']
            root_dir_release_url = \
                reverse('browse-origin-directory',
                        kwargs=url_args,
                        query_params=query_params)

            self.assertContains(resp, '<a href="%s">' % root_dir_release_url)
        self.assertContains(resp, 'vault-cook-directory')
        self.assertContains(resp, 'vault-cook-revision')

    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.origin.service')
    @istest
    def origin_root_directory_view(self, mock_origin_service,
                                   mock_utils_service,
                                   mock_get_origin_visit_snapshot,
                                   mock_get_origin_visits):

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_utils_service.lookup_directory.return_value = \
            stub_origin_root_directory_entries
        mock_utils_service.lookup_origin.return_value = stub_origin_info

        self.origin_directory_view(stub_origin_info, stub_origin_visits,
                                   stub_origin_snapshot[0],
                                   stub_origin_snapshot[1],
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_root_directory_entries)

        self.origin_directory_view(stub_origin_info, stub_origin_visits,
                                   stub_origin_snapshot[0],
                                   stub_origin_snapshot[1],
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_root_directory_entries,
                                   visit_id=stub_visit_id)

        self.origin_directory_view(stub_origin_info, stub_origin_visits,
                                   stub_origin_snapshot[0],
                                   stub_origin_snapshot[1],
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_root_directory_entries,
                                   timestamp=stub_visit_unix_ts)

        self.origin_directory_view(stub_origin_info, stub_origin_visits,
                                   stub_origin_snapshot[0],
                                   stub_origin_snapshot[1],
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_root_directory_entries,
                                   timestamp=stub_visit_iso_date)

    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.origin.service')
    @istest
    def origin_sub_directory_view(self, mock_origin_service,
                                  mock_utils_service,
                                  mock_get_origin_visit_snapshot,
                                  mock_get_origin_visits):

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_utils_service.lookup_directory.return_value = \
            stub_origin_sub_directory_entries
        mock_origin_service.lookup_directory_with_path.return_value = \
            {'target': '120c39eeb566c66a77ce0e904d29dfde42228adb'}
        mock_utils_service.lookup_origin.return_value = stub_origin_info

        self.origin_directory_view(stub_origin_info, stub_origin_visits,
                                   stub_origin_snapshot[0],
                                   stub_origin_snapshot[1],
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_sub_directory_entries,
                                   path=stub_origin_sub_directory_path)

        self.origin_directory_view(stub_origin_info, stub_origin_visits,
                                   stub_origin_snapshot[0],
                                   stub_origin_snapshot[1],
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_sub_directory_entries,
                                   visit_id=stub_visit_id,
                                   path=stub_origin_sub_directory_path)

        self.origin_directory_view(stub_origin_info, stub_origin_visits,
                                   stub_origin_snapshot[0],
                                   stub_origin_snapshot[1],
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_sub_directory_entries,
                                   timestamp=stub_visit_unix_ts,
                                   path=stub_origin_sub_directory_path)

        self.origin_directory_view(stub_origin_info, stub_origin_visits,
                                   stub_origin_snapshot[0],
                                   stub_origin_snapshot[1],
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_sub_directory_entries,
                                   timestamp=stub_visit_iso_date,
                                   path=stub_origin_sub_directory_path)

    @patch('swh.web.browse.views.origin.request_content')
    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.origin.service')
    @istest
    def origin_request_errors(self, mock_origin_service,
                              mock_utils_service,
                              mock_get_origin_visit_snapshot,
                              mock_get_origin_visits,
                              mock_request_content):

        mock_origin_service.lookup_origin.side_effect = \
            NotFoundExc('origin not found')
        url = reverse('browse-origin',
                      kwargs={'origin_type': 'foo',
                              'origin_url': 'bar'})
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, "origin not found", status_code=404)

        mock_utils_service.lookup_origin.side_effect = None
        mock_utils_service.lookup_origin.return_value = origin_info_test_data
        mock_get_origin_visits.return_value = []
        url = reverse('browse-origin-directory',
                      kwargs={'origin_type': 'foo',
                              'origin_url': 'bar'})
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, "No SWH visit", status_code=404)

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.side_effect = \
            NotFoundExc('visit not found')
        url = reverse('browse-origin-directory',
                      kwargs={'origin_type': 'foo',
                              'origin_url': 'bar'},
                      query_params={'visit_id': len(stub_origin_visits)+1})
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertRegex(resp.content.decode('utf-8'), 'Visit.*not found')

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.side_effect = None
        mock_get_origin_visit_snapshot.return_value = ([], [])
        url = reverse('browse-origin-directory',
                      kwargs={'origin_type': 'foo',
                              'origin_url': 'bar'})
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertRegex(resp.content.decode('utf-8'),
                         'Origin.*has an empty list of branches')

        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_utils_service.lookup_directory.side_effect = \
            NotFoundExc('Directory not found')
        url = reverse('browse-origin-directory',
                      kwargs={'origin_type': 'foo',
                              'origin_url': 'bar'})
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'Directory not found', status_code=404)

        mock_origin_service.lookup_origin.side_effect = None
        mock_origin_service.lookup_origin.return_value = origin_info_test_data
        mock_get_origin_visits.return_value = []
        url = reverse('browse-origin-content',
                      kwargs={'origin_type': 'foo',
                              'origin_url': 'bar',
                              'path': 'foo'})
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, "No SWH visit", status_code=404)

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.side_effect = \
            NotFoundExc('visit not found')
        url = reverse('browse-origin-content',
                      kwargs={'origin_type': 'foo',
                              'origin_url': 'bar',
                              'path': 'foo'},
                      query_params={'visit_id': len(stub_origin_visits)+1})
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertRegex(resp.content.decode('utf-8'), 'Visit.*not found')

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.side_effect = None
        mock_get_origin_visit_snapshot.return_value = ([], [])
        url = reverse('browse-origin-content',
                      kwargs={'origin_type': 'foo',
                              'origin_url': 'bar',
                              'path': 'baz'})
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertRegex(resp.content.decode('utf-8'),
                         'Origin.*has an empty list of branches')

        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_origin_service.lookup_directory_with_path.return_value = \
            {'target': stub_content_text_data['checksums']['sha1']}
        mock_request_content.side_effect = \
            NotFoundExc('Content not found')
        url = reverse('browse-origin-content',
                      kwargs={'origin_type': 'foo',
                              'origin_url': 'bar',
                              'path': 'baz'})
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'Content not found', status_code=404)


    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.origin.service')
    @istest
    def origin_branches(self, mock_origin_service,
                        mock_utils_service,
                        mock_get_origin_visit_snapshot,
                        mock_get_origin_visits):
        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_utils_service.lookup_origin.return_value = stub_origin_info

        url_args = {'origin_type': stub_origin_info['type'],
                    'origin_url': stub_origin_info['url']}

        url = reverse('browse-origin-branches',
                      kwargs=url_args)

        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('branches.html')

        origin_branches = stub_origin_snapshot[0]
        origin_releases = stub_origin_snapshot[1]

        origin_branches_url = \
                reverse('browse-origin-branches',
                        kwargs=url_args)

        self.assertContains(resp, '<a href="%s">Branches (%s)</a>' %
            (origin_branches_url, len(origin_branches)))

        origin_releases_url = \
                reverse('browse-origin-releases',
                        kwargs=url_args)

        self.assertContains(resp, '<a href="%s">Releases (%s)</a>' %
            (origin_releases_url, len(origin_releases)))

        self.assertContains(resp, '<tr class="swh-origin-branch">',
                            count=len(origin_branches))

        for branch in origin_branches:
            browse_branch_url = reverse('browse-origin-directory',
                                        kwargs={'origin_type': stub_origin_info['type'],
                                                'origin_url': stub_origin_info['url']},
                                        query_params={'branch': branch['name']})
            self.assertContains(resp, '<a href="%s">%s</a>' % (escape(browse_branch_url), branch['name']))

            browse_revision_url = reverse('browse-revision',
                                          kwargs={'sha1_git': branch['revision']},
                                          query_params={'origin_type': stub_origin_info['type'],
                                                        'origin_url': stub_origin_info['url']})
            self.assertContains(resp, '<a href="%s">%s</a>' % (escape(browse_revision_url), branch['revision'][:7]))


    @patch('swh.web.browse.utils.get_origin_visits')
    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.origin.service')
    @istest
    def origin_releases(self, mock_origin_service,
                        mock_utils_service,
                        mock_get_origin_visit_snapshot,
                        mock_get_origin_visits):
        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_utils_service.lookup_origin.return_value = stub_origin_info

        url_args = {'origin_type': stub_origin_info['type'],
                    'origin_url': stub_origin_info['url']}

        url = reverse('browse-origin-releases',
                      kwargs=url_args)

        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('releases.html')

        origin_branches = stub_origin_snapshot[0]
        origin_releases = stub_origin_snapshot[1]

        origin_branches_url = \
                reverse('browse-origin-branches',
                        kwargs=url_args)

        self.assertContains(resp, '<a href="%s">Branches (%s)</a>' %
            (origin_branches_url, len(origin_branches)))

        origin_releases_url = \
                reverse('browse-origin-releases',
                        kwargs=url_args)

        self.assertContains(resp, '<a href="%s">Releases (%s)</a>' %
            (origin_releases_url, len(origin_releases)))

        self.assertContains(resp, '<tr class="swh-origin-release">',
                            count=len(origin_releases))

        for release in origin_releases:
            browse_release_url = reverse('browse-release',
                                         kwargs={'sha1_git': release['id']},
                                         query_params={'origin_type': stub_origin_info['type'],
                                                       'origin_url': stub_origin_info['url']})
            self.assertContains(resp, '<a href="%s">%s</a>' % (escape(browse_release_url), release['name']))

