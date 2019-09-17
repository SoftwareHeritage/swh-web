# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given
from rest_framework.test import APITestCase
from unittest.mock import patch

from swh.web.common.exc import NotFoundExc

from swh.web.common.utils import reverse
from swh.web.tests.data import random_sha1
from swh.web.tests.strategies import revision
from swh.web.tests.testcase import WebTestCase


class RevisionApiTestCase(WebTestCase, APITestCase):

    @given(revision())
    def test_api_revision(self, revision):

        url = reverse('api-1-revision', url_args={'sha1_git': revision})
        rv = self.client.get(url)

        expected_revision = self.revision_get(revision)

        self._enrich_revision(expected_revision)

        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_revision)

    def test_api_revision_not_found(self):
        unknown_revision_ = random_sha1()

        url = reverse('api-1-revision',
                      url_args={'sha1_git': unknown_revision_})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Revision with sha1_git %s not found.' %
            unknown_revision_})

    @given(revision())
    def test_api_revision_raw_ok(self, revision):

        url = reverse('api-1-revision-raw-message',
                      url_args={'sha1_git': revision})
        rv = self.client.get(url)

        expected_message = self.revision_get(revision)['message']

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/octet-stream')
        self.assertEqual(rv.content, expected_message.encode())

    def test_api_revision_raw_ko_no_rev(self):
        unknown_revision_ = random_sha1()

        url = reverse('api-1-revision-raw-message',
                      url_args={'sha1_git': unknown_revision_})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Revision with sha1_git %s not found.' %
            unknown_revision_})

    @given(revision())
    def test_api_revision_log(self, revision):

        per_page = 10

        url = reverse('api-1-revision-log', url_args={'sha1_git': revision},
                      query_params={'per_page': per_page})

        rv = self.client.get(url)

        expected_log = self.revision_log(revision, limit=per_page+1)
        expected_log = list(map(self._enrich_revision, expected_log))

        has_next = len(expected_log) > per_page

        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data,
                         expected_log[:-1] if has_next else expected_log)

        if has_next:
            self.assertIn('Link', rv)
            next_log_url = reverse(
                'api-1-revision-log',
                url_args={'sha1_git': expected_log[-1]['id']},
                query_params={'per_page': per_page})
            self.assertIn(next_log_url, rv['Link'])

    def test_api_revision_log_not_found(self):
        unknown_revision_ = random_sha1()

        url = reverse('api-1-revision-log',
                      url_args={'sha1_git': unknown_revision_})

        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Revision with sha1_git %s not found.' %
            unknown_revision_})
        self.assertFalse(rv.has_header('Link'))

    @given(revision())
    def test_api_revision_log_context(self, revision):

        revisions = self.revision_log(revision, limit=4)

        prev_rev = revisions[0]['id']
        rev = revisions[-1]['id']

        per_page = 10

        url = reverse('api-1-revision-log',
                      url_args={'sha1_git': rev,
                                'prev_sha1s': prev_rev},
                      query_params={'per_page': per_page})

        rv = self.client.get(url)

        expected_log = self.revision_log(rev, limit=per_page)
        prev_revision = self.revision_get(prev_rev)
        expected_log.insert(0, prev_revision)
        expected_log = list(map(self._enrich_revision, expected_log))

        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_log)

    @patch('swh.web.api.views.revision._revision_directory_by')
    def test_api_revision_directory_ko_not_found(self, mock_rev_dir):
        # given
        mock_rev_dir.side_effect = NotFoundExc('Not found')

        # then
        rv = self.client.get('/api/1/revision/999/directory/some/path/to/dir/')

        self.assertEqual(rv.status_code, 404, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Not found'})

        mock_rev_dir.assert_called_once_with(
            {'sha1_git': '999'},
            'some/path/to/dir',
            '/api/1/revision/999/directory/some/path/to/dir/',
            with_data=False)

    @patch('swh.web.api.views.revision._revision_directory_by')
    def test_api_revision_directory_ok_returns_dir_entries(self, mock_rev_dir):
        stub_dir = {
            'type': 'dir',
            'revision': '999',
            'content': [
                {
                    'sha1_git': '789',
                    'type': 'file',
                    'target': '101',
                    'target_url': '/api/1/content/sha1_git:101/',
                    'name': 'somefile',
                    'file_url': '/api/1/revision/999/directory/some/path/'
                    'somefile/'
                },
                {
                    'sha1_git': '123',
                    'type': 'dir',
                    'target': '456',
                    'target_url': '/api/1/directory/456/',
                    'name': 'to-subdir',
                    'dir_url': '/api/1/revision/999/directory/some/path/'
                    'to-subdir/',
                }]
        }

        # given
        mock_rev_dir.return_value = stub_dir

        # then
        rv = self.client.get('/api/1/revision/999/directory/some/path/')

        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, stub_dir)

        mock_rev_dir.assert_called_once_with(
            {'sha1_git': '999'},
            'some/path',
            '/api/1/revision/999/directory/some/path/',
            with_data=False)

    @patch('swh.web.api.views.revision._revision_directory_by')
    def test_api_revision_directory_ok_returns_content(self, mock_rev_dir):
        stub_content = {
            'type': 'file',
            'revision': '999',
            'content': {
                'sha1_git': '789',
                'sha1': '101',
                'data_url': '/api/1/content/101/raw/',
            }
        }

        # given
        mock_rev_dir.return_value = stub_content

        # then
        url = '/api/1/revision/666/directory/some/other/path/'
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, stub_content)

        mock_rev_dir.assert_called_once_with(
            {'sha1_git': '666'}, 'some/other/path', url, with_data=False)

    def _enrich_revision(self, revision):
        directory_url = reverse(
            'api-1-directory',
            url_args={'sha1_git': revision['directory']})

        history_url = reverse('api-1-revision-log',
                              url_args={'sha1_git': revision['id']})

        parents_id_url = []
        for p in revision['parents']:
            parents_id_url.append({
                'id': p,
                'url': reverse('api-1-revision', url_args={'sha1_git': p})
            })

        revision_url = reverse('api-1-revision',
                               url_args={'sha1_git': revision['id']})

        revision['directory_url'] = directory_url
        revision['history_url'] = history_url
        revision['url'] = revision_url
        revision['parents'] = parents_id_url

        return revision

    @given(revision())
    def test_api_revision_uppercase(self, revision):
        url = reverse('api-1-revision-uppercase-checksum',
                      url_args={'sha1_git': revision.upper()})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        redirect_url = reverse('api-1-revision',
                               url_args={'sha1_git': revision})

        self.assertEqual(resp['location'], redirect_url)
