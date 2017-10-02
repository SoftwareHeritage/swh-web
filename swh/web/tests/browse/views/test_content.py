# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import base64

from unittest.mock import patch
from nose.tools import istest, nottest

from django.test import TestCase
from django.utils.html import escape

from swh.web.common.utils import reverse
from swh.web.browse.utils import (
    gen_path_info
)
from .data.content_test_data import (
    stub_content_root_dir,
    stub_content_text_data, stub_content_text_sha1,
    stub_content_text_path_with_root_dir,
    stub_content_text_path, stub_content_bin_data,
    stub_content_bin_sha1, stub_content_bin_filename,
    stub_content_text_no_highlight_sha1,
    stub_content_text_no_highlight_data,
    stub_content_origin_id, stub_content_origin_visit_id,
    stub_content_origin_visit_ts, stub_content_origin_branch,
    stub_content_origin_visits, stub_content_origin_branches
)


class SwhBrowseContentViewTest(TestCase):

    @patch('swh.web.browse.views.content.service')
    @istest
    def content_view_text(self, mock_service):
        mock_service.lookup_content_raw.return_value =\
            stub_content_text_data

        mock_service.lookup_content_filetype.return_value =\
            None

        url = reverse('browse-content',
                      kwargs={'query_string': stub_content_text_sha1})

        url_raw = reverse('browse-content-raw',
                          kwargs={'query_string': stub_content_text_sha1})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('content.html')

        self.assertContains(resp, '<code class="cpp">')
        self.assertContains(resp, escape(stub_content_text_data['data']))
        self.assertContains(resp, url_raw)

    @patch('swh.web.browse.views.content.service')
    @istest
    def content_view_text_no_highlight(self, mock_service):
        mock_service.lookup_content_raw.return_value =\
            stub_content_text_no_highlight_data

        mock_service.lookup_content_filetype.return_value =\
            {'mimetype': 'text/plain'}

        url = reverse('browse-content',
                      kwargs={'query_string': stub_content_text_no_highlight_sha1}) # noqa

        url_raw = reverse('browse-content-raw',
                          kwargs={'query_string': stub_content_text_no_highlight_sha1}) # noqa

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('content.html')

        self.assertContains(resp, '<code class="nohighlight-swh">')
        self.assertContains(resp, escape(stub_content_text_no_highlight_data['data'])) # noqa
        self.assertContains(resp, url_raw)

    @patch('swh.web.browse.views.content.service')
    @istest
    def content_view_image(self, mock_service):
        mock_service.lookup_content_raw.return_value =\
            stub_content_bin_data

        mime_type = 'image/png'

        mock_service.lookup_content_filetype.return_value =\
            {'mimetype': mime_type}

        url = reverse('browse-content',
                      kwargs={'query_string': stub_content_bin_sha1})

        url_raw = reverse('browse-content-raw',
                          kwargs={'query_string': stub_content_bin_sha1})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('content.html')

        pngEncoded = base64.b64encode(stub_content_bin_data['data']) \
                           .decode('utf-8')

        self.assertContains(resp, '<img src="data:%s;base64,%s"/>'
                                  % (mime_type, pngEncoded))
        self.assertContains(resp, url_raw)

    @patch('swh.web.browse.views.content.service')
    @istest
    def content_view_with_path(self, mock_service):
        mock_service.lookup_content_raw.return_value =\
            stub_content_text_data

        mock_service.lookup_content_filetype.return_value =\
            {'mimetype': 'text/x-c++'}

        url = reverse('browse-content',
                      kwargs={'query_string': stub_content_text_sha1},
                      query_params={'path': stub_content_text_path_with_root_dir}) # noqa

        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('content.html')

        self.assertContains(resp, '<code class="cpp">')
        self.assertContains(resp, escape(stub_content_text_data['data']))

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

    @patch('swh.web.browse.views.content.service')
    @istest
    def content_raw_text(self, mock_service):
        mock_service.lookup_content_raw.return_value =\
            stub_content_text_data

        url = reverse('browse-content-raw',
                      kwargs={'query_string': stub_content_text_sha1})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/plain')
        self.assertEqual(resp['Content-disposition'],
                         'filename=%s_%s' % ('sha1', stub_content_text_sha1))
        self.assertEqual(resp.content, stub_content_text_data['data'])

        filename = stub_content_text_path_with_root_dir.split('/')[-1]

        url = reverse('browse-content-raw',
                      kwargs={'query_string': stub_content_text_sha1},
                      query_params={'filename': filename})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'text/plain')
        self.assertEqual(resp['Content-disposition'],
                         'filename=%s' % filename)
        self.assertEqual(resp.content, stub_content_text_data['data'])

    @patch('swh.web.browse.views.content.service')
    @istest
    def content_raw_bin(self, mock_service):
        mock_service.lookup_content_raw.return_value =\
            stub_content_bin_data

        url = reverse('browse-content-raw',
                      kwargs={'query_string': stub_content_bin_sha1})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/octet-stream')
        self.assertEqual(resp['Content-disposition'],
                         'attachment; filename=%s_%s' %
                         ('sha1', stub_content_bin_sha1))
        self.assertEqual(resp.content, stub_content_bin_data['data'])

        url = reverse('browse-content-raw',
                      kwargs={'query_string': stub_content_bin_sha1},
                      query_params={'filename': stub_content_bin_filename})

        resp = self.client.get(url)

        self.assertEquals(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/octet-stream')
        self.assertEqual(resp['Content-disposition'],
                         'attachment; filename=%s' % stub_content_bin_filename)
        self.assertEqual(resp.content, stub_content_bin_data['data'])

    @nottest
    def origin_content_view_test(self, origin_id, origin_visits,
                                 origin_branches, origin_branch,
                                 root_dir_sha1, content_sha1, content_path,
                                 content_data, content_language,
                                 visit_id=None, ts=None):

        url_args = {'origin_id': origin_id,
                    'path': content_path}

        if not visit_id:
            visit_id = origin_visits[-1]['visit']

        if ts:
            url_args['ts'] = ts
        else:
            url_args['visit_id'] = visit_id

        url = reverse('browse-origin-content',
                      kwargs=url_args)

        resp = self.client.get(url)
        self.assertEquals(resp.status_code, 200)
        self.assertTemplateUsed('content.html')

        self.assertContains(resp, '<code class="%s">' % content_language)
        self.assertContains(resp, escape(content_data))

        split_path = content_path.split('/')

        filename = split_path[-1]
        path = content_path.replace(filename, '')[:-1]

        path_info = gen_path_info(path)

        del url_args['path']

        root_dir_url = reverse('browse-origin-directory',
                               kwargs=url_args,
                               query_params={'branch': origin_branch})

        self.assertContains(resp, '<li class="swh-path">',
                            count=len(path_info)+1)

        self.assertContains(resp, '<a href="%s">%s</a>' %
                            (root_dir_url, root_dir_sha1[:7]))

        for p in path_info:
            url_args['path'] = p['path']
            dir_url = reverse('browse-origin-directory',
                              kwargs=url_args,
                              query_params={'branch': origin_branch})
            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (dir_url, p['name']))

        self.assertContains(resp, '<li>%s</li>' % filename)

        query_string = 'sha1_git:' + content_sha1

        url_raw = reverse('browse-content-raw',
                          kwargs={'query_string': query_string},
                          query_params={'filename': filename})
        self.assertContains(resp, url_raw)

        self.assertContains(resp, '<li class="swh-branch">',
                            count=len(origin_branches))

        url_args['path'] = content_path

        for branch in origin_branches:
            root_dir_branch_url = \
                reverse('browse-origin-content',
                        kwargs=url_args,
                        query_params={'branch': branch['name']})

            self.assertContains(resp, '<a href="%s">%s</a>' %
                                (root_dir_branch_url, branch['name']))

    @patch('swh.web.browse.views.content.get_origin_visits')
    @patch('swh.web.browse.views.content.get_origin_visit_branches')
    @patch('swh.web.browse.views.content.service')
    @istest
    def origin_content_view(self, mock_service,
                            mock_get_origin_visit_branches,
                            mock_get_origin_visits):

        mock_get_origin_visits.return_value = stub_content_origin_visits
        mock_get_origin_visit_branches.return_value = stub_content_origin_branches # noqa
        mock_service.lookup_directory_with_path.return_value = \
            {'target': stub_content_text_sha1}
        mock_service.lookup_content_raw.return_value = stub_content_text_data
        mock_service.lookup_content_filetype.return_value = {'mimetype': 'text/x-c++'} # noqa

        self.origin_content_view_test(stub_content_origin_id,
                                      stub_content_origin_visits,
                                      stub_content_origin_branches,
                                      stub_content_origin_branch,
                                      stub_content_root_dir,
                                      stub_content_text_sha1,
                                      stub_content_text_path,
                                      stub_content_text_data['data'], 'cpp')

        self.origin_content_view_test(stub_content_origin_id,
                                      stub_content_origin_visits,
                                      stub_content_origin_branches,
                                      stub_content_origin_branch,
                                      stub_content_root_dir,
                                      stub_content_text_sha1,
                                      stub_content_text_path,
                                      stub_content_text_data['data'], 'cpp',
                                      visit_id=stub_content_origin_visit_id)

        self.origin_content_view_test(stub_content_origin_id,
                                      stub_content_origin_visits,
                                      stub_content_origin_branches,
                                      stub_content_origin_branch,
                                      stub_content_root_dir,
                                      stub_content_text_sha1,
                                      stub_content_text_path,
                                      stub_content_text_data['data'], 'cpp',
                                      ts=stub_content_origin_visit_ts)
