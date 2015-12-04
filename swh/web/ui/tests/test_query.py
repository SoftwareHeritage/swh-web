# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.core import hashutil
from swh.web.ui import query
from swh.web.ui.exc import BadInputExc


class QueryTestCase(unittest.TestCase):
    @istest
    def parse_hash_malformed_query_with_more_than_2_parts(self):
        with self.assertRaises(BadInputExc):
            query.parse_hash('sha1:1234567890987654:other-stuff')

    @istest
    def parse_hash_guess_sha1(self):
        h = 'f1d2d2f924e986ac86fdf7b36c94bcdf32beec15'
        r = query.parse_hash(h)
        self.assertEquals(r, ('sha1', hashutil.hex_to_hash(h)))

    @istest
    def parse_hash_guess_sha256(self):
        h = '084C799CD551DD1D8D5C5F9A5D593B2' \
            'E931F5E36122ee5c793c1d08a19839cc0'
        r = query.parse_hash(h)
        self.assertEquals(r, ('sha256', hashutil.hex_to_hash(h)))

    @istest
    def parse_hash_guess_algo_malformed_hash(self):
        with self.assertRaises(BadInputExc):
            query.parse_hash('1234567890987654')

    @istest
    def parse_hash_check_sha1(self):
        h = 'f1d2d2f924e986ac86fdf7b36c94bcdf32beec15'
        r = query.parse_hash('sha1:' + h)
        self.assertEquals(r, ('sha1', hashutil.hex_to_hash(h)))

    @istest
    def parse_hash_check_sha1_git(self):
        h = 'e1d2d2f924e986ac86fdf7b36c94bcdf32beec15'
        r = query.parse_hash('sha1_git:' + h)
        self.assertEquals(r, ('sha1_git', hashutil.hex_to_hash(h)))

    @istest
    def parse_hash_check_sha256(self):
        h = '084C799CD551DD1D8D5C5F9A5D593B2E931F5E36122ee5c793c1d08a19839cc0'
        r = query.parse_hash('sha256:' + h)
        self.assertEquals(r, ('sha256', hashutil.hex_to_hash(h)))

    @istest
    def parse_hash_check_algo_malformed_sha1_hash(self):
        with self.assertRaises(BadInputExc):
            query.parse_hash('sha1:1234567890987654')

    @istest
    def parse_hash_check_algo_malformed_sha1_git_hash(self):
        with self.assertRaises(BadInputExc):
            query.parse_hash('sha1_git:1234567890987654')

    @istest
    def parse_hash_check_algo_malformed_sha256_hash(self):
        with self.assertRaises(BadInputExc):
            query.parse_hash('sha256:1234567890987654')

    @istest
    def parse_hash_check_algo_unknown_one(self):
        with self.assertRaises(BadInputExc):
            query.parse_hash('sha2:1234567890987654')
