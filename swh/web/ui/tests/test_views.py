# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from nose.tools import istest

from swh.web.ui.tests import test_app


class ViewTestCase(test_app.SWHViewTestCase):

    @istest
    def info(self):
        # when
        rv = self.client.get('/about')

        self.assertEquals(rv.status_code, 200)
        self.assertIn(b'About', rv.data)

    # @istest
    def search_1(self):
        # when
        rv = self.client.get('/search')

        self.assertEquals(rv.status_code, 200)  # check this api
        self.assertRegexpMatches(rv.data, b'name=q value=>')

    # @istest
    def search_2(self):
        # when
        rv = self.client.get('/search?q=one-hash-to-look-for:another-one')

        self.assertEquals(rv.status_code, 200)  # check this api
        self.assertRegexpMatches(
            rv.data,
            b'name=q value=one-hash-to-look-for:another-one')
