# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.web.ui.back import http


class HttpTestCase(unittest.TestCase):

    @istest
    def create_request(self):
        # given
        actual_query = http.create_request('get', '/call/to/api')

        # then
        self.assertEquals(actual_query, {'method': 'get',
                                         'url': '/call/to/api'})

    @istest
    def create_request_2(self):
        # given
        actual_query = http.create_request('post', '/call/to/api', {'some-key':'some-value'})

        # then
        self.assertEquals(actual_query, {'data': '{"some-key": "some-value"}',
                                         'headers': {'Content-Type': 'application/json'},
                                         'method': 'post',
                                         'url': '/call/to/api'})
