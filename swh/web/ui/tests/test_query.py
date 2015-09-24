# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.web.ui import query
from swh.core import hashutil

class QueryTestCase(unittest.TestCase):
    @istest
    def parse(self):
        # when
        actual_hashes = query.parse("a:b:c")

        # then
        self.assertEquals(actual_hashes, ['a', 'b', 'c'],
                          "Should be a, b, c hashes")

    @istest
    def parse_with_error(self):
        # when
        with self.assertRaises(AttributeError):
            query.parse(None)

    @istest
    def parse_2(self):
        # when
        actual_hashes = query.parse("a")

        # then
        self.assertEquals(actual_hashes, ['a'], "Should be only a hash")


    @istest
    def group_by_checksum(self):
        input_sha1 = 'f1d2d2f924e986ac86fdf7b36c94bcdf32beec15'
        input_sha256 = \
            '084c799cd551dd1d8d5c5f9a5d593b2e931f5e36122ee5c793c1d08a19839cc0'
        input_bad_length = '1234567890987654'

        res = query.group_by_checksums([input_sha1,
                                        input_sha256,
                                        input_bad_length,
                                        input_sha1])

        self.assertEquals(len(res), 2,
                          "Only 2 elements because no duplicates and filter out bad inputs.")
        self.assertEquals(res['sha1'], hashutil.hex_to_hash(input_sha1))
        self.assertEquals(res['sha256'], hashutil.hex_to_hash(input_sha256))

    @istest
    def group_by_checksum_with_only_bad_inputs(self):
        input_sha1 = 'e986ac86fdf7b36c94bcdf32beec15'
        input_bad_length = '1234567890987654'

        res = query.group_by_checksums([input_sha1,
                                        input_bad_length,
                                        input_sha1])

        self.assertEquals(res, {}, "Absolutely no good inputs.")
