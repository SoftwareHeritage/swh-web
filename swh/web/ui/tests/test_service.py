# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest
from unittest.mock import MagicMock, patch

from swh.core.hashutil import hex_to_hash
from swh.web.ui import service
from swh.web.ui.tests import test_app


class ServiceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, _, cls.storage = test_app.init_app()

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
            hex_to_hash('123caf10e9535160d90e874b45aa426de762f19f')})

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
            hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')})

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
             hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')})

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

    @istest
    def hash_and_search(self):
        # given
        self.storage.content_exist = MagicMock(return_value=False)

        bhash = hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')
        # when
        with patch(
                'swh.core.hashutil.hashfile',
                return_value={'sha1': bhash}):
            actual_hash, actual_search = service.hash_and_search('/some/path')

        # then
        self.assertEqual(actual_hash,
                         '456caf10e9535160d90e874b45aa426de762f19f')
        self.assertFalse(actual_search)

        self.storage.content_exist.assert_called_with({'sha1': bhash})

    @patch('swh.web.ui.service.upload')
    @istest
    def test_upload_and_search_upload_OK_basic_case(self, mock_upload):
        # given (cf. decorators patch)
        mock_upload.save_in_upload_folder.return_value = (
            '/tmp/blah', 'some-filename', None)
        mock_upload.cleanup.return_value = None

        file = MagicMock()
        file.filename = 'some-filename'

        # when
        actual_file, actual_hash, actual_search = service.upload_and_search(
            file)

        # then
        self.assertEqual(actual_file, 'some-filename')
        self.assertIsNone(actual_hash)
        self.assertIsNone(actual_search)

        mock_upload.save_in_upload_folder.assert_called_with(file)
        mock_upload.cleanup.assert_called_with('/tmp/blah')

    @istest
    def lookup_origin(self):
        # given
        self.storage.origin_get = MagicMock(return_value={
            'id': 'origin-id',
            'lister': 'uuid-lister',
            'project': 'uuid-project',
            'url': 'ftp://some/url/to/origin',
            'type': 'ftp'})

        # when
        actual_origin = service.lookup_origin('origin-id')

        # then
        self.assertEqual(actual_origin, {'id': 'origin-id',
                                         'lister': 'uuid-lister',
                                         'project': 'uuid-project',
                                         'url': 'ftp://some/url/to/origin',
                                         'type': 'ftp'})

        self.storage.origin_get.assert_called_with({'id': 'origin-id'})
