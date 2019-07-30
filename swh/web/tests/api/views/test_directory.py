# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from hypothesis import given
from rest_framework.test import APITestCase

from swh.web.common.utils import reverse
from swh.web.tests.data import random_sha1
from swh.web.tests.strategies import directory
from swh.web.tests.testcase import WebTestCase


class DirectoryApiTestCase(WebTestCase, APITestCase):

    @given(directory())
    def test_api_directory(self, directory):

        url = reverse('api-1-directory', url_args={'sha1_git': directory})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')

        expected_data = list(map(self._enrich_dir_data,
                                 self.directory_ls(directory)))

        self.assertEqual(rv.data, expected_data)

    def test_api_directory_not_found(self):
        unknown_directory_ = random_sha1()

        url = reverse('api-1-directory',
                      url_args={'sha1_git': unknown_directory_})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Directory with sha1_git %s not found'
            % unknown_directory_})

    @given(directory())
    def test_api_directory_with_path_found(self, directory):

        directory_content = self.directory_ls(directory)
        path = random.choice(directory_content)

        url = reverse('api-1-directory',
                      url_args={'sha1_git': directory,
                                'path': path['name']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, self._enrich_dir_data(path))

    @given(directory())
    def test_api_directory_with_path_not_found(self, directory):

        path = 'some/path/to/nonexistent/dir/'
        url = reverse('api-1-directory',
                      url_args={'sha1_git': directory,
                                'path': path})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': ('Directory entry with path %s from %s not found'
                       % (path, directory))})

    @given(directory())
    def test_api_directory_uppercase(self, directory):
        url = reverse('api-1-directory-uppercase-checksum',
                      url_args={'sha1_git': directory.upper()})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        redirect_url = reverse('api-1-directory',
                               url_args={'sha1_git': directory})

        self.assertEqual(resp['location'], redirect_url)

    @classmethod
    def _enrich_dir_data(cls, dir_data):
        if dir_data['type'] == 'file':
            dir_data['target_url'] = \
                reverse('api-1-content',
                        url_args={'q': 'sha1_git:%s' % dir_data['target']})
        elif dir_data['type'] == 'dir':
            dir_data['target_url'] = \
                reverse('api-1-directory',
                        url_args={'sha1_git': dir_data['target']})
        elif dir_data['type'] == 'rev':
            dir_data['target_url'] = \
                reverse('api-1-revision',
                        url_args={'sha1_git': dir_data['target']})

        return dir_data
