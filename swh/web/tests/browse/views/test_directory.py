# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from unittest.mock import patch
from nose.tools import istest, nottest

from django.test import TestCase

from swh.web.common.utils import reverse
from swh.web.browse.utils import gen_path_info
from .data.directory_test_data import (
    stub_root_directory_sha1, stub_root_directory_data,
    stub_sub_directory_path, stub_sub_directory_data
)

from .data.origin_directory_test_data import (
    stub_origin_id, stub_visit_id,
    stub_origin_visits, stub_origin_branches,
    stub_origin_root_directory_entries, stub_origin_master_branch,
    stub_origin_root_directory_sha1, stub_origin_sub_directory_path,
    stub_origin_sub_directory_entries, stub_visit_ts
)


class SwhBrowseDirectoryViewTest(TestCase):

    @nottest
    def directory_view(self, root_directory_sha1, directory_entries,
                       path=None):
        dirs = [e for e in directory_entries if e['type'] == 'dir']
        files = [e for e in directory_entries if e['type'] == 'file']

        url_args = {'sha1_git': root_directory_sha1}
        if path:
            url_args['path'] = path

        url = reverse('browse-directory',
                      kwargs=url_args)

        root_dir_url = reverse('browse-directory',
                               kwargs={'sha1_git': root_directory_sha1})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('directory.html')
        self.assertContains(resp, '<a href="' + root_dir_url + '">' +
                            root_directory_sha1[:7] + '</a>')
        self.assertContains(resp, '<td class="swh-directory">',
                            count=len(dirs))
        self.assertContains(resp, '<td class="swh-content">',
                            count=len(files))

        for d in dirs:
            dir_path = d['name']
            if path:
                dir_path = "%s/%s" % (path, d['name'])
            dir_url = reverse('browse-directory',
                              kwargs={'sha1_git': root_directory_sha1,
                                      'path': dir_path})
            self.assertContains(resp, dir_url)

        for f in files:
            file_path = "%s/%s" % (root_directory_sha1, f['name'])
            if path:
                file_path = "%s/%s/%s" % (root_directory_sha1, path, f['name'])
            file_url = reverse('browse-content',
                               kwargs={'sha1_git': f['target']},
                               query_params={'path': file_path})
            self.assertContains(resp, file_url)

        path_info = gen_path_info(path)

        self.assertContains(resp, '<li class="swh-path">',
                            count=len(path_info)+1)
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (root_dir_url, root_directory_sha1[:7]))

        for p in path_info:
            dir_url = reverse('browse-directory',
                              kwargs={'sha1_git': root_directory_sha1,
                                      'path': p['path']})
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                      (dir_url, p['name']))

    @patch('swh.web.browse.views.directory.service')
    @istest
    def root_directory_view(self, mock_service):
        mock_service.lookup_directory.return_value = \
            stub_root_directory_data

        self.directory_view(stub_root_directory_sha1, stub_root_directory_data)

    @patch('swh.web.browse.views.directory.service')
    @istest
    def sub_directory_view(self, mock_service):
        mock_service.lookup_directory.return_value = \
            stub_sub_directory_data

        self.directory_view(stub_root_directory_sha1, stub_sub_directory_data,
                            stub_sub_directory_path)

    @nottest
    def origin_directory_view(self, origin_id, origin_visits,
                              origin_branches, origin_branch,
                              root_directory_sha1, directory_entries,
                              visit_id=None, ts=None, path=None):

        dirs = [e for e in directory_entries
                if e['type'] == 'dir']
        files = [e for e in directory_entries
                 if e['type'] == 'file']

        if not visit_id:
            visit_id = origin_visits[-1]['visit']

        url_args = {'origin_id': origin_id}

        if ts:
            url_args['ts'] = ts
        else:
            url_args['visit_id'] = visit_id

        if path:
            url_args['path'] = path

        url = reverse('browse-origin-directory',
                      kwargs=url_args)

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('directory.html')
        self.assertContains(resp, '<td class="swh-directory">',
                            count=len(dirs))
        self.assertContains(resp, '<td class="swh-content">',
                            count=len(files))

        for d in dirs:
            dir_path = d['name']
            if path:
                dir_path = "%s/%s" % (path, d['name'])
            dir_url_args = dict(url_args)
            dir_url_args['path'] = dir_path
            dir_url = reverse('browse-origin-directory',
                              kwargs=dir_url_args,
                              query_params={'branch': origin_branch}) # noqa
            self.assertContains(resp, dir_url)

        for f in files:
            file_path = f['name']
            if path:
                file_path = "%s/%s" % (path, f['name'])
            file_url_args = dict(url_args)
            file_url_args['path'] = file_path
            file_url = reverse('browse-origin-content',
                               kwargs=file_url_args,
                               query_params={'branch': origin_branch}) # noqa
            self.assertContains(resp, file_url)

        if 'path' in url_args:
            del url_args['path']

        root_dir_branch_url = \
            reverse('browse-origin-directory',
                    kwargs=url_args,
                    query_params={'branch': origin_branch})

        nb_bc_paths = 1
        if path:
            nb_bc_paths = len(path.split('/')) + 1

        self.assertContains(resp, '<li class="swh-path">', count=nb_bc_paths)
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (root_dir_branch_url,
                                   root_directory_sha1[:7]))

        self.assertContains(resp, '<li class="swh-branch">',
                            count=len(origin_branches))

        if path:
            url_args['path'] = path

        for branch in origin_branches:
            root_dir_branch_url = \
                reverse('browse-origin-directory',
                        kwargs=url_args,
                        query_params={'branch': branch['name']})

            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (root_dir_branch_url, branch['name']))

    @patch('swh.web.browse.views.directory.get_origin_visits')
    @patch('swh.web.browse.views.directory.get_origin_visit_branches')
    @patch('swh.web.browse.views.directory.service')
    @istest
    def origin_root_directory_view(self, mock_service,
                                   mock_get_origin_visit_branches,
                                   mock_get_origin_visits):

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_branches.return_value = stub_origin_branches
        mock_service.lookup_directory.return_value = \
            stub_origin_root_directory_entries

        self.origin_directory_view(stub_origin_id, stub_origin_visits,
                                   stub_origin_branches,
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_root_directory_entries)

        self.origin_directory_view(stub_origin_id, stub_origin_visits,
                                   stub_origin_branches,
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_root_directory_entries,
                                   visit_id=stub_visit_id)

        self.origin_directory_view(stub_origin_id, stub_origin_visits,
                                   stub_origin_branches,
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_root_directory_entries,
                                   ts=stub_visit_ts)

    @patch('swh.web.browse.views.directory.get_origin_visits')
    @patch('swh.web.browse.views.directory.get_origin_visit_branches')
    @patch('swh.web.browse.views.directory.service')
    @istest
    def origin_sub_directory_view(self, mock_service,
                                  mock_get_origin_visit_branches,
                                  mock_get_origin_visits):

        mock_get_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_branches.return_value = stub_origin_branches
        mock_service.lookup_directory.return_value = \
            stub_origin_sub_directory_entries

        self.origin_directory_view(stub_origin_id, stub_origin_visits,
                                   stub_origin_branches,
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_sub_directory_entries,
                                   path=stub_origin_sub_directory_path)

        self.origin_directory_view(stub_origin_id, stub_origin_visits,
                                   stub_origin_branches,
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_sub_directory_entries,
                                   visit_id=stub_visit_id,
                                   path=stub_origin_sub_directory_path)

        self.origin_directory_view(stub_origin_id, stub_origin_visits,
                                   stub_origin_branches,
                                   stub_origin_master_branch,
                                   stub_origin_root_directory_sha1,
                                   stub_origin_sub_directory_entries,
                                   ts=stub_visit_ts,
                                   path=stub_origin_sub_directory_path)
