# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from hypothesis import given
from rest_framework.test import APITestCase

from swh.web.common.utils import reverse
from swh.web.tests.strategies import (
    content, unknown_content, contents_with_ctags
)
from swh.web.tests.testcase import (
    WebTestCase, ctags_json_missing, fossology_missing
)


class ContentApiTestCase(WebTestCase, APITestCase):

    @given(content())
    def test_api_content_filetype(self, content):

        self.content_add_mimetype(content['sha1'])
        url = reverse('api-content-filetype',
                      url_args={'q': 'sha1_git:%s' % content['sha1_git']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        content_url = reverse('api-content',
                              url_args={'q': 'sha1:%s' % content['sha1']})
        expected_data = self.content_get_mimetype(content['sha1'])
        expected_data['content_url'] = content_url
        self.assertEqual(rv.data, expected_data)

    @given(unknown_content())
    def test_api_content_filetype_sha_not_found(self, unknown_content):

        url = reverse('api-content-filetype',
                      url_args={'q': 'sha1:%s' % unknown_content['sha1']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'No filetype information found for content '
            'sha1:%s.' % unknown_content['sha1']
        })

    @given(content())
    def test_api_content_language(self, content):

        self.content_add_language(content['sha1'])
        url = reverse('api-content-language',
                      url_args={'q': 'sha1_git:%s' % content['sha1_git']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        content_url = reverse('api-content',
                              url_args={'q': 'sha1:%s' % content['sha1']})
        expected_data = self.content_get_language(content['sha1'])
        expected_data['content_url'] = content_url
        self.assertEqual(rv.data, expected_data)

    @given(unknown_content())
    def test_api_content_language_sha_not_found(self, unknown_content):

        url = reverse('api-content-language',
                      url_args={'q': 'sha1:%s' % unknown_content['sha1']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'No language information found for content '
            'sha1:%s.' % unknown_content['sha1']
        })

    @pytest.mark.skipif(ctags_json_missing,
                        reason="requires ctags with json output support")
    @given(contents_with_ctags())
    def test_api_content_symbol(self, contents_with_ctags):

        expected_data = {}
        for content_sha1 in contents_with_ctags['sha1s']:
            self.content_add_ctags(content_sha1)
            for ctag in self.content_get_ctags(content_sha1):
                if ctag['name'] == contents_with_ctags['symbol_name']:
                    expected_data[content_sha1] = ctag
                    break
        url = reverse('api-content-symbol',
                      url_args={'q': contents_with_ctags['symbol_name']},
                      query_params={'per_page': 100})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        for entry in rv.data:
            content_sha1 = entry['sha1']
            expected_entry = expected_data[content_sha1]
            for key, view_name in (('content_url', 'api-content'),
                                   ('data_url', 'api-content-raw'),
                                   ('license_url', 'api-content-license'),
                                   ('language_url', 'api-content-language'),
                                   ('filetype_url', 'api-content-filetype')):
                expected_entry[key] = reverse(view_name,
                                              url_args={'q': 'sha1:%s' %
                                                        content_sha1})
            expected_entry['sha1'] = content_sha1
            del expected_entry['id']
            self.assertEqual(entry, expected_entry)
        self.assertFalse('Link' in rv)

        url = reverse('api-content-symbol',
                      url_args={'q': contents_with_ctags['symbol_name']},
                      query_params={'per_page': 2})
        rv = self.client.get(url)

        next_url = reverse('api-content-symbol',
                           url_args={'q': contents_with_ctags['symbol_name']},
                           query_params={'last_sha1': rv.data[1]['sha1'],
                                         'per_page': 2})
        self.assertEqual(rv['Link'], '<%s>; rel="next"' % next_url)

    @pytest.mark.xfail(reason='FIXME: exception should be raised in service')
    @given(unknown_content())
    def test_api_content_symbol_not_found(self, unknown_content):

        url = reverse('api-content-symbol', url_args={'q': 'bar'},
                      query_params={'last_sha1': 'hash'})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'No indexed raw content match expression \'bar\'.'
        })
        self.assertFalse('Link' in rv)

    @pytest.mark.skipif(ctags_json_missing,
                        reason="requires ctags with json output support")
    @given(content())
    def test_api_content_ctags(self, content):

        self.content_add_ctags(content['sha1'])
        url = reverse('api-content-ctags',
                      url_args={'q': 'sha1_git:%s' % content['sha1_git']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        content_url = reverse('api-content',
                              url_args={'q': 'sha1:%s' % content['sha1']})
        expected_data = list(self.content_get_ctags(content['sha1']))
        for e in expected_data:
            e['content_url'] = content_url
        self.assertEqual(rv.data, expected_data)

    @pytest.mark.skipif(fossology_missing,
                        reason="requires fossology-nomossa installed")
    @given(content())
    def test_api_content_license(self, content):

        self.content_add_license(content['sha1'])
        url = reverse('api-content-license',
                      url_args={'q': 'sha1_git:%s' % content['sha1_git']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        content_url = reverse('api-content',
                              url_args={'q': 'sha1:%s' % content['sha1']})
        expected_data = self.content_get_license(content['sha1'])
        expected_data['content_url'] = content_url
        self.assertEqual(rv.data, expected_data)

    @given(unknown_content())
    def test_api_content_license_sha_not_found(self, unknown_content):

        url = reverse('api-content-license',
                      url_args={'q': 'sha1:%s' % unknown_content['sha1']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'No license information found for content '
            'sha1:%s.' % unknown_content['sha1']
        })

    @given(content())
    def test_api_content_metadata(self, content):

        url = reverse('api-content', {'q': 'sha1:%s' % content['sha1']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        expected_data = self.content_get_metadata(content['sha1'])
        for key, view_name in (('data_url', 'api-content-raw'),
                               ('license_url', 'api-content-license'),
                               ('language_url', 'api-content-language'),
                               ('filetype_url', 'api-content-filetype')):
            expected_data[key] = reverse(view_name,
                                         url_args={'q': 'sha1:%s' %
                                                   content['sha1']})
        self.assertEqual(rv.data, expected_data)

    @given(unknown_content())
    def test_api_content_not_found_as_json(self, unknown_content):

        url = reverse('api-content',
                      url_args={'q': 'sha1:%s' % unknown_content['sha1']})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Content with sha1 checksum equals to %s not found!'
            % unknown_content['sha1']
        })

    @given(unknown_content())
    def test_api_content_not_found_as_yaml(self, unknown_content):

        url = reverse('api-content',
                      url_args={'q': 'sha256:%s' % unknown_content['sha256']})
        rv = self.client.get(url, HTTP_ACCEPT='application/yaml')

        self.assertEqual(rv.status_code, 404)
        self.assertTrue('application/yaml' in rv['Content-Type'])

        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Content with sha256 checksum equals to %s not found!' %
            unknown_content['sha256']
        })

    @given(unknown_content())
    def test_api_content_raw_ko_not_found(self, unknown_content):

        url = reverse('api-content-raw',
                      url_args={'q': 'sha1:%s' % unknown_content['sha1']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Content with sha1 checksum equals to %s not found!' %
            unknown_content['sha1']
        })

    @given(content())
    def test_api_content_raw_text(self, content):

        url = reverse('api-content-raw',
                      url_args={'q': 'sha1:%s' % content['sha1']})

        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/octet-stream')
        self.assertEqual(
            rv['Content-disposition'],
            'attachment; filename=content_sha1_%s_raw' % content['sha1'])
        self.assertEqual(
            rv['Content-Type'], 'application/octet-stream')
        expected_data = self.content_get(content['sha1'])
        self.assertEqual(rv.content, expected_data['data'])

    @given(content())
    def test_api_content_raw_text_with_filename(self, content):

        url = reverse('api-content-raw',
                      url_args={'q': 'sha1:%s' % content['sha1']},
                      query_params={'filename': 'filename.txt'})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/octet-stream')
        self.assertEqual(
            rv['Content-disposition'],
            'attachment; filename=filename.txt')
        self.assertEqual(
            rv['Content-Type'], 'application/octet-stream')
        expected_data = self.content_get(content['sha1'])
        self.assertEqual(rv.content, expected_data['data'])

    @given(content())
    def test_api_check_content_known(self, content):

        url = reverse('api-content-known',
                      url_args={'q': content['sha1']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')

        self.assertEqual(rv.data, {
            'search_res': [
                {
                    'found': True,
                    'sha1': content['sha1']
                }
            ],
            'search_stats': {'nbfiles': 1, 'pct': 100.0}
        })

    @given(content())
    def test_api_check_content_known_as_yaml(self, content):

        url = reverse('api-content-known',
                      url_args={'q': content['sha1']})
        rv = self.client.get(url, HTTP_ACCEPT='application/yaml')

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/yaml')

        self.assertEqual(rv.data, {
            'search_res': [
                {
                    'found': True,
                    'sha1': content['sha1']
                }
            ],
            'search_stats': {'nbfiles': 1, 'pct': 100.0}
        })

    @given(content())
    def test_api_check_content_known_post_as_yaml(self, content):

        url = reverse('api-content-known')
        rv = self.client.post(
            url,
            data={
                'q': content['sha1']
            },
            HTTP_ACCEPT='application/yaml'
        )

        self.assertEqual(rv.status_code, 200)
        self.assertTrue('application/yaml' in rv['Content-Type'])
        self.assertEqual(rv.data, {
            'search_res': [
                {
                    'found': True,
                    'sha1': content['sha1']
                }
            ],
            'search_stats': {'nbfiles': 1, 'pct': 100.0}
        })

    @given(unknown_content())
    def test_api_check_content_known_not_found(self, unknown_content):

        url = reverse('api-content-known',
                      url_args={'q': unknown_content['sha1']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'search_res': [
                {
                    'found': False,
                    'sha1': unknown_content['sha1']
                }
            ],
            'search_stats': {'nbfiles': 1, 'pct': 0.0}
        })
