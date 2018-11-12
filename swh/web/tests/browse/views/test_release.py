# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# flake8: noqa

from unittest.mock import patch

from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import (
    reverse, format_utc_iso_date, get_swh_persistent_id
)
from swh.web.tests.testcase import SWHWebTestCase

from .data.release_test_data import (
    stub_release
)

from .data.origin_test_data import stub_origin_visits


class SwhBrowseReleaseTest(SWHWebTestCase):

    @patch('swh.web.browse.views.release.service')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.common.utils.service')
    def test_release_browse(self, mock_service_common, mock_service_utils,
                       mock_service):
        mock_service.lookup_release.return_value = stub_release

        url = reverse('browse-release',
                      url_args={'sha1_git': stub_release['id']})

        release_id = stub_release['id']
        release_name = stub_release['name']
        author_id = stub_release['author']['id']
        author_name = stub_release['author']['name']
        author_url = reverse('browse-person',
                             url_args={'person_id': author_id})

        release_date = stub_release['date']
        message = stub_release['message']
        target_type = stub_release['target_type']
        target = stub_release['target']
        target_url = reverse('browse-revision', url_args={'sha1_git': target})

        message_lines = stub_release['message'].split('\n')

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/release.html')
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (author_url, author_name))
        self.assertContains(resp, format_utc_iso_date(release_date))
        self.assertContains(resp, '<h6>%s</h6>%s' % (message_lines[0],
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

        origin_info = {
            'id': 13706355,
            'type': 'git',
            'url': 'https://github.com/python/cpython'
        }

        mock_service_utils.lookup_origin.return_value = origin_info
        mock_service_common.lookup_origin_visits.return_value = stub_origin_visits
        mock_service_common.MAX_LIMIT = 20

        url = reverse('browse-release',
                      url_args={'sha1_git': stub_release['id']},
                      query_params={'origin': origin_info['url']})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/release.html')

        self.assertContains(resp, author_url)
        self.assertContains(resp, author_name)
        self.assertContains(resp, format_utc_iso_date(release_date))
        self.assertContains(resp, '<h6>%s</h6>%s' % (message_lines[0],
                                                     '\n'.join(message_lines[1:])))
        self.assertContains(resp, release_id)
        self.assertContains(resp, release_name)
        self.assertContains(resp, target_type)

        target_url = reverse('browse-revision', url_args={'sha1_git': target},
                             query_params={'origin': origin_info['url']})

        self.assertContains(resp, '<a href="%s">%s</a>' % (target_url, target))

        mock_service.lookup_release.side_effect = \
            NotFoundExc('Release not found')
        url = reverse('browse-release',
                      url_args={'sha1_git': 'ffff'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'Release not found', status_code=404)
