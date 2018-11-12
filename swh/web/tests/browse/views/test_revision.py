# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# flake8: noqa

from unittest.mock import patch, MagicMock
from django.utils.html import escape

from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import (
    reverse, format_utc_iso_date, get_swh_persistent_id,
    parse_timestamp
)
from swh.web.tests.testcase import SWHWebTestCase

from .data.revision_test_data import (
    revision_id_test, revision_metadata_test,
    revision_history_log_test
)

from .data.origin_test_data import stub_origin_visits, stub_origin_snapshot


class SwhBrowseRevisionTest(SWHWebTestCase):

    @patch('swh.web.browse.utils.get_origin_visit_snapshot')
    @patch('swh.web.browse.views.revision.service')
    @patch('swh.web.browse.utils.service')
    @patch('swh.web.common.utils.service')
    def test_revision_browse(self, mock_service_common, mock_service_utils,
                             mock_service, mock_get_origin_visit_snapshot):
        mock_service.lookup_revision.return_value = revision_metadata_test

        url = reverse('browse-revision',
                      url_args={'sha1_git': revision_id_test})

        author_id = revision_metadata_test['author']['id']
        author_name = revision_metadata_test['author']['name']
        committer_id = revision_metadata_test['committer']['id']
        committer_name = revision_metadata_test['committer']['name']
        dir_id = revision_metadata_test['directory']

        author_url = reverse('browse-person',
                             url_args={'person_id': author_id})
        committer_url = reverse('browse-person',
                                url_args={'person_id': committer_id})

        directory_url = reverse('browse-directory',
                                url_args={'sha1_git': dir_id})

        history_url = reverse('browse-revision-log',
                              url_args={'sha1_git': revision_id_test})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/revision.html')
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (author_url, author_name))
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (committer_url, committer_name))
        self.assertContains(resp, directory_url)
        self.assertContains(resp, history_url)

        for parent in revision_metadata_test['parents']:
            parent_url = reverse('browse-revision',
                                 url_args={'sha1_git': parent})
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (parent_url, parent))

        author_date = revision_metadata_test['date']
        committer_date = revision_metadata_test['committer_date']

        message_lines = revision_metadata_test['message'].split('\n')

        self.assertContains(resp, format_utc_iso_date(author_date))
        self.assertContains(resp, format_utc_iso_date(committer_date))
        self.assertContains(resp, message_lines[0])
        self.assertContains(resp, '\n'.join(message_lines[1:]))

        origin_info = {
            'id': '7416001',
            'type': 'git',
            'url': 'https://github.com/webpack/webpack'
        }

        mock_service_utils.lookup_origin.return_value = origin_info
        mock_service_common.lookup_origin_visits.return_value = stub_origin_visits
        mock_get_origin_visit_snapshot.return_value = stub_origin_snapshot
        mock_service_utils.lookup_snapshot_size.return_value = {
            'revision': len(stub_origin_snapshot[0]),
            'release': len(stub_origin_snapshot[1])
        }
        mock_service_common.MAX_LIMIT = 20

        origin_directory_url = reverse('browse-origin-directory',
                                       url_args={'origin_url': origin_info['url']},
                                       query_params={'revision': revision_id_test})

        origin_revision_log_url = reverse('browse-origin-log',
                                          url_args={'origin_url': origin_info['url']},
                                          query_params={'revision': revision_id_test})

        url = reverse('browse-revision',
                      url_args={'sha1_git': revision_id_test},
                      query_params={'origin': origin_info['url']})

        resp = self.client.get(url)

        self.assertContains(resp, origin_directory_url)

        self.assertContains(resp, origin_revision_log_url)

        for parent in revision_metadata_test['parents']:
            parent_url = reverse('browse-revision',
                                 url_args={'sha1_git': parent},
                                 query_params={'origin': origin_info['url']})
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (parent_url, parent))

        self.assertContains(resp, 'vault-cook-directory')
        self.assertContains(resp, 'vault-cook-revision')

        swh_rev_id = get_swh_persistent_id('revision', revision_id_test)
        swh_rev_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_rev_id})
        self.assertContains(resp, swh_rev_id)
        self.assertContains(resp, swh_rev_id_url)

        swh_dir_id = get_swh_persistent_id('directory', dir_id)
        swh_dir_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_dir_id})
        self.assertContains(resp, swh_dir_id)
        self.assertContains(resp, swh_dir_id_url)

    @patch('swh.web.browse.views.revision.service')
    def test_revision_log_browse(self, mock_service):
        per_page = 10

        revision_history_log_test_sorted = \
            sorted(revision_history_log_test,
                   key=lambda rev: -parse_timestamp(rev['committer_date']).timestamp())

        mock_revs_walker = MagicMock()
        mock_revs_walker.__iter__.return_value = revision_history_log_test_sorted
        mock_revs_walker.export_state.return_value = {}

        mock_service.get_revisions_walker.return_value = mock_revs_walker

        url = reverse('browse-revision-log',
                      url_args={'sha1_git': revision_id_test},
                      query_params={'per_page': per_page})

        resp = self.client.get(url)

        next_page_url = reverse('browse-revision-log',
                                url_args={'sha1_git': revision_id_test},
                                query_params={'offset': per_page,
                                              'per_page': per_page})

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/revision-log.html')
        self.assertContains(resp, '<tr class="swh-revision-log-entry',
                            count=per_page)
        self.assertContains(resp, '<a class="page-link">Newer</a>')
        self.assertContains(resp, '<a class="page-link" href="%s">Older</a>' %
                            escape(next_page_url))

        for log in revision_history_log_test_sorted[:per_page]:
            author_url = reverse('browse-person',
                                 url_args={'person_id': log['author']['id']})
            revision_url = reverse('browse-revision',
                                   url_args={'sha1_git': log['id']})
            self.assertContains(resp, log['id'][:7])
            self.assertContains(resp, log['author']['name'])
            self.assertContains(resp, format_utc_iso_date(log['date']))
            self.assertContains(resp, escape(log['message']))
            self.assertContains(resp, format_utc_iso_date(log['committer_date']))
            self.assertContains(resp, revision_url)

        resp = self.client.get(next_page_url)

        prev_page_url = reverse('browse-revision-log',
                                url_args={'sha1_git': revision_id_test},
                                query_params={'per_page': per_page})
        next_page_url = reverse('browse-revision-log',
                                url_args={'sha1_git': revision_id_test},
                                query_params={'offset': 2 * per_page,
                                              'per_page': per_page})

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/revision-log.html')
        self.assertContains(resp, '<tr class="swh-revision-log-entry',
                            count=per_page)
        self.assertContains(resp, '<a class="page-link" href="%s">Newer</a>' %
                            escape(prev_page_url))
        self.assertContains(resp, '<a class="page-link" href="%s">Older</a>' %
                            escape(next_page_url))

        resp = self.client.get(next_page_url)

        prev_page_url = reverse('browse-revision-log',
                                url_args={'sha1_git': revision_id_test},
                                query_params={'offset': per_page,
                                              'per_page': per_page})
        next_page_url = reverse('browse-revision-log',
                                url_args={'sha1_git': revision_id_test},
                                query_params={'offset': 3 * per_page,
                                              'per_page': per_page})

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/revision-log.html')
        self.assertContains(resp, '<tr class="swh-revision-log-entry',
                            count=per_page)
        self.assertContains(resp, '<a class="page-link" href="%s">Newer</a>' %
                            escape(prev_page_url))
        self.assertContains(resp, '<a class="page-link" href="%s">Older</a>' %
                            escape(next_page_url))

    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.revision.service')
    def test_revision_request_errors(self, mock_service, mock_utils_service):
        mock_service.lookup_revision.side_effect = \
            NotFoundExc('Revision not found')
        url = reverse('browse-revision',
                      url_args={'sha1_git': revision_id_test})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'Revision not found', status_code=404)

        mock_service.get_revisions_walker.side_effect = \
            NotFoundExc('Revision not found')
        url = reverse('browse-revision-log',
                      url_args={'sha1_git': revision_id_test})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'Revision not found', status_code=404)

        url = reverse('browse-revision',
                      url_args={'sha1_git': revision_id_test},
                      query_params={'origin_type': 'git',
                                    'origin': 'https://github.com/foo/bar'})

        mock_service.lookup_revision.side_effect = None
        mock_utils_service.lookup_origin.side_effect = \
            NotFoundExc('Origin not found')

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'Origin not found', status_code=404)
