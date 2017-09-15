# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from unittest.mock import patch
from nose.tools import istest

from django.test import TestCase

from swh.web.common.utils import reverse
from swh.web.browse.utils import gen_path_info
from .data.directory_test_data import (
    stub_root_directory_sha1, stub_root_directory_data,
    stub_sub_directory_path, stub_sub_directory_data
)


class SwhUiDirectoryViewTest(TestCase):

    @patch('swh.web.browse.views.directory.service')
    @istest
    def root_directory_view(self, mock_service):
        mock_service.lookup_directory.return_value = \
            stub_root_directory_data

        dirs = [e for e in stub_root_directory_data if e['type'] == 'dir']
        files = [e for e in stub_root_directory_data if e['type'] == 'file']

        url = reverse('browse-directory',
                      kwargs={'sha1_git': stub_root_directory_sha1})
        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('directory.html')
        self.assertContains(resp, '<td class="swh-directory">',
                            count=len(dirs))
        self.assertContains(resp, '<td class="swh-content">',
                            count=len(files))

        for d in dirs:
            dir_url = reverse('browse-directory',
                              kwargs={'sha1_git': stub_root_directory_sha1,
                                      'path': d['name']})
            self.assertContains(resp, dir_url)

        for f in files:
            file_path = stub_root_directory_sha1 + '/' + f['name']
            file_url = reverse('browse-content',
                               kwargs={'sha1_git': f['target']},
                               query_params={'path': file_path})
            self.assertContains(resp, file_url)

        self.assertContains(resp, '<li class="swh-path">',
                            count=1)
        self.assertContains(resp, '<a href="' + url + '">' +
                            stub_root_directory_sha1[:7] + '</a>')

    @patch('swh.web.browse.views.directory.service')
    @istest
    def sub_directory_view(self, mock_service):
        mock_service.lookup_directory.return_value = \
            stub_sub_directory_data

        dirs = [e for e in stub_sub_directory_data if e['type'] == 'dir']
        files = [e for e in stub_sub_directory_data if e['type'] == 'file']

        url = reverse('browse-directory',
                      kwargs={'sha1_git': stub_root_directory_sha1,
                              'path': stub_sub_directory_path})

        root_dir_url = reverse('browse-directory',
                               kwargs={'sha1_git': stub_root_directory_sha1})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('directory.html')
        self.assertContains(resp, '<a href="' + root_dir_url + '">' +
                            stub_root_directory_sha1[:7] + '</a>')
        self.assertContains(resp, '<td class="swh-directory">',
                            count=len(dirs))
        self.assertContains(resp, '<td class="swh-content">',
                            count=len(files))

        for d in dirs:
            dir_url = reverse('browse-directory',
                              kwargs={'sha1_git': stub_root_directory_sha1,
                                      'path': d['name']})
            self.assertContains(resp, dir_url)

        for f in files:
            file_path = stub_root_directory_sha1 + '/' + \
                        stub_sub_directory_path + '/' + f['name']
            file_url = reverse('browse-content',
                               kwargs={'sha1_git': f['target']},
                               query_params={'path': file_path})
            self.assertContains(resp, file_url)

        path_info = gen_path_info(stub_sub_directory_path)

        self.assertContains(resp, '<li class="swh-path">',
                            count=len(path_info)+1)
        self.assertContains(resp, '<a href="' + root_dir_url + '">' +
                            stub_root_directory_sha1[:7] + '</a>')

        for p in path_info:
            dir_url = reverse('browse-directory',
                              kwargs={'sha1_git': stub_root_directory_sha1,
                                      'path': p['path']})
            self.assertContains(resp, '<a href="' + dir_url + '">' +
                                p['name'] + '</a>')
