# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given

from swh.web.common.utils import reverse
from swh.web.tests.strategies import (
    content, directory, revision, release, snapshot
)
from swh.web.tests.testcase import WebTestCase

swh_id_prefix = 'swh:1:'


class SwhBrowseIdTest(WebTestCase):

    @given(content())
    def test_content_id_browse(self, content):
        cnt_sha1_git = content['sha1_git']
        swh_id = swh_id_prefix + 'cnt:' + cnt_sha1_git
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        query_string = 'sha1_git:' + cnt_sha1_git
        content_browse_url = reverse('browse-content',
                                     url_args={'query_string': query_string})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], content_browse_url)

    @given(directory())
    def test_directory_id_browse(self, directory):
        swh_id = swh_id_prefix + 'dir:' + directory
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        directory_browse_url = reverse('browse-directory',
                                       url_args={'sha1_git': directory})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], directory_browse_url)

    @given(revision())
    def test_revision_id_browse(self, revision):
        swh_id = swh_id_prefix + 'rev:' + revision
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        revision_browse_url = reverse('browse-revision',
                                      url_args={'sha1_git': revision})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], revision_browse_url)

        query_params = {'origin_type': 'git',
                        'origin': 'https://github.com/user/repo'}

        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id},
                      query_params=query_params)

        revision_browse_url = reverse('browse-revision',
                                      url_args={'sha1_git': revision},
                                      query_params=query_params)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], revision_browse_url)

    @given(release())
    def test_release_id_browse(self, release):
        swh_id = swh_id_prefix + 'rel:' + release
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        release_browse_url = reverse('browse-release',
                                     url_args={'sha1_git': release})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], release_browse_url)

        query_params = {'origin_type': 'git',
                        'origin': 'https://github.com/user/repo'}

        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id},
                      query_params=query_params)

        release_browse_url = reverse('browse-release',
                                     url_args={'sha1_git': release},
                                     query_params=query_params)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], release_browse_url)

    @given(snapshot())
    def test_snapshot_id_browse(self, snapshot):
        swh_id = swh_id_prefix + 'snp:' + snapshot
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        snapshot_browse_url = reverse('browse-snapshot',
                                      url_args={'snapshot_id': snapshot})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], snapshot_browse_url)

        query_params = {'origin_type': 'git',
                        'origin': 'https://github.com/user/repo'}

        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id},
                      query_params=query_params)

        release_browse_url = reverse('browse-snapshot',
                                     url_args={'snapshot_id': snapshot},
                                     query_params=query_params)

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], release_browse_url)

    @given(release())
    def test_bad_id_browse(self, release):
        swh_id = swh_id_prefix + 'foo:' + release
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 400)

    @given(content())
    def test_content_id_optional_parts_browse(self, content):
        cnt_sha1_git = content['sha1_git']
        optional_parts = ';lines=4-20;origin=https://github.com/user/repo'
        swh_id = swh_id_prefix + 'cnt:' + cnt_sha1_git + optional_parts
        url = reverse('browse-swh-id',
                      url_args={'swh_id': swh_id})

        query_string = 'sha1_git:' + cnt_sha1_git
        content_browse_url = reverse(
            'browse-content', url_args={'query_string': query_string},
            query_params={'origin': 'https://github.com/user/repo'})
        content_browse_url += '#L4-L20'

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['location'], content_browse_url)
