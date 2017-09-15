# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.web.browse import utils


class SwhUiUtilsTestCase(unittest.TestCase):

    @istest
    def gen_path_info(self):
        input_path = '/home/user/swh-environment/swh-web/'
        expected_result = [
            {'name': 'home', 'path': 'home'},
            {'name': 'user', 'path': 'home/user'},
            {'name': 'swh-environment', 'path': 'home/user/swh-environment'},
            {'name': 'swh-web', 'path': 'home/user/swh-environment/swh-web'}
        ]
        path_info = utils.gen_path_info(input_path)
        self.assertEquals(path_info, expected_result)

        input_path = 'home/user/swh-environment/swh-web'
        path_info = utils.gen_path_info(input_path)
        self.assertEquals(path_info, expected_result)

    @istest
    def get_mimetype_for_content(self):
        text = b'Hello world!'
        self.assertEqual(utils.get_mimetype_for_content(text), 'text/plain')
