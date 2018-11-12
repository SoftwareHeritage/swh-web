# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# flake8: noqa

from unittest.mock import patch

from swh.web.common.exc import BadInputExc
from swh.web.common.utils import reverse
from swh.web.tests.testcase import SWHWebTestCase

from .data.content_test_data import stub_content_text_data

from .data.directory_test_data import stub_root_directory_sha1

from .data.revision_test_data import revision_id_test

from .data.release_test_data import stub_release

swh_id_prefix = 'swh:1:'


class SwhBrowseIdTest(SWHWebTestCase):

    def test_content_id_browse(self):
        cnt_sha1_git = stub_content_text_data['checksums']['sha1_git']
        swh_id = swh_id_prefix + 'cnt:' + cnt_sha1_git
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        query_string = 'sha1_git:' + cnt_sha1_git
        content_browse_url = reverse('browse-content',
                                     url_args={'query_string': query_string})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], content_browse_url)

    def test_directory_id_browse(self):
        swh_id = swh_id_prefix + 'dir:' + stub_root_directory_sha1
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        directory_browse_url = reverse('browse-directory',
                                       url_args={'sha1_git': stub_root_directory_sha1})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], directory_browse_url)

    def test_revision_id_browse(self):
        swh_id = swh_id_prefix + 'rev:' + revision_id_test
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        revision_browse_url = reverse('browse-revision',
                                       url_args={'sha1_git': revision_id_test})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], revision_browse_url)

        query_params = {'origin_type': 'git',
                        'origin': 'https://github.com/webpack/webpack'}

        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id},
                      query_params=query_params)

        revision_browse_url = reverse('browse-revision',
                                       url_args={'sha1_git': revision_id_test},
                                       query_params=query_params)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], revision_browse_url)

    def test_release_id_browse(self):
        swh_id = swh_id_prefix + 'rel:' + stub_release['id']
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        release_browse_url = reverse('browse-release',
                                     url_args={'sha1_git': stub_release['id']})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], release_browse_url)

        query_params = {'origin_type': 'git',
                        'origin': 'https://github.com/python/cpython'}

        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id},
                      query_params=query_params)

        release_browse_url = reverse('browse-release',
                                     url_args={'sha1_git': stub_release['id']},
                                     query_params=query_params)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], release_browse_url)

    def test_bad_id_browse(self):
        swh_id = swh_id_prefix + 'foo:' + stub_release['id']
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 400)

    def test_content_id_optional_parts_browse(self):
        cnt_sha1_git = stub_content_text_data['checksums']['sha1_git']
        optional_parts = ';lines=4-20;origin=https://github.com/user/repo'
        swh_id = swh_id_prefix + 'cnt:' + cnt_sha1_git + optional_parts
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        query_string = 'sha1_git:' + cnt_sha1_git
        content_browse_url = reverse('browse-content',
                                     url_args={'query_string': query_string},
                                     query_params={'origin' : 'https://github.com/user/repo'})
        content_browse_url += '#L4-L20'

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], content_browse_url)

