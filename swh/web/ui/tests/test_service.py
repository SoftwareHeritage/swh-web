# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest
from unittest.mock import MagicMock

from swh.core import hashutil
from swh.web.ui import service
from swh.web.ui.tests.test_app import init_app_test_with_mock_storage


class ServiceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app, cls.storage = init_app_test_with_mock_storage()

    @istest
    def lookup_hash_does_not_exist(self):
        # given
        self.storage.content_exist = MagicMock(return_value=False)

        # when
        actual_lookup = service.lookup_hash(
            'sha1:123caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertFalse(actual_lookup)

        # check the function has been called with parameters
        self.storage.content_exist.assert_called_with({
            'sha1':
            hashutil.hex_to_hash('123caf10e9535160d90e874b45aa426de762f19f')})

    @istest
    def lookup_hash_exist(self):
        # given
        self.storage.content_exist = MagicMock(return_value=True)

        # when
        actual_lookup = service.lookup_hash(
            'sha1:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertTrue(actual_lookup)

        self.storage.content_exist.assert_called_with({
            'sha1':
            hashutil.hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')})

    @istest
    def lookup_hash_origin(self):
        # given
        self.storage.content_find_occurrence = MagicMock(return_value={
            'origin_type': 'sftp',
            'origin_url': 'sftp://ftp.gnu.org/gnu/octave',
            'branch': 'octavio-3.4.0.tar.gz',
            'revision': b'\xb0L\xaf\x10\xe9SQ`\xd9\x0e\x87KE\xaaBm\xe7b\xf1\x9f',  # noqa
            'path': b'octavio-3.4.0/doc/interpreter/octave.html/doc_002dS_005fISREG.html'  # noqa
        })
        expected_origin = {
            'origin_type': 'sftp',
            'origin_url': 'sftp://ftp.gnu.org/gnu/octave',
            'branch': 'octavio-3.4.0.tar.gz',
            'revision': 'b04caf10e9535160d90e874b45aa426de762f19f',
            'path': 'octavio-3.4.0/doc/interpreter/octave.html/doc'
                    '_002dS_005fISREG.html'
        }

        # when
        actual_origin = service.lookup_hash_origin(
            'sha1_git:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual(actual_origin, expected_origin)

        self.storage.content_find_occurrence.assert_called_with(
            {'sha1_git':
             hashutil.hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')})

    @istest
    def stat_counters(self):
        # given
        input_stats = {
            "content": 1770830,
            "directory": 211683,
            "directory_entry_dir": 209167,
            "directory_entry_file": 1807094,
            "directory_entry_rev": 0,
            "entity": 0,
            "entity_history": 0,
            "occurrence": 0,
            "occurrence_history": 19600,
            "origin": 1096,
            "person": 0,
            "release": 8584,
            "revision": 7792,
            "revision_history": 0,
            "skipped_content": 0
        }
        self.storage.stat_counters = MagicMock(return_value=input_stats)

        # when
        actual_stats = service.stat_counters()

        # then
        expected_stats = input_stats
        self.assertEqual(actual_stats, expected_stats)

        self.storage.stat_counters.assert_called_with()
