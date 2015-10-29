# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

from unittest.mock import patch

from swh.web.ui import service


class MockStorage():
    def stat_counters(self):
        return {
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

    def content_find_occurrence(self, h):
        return {
            'origin_type': 'sftp',
            'origin_url': 'sftp://ftp.gnu.org/gnu/octave',
            'branch': 'octavio-3.4.0.tar.gz',
            'revision': b'\xb0L\xaf\x10\xe9SQ`\xd9\x0e\x87KE\xaaBm\xe7b\xf1\x9f',  # noqa
            'path': b'octavio-3.4.0/doc/interpreter/octave.html/doc_002dS_005fISREG.html'  # noqa
        }

    def content_exist(self, h):
        return False


class ServiceTestCase(unittest.TestCase):

    @istest
    def lookup_hash(self):
        with patch('swh.web.ui.main.storage',
                   return_value=MockStorage()):
            actual_lookup = service.lookup_hash(
                'sha1:123caf10e9535160d90e874b45aa426de762f19f')

        self.assertFalse(actual_lookup)

    @istest
    def lookup_hash_origin(self):
        # given
        expected_origin = {
            'origin_type': 'sftp',
            'origin_url': 'sftp://ftp.gnu.org/gnu/octave',
            'branch': 'octavio-3.4.0.tar.gz',
            'revision': 'b04caf10e9535160d90e874b45aa426de762f19f',
            'path': 'octavio-3.4.0/doc/interpreter/octave.html/doc'
                    '_002dS_005fISREG.html'
        }

        # when
        with patch('swh.web.ui.main.storage',
                   return_value=MockStorage()):
            actual_origin = service.lookup_hash_origin(
                'sha1_git:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual(actual_origin, expected_origin)

    @istest
    def stat_counters(self):
        # given
        expected_stats = MockStorage().stat_counters()

        # when
        with patch('swh.web.ui.main.storage', return_value=MockStorage()):
            actual_stats = service.stat_counters()

        # then
        self.assertEqual(actual_stats, expected_stats)
