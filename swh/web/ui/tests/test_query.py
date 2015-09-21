# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from swh.web.ui import query


class QueryTestCase(unittest.TestCase):
    @istest
    def parse(self):
        # when
        nb_hashes, hashes = query.parse({'nb_hashes': '1', 'hash1': 'some-hash'})

        # then
        self.assertEquals(nb_hashes, 1, "Should be 1 hash")
        self.assertEquals(hashes, ['some-hash'])

    @istest
    def parse_2(self):
        # when
        nb_hashes, hashes = query.parse({'nb_hashes': '3',
                                         'hash3': 'some other hash',
                                         'hash2': 'yet again hash',
                                         'hash1': 'some-hash'})

        # then
        self.assertEquals(nb_hashes, 3, "Should be 3 hashes")
        self.assertEquals(len(hashes), nb_hashes)
        self.assertIn('some-hash', hashes)
        self.assertIn('yet again hash', hashes)
        self.assertIn('some other hash', hashes)

    @istest
    def parse_3(self):
        # when
        nb_hashes, hashes = query.parse({'nb_hashes': '3',
                                         'hash3': 'some other hash',
                                         'hash2': '',
                                         'hash1': 'some-hash'})

        # then
        self.assertEquals(nb_hashes, 2, "Should be 2 hashes")
        self.assertEquals(len(hashes), nb_hashes)
        self.assertIn('some-hash', hashes)
        self.assertIn('some other hash', hashes)


    @istest
    def group_by_checksum(self):
        input_sha1 = 'f1d2d2f924e986ac86fdf7b36c94bcdf32beec15'
        input_sha256 = '084c799cd551dd1d8d5c5f9a5d593b2e931f5e36122ee5c793c1d08a19839cc0'

        res = query.group_by_checksums([input_sha1, input_sha256, input_sha1])

        # for i in res:
        #     print(i)
        self.assertEquals(res['sha1'], input_sha1)
        self.assertEquals(res['sha256'], input_sha256)
