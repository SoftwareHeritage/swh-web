# Copyright (C) 2016 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from nose.tools import istest

from .. import test_app


class MainViewTestCase(test_app.SWHViewTestCase):
    render_template = False

    @istest
    def homepage(self):
        # when
        rv = self.client.get('/')

        # then
        self.assertEquals(rv.status_code, 302)
        self.assertRedirects(rv, '/api/')

    @istest
    def info(self):
        # when
        rv = self.client.get('/about/')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('about.html')
        self.assertIn(b'About', rv.data)
