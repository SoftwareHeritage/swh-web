# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from unittest.mock import patch

from django.utils.html import escape

from hypothesis import given

from swh.web.browse.utils import (
    get_mimetype_and_encoding_for_content, prepare_content_for_display,
    _reencode_content
)
from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import reverse, get_swh_persistent_id
from swh.web.common.utils import gen_path_info
from swh.web.tests.strategies import (
    content, content_text_non_utf8, content_text_no_highlight,
    content_image_type, content_text, invalid_sha1, unknown_content
)
from swh.web.tests.testcase import WebTestCase


class SwhBrowseContentTest(WebTestCase):

    @given(content())
    def test_content_view_text(self, content):

        sha1_git = content['sha1_git']

        url = reverse('browse-content',
                      url_args={'query_string': content['sha1']},
                      query_params={'path': content['path']})

        url_raw = reverse('browse-content-raw',
                          url_args={'query_string': content['sha1']})

        resp = self.client.get(url)

        content_display = self._process_content_for_display(content)
        mimetype = content_display['mimetype']

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')

        if mimetype.startswith('text/'):
            self.assertContains(resp, '<code class="%s">' %
                                      content_display['language'])
            self.assertContains(resp, escape(content_display['content_data']))
        self.assertContains(resp, url_raw)

        swh_cnt_id = get_swh_persistent_id('content', sha1_git)
        swh_cnt_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_cnt_id})
        self.assertContains(resp, swh_cnt_id)
        self.assertContains(resp, swh_cnt_id_url)

    @given(content_text_no_highlight())
    def test_content_view_text_no_highlight(self, content):

        sha1_git = content['sha1_git']

        url = reverse('browse-content',
                      url_args={'query_string': content['sha1']})

        url_raw = reverse('browse-content-raw',
                          url_args={'query_string': content['sha1']})

        resp = self.client.get(url)

        content_display = self._process_content_for_display(content)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')

        self.assertContains(resp, '<code class="nohighlight">')
        self.assertContains(resp, escape(content_display['content_data'])) # noqa
        self.assertContains(resp, url_raw)

        swh_cnt_id = get_swh_persistent_id('content', sha1_git)
        swh_cnt_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_cnt_id})

        self.assertContains(resp, swh_cnt_id)
        self.assertContains(resp, swh_cnt_id_url)

    @given(content_text_non_utf8())
    def test_content_view_no_utf8_text(self, content):

        sha1_git = content['sha1_git']

        url = reverse('browse-content',
                      url_args={'query_string': content['sha1']})

        resp = self.client.get(url)

        content_display = self._process_content_for_display(content)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')
        swh_cnt_id = get_swh_persistent_id('content', sha1_git)
        swh_cnt_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_cnt_id})
        self.assertContains(resp, swh_cnt_id_url)
        self.assertContains(resp, escape(content_display['content_data']))

    @given(content_image_type())
    def test_content_view_image(self, content):

        url = reverse('browse-content',
                      url_args={'query_string': content['sha1']})

        url_raw = reverse('browse-content-raw',
                          url_args={'query_string': content['sha1']})

        resp = self.client.get(url)

        content_display = self._process_content_for_display(content)
        mimetype = content_display['mimetype']
        content_data = content_display['content_data']

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')

        self.assertContains(resp, '<img src="data:%s;base64,%s"/>'
                                  % (mimetype, content_data.decode('utf-8')))
        self.assertContains(resp, url_raw)

    @given(content())
    def test_content_view_with_path(self, content):

        path = content['path']

        url = reverse('browse-content',
                      url_args={'query_string': content['sha1']},
                      query_params={'path': path})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')

        self.assertContains(resp, '<nav class="bread-crumbs')

        content_display = self._process_content_for_display(content)
        mimetype = content_display['mimetype']

        if mimetype.startswith('text/'):
            hljs_language = content['hljs_language']
            self.assertContains(resp, '<code class="%s">' % hljs_language)
            self.assertContains(resp, escape(content_display['content_data']))

        split_path = path.split('/')

        root_dir_sha1 = split_path[0]
        filename = split_path[-1]
        path = path.replace(root_dir_sha1 + '/', '').replace(filename, '')

        path_info = gen_path_info(path)

        root_dir_url = reverse('browse-directory',
                               url_args={'sha1_git': root_dir_sha1})

        self.assertContains(resp, '<li class="swh-path">',
                            count=len(path_info)+1)

        self.assertContains(resp, '<a href="' + root_dir_url + '">' +
                            root_dir_sha1[:7] + '</a>')

        for p in path_info:
            dir_url = reverse('browse-directory',
                              url_args={'sha1_git': root_dir_sha1,
                                        'path': p['path']})
            self.assertContains(resp, '<a href="' + dir_url + '">' +
                                p['name'] + '</a>')

        self.assertContains(resp, '<li>' + filename + '</li>')

        url_raw = reverse('browse-content-raw',
                          url_args={'query_string': content['sha1']},
                          query_params={'filename': filename})
        self.assertContains(resp, url_raw)

        url = reverse('browse-content',
                      url_args={'query_string': content['sha1']},
                      query_params={'path': filename})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')

        self.assertNotContains(resp, '<nav class="bread-crumbs')

    @given(content_text())
    def test_content_raw_text(self, content):

        url = reverse('browse-content-raw',
                      url_args={'query_string': content['sha1']})

        resp = self.client.get(url)

        content_data = self.content_get(content['sha1'])['data']

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/plain')
        self.assertEqual(resp['Content-disposition'],
                         'filename=%s_%s' % ('sha1', content['sha1']))
        self.assertEqual(resp.content, content_data)

        filename = content['path'].split('/')[-1]

        url = reverse('browse-content-raw',
                      url_args={'query_string': content['sha1']}, # noqa
                      query_params={'filename': filename})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/plain')
        self.assertEqual(resp['Content-disposition'],
                         'filename=%s' % filename)
        self.assertEqual(resp.content, content_data)

    @given(content_text_non_utf8())
    def test_content_raw_no_utf8_text(self, content):

        url = reverse('browse-content-raw',
                      url_args={'query_string': content['sha1']})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        _, encoding = get_mimetype_and_encoding_for_content(resp.content)
        self.assertEqual(encoding, content['encoding'])

    @given(content_image_type())
    def test_content_raw_bin(self, content):

        url = reverse('browse-content-raw',
                      url_args={'query_string': content['sha1']})

        resp = self.client.get(url)

        filename = content['path'].split('/')[-1]
        content_data = self.content_get(content['sha1'])['data']

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/octet-stream')
        self.assertEqual(resp['Content-disposition'],
                         'attachment; filename=%s_%s' %
                         ('sha1', content['sha1']))
        self.assertEqual(resp.content, content_data)

        url = reverse('browse-content-raw',
                      url_args={'query_string': content['sha1']},
                      query_params={'filename': filename})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/octet-stream')
        self.assertEqual(resp['Content-disposition'],
                         'attachment; filename=%s' % filename)
        self.assertEqual(resp.content, content_data)

    @given(invalid_sha1(), unknown_content())
    def test_content_request_errors(self, invalid_sha1, unknown_content):

        url = reverse('browse-content',
                      url_args={'query_string': invalid_sha1})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 400)
        self.assertTemplateUsed('error.html')

        url = reverse('browse-content',
                      url_args={'query_string': unknown_content['sha1']})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')

    @patch('swh.web.browse.utils.service')
    @given(content())
    def test_content_bytes_missing(self, mock_service, content):

        content_data = self.content_get_metadata(content['sha1'])
        content_data['data'] = None

        mock_service.lookup_content.return_value = content_data
        mock_service.lookup_content_raw.side_effect = NotFoundExc(
            'Content bytes not available!')

        url = reverse('browse-content',
                      url_args={'query_string': content['sha1']})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('browse/content.html')

    @patch('swh.web.browse.views.content.request_content')
    def test_content_too_large(self, mock_request_content):
        stub_content_too_large_data = {
            'checksums': {
                'sha1': '8624bcdae55baeef00cd11d5dfcfa60f68710a02',
                'sha1_git': '94a9ed024d3859793618152ea559a168bbcbb5e2',
                'sha256': ('8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b16'
                           '5a1dcd80c7c545eb65b903'),
                'blake2s256': ('38702b7168c7785bfe748b51b45d9856070ba90'
                               'f9dc6d90f2ea75d4356411ffe')
            },
            'length': 30000000,
            'raw_data': None,
            'mimetype': 'text/plain',
            'encoding': 'us-ascii',
            'language': 'not detected',
            'licenses': 'GPL',
            'error_code': 200,
            'error_message': '',
            'error_description': ''
        }

        content_sha1 = stub_content_too_large_data['checksums']['sha1']

        mock_request_content.return_value = stub_content_too_large_data

        url = reverse('browse-content',
                      url_args={'query_string': content_sha1})

        url_raw = reverse('browse-content-raw',
                          url_args={'query_string': content_sha1})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')

        self.assertContains(resp, 'Content is too large to be displayed')
        self.assertContains(resp, url_raw)

    def _process_content_for_display(self, content):
        content_data = self.content_get(content['sha1'])

        mime_type, encoding = get_mimetype_and_encoding_for_content(
            content_data['data'])

        mime_type, content_data = _reencode_content(mime_type, encoding,
                                                    content_data['data'])

        return prepare_content_for_display(content_data, mime_type,
                                           content['path'])

    @given(content())
    def test_content_uppercase(self, content):
        url = reverse('browse-content-uppercase-checksum',
                      url_args={'query_string': content['sha1'].upper()})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)

        redirect_url = reverse('browse-content',
                               url_args={'query_string': content['sha1']})

        self.assertEqual(resp['location'], redirect_url)
