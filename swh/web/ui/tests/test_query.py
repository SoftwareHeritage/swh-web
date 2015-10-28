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
    def parse_hash(self):
        q = 'f1d2d2f924e986ac86fdf7b36c94bcdf32beec15'
        r = query.parse_hash(q)
        self.assertEquals(r, ('sha1', hashutil.hex_to_hash(q)))

    @istest
    def parse_hash_2(self):
        q = '084C799CD551DD1D8D5C5F9A5D593B2' \
            'E931F5E36122ee5c793c1d08a19839cc0'
        r = query.parse_hash(q)
        self.assertEquals(r, ('sha256', hashutil.hex_to_hash(q)))

    @istest
    def parse_hash_3(self):
        q = '1234567890987654'
        with self.assertRaises(ValueError):
            query.parse_hash(q)
