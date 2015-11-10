# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.web.ui import upload
from swh.web.ui.tests import test_app


class UploadTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app, cls.storage = test_app.init_app()

    @istest
    def allowed_file_ok(self):
        # when
        actual_perm = upload.allowed_file('README')
        self.assertTrue(actual_perm)

        # when
        actual_perm2 = upload.allowed_file('README', [])
        self.assertTrue(actual_perm2)

        # when
        actual_perm3 = upload.allowed_file('README', ['README',
                                                      'LICENCE',
                                                      'BUGS'])
        self.assertTrue(actual_perm3)

        # when
        actual_perm4 = upload.allowed_file('some-filename.txt', ['txt',
                                                                 'blah',
                                                                 'gz'])
        self.assertTrue(actual_perm4)

        # when
        actual_perm5 = upload.allowed_file('something.tar.gz', ['gz',
                                                                'txt',
                                                                'tar.gz'])
        # then
        self.assertTrue(actual_perm5)

    @istest
    def allowed_file_denied(self):
        # when
        actual_perm = upload.allowed_file('some-filename', ['blah'])
        self.assertFalse(actual_perm)

        # when
        actual_perm = upload.allowed_file('something.tgz', ['gz',
                                                            'txt',
                                                            'tar.gz'])
        # then
        self.assertFalse(actual_perm)
