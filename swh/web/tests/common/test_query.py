# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from unittest.mock import patch

from swh.model import hashutil

from swh.web.common import query
from swh.web.common.exc import BadInputExc
from swh.web.tests.testcase import SWHWebTestCase


class QueryTestCase(SWHWebTestCase):
    def test_parse_hash_malformed_query_with_more_than_2_parts(self):
        with self.assertRaises(BadInputExc):
            query.parse_hash('sha1:1234567890987654:other-stuff')

    def test_parse_hash_guess_sha1(self):
        h = 'f1d2d2f924e986ac86fdf7b36c94bcdf32beec15'
        r = query.parse_hash(h)
        self.assertEqual(r, ('sha1', hashutil.hash_to_bytes(h)))

    def test_parse_hash_guess_sha256(self):
        h = '084C799CD551DD1D8D5C5F9A5D593B2' \
            'E931F5E36122ee5c793c1d08a19839cc0'
        r = query.parse_hash(h)
        self.assertEqual(r, ('sha256', hashutil.hash_to_bytes(h)))

    def test_parse_hash_guess_algo_malformed_hash(self):
        with self.assertRaises(BadInputExc):
            query.parse_hash('1234567890987654')

    def test_parse_hash_check_sha1(self):
        h = 'f1d2d2f924e986ac86fdf7b36c94bcdf32beec15'
        r = query.parse_hash('sha1:' + h)
        self.assertEqual(r, ('sha1', hashutil.hash_to_bytes(h)))

    def test_parse_hash_check_sha1_git(self):
        h = 'e1d2d2f924e986ac86fdf7b36c94bcdf32beec15'
        r = query.parse_hash('sha1_git:' + h)
        self.assertEqual(r, ('sha1_git', hashutil.hash_to_bytes(h)))

    def test_parse_hash_check_sha256(self):
        h = '084C799CD551DD1D8D5C5F9A5D593B2E931F5E36122ee5c793c1d08a19839cc0'
        r = query.parse_hash('sha256:' + h)
        self.assertEqual(r, ('sha256', hashutil.hash_to_bytes(h)))

    def test_parse_hash_check_algo_malformed_sha1_hash(self):
        with self.assertRaises(BadInputExc):
            query.parse_hash('sha1:1234567890987654')

    def test_parse_hash_check_algo_malformed_sha1_git_hash(self):
        with self.assertRaises(BadInputExc):
            query.parse_hash('sha1_git:1234567890987654')

    def test_parse_hash_check_algo_malformed_sha256_hash(self):
        with self.assertRaises(BadInputExc):
            query.parse_hash('sha256:1234567890987654')

    def test_parse_hash_check_algo_unknown_one(self):
        with self.assertRaises(BadInputExc):
            query.parse_hash('sha2:1234567890987654')

    @patch('swh.web.common.query.parse_hash')
    def test_parse_hash_with_algorithms_or_throws_bad_query(self, mock_hash):
        # given
        mock_hash.side_effect = BadInputExc('Error input')

        # when
        with self.assertRaises(BadInputExc) as cm:
            query.parse_hash_with_algorithms_or_throws(
                'sha1:blah',
                ['sha1'],
                'useless error message for this use case')
        self.assertIn('Error input', cm.exception.args[0])

        mock_hash.assert_called_once_with('sha1:blah')

    @patch('swh.web.common.query.parse_hash')
    def test_parse_hash_with_algorithms_or_throws_bad_algo(self, mock_hash):
        # given
        mock_hash.return_value = 'sha1', '123'

        # when
        with self.assertRaises(BadInputExc) as cm:
            query.parse_hash_with_algorithms_or_throws(
                'sha1:431',
                ['sha1_git'],
                'Only sha1_git!')
        self.assertIn('Only sha1_git!', cm.exception.args[0])

        mock_hash.assert_called_once_with('sha1:431')

    @patch('swh.web.common.query.parse_hash')
    def test_parse_hash_with_algorithms(self, mock_hash):
        # given
        mock_hash.return_value = ('sha256', b'123')

        # when
        algo, sha = query.parse_hash_with_algorithms_or_throws(
            'sha256:123',
            ['sha256', 'sha1_git'],
            'useless error message for this use case')

        self.assertEqual(algo, 'sha256')
        self.assertEqual(sha, b'123')

        mock_hash.assert_called_once_with('sha256:123')

    def test_parse_uuid4(self):
        # when
        actual_uuid = query.parse_uuid4('7c33636b-8f11-4bda-89d9-ba8b76a42cec')

        # then
        self.assertEqual(actual_uuid, '7c33636b-8f11-4bda-89d9-ba8b76a42cec')

    def test_parse_uuid4_ko(self):
        # when
        with self.assertRaises(BadInputExc) as cm:
            query.parse_uuid4('7c33636b-8f11-4bda-89d9-ba8b76a42')
        self.assertIn('badly formed hexadecimal UUID string',
                      cm.exception.args[0])
