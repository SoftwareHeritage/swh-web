# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from hypothesis import given

from swh.web.common.utils import (
    reverse, format_utc_iso_date, get_swh_persistent_id
)
from swh.web.tests.strategies import (
    release, origin_with_release, unknown_release
)
from swh.web.tests.testcase import WebTestCase


class SwhBrowseReleaseTest(WebTestCase):

    @given(release())
    def test_release_browse(self, release):

        url = reverse('browse-release',
                      url_args={'sha1_git': release})

        release_data = self.release_get(release)

        resp = self.client.get(url)

        self._release_browse_checks(resp, release_data)

    @given(origin_with_release())
    def test_release_browse_with_origin(self, origin):
        snapshot = self.snapshot_get_latest(origin['url'])
        release = random.choice([b for b in snapshot['branches'].values()
                                 if b['target_type'] == 'release'])
        url = reverse('browse-release',
                      url_args={'sha1_git': release['target']},
                      query_params={'origin': origin['url']})

        release_data = self.release_get(release['target'])

        resp = self.client.get(url)

        self._release_browse_checks(resp, release_data, origin)

    @given(unknown_release())
    def test_release_browse_not_found(self, unknown_release):
        url = reverse('browse-release',
                      url_args={'sha1_git': unknown_release})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        err_msg = 'Release with sha1_git %s not found' % unknown_release
        self.assertContains(resp, err_msg, status_code=404)

    def _release_browse_checks(self, resp, release_data, origin_info=None):

        query_params = {}
        if origin_info:
            query_params['origin'] = origin_info['url']

        release_id = release_data['id']
        release_name = release_data['name']
        author_id = release_data['author']['id']
        author_name = release_data['author']['name']
        author_url = reverse('browse-person',
                             url_args={'person_id': author_id},
                             query_params=query_params)

        release_date = release_data['date']
        message = release_data['message']
        target_type = release_data['target_type']
        target = release_data['target']

        target_url = reverse('browse-revision',
                             url_args={'sha1_git': target},
                             query_params=query_params)
        message_lines = message.split('\n')

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/release.html')
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (author_url, author_name))
        self.assertContains(resp, format_utc_iso_date(release_date))
        self.assertContains(resp,
                            '<h6>%s</h6>%s' % (message_lines[0] or 'None',
                                               '\n'.join(message_lines[1:])))
        self.assertContains(resp, release_id)
        self.assertContains(resp, release_name)
        self.assertContains(resp, target_type)
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (target_url, target))

        swh_rel_id = get_swh_persistent_id('release', release_id)
        swh_rel_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_rel_id})
        self.assertContains(resp, swh_rel_id)
        self.assertContains(resp, swh_rel_id_url)

    @given(release())
    def test_release_uppercase(self, release):
        url = reverse('browse-release-uppercase-checksum',
                      url_args={'sha1_git': release.upper()})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        redirect_url = reverse('browse-release',
                               url_args={'sha1_git': release})

        self.assertEqual(resp['location'], redirect_url)
