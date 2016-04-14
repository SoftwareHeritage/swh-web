# Copyright (C) 2016 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from nose.tools import istest

from unittest.mock import patch

from .. import test_app


class MainViewTestCase(test_app.SWHViewTestCase):
    render_template = False

    @patch('flask.flash')
    @istest
    def homepage(self, mock_flash):
        # given
        mock_flash.return_value = 'something'

        # when
        rv = self.client.get('/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('home.html')

        mock_flash.assert_called_once_with(
            'This Web app is still work in progress, use at your own risk',
            'warning')

    @istest
    def info(self):
        # when
        rv = self.client.get('/about/')

        self.assertEquals(rv.status_code, 200)
        self.assert_template_used('about.html')
        self.assertIn(b'About', rv.data)
