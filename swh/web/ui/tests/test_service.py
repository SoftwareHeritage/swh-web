# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime

from nose.tools import istest
from unittest.mock import MagicMock, patch

from swh.core.hashutil import hex_to_hash
from swh.web.ui import service
from swh.web.ui.exc import BadInputExc
from swh.web.ui.tests import test_app


class ServiceTestCase(test_app.SWHApiTestCase):

    @istest
    def lookup_hash_does_not_exist(self):
        # given
        self.storage.content_find = MagicMock(return_value=None)

        # when
        actual_lookup = service.lookup_hash(
            'sha1_git:123caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEquals({'found': None,
                           'algo': 'sha1_git'}, actual_lookup)

        # check the function has been called with parameters
        self.storage.content_find.assert_called_with({
            'sha1_git':
            hex_to_hash('123caf10e9535160d90e874b45aa426de762f19f')
        })

    @istest
    def lookup_hash_exist(self):
        # given
        stub_content = {
                'sha1': hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')
            }
        self.storage.content_find = MagicMock(return_value=stub_content)

        # when
        actual_lookup = service.lookup_hash(
            'sha1:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEquals({'found': stub_content,
                           'algo': 'sha1'}, actual_lookup)

        self.storage.content_find.assert_called_with({
            'sha1':
            hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f'),
        })

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

    @patch('swh.web.ui.service.hashutil')
    @istest
    def hash_and_search(self, mock_hashutil):
        # given
        bhash = hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')
        mock_hashutil.hashfile.return_value = {'sha1': bhash}
        self.storage.content_find = MagicMock(return_value={
            'sha1': bhash,
            'sha1_git': bhash,
        })

        # when
        actual_content = service.hash_and_search('/some/path')

        # then
        self.assertEqual(actual_content, {
            'sha1': '456caf10e9535160d90e874b45aa426de762f19f',
            'sha1_git': '456caf10e9535160d90e874b45aa426de762f19f',
            'found': True,
        })

        mock_hashutil.hashfile.assert_called_once_with('/some/path')
        self.storage.content_find.assert_called_once_with({'sha1': bhash})

    @patch('swh.web.ui.service.hashutil')
    @istest
    def hash_and_search_not_found(self, mock_hashutil):
        # given
        bhash = hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')
        mock_hashutil.hashfile.return_value = {'sha1': bhash}
        mock_hashutil.hash_to_hex = MagicMock(
            return_value='456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_find = MagicMock(return_value=None)

        # when
        actual_content = service.hash_and_search('/some/path')

        # then
        self.assertEqual(actual_content, {
            'sha1': '456caf10e9535160d90e874b45aa426de762f19f',
            'found': False,
        })

        mock_hashutil.hashfile.assert_called_once_with('/some/path')
        self.storage.content_find.assert_called_once_with({'sha1': bhash})
        mock_hashutil.hash_to_hex.assert_called_once_with(bhash)

    @patch('swh.web.ui.service.upload')
    @istest
    def test_upload_and_search(self, mock_upload):
        mock_upload.save_in_upload_folder.return_value = (
            '/tmp/dir', 'some-filename', '/tmp/dir/path/some-filename')

        service.hash_and_search = MagicMock(side_effect=lambda filepath:
                                            {'sha1': 'blah',
                                             'found': True})
        mock_upload.cleanup.return_value = None

        file = MagicMock(filename='some-filename')

        # when
        actual_res = service.upload_and_search(file)

        # then
        self.assertEqual(actual_res, {
            'filename': 'some-filename',
            'sha1': 'blah',
            'found': True})

        mock_upload.save_in_upload_folder.assert_called_with(file)
        mock_upload.cleanup.assert_called_with('/tmp/dir')
        service.hash_and_search.assert_called_once_with(
            '/tmp/dir/path/some-filename')

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

    @istest
    def lookup_release(self):
        # given
        self.storage.release_get = MagicMock(return_value=[{
            'id': hex_to_hash('65a55bbdf3629f916219feb3dcc7393ded1bc8db'),
            'target': None,
            'date': datetime.datetime(2015, 1, 1, 22, 0, 0,
                                      tzinfo=datetime.timezone.utc),
            'name': b'v0.0.1',
            'message': b'synthetic release',
            'synthetic': True,
        }])

        # when
        actual_release = service.lookup_release(
            '65a55bbdf3629f916219feb3dcc7393ded1bc8db')

        # then
        self.assertEqual(actual_release, {
            'id': '65a55bbdf3629f916219feb3dcc7393ded1bc8db',
            'target': None,
            'date': datetime.datetime(2015, 1, 1, 22, 0, 0,
                                      tzinfo=datetime.timezone.utc),
            'name': 'v0.0.1',
            'message': 'synthetic release',
            'synthetic': True,
        })

        self.storage.release_get.assert_called_with(
            [hex_to_hash('65a55bbdf3629f916219feb3dcc7393ded1bc8db')])

    @istest
    def lookup_release_ko_id_checksum_not_ok_because_not_a_sha1(self):
        # given
        self.storage.release_get = MagicMock()

        with self.assertRaises(BadInputExc) as cm:
            # when
            service.lookup_release('not-a-sha1')
            self.assertIn('invalid checksum', cm.exception.args[0])

        self.storage.release_get.called = False

    @istest
    def lookup_release_ko_id_checksum_ok_but_not_a_sha1(self):
        # given
        self.storage.release_get = MagicMock()

        # when
        with self.assertRaises(BadInputExc) as cm:
            service.lookup_release(
                '13c1d34d138ec13b5ebad226dc2528dc7506c956e4646f62d4daf5'
                '1aea892abe')
            self.assertIn('sha1_git supported', cm.exception.args[0])

        self.storage.release_get.called = False

    @istest
    def lookup_revision(self):
        # given
        self.storage.revision_get = MagicMock(return_value=[{
            'id': hex_to_hash('18d8be353ed3480476f032475e7c233eff7371d5'),
            'directory': hex_to_hash(
                '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6'),
            'author': {
                'name': b'bill & boule',
                'email': b'bill@boule.org',
            },
            'committer': {
                'name': b'boule & bill',
                'email': b'boule@bill.org',
            },
            'message': b'elegant fix for bug 31415957',
            'date': datetime.datetime(2000, 1, 17, 11, 23, 54),
            'date_offset': 0,
            'committer_date': datetime.datetime(2000, 1, 17, 11, 23, 54),
            'committer_date_offset': 0,
            'synthetic': False,
            'type': 'git',
            'parents': [],
            'metadata': [],
        }])

        # when
        actual_revision = service.lookup_revision(
            '18d8be353ed3480476f032475e7c233eff7371d5')

        # then
        self.assertEqual(actual_revision, {
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'author': {
                'name': 'bill & boule',
                'email': 'bill@boule.org',
            },
            'committer': {
                'name': 'boule & bill',
                'email': 'boule@bill.org',
            },
            'message': 'elegant fix for bug 31415957',
            'date': datetime.datetime(2000, 1, 17, 11, 23, 54),
            'date_offset': 0,
            'committer_date': datetime.datetime(2000, 1, 17, 11, 23, 54),
            'committer_date_offset': 0,
            'synthetic': False,
            'type': 'git',
            'parents': [],
            'metadata': [],
        })

        self.storage.revision_get.assert_called_with(
            [hex_to_hash('18d8be353ed3480476f032475e7c233eff7371d5')])

    @istest
    def lookup_revision_log(self):
        # given
        stub_revision_log = [{
            'id': hex_to_hash('28d8be353ed3480476f032475e7c233eff7371d5'),
            'directory': hex_to_hash(
                '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6'),
            'author': {
                'name': b'bill & boule',
                'email': b'bill@boule.org',
            },
            'committer': {
                'name': b'boule & bill',
                'email': b'boule@bill.org',
            },
            'message': b'elegant fix for bug 31415957',
            'date': datetime.datetime(2000, 1, 17, 11, 23, 54),
            'date_offset': 0,
            'committer_date': datetime.datetime(2000, 1, 17, 11, 23, 54),
            'committer_date_offset': 0,
            'synthetic': False,
            'type': 'git',
            'parents': [],
            'metadata': [],
        }]
        self.storage.revision_log = MagicMock(return_value=stub_revision_log)

        # when
        actual_revision = service.lookup_revision_log(
            'abcdbe353ed3480476f032475e7c233eff7371d5')

        # then
        self.assertEqual(list(actual_revision), [{
            'id': '28d8be353ed3480476f032475e7c233eff7371d5',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'author': {
                'name': 'bill & boule',
                'email': 'bill@boule.org',
            },
            'committer': {
                'name': 'boule & bill',
                'email': 'boule@bill.org',
            },
            'message': 'elegant fix for bug 31415957',
            'date': datetime.datetime(2000, 1, 17, 11, 23, 54),
            'date_offset': 0,
            'committer_date': datetime.datetime(2000, 1, 17, 11, 23, 54),
            'committer_date_offset': 0,
            'synthetic': False,
            'type': 'git',
            'parents': [],
            'metadata': [],
        }])

        self.storage.revision_log.assert_called_with(
            hex_to_hash('abcdbe353ed3480476f032475e7c233eff7371d5'))

    @istest
    def lookup_content_raw_not_found(self):
        # given
        self.storage.content_find = MagicMock(return_value=None)

        # when
        actual_content = service.lookup_content_raw(
            'sha1:18d8be353ed3480476f032475e7c233eff7371d5')

        # then
        self.assertIsNone(actual_content)

        self.storage.content_find.assert_called_with(
            {'sha1': hex_to_hash('18d8be353ed3480476f032475e7c233eff7371d5')})

    @istest
    def lookup_content_raw(self):
        # given
        self.storage.content_find = MagicMock(return_value={
            'sha1': '18d8be353ed3480476f032475e7c233eff7371d5',
        })
        self.storage.content_get = MagicMock(return_value=[{
            'data': b'binary data',
        }, {}])

        # when
        actual_content = service.lookup_content_raw(
            'sha256:39007420ca5de7cb3cfc15196335507e'
            'e76c98930e7e0afa4d2747d3bf96c926')

        # then
        self.assertEquals(actual_content, {'data': b'binary data'})

        self.storage.content_find.assert_called_once_with(
            {'sha256': hex_to_hash('39007420ca5de7cb3cfc15196335507e'
                                   'e76c98930e7e0afa4d2747d3bf96c926')})
        self.storage.content_get.assert_called_once_with(
            ['18d8be353ed3480476f032475e7c233eff7371d5'])

    @istest
    def lookup_content_not_found(self):
        # given
        self.storage.content_find = MagicMock(return_value=None)

        # when
        actual_content = service.lookup_content(
            'sha1:18d8be353ed3480476f032475e7c233eff7371d5')

        # then
        self.assertIsNone(actual_content)

        self.storage.content_find.assert_called_with(
            {'sha1': hex_to_hash('18d8be353ed3480476f032475e7c233eff7371d5')})

    @istest
    def lookup_content_with_sha1(self):
        # given
        self.storage.content_find = MagicMock(return_value={
            'sha1': hex_to_hash('18d8be353ed3480476f032475e7c233eff7371d5'),
            'sha256': hex_to_hash('39007420ca5de7cb3cfc15196335507e'
                                  'e76c98930e7e0afa4d2747d3bf96c926'),
            'sha1_git': hex_to_hash('40e71b8614fcd89ccd17ca2b1d9e66'
                                    'c5b00a6d03'),
            'length': 190,
            'status': 'hidden',
        })

        # when
        actual_content = service.lookup_content(
            'sha1:18d8be353ed3480476f032475e7c233eff7371d5')

        # then
        self.assertEqual(actual_content, {
            'sha1': '18d8be353ed3480476f032475e7c233eff7371d5',
            'sha256': '39007420ca5de7cb3cfc15196335507ee76c98930e7e0afa4d274'
            '7d3bf96c926',
            'sha1_git': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'length': 190,
            'status': 'absent',
        })

        self.storage.content_find.assert_called_with(
            {'sha1': hex_to_hash('18d8be353ed3480476f032475e7c233eff7371d5')})

    @istest
    def lookup_content_with_sha256(self):
        # given
        self.storage.content_find = MagicMock(return_value={
            'sha1': hex_to_hash('18d8be353ed3480476f032475e7c233eff7371d5'),
            'sha256': hex_to_hash('39007420ca5de7cb3cfc15196335507e'
                                  'e76c98930e7e0afa4d2747d3bf96c926'),
            'sha1_git': hex_to_hash('40e71b8614fcd89ccd17ca2b1d9e66'
                                    'c5b00a6d03'),
            'length': 360,
            'status': 'visible',
        })

        # when
        actual_content = service.lookup_content(
            'sha256:39007420ca5de7cb3cfc15196335507e'
            'e76c98930e7e0afa4d2747d3bf96c926')

        # then
        self.assertEqual(actual_content, {
            'sha1': '18d8be353ed3480476f032475e7c233eff7371d5',
            'sha256': '39007420ca5de7cb3cfc15196335507ee76c98930e7e0afa4d274'
            '7d3bf96c926',
            'sha1_git': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'length': 360,
            'status': 'visible',
        })

        self.storage.content_find.assert_called_with(
            {'sha256': hex_to_hash('39007420ca5de7cb3cfc15196335507e'
                                   'e76c98930e7e0afa4d2747d3bf96c926')})

    @istest
    def lookup_person(self):
        # given
        self.storage.person_get = MagicMock(return_value=[{
            'id': 'person_id',
            'name': b'some_name',
            'email': b'some-email',
        }])

        # when
        actual_person = service.lookup_person('person_id')

        # then
        self.assertEqual(actual_person, {
            'id': 'person_id',
            'name': 'some_name',
            'email': 'some-email',
        })

        self.storage.person_get.assert_called_with(['person_id'])

    @istest
    def lookup_person_not_found(self):
        # given
        self.storage.person_get = MagicMock(return_value=[])

        # when
        actual_person = service.lookup_person('person_id')

        # then
        self.assertIsNone(actual_person)

        self.storage.person_get.assert_called_with(['person_id'])

    @istest
    def lookup_directory_bad_checksum(self):
        # given
        self.storage.directory_get = MagicMock()

        # when
        with self.assertRaises(BadInputExc):
            service.lookup_directory('directory_id')

        # then
        self.storage.directory_get.called = False

    @istest
    def lookup_directory_not_found(self):
        # given
        self.storage.directory_get = MagicMock(return_value=[])

        # when
        actual_directory = service.lookup_directory(
            '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

        # then
        self.assertIsNone(actual_directory)

        self.storage.directory_get.assert_called_with(
            hex_to_hash('40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'))

    @istest
    def lookup_directory(self):
        # given
        dir_entries_input = {
            'sha1': hex_to_hash('5c6f0e2750f48fa0bd0c4cf5976ba0b9e0'
                                '2ebda5'),
            'sha256': hex_to_hash('39007420ca5de7cb3cfc15196335507e'
                                  'e76c98930e7e0afa4d2747d3bf96c926'),
            'sha1_git': hex_to_hash('40e71b8614fcd89ccd17ca2b1d9e66'
                                    'c5b00a6d03'),
            'target': hex_to_hash('40e71b8614fcd89ccd17ca2b1d9e66'
                                  'c5b00a6d03'),
            'dir_id': hex_to_hash('40e71b8614fcd89ccd17ca2b1d9e66'
                                  'c5b00a6d03'),
            'name': b'bob',
            'type': 10,
        }

        expected_dir_entries = {
            'sha1': '5c6f0e2750f48fa0bd0c4cf5976ba0b9e02ebda5',
            'sha256': '39007420ca5de7cb3cfc15196335507ee76c98930e7e0afa4d2747'
            'd3bf96c926',
            'sha1_git': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'target': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'dir_id': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'name': 'bob',
            'type': 10,
        }

        self.storage.directory_get = MagicMock(
            return_value=[dir_entries_input])

        # when
        actual_directory = service.lookup_directory(
            '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

        # then
        self.assertIsNotNone(actual_directory)
        self.assertEqual(list(actual_directory), [expected_dir_entries])

        self.storage.directory_get.assert_called_with(
            hex_to_hash('40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'))
