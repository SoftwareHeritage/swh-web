# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import base64

from unittest.mock import patch
from nose.tools import istest

from django.test import TestCase
from django.utils.html import escape

from swh.web.common.utils import reverse
from swh.web.browse.utils import (
    gen_path_info
)
from .data.content_test_data import (
    stub_content_text_data, stub_content_text_sha1,
    stub_content_text_path_with_root_dir,
    stub_content_bin_data,
    stub_content_bin_sha1, stub_content_bin_filename,
    stub_content_text_no_highlight_sha1,
    stub_content_text_no_highlight_data
)


class SwhBrowseContentTest(TestCase):

    @patch('swh.web.browse.views.content.request_content')
    @istest
    def content_view_text(self, mock_request_content):
        mock_request_content.return_value =\
            stub_content_text_data, 'text/x-c++'

        url = reverse('browse-content',
                      kwargs={'query_string': stub_content_text_sha1})

        url_raw = reverse('browse-content-raw',
                          kwargs={'query_string': stub_content_text_sha1})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('content.html')

        self.assertContains(resp, '<code class="cpp">')
        self.assertContains(resp, escape(stub_content_text_data))
        self.assertContains(resp, url_raw)

    @patch('swh.web.browse.views.content.request_content')
    @istest
    def content_view_text_no_highlight(self, mock_request_content):
        mock_request_content.return_value =\
            stub_content_text_no_highlight_data, 'text/plain'

        url = reverse('browse-content',
                      kwargs={'query_string': stub_content_text_no_highlight_sha1}) # noqa

        url_raw = reverse('browse-content-raw',
                          kwargs={'query_string': stub_content_text_no_highlight_sha1}) # noqa

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('content.html')

        self.assertContains(resp, '<code class="nohighlight-swh">')
        self.assertContains(resp, escape(stub_content_text_no_highlight_data)) # noqa
        self.assertContains(resp, url_raw)

    @patch('swh.web.browse.views.content.request_content')
    @istest
    def content_view_image(self, mock_request_content):

        mime_type = 'image/png'
        mock_request_content.return_value =\
            stub_content_bin_data, mime_type

        url = reverse('browse-content',
                      kwargs={'query_string': stub_content_bin_sha1})

        url_raw = reverse('browse-content-raw',
                          kwargs={'query_string': stub_content_bin_sha1})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('content.html')

        pngEncoded = base64.b64encode(stub_content_bin_data) \
                           .decode('utf-8')

        self.assertContains(resp, '<img src="data:%s;base64,%s"/>'
                                  % (mime_type, pngEncoded))
        self.assertContains(resp, url_raw)

    @patch('swh.web.browse.views.content.request_content')
    @istest
    def content_view_with_path(self, mock_request_content):
        mock_request_content.return_value =\
            stub_content_text_data, 'text/x-c++'

        url = reverse('browse-content',
                      kwargs={'query_string': stub_content_text_sha1},
                      query_params={'path': stub_content_text_path_with_root_dir}) # noqa

        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('content.html')

        self.assertContains(resp, '<code class="cpp">')
        self.assertContains(resp, escape(stub_content_text_data))

        split_path = stub_content_text_path_with_root_dir.split('/')

        root_dir_sha1 = split_path[0]
        filename = split_path[-1]
        path = stub_content_text_path_with_root_dir \
            .replace(root_dir_sha1 + '/', '') \
            .replace(filename, '')

        path_info = gen_path_info(path)

        root_dir_url = reverse('browse-directory',
                               kwargs={'sha1_git': root_dir_sha1})

        self.assertContains(resp, '<li class="swh-path">',
                            count=len(path_info)+1)

        self.assertContains(resp, '<a href="' + root_dir_url + '">' +
                            root_dir_sha1[:7] + '</a>')

        for p in path_info:
            dir_url = reverse('browse-directory',
                              kwargs={'sha1_git': root_dir_sha1,
                                      'path': p['path']})
            self.assertContains(resp, '<a href="' + dir_url + '">' +
                                p['name'] + '</a>')

        self.assertContains(resp, '<li>' + filename + '</li>')

        url_raw = reverse('browse-content-raw',
                          kwargs={'query_string': stub_content_text_sha1},
                          query_params={'filename': filename})
        self.assertContains(resp, url_raw)

    @patch('swh.web.browse.views.content.request_content')
    @istest
    def content_raw_text(self, mock_request_content):
        mock_request_content.return_value =\
            stub_content_text_data, 'text/plain'

        url = reverse('browse-content-raw',
                      kwargs={'query_string': stub_content_text_sha1})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/plain')
        self.assertEqual(resp['Content-disposition'],
                         'filename=%s_%s' % ('sha1', stub_content_text_sha1))
        self.assertEqual(resp.content, stub_content_text_data)

        filename = stub_content_text_path_with_root_dir.split('/')[-1]

        url = reverse('browse-content-raw',
                      kwargs={'query_string': stub_content_text_sha1},
                      query_params={'filename': filename})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/plain')
        self.assertEqual(resp['Content-disposition'],
                         'filename=%s' % filename)
        self.assertEqual(resp.content, stub_content_text_data)

    @patch('swh.web.browse.views.content.request_content')
    @istest
    def content_raw_bin(self, mock_request_content):
        mock_request_content.return_value =\
            stub_content_bin_data, 'image/png'

        url = reverse('browse-content-raw',
                      kwargs={'query_string': stub_content_bin_sha1})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/octet-stream')
        self.assertEqual(resp['Content-disposition'],
                         'attachment; filename=%s_%s' %
                         ('sha1', stub_content_bin_sha1))
        self.assertEqual(resp.content, stub_content_bin_data)

        url = reverse('browse-content-raw',
                      kwargs={'query_string': stub_content_bin_sha1},
                      query_params={'filename': stub_content_bin_filename})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/octet-stream')
        self.assertEqual(resp['Content-disposition'],
                         'attachment; filename=%s' % stub_content_bin_filename)
        self.assertEqual(resp.content, stub_content_bin_data)
