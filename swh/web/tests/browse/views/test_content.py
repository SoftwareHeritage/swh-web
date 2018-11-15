# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import base64

from unittest.mock import patch

from django.utils.html import escape
from django.utils.encoding import DjangoUnicodeDecodeError

from swh.web.browse.utils import get_mimetype_and_encoding_for_content
from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import reverse, get_swh_persistent_id
from swh.web.common.utils import gen_path_info
from swh.web.tests.testcase import SWHWebTestCase

from .data.content_test_data import (
    stub_content_text_data,
    stub_content_text_path_with_root_dir,
    stub_content_bin_data,
    stub_content_bin_filename,
    stub_content_text_no_highlight_data,
    non_utf8_encoded_content_data,
    non_utf8_encoded_content,
    non_utf8_encoding,
    stub_content_too_large_data
)


class SwhBrowseContentTest(SWHWebTestCase):

    @patch('swh.web.browse.views.content.request_content')
    def test_content_view_text(self, mock_request_content):
        mock_request_content.return_value = stub_content_text_data

        sha1_git = stub_content_text_data['checksums']['sha1_git']

        url = reverse('browse-content',
                      url_args={'query_string': stub_content_text_data['checksums']['sha1']}) # noqa

        url_raw = reverse('browse-content-raw',
                          url_args={'query_string': stub_content_text_data['checksums']['sha1']}) # noqa

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')

        self.assertContains(resp, '<code class="cpp">')
        self.assertContains(resp, escape(stub_content_text_data['raw_data']))
        self.assertContains(resp, url_raw)

        swh_cnt_id = get_swh_persistent_id('content', sha1_git)
        swh_cnt_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_cnt_id})
        self.assertContains(resp, swh_cnt_id)
        self.assertContains(resp, swh_cnt_id_url)

    @patch('swh.web.browse.views.content.request_content')
    def test_content_view_text_no_highlight(self, mock_request_content):
        mock_request_content.return_value = stub_content_text_no_highlight_data

        sha1_git = stub_content_text_no_highlight_data['checksums']['sha1_git']

        url = reverse('browse-content',
                      url_args={'query_string': stub_content_text_no_highlight_data['checksums']['sha1']}) # noqa

        url_raw = reverse('browse-content-raw',
                          url_args={'query_string': stub_content_text_no_highlight_data['checksums']['sha1']}) # noqa

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')

        self.assertContains(resp, '<code class="nohighlight">')
        self.assertContains(resp, escape(stub_content_text_no_highlight_data['raw_data'])) # noqa
        self.assertContains(resp, url_raw)

        swh_cnt_id = get_swh_persistent_id('content', sha1_git)
        swh_cnt_id_url = reverse('browse-swh-id',
                                 url_args={'swh_id': swh_cnt_id})

        self.assertContains(resp, swh_cnt_id)
        self.assertContains(resp, swh_cnt_id_url)

    @patch('swh.web.browse.utils.service')
    def test_content_view_no_utf8_text(self, mock_service):
        mock_service.lookup_content.return_value = \
            non_utf8_encoded_content_data

        mock_service.lookup_content_raw.return_value = \
            {'data': non_utf8_encoded_content}

        mock_service.lookup_content_filetype.return_value = None
        mock_service.lookup_content_language.return_value = None
        mock_service.lookup_content_license.return_value = None

        sha1_git = non_utf8_encoded_content_data['checksums']['sha1_git']

        url = reverse('browse-content',
                      url_args={'query_string': non_utf8_encoded_content_data['checksums']['sha1']}) # noqa

        try:
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assertTemplateUsed('browse/content.html')
            swh_cnt_id = get_swh_persistent_id('content', sha1_git)
            swh_cnt_id_url = reverse('browse-swh-id',
                                     url_args={'swh_id': swh_cnt_id})
            self.assertContains(resp, swh_cnt_id_url)
            self.assertContains(resp, escape(non_utf8_encoded_content.decode(non_utf8_encoding).encode('utf-8'))) # noqa
        except DjangoUnicodeDecodeError:
            self.fail('Textual content is not encoded in utf-8')

    @patch('swh.web.browse.views.content.request_content')
    def test_content_view_image(self, mock_request_content):

        mime_type = 'image/png'
        mock_request_content.return_value = stub_content_bin_data

        url = reverse('browse-content',
                      url_args={'query_string': stub_content_bin_data['checksums']['sha1']}) # noqa

        url_raw = reverse('browse-content-raw',
                          url_args={'query_string': stub_content_bin_data['checksums']['sha1']}) # noqa

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')

        png_encoded = base64.b64encode(stub_content_bin_data['raw_data']) \
                            .decode('utf-8')

        self.assertContains(resp, '<img src="data:%s;base64,%s"/>'
                                  % (mime_type, png_encoded))
        self.assertContains(resp, url_raw)

    @patch('swh.web.browse.views.content.request_content')
    def test_content_view_with_path(self, mock_request_content):
        mock_request_content.return_value = stub_content_text_data

        url = reverse('browse-content',
                      url_args={'query_string': stub_content_text_data['checksums']['sha1']}, # noqa
                      query_params={'path': stub_content_text_path_with_root_dir}) # noqa

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')

        self.assertContains(resp, '<nav class="bread-crumbs')
        self.assertContains(resp, '<code class="cpp">')
        self.assertContains(resp, escape(stub_content_text_data['raw_data']))

        split_path = stub_content_text_path_with_root_dir.split('/')

        root_dir_sha1 = split_path[0]
        filename = split_path[-1]
        path = stub_content_text_path_with_root_dir \
            .replace(root_dir_sha1 + '/', '') \
            .replace(filename, '')

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
                          url_args={'query_string': stub_content_text_data['checksums']['sha1']}, # noqa
                          query_params={'filename': filename})
        self.assertContains(resp, url_raw)

        url = reverse('browse-content',
                      url_args={'query_string': stub_content_text_data['checksums']['sha1']}, # noqa
                      query_params={'path': filename})

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')

        self.assertNotContains(resp, '<nav class="bread-crumbs')

    @patch('swh.web.browse.views.content.request_content')
    def test_content_raw_text(self, mock_request_content):
        mock_request_content.return_value = stub_content_text_data

        url = reverse('browse-content-raw',
                      url_args={'query_string': stub_content_text_data['checksums']['sha1']}) # noqa

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/plain')
        self.assertEqual(resp['Content-disposition'],
                         'filename=%s_%s' % ('sha1', stub_content_text_data['checksums']['sha1'])) # noqa
        self.assertEqual(resp.content, stub_content_text_data['raw_data'])

        filename = stub_content_text_path_with_root_dir.split('/')[-1]

        url = reverse('browse-content-raw',
                      url_args={'query_string': stub_content_text_data['checksums']['sha1']}, # noqa
                      query_params={'filename': filename})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/plain')
        self.assertEqual(resp['Content-disposition'],
                         'filename=%s' % filename)
        self.assertEqual(resp.content, stub_content_text_data['raw_data'])

    @patch('swh.web.browse.utils.service')
    def test_content_raw_no_utf8_text(self, mock_service):
        mock_service.lookup_content.return_value = \
            non_utf8_encoded_content_data

        mock_service.lookup_content_raw.return_value = \
            {'data': non_utf8_encoded_content}

        mock_service.lookup_content_filetype.return_value = None
        mock_service.lookup_content_language.return_value = None
        mock_service.lookup_content_license.return_value = None

        url = reverse('browse-content-raw',
                      url_args={'query_string': non_utf8_encoded_content_data['checksums']['sha1']}) # noqa

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        _, encoding = get_mimetype_and_encoding_for_content(resp.content)
        self.assertEqual(encoding, non_utf8_encoding)

    @patch('swh.web.browse.views.content.request_content')
    def test_content_raw_bin(self, mock_request_content):
        mock_request_content.return_value = stub_content_bin_data

        url = reverse('browse-content-raw',
                      url_args={'query_string': stub_content_bin_data['checksums']['sha1']}) # noqa

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/octet-stream')
        self.assertEqual(resp['Content-disposition'],
                         'attachment; filename=%s_%s' %
                         ('sha1', stub_content_bin_data['checksums']['sha1']))
        self.assertEqual(resp.content, stub_content_bin_data['raw_data'])

        url = reverse('browse-content-raw',
                      url_args={'query_string': stub_content_bin_data['checksums']['sha1']}, # noqa
                      query_params={'filename': stub_content_bin_filename})

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/octet-stream')
        self.assertEqual(resp['Content-disposition'],
                         'attachment; filename=%s' % stub_content_bin_filename)
        self.assertEqual(resp.content, stub_content_bin_data['raw_data'])

    @patch('swh.web.browse.views.content.request_content')
    def test_content_request_errors(self, mock_request_content):

        url = reverse('browse-content', url_args={'query_string': '123456'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 400)
        self.assertTemplateUsed('error.html')

        mock_request_content.side_effect = NotFoundExc('content not found')

        url = reverse('browse-content',
                      url_args={'query_string': stub_content_text_data['checksums']['sha1']}) # noqa
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('error.html')

    @patch('swh.web.browse.utils.service')
    def test_content_bytes_missing(self, mock_service):

        content_data = dict(stub_content_text_data)
        content_data['raw_data'] = None

        mock_service.lookup_content.return_value = content_data
        mock_service.lookup_content_raw.side_effect = NotFoundExc('Content bytes not available!') # noqa

        url = reverse('browse-content',
                      url_args={'query_string': content_data['checksums']['sha1']}) # noqa

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 404)
        self.assertTemplateUsed('browse/content.html')

    @patch('swh.web.browse.views.content.request_content')
    def test_content_too_large(self, mock_request_content):
        mock_request_content.return_value = stub_content_too_large_data

        url = reverse('browse-content',
                      url_args={'query_string': stub_content_too_large_data['checksums']['sha1']}) # noqa

        url_raw = reverse('browse-content-raw',
                          url_args={'query_string': stub_content_too_large_data['checksums']['sha1']}) # noqa

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed('browse/content.html')

        self.assertContains(resp, 'Content is too large to be displayed')
        self.assertContains(resp, url_raw)
