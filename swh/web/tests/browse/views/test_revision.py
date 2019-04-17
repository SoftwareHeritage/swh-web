# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.utils.html import escape
from hypothesis import given

from swh.web.common.utils import (
    reverse, format_utc_iso_date, get_swh_persistent_id,
    parse_timestamp
)
from swh.web.tests.strategies import (
    origin, revision, unknown_revision, new_origin
)
from swh.web.tests.testcase import WebTestCase


class SwhBrowseRevisionTest(WebTestCase):

    @given(revision())
    def test_revision_browse(self, revision):

        url = reverse('browse-revision',
                      url_args={'sha1_git': revision})

        revision_data = self.revision_get(revision)

        author_id = revision_data['author']['id']
        author_name = revision_data['author']['name']
        committer_id = revision_data['committer']['id']
        committer_name = revision_data['committer']['name']
        dir_id = revision_data['directory']

        author_url = reverse('browse-person',
                             url_args={'person_id': author_id})
        committer_url = reverse('browse-person',
                                url_args={'person_id': committer_id})

        directory_url = reverse('browse-directory',
                                url_args={'sha1_git': dir_id})

        history_url = reverse('browse-revision-log',
                              url_args={'sha1_git': revision})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/revision.html')
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (author_url, author_name))
        self.assertContains(resp, '<a href="%s">%s</a>' %
                                  (committer_url, committer_name))
        self.assertContains(resp, directory_url)
        self.assertContains(resp, history_url)

        for parent in revision_data['parents']:
            parent_url = reverse('browse-revision',
                                 url_args={'sha1_git': parent})
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (parent_url, parent))

        author_date = revision_data['date']
        committer_date = revision_data['committer_date']

        message_lines = revision_data['message'].split('\n')

        self.assertContains(resp, format_utc_iso_date(author_date))
        self.assertContains(resp, format_utc_iso_date(committer_date))
        self.assertContains(resp, escape(message_lines[0]))
        self.assertContains(resp, escape('\n'.join(message_lines[1:])))

    @given(origin())
    def test_revision_origin_browse(self, origin):

        snapshot = self.snapshot_get_latest(origin['id'])
        revision = snapshot['branches']['HEAD']['target']
        revision_data = self.revision_get(revision)
        dir_id = revision_data['directory']

        origin_revision_log_url = reverse('browse-origin-log',
                                          url_args={'origin_url': origin['url']}, # noqa
                                          query_params={'revision': revision})

        url = reverse('browse-revision',
                      url_args={'sha1_git': revision},
                      query_params={'origin': origin['url']})

        resp = self.client.get(url)

        self.assertContains(resp, origin_revision_log_url)

        for parent in revision_data['parents']:
            parent_url = reverse('browse-revision',
                                 url_args={'sha1_git': parent},
                                 query_params={'origin': origin['url']})
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (parent_url, parent))

        self.assertContains(resp, 'vault-cook-directory')
        self.assertContains(resp, 'vault-cook-revision')

        swh_rev_id = get_swh_persistent_id('revision', revision)
        swh_rev_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_rev_id})
        self.assertContains(resp, swh_rev_id)
        self.assertContains(resp, swh_rev_id_url)

        swh_dir_id = get_swh_persistent_id('directory', dir_id)
        swh_dir_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_dir_id})
        self.assertContains(resp, swh_dir_id)
        self.assertContains(resp, swh_dir_id_url)

        self.assertContains(resp, 'swh-take-new-snapshot')

    @given(revision())
    def test_revision_log_browse(self, revision):
        per_page = 10

        revision_log = self.revision_log(revision)

        revision_log_sorted = \
            sorted(revision_log,
                   key=lambda rev: -parse_timestamp(
                       rev['committer_date']).timestamp())

        url = reverse('browse-revision-log',
                      url_args={'sha1_git': revision},
                      query_params={'per_page': per_page})

        resp = self.client.get(url)

        next_page_url = reverse('browse-revision-log',
                                url_args={'sha1_git': revision},
                                query_params={'offset': per_page,
                                              'per_page': per_page})

        nb_log_entries = per_page
        if len(revision_log_sorted) < per_page:
            nb_log_entries = len(revision_log_sorted)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/revision-log.html')
        self.assertContains(resp, '<tr class="swh-revision-log-entry',
                            count=nb_log_entries)
        self.assertContains(resp, '<a class="page-link">Newer</a>')

        if len(revision_log_sorted) > per_page:
            self.assertContains(resp, '<a class="page-link" href="%s">Older</a>' % # noqa
                                escape(next_page_url))

        for log in revision_log_sorted[:per_page]:
            revision_url = reverse('browse-revision',
                                   url_args={'sha1_git': log['id']})
            self.assertContains(resp, log['id'][:7])
            self.assertContains(resp, log['author']['name'])
            self.assertContains(resp, format_utc_iso_date(log['date']))
            self.assertContains(resp, escape(log['message']))
            self.assertContains(resp, format_utc_iso_date(log['committer_date'])) # noqa
            self.assertContains(resp, revision_url)

        if len(revision_log_sorted) <= per_page:
            return

        resp = self.client.get(next_page_url)

        prev_page_url = reverse('browse-revision-log',
                                url_args={'sha1_git': revision},
                                query_params={'per_page': per_page})
        next_page_url = reverse('browse-revision-log',
                                url_args={'sha1_git': revision},
                                query_params={'offset': 2 * per_page,
                                              'per_page': per_page})

        nb_log_entries = len(revision_log_sorted) - per_page
        if nb_log_entries > per_page:
            nb_log_entries = per_page

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/revision-log.html')
        self.assertContains(resp, '<tr class="swh-revision-log-entry',
                            count=nb_log_entries)

        self.assertContains(resp, '<a class="page-link" href="%s">Newer</a>' %
                            escape(prev_page_url))

        if len(revision_log_sorted) > 2 * per_page:
            self.assertContains(resp, '<a class="page-link" href="%s">Older</a>' % # noqa
                                escape(next_page_url))

        if len(revision_log_sorted) <= 2 * per_page:
            return

        resp = self.client.get(next_page_url)

        prev_page_url = reverse('browse-revision-log',
                                url_args={'sha1_git': revision},
                                query_params={'offset': per_page,
                                              'per_page': per_page})
        next_page_url = reverse('browse-revision-log',
                                url_args={'sha1_git': revision},
                                query_params={'offset': 3 * per_page,
                                              'per_page': per_page})

        nb_log_entries = len(revision_log_sorted) - 2 * per_page
        if nb_log_entries > per_page:
            nb_log_entries = per_page

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/revision-log.html')
        self.assertContains(resp, '<tr class="swh-revision-log-entry',
                            count=nb_log_entries)
        self.assertContains(resp, '<a class="page-link" href="%s">Newer</a>' %
                            escape(prev_page_url))

        if len(revision_log_sorted) > 3 * per_page:
            self.assertContains(resp, '<a class="page-link" href="%s">Older</a>' % # noqa
                                escape(next_page_url))

    @given(revision(), unknown_revision(), new_origin())
    def test_revision_request_errors(self, revision, unknown_revision,
                                     new_origin):

        url = reverse('browse-revision',
                      url_args={'sha1_git': unknown_revision})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp,
                            'Revision with sha1_git %s not found' %
                            unknown_revision, status_code=404)

        url = reverse('browse-revision',
                      url_args={'sha1_git': revision},
                      query_params={'origin_type': new_origin['type'],
                                    'origin': new_origin['url']})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')
        self.assertContains(resp, 'the origin mentioned in your request'
                                  ' appears broken', status_code=404)

    @given(revision())
    def test_revision_uppercase(self, revision):
        url = reverse('browse-revision-uppercase-checksum',
                      url_args={'sha1_git': revision.upper()})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        redirect_url = reverse('browse-revision',
                               url_args={'sha1_git': revision})

        self.assertEqual(resp['location'], redirect_url)
