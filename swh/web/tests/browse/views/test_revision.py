# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

# flake8: noqa

from unittest.mock import patch
from nose.tools import istest
from django.test import TestCase
from django.utils.html import escape

from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import reverse, format_utc_iso_date
from swh.web.tests.testbase import SWHWebTestBase

from .data.revision_test_data import (
    revision_id_test, revision_metadata_test,
    revision_history_log_test
)

from .data.origin_test_data import stub_origin_visits


class SwhBrowseRevisionTest(SWHWebTestBase, TestCase):

    @patch('swh.web.browse.views.revision.service')
    @patch('swh.web.browse.utils.service')
    @istest
    def revision_browse(self, mock_service_utils, mock_service):
        mock_service.lookup_revision.return_value = revision_metadata_test

        url = reverse('browse-revision',
                      kwargs={'sha1_git': revision_id_test})

        author_id = revision_metadata_test['author']['id']
        author_name = revision_metadata_test['author']['name']
        committer_id = revision_metadata_test['committer']['id']
        committer_name = revision_metadata_test['committer']['name']
        dir_id = revision_metadata_test['directory']

        author_url = reverse('browse-person',
                             kwargs={'person_id': author_id})
        committer_url = reverse('browse-person',
                                kwargs={'person_id': committer_id})

        directory_url = reverse('browse-directory',
                                kwargs={'sha1_git': dir_id})

        history_url = reverse('browse-revision-log',
                              kwargs={'sha1_git': revision_id_test})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('revision.html')
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (author_url, author_name))
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (committer_url, committer_name))
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (directory_url, directory_url))
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (history_url, history_url))

        for parent in revision_metadata_test['parents']:
            parent_url = reverse('browse-revision',
                                 kwargs={'sha1_git': parent})
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (parent_url, parent))

        author_date = revision_metadata_test['date']
        committer_date = revision_metadata_test['committer_date']
        message = revision_metadata_test['message']

        self.assertContains(resp, format_utc_iso_date(author_date))
        self.assertContains(resp, format_utc_iso_date(committer_date))
        self.assertContains(resp, message)

        origin_info = {
            'id': '7416001',
            'type': 'git',
            'url': 'https://github.com/webpack/webpack'
        }

        mock_service_utils.lookup_origin.return_value = origin_info
        mock_service_utils.lookup_origin_visits.return_value = stub_origin_visits
        mock_service_utils.MAX_LIMIT = 20

        origin_directory_url = reverse('browse-origin-directory',
                                       kwargs={'origin_type': origin_info['type'],
                                               'origin_url': origin_info['url']},
                                       query_params={'revision': revision_id_test})

        origin_revision_log_url = reverse('browse-origin-log',
                                          kwargs={'origin_type': origin_info['type'],
                                                  'origin_url': origin_info['url']},
                                          query_params={'revision': revision_id_test})

        url = reverse('browse-revision',
                      kwargs={'sha1_git': revision_id_test},
                      query_params={'origin_type': origin_info['type'],
                                    'origin_url': origin_info['url']})

        resp = self.client.get(url)

        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (origin_directory_url, origin_directory_url))

        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (origin_revision_log_url, origin_revision_log_url))

        for parent in revision_metadata_test['parents']:
            parent_url = reverse('browse-revision',
                                 kwargs={'sha1_git': parent},
                                 query_params={'origin_type': origin_info['type'],
                                               'origin_url': origin_info['url']})
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (parent_url, parent))

    @patch('swh.web.browse.views.revision.service')
    @istest
    def revision_log_browse(self, mock_service):
        per_page = 10
        mock_service.lookup_revision_log.return_value = \
            revision_history_log_test[:per_page+1]

        url = reverse('browse-revision-log',
                      kwargs={'sha1_git': revision_id_test},
                      query_params={'per_page': per_page})

        resp = self.client.get(url)

        prev_rev = revision_history_log_test[per_page]['id']
        next_page_url = reverse('browse-revision-log',
                                kwargs={'sha1_git': prev_rev},
                                query_params={'revs_breadcrumb': revision_id_test,
                                              'per_page': per_page})

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('revision-log.html')
        self.assertContains(resp, '<tr class="swh-revision-log-entry">',
                            count=per_page)
        self.assertContains(resp, '<li class="disabled"><a>Newer</a></li>')
        self.assertContains(resp, '<li><a href="%s">Older</a></li>' %
                            escape(next_page_url))

        for log in revision_history_log_test[:per_page]:
            author_url = reverse('browse-person',
                                 kwargs={'person_id': log['author']['id']})
            revision_url = reverse('browse-revision',
                                   kwargs={'sha1_git': log['id']})
            directory_url = reverse('browse-directory',
                                    kwargs={'sha1_git': log['directory']})
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (author_url, log['author']['name']))
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (revision_url, log['id'][:7]))
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (directory_url, 'Tree'))

        mock_service.lookup_revision_log.return_value = \
            revision_history_log_test[per_page:2*per_page+1]

        resp = self.client.get(next_page_url)

        prev_prev_rev = revision_history_log_test[2*per_page]['id']
        prev_page_url = reverse('browse-revision-log',
                                kwargs={'sha1_git': revision_id_test},
                                query_params={'per_page': per_page})
        next_page_url = reverse('browse-revision-log',
                                kwargs={'sha1_git': prev_prev_rev},
                                query_params={'revs_breadcrumb': revision_id_test + '/' + prev_rev,
                                              'per_page': per_page})

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('revision-log.html')
        self.assertContains(resp, '<tr class="swh-revision-log-entry">',
                            count=per_page)
        self.assertContains(resp, '<li><a href="%s">Newer</a></li>' %
                            escape(prev_page_url))
        self.assertContains(resp, '<li><a href="%s">Older</a></li>' %
                            escape(next_page_url))

        mock_service.lookup_revision_log.return_value = \
            revision_history_log_test[2*per_page:3*per_page+1]

        resp = self.client.get(next_page_url)

        prev_prev_prev_rev = revision_history_log_test[3*per_page]['id']
        prev_page_url = reverse('browse-revision-log',
                                kwargs={'sha1_git': prev_rev},
                                query_params={'revs_breadcrumb': revision_id_test,
                                              'per_page': per_page})
        next_page_url = reverse('browse-revision-log',
                                kwargs={'sha1_git': prev_prev_prev_rev},
                                query_params={'revs_breadcrumb': revision_id_test + '/' + prev_rev + '/' + prev_prev_rev,
                                              'per_page': per_page})

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('revision-log.html')
        self.assertContains(resp, '<tr class="swh-revision-log-entry">',
                            count=per_page)
        self.assertContains(resp, '<li><a href="%s">Newer</a></li>' %
                            escape(prev_page_url))
        self.assertContains(resp, '<li><a href="%s">Older</a></li>' %
                            escape(next_page_url))

        mock_service.lookup_revision_log.return_value = \
            revision_history_log_test[3*per_page:3*per_page+per_page//2]

        resp = self.client.get(next_page_url)

        prev_page_url = reverse('browse-revision-log',
                                kwargs={'sha1_git': prev_prev_rev},
                                query_params={'revs_breadcrumb': revision_id_test + '/' + prev_rev,
                                              'per_page': per_page})

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('revision-log.html')
        self.assertContains(resp, '<tr class="swh-revision-log-entry">',
                            count=per_page//2)
        self.assertContains(resp, '<li class="disabled"><a>Older</a></li>')
        self.assertContains(resp, '<li><a href="%s">Newer</a></li>' %
                            escape(prev_page_url))

    @patch('swh.web.browse.utils.service')
    @patch('swh.web.browse.views.revision.service')
    @istest
    def revision_request_errors(self, mock_service, mock_utils_service):
        mock_service.lookup_revision.side_effect = \
            NotFoundExc('Revision not found')
        url = reverse('browse-revision',
                      kwargs={'sha1_git': revision_id_test})
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'Revision not found', status_code=404)

        mock_service.lookup_revision_log.side_effect = \
            NotFoundExc('Revision not found')
        url = reverse('browse-revision-log',
                      kwargs={'sha1_git': revision_id_test})
        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'Revision not found', status_code=404)

        url = reverse('browse-revision',
                      kwargs={'sha1_git': revision_id_test},
                      query_params={'origin_type': 'git',
                                    'origin_url': 'https://github.com/foo/bar'})

        mock_service.lookup_revision.side_effect = None
        mock_utils_service.lookup_origin.side_effect = \
            NotFoundExc('Origin not found')

        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'Origin not found', status_code=404)
