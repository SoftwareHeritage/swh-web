# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from unittest.mock import patch

from swh.web.common.exc import BadInputExc, NotFoundExc
from swh.web.common.utils import reverse, get_swh_persistent_id
from swh.web.common.utils import gen_path_info
from swh.web.tests.testcase import SWHWebTestCase

from .data.directory_test_data import (
    stub_root_directory_sha1, stub_root_directory_data,
    stub_sub_directory_path, stub_sub_directory_data
)


class SwhBrowseDirectoryTest(SWHWebTestCase):

    def directory_view(self, root_directory_sha1, directory_entries,
                       path=None):
        dirs = [e for e in directory_entries if e['type'] in ('dir', 'rev')]
        files = [e for e in directory_entries if e['type'] == 'file']

        url_args = {'sha1_git': root_directory_sha1}
        if path:
            url_args['path'] = path

        url = reverse('browse-directory',
                      url_args=url_args)

        root_dir_url = reverse('browse-directory',
                               url_args={'sha1_git': root_directory_sha1})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/directory.html')
        self.assertContains(resp, '<a href="' + root_dir_url + '">' +
                            root_directory_sha1[:7] + '</a>')
        self.assertContains(resp, '<td class="swh-directory">',
                            count=len(dirs))
        self.assertContains(resp, '<td class="swh-content">',
                            count=len(files))

        for d in dirs:
            if d['type'] == 'rev':
                dir_url = reverse('browse-revision',
                                  url_args={'sha1_git': d['target']})
            else:
                dir_path = d['name']
                if path:
                    dir_path = "%s/%s" % (path, d['name'])
                dir_url = reverse('browse-directory',
                                  url_args={'sha1_git': root_directory_sha1,
                                            'path': dir_path})
            self.assertContains(resp, dir_url)

        for f in files:
            file_path = "%s/%s" % (root_directory_sha1, f['name'])
            if path:
                file_path = "%s/%s/%s" % (root_directory_sha1, path, f['name'])
            query_string = 'sha1_git:' + f['target']
            file_url = reverse('browse-content',
                               url_args={'query_string': query_string},
                               query_params={'path': file_path})
            self.assertContains(resp, file_url)

        path_info = gen_path_info(path)

        self.assertContains(resp, '<li class="swh-path">',
                            count=len(path_info)+1)
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (root_dir_url, root_directory_sha1[:7]))

        for p in path_info:
            dir_url = reverse('browse-directory',
                              url_args={'sha1_git': root_directory_sha1,
                                        'path': p['path']})
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                      (dir_url, p['name']))

        self.assertContains(resp, 'vault-cook-directory')

        swh_dir_id = get_swh_persistent_id('directory', directory_entries[0]['dir_id']) # noqa
        swh_dir_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_dir_id})
        self.assertContains(resp, swh_dir_id)
        self.assertContains(resp, swh_dir_id_url)

    @patch('swh.web.browse.utils.service')
    def test_root_directory_view(self, mock_service):
        mock_service.lookup_directory.return_value = \
            stub_root_directory_data

        self.directory_view(stub_root_directory_sha1, stub_root_directory_data)

    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.directory.service')
    def test_sub_directory_view(self, mock_directory_service,
                                mock_utils_service):
        mock_utils_service.lookup_directory.return_value = \
            stub_sub_directory_data
        mock_directory_service.lookup_directory_with_path.return_value = \
            {'target': stub_sub_directory_data[0]['dir_id'],
             'type': 'dir'}

        self.directory_view(stub_root_directory_sha1, stub_sub_directory_data,
                            stub_sub_directory_path)

    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.directory.service')
    def test_directory_request_errors(self, mock_directory_service,
                                      mock_utils_service):

        mock_utils_service.lookup_directory.side_effect = \
            BadInputExc('directory not found')

        dir_url = reverse('browse-directory',
                          url_args={'sha1_git': '1253456'})

        resp = self.client.get(dir_url)
        self.assertEqual(resp.status_code, 400)
        self.assertTemplateUsed('browse/error.html')

        mock_utils_service.lookup_directory.side_effect = \
            NotFoundExc('directory not found')

        dir_url = reverse('browse-directory',
                          url_args={'sha1_git': '1253456'})

        resp = self.client.get(dir_url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('browse/error.html')
