# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.web.ui.back import api_query


class HttpTestCase(unittest.TestCase):

    @istest
    def create_request(self):
        # given
        actual_query = api_query.api_storage_content_present({'sha1': 'some-hash'})

        self.assertEquals(actual_query, {'data': '{"sha1": "some-hash"}',
                                         'headers': {'Content-Type':'application/json'},
                                         'method': 'post',
                                         'url': '/content/present'})
