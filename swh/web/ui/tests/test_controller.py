# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.web.ui import controller


class ApiTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        conf = {'api_backend': 'https://somewhere.org:4321'}

        controller.app.config['TESTING'] = True
        controller.app.config.update({'conf': conf})
        self.app = controller.app.test_client()

    @istest
    def info(self):
        # when
        rv = self.app.get('/info')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.data, b'Dev SWH UI')

    @istest
    def main_redirects_to_info(self):
        # when
        rv = self.app.get('/', follow_redirects=False)

        self.assertEquals(rv.status_code, 302)  # check redirects to /info

    # @istest
    def search_1(self):
        # when
        rv = self.app.get('/search')

        self.assertEquals(rv.status_code, 200)  # check this api
        self.assertRegexpMatches(rv.data, b'name=q value=>')

    # @istest
    def search_2(self):
        # when
        rv = self.app.get('/search?q=one-hash-to-look-for:another-one')

        self.assertEquals(rv.status_code, 200)  # check this api
        self.assertRegexpMatches(
            rv.data,
            b'name=q value=one-hash-to-look-for:another-one')

    # @istest
    def api_1_stat_counters(self):
        rv = self.app.get('/api/1/stat/counters')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
