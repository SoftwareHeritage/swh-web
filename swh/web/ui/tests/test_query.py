# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.web.ui import query
from swh.core import hashutil


class QueryTestCase(unittest.TestCase):
    @istest
    def categorize_hash(self):
        input_sha1 = 'f1d2d2f924e986ac86fdf7b36c94bcdf32beec15'

        res = query.categorize_hash(input_sha1)

        self.assertEquals(res, {'sha1': hashutil.hex_to_hash(input_sha1)})

    def categorize_hash_2(self):
        input_sha256 = \
            '084c799cd551dd1d8d5c5f9a5d593b2e931f5e36122ee5c793c1d08a19839cc0'

        res = query.categorize_hash(input_sha256)

        self.assertEquals(res, {'sha256': hashutil.hex_to_hash(input_sha256)})

    def categorize_hash_3(self):
        input_bad_length = '1234567890987654'

        res = query.categorize_hash(input_bad_length)

        self.assertEquals(res, {})
