# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime

from nose.tools import istest
from unittest.mock import MagicMock, patch, call

from swh.core.hashutil import hex_to_hash, hash_to_hex
from swh.web.ui import service
from swh.web.ui.exc import BadInputExc, NotFoundExc
from swh.web.ui.tests import test_app


class ServiceTestCase(test_app.SWHApiTestCase):

    def setUp(self):
        self.SHA1_SAMPLE = '18d8be353ed3480476f032475e7c233eff7371d5'
        self.SHA1_SAMPLE_BIN = hex_to_hash(self.SHA1_SAMPLE)
        self.SHA256_SAMPLE = ('39007420ca5de7cb3cfc15196335507e'
                              'e76c98930e7e0afa4d2747d3bf96c926')
        self.SHA256_SAMPLE_BIN = hex_to_hash(self.SHA256_SAMPLE)
        self.SHA1GIT_SAMPLE = '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'
        self.SHA1GIT_SAMPLE_BIN = hex_to_hash(self.SHA1GIT_SAMPLE)
        self.DIRECTORY_ID = '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6'
        self.DIRECTORY_ID_BIN = hex_to_hash(self.DIRECTORY_ID)
        self.AUTHOR_ID_BIN = {
            'name': b'author',
            'email': b'author@company.org',
        }
        self.AUTHOR_ID = {
            'name': 'author',
            'email': 'author@company.org',
        }
        self.COMMITTER_ID_BIN = {
            'name': b'committer',
            'email': b'committer@corp.org',
        }
        self.COMMITTER_ID = {
            'name': 'committer',
            'email': 'committer@corp.org',
        }
        self.SAMPLE_DATE_RAW = {
            'timestamp': datetime.datetime(
                2000, 1, 17, 11, 23, 54,
                tzinfo=datetime.timezone.utc,
            ).timestamp(),
            'offset': 0,
            'negative_utc': False,
        }
        self.SAMPLE_DATE = '2000-01-17T11:23:54+00:00'
        self.SAMPLE_MESSAGE_BIN = b'elegant fix for bug 31415957'
        self.SAMPLE_MESSAGE = 'elegant fix for bug 31415957'

        self.SAMPLE_REVISION = {
            'id': self.SHA1_SAMPLE,
            'directory': self.DIRECTORY_ID,
            'author': self.AUTHOR_ID,
            'committer': self.COMMITTER_ID,
            'message': self.SAMPLE_MESSAGE,
            'date': self.SAMPLE_DATE,
            'committer_date': self.SAMPLE_DATE,
            'synthetic': False,
            'type': 'git',
            'parents': [],
            'metadata': [],
            'merge': False
        }
        self.SAMPLE_REVISION_RAW = {
            'id': self.SHA1_SAMPLE_BIN,
            'directory': self.DIRECTORY_ID_BIN,
            'author': self.AUTHOR_ID_BIN,
            'committer': self.COMMITTER_ID_BIN,
            'message': self.SAMPLE_MESSAGE_BIN,
            'date': self.SAMPLE_DATE_RAW,
            'committer_date': self.SAMPLE_DATE_RAW,
            'synthetic': False,
            'type': 'git',
            'parents': [],
            'metadata': [],
        }

        self.SAMPLE_CONTENT = {
            'sha1': self.SHA1_SAMPLE,
            'sha256': self.SHA256_SAMPLE,
            'sha1_git': self.SHA1GIT_SAMPLE,
            'length': 190,
            'status': 'absent'
        }
        self.SAMPLE_CONTENT_RAW = {
            'sha1': self.SHA1_SAMPLE_BIN,
            'sha256': self.SHA256_SAMPLE_BIN,
            'sha1_git': self.SHA1GIT_SAMPLE_BIN,
            'length': 190,
            'status': 'hidden'
        }

        self.date_origin_visit1 = datetime.datetime(
            2015, 1, 1, 22, 0, 0,
            tzinfo=datetime.timezone.utc)

        self.origin_visit1 = {
            'date': self.date_origin_visit1,
            'origin': 1,
            'visit': 1
        }

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_multiple_hashes_ball_missing(self, mock_backend):
        # given
        mock_backend.content_missing_per_sha1 = MagicMock(return_value=[])

        # when
        actual_lookup = service.lookup_multiple_hashes(
            [{'filename': 'a',
              'sha1': '456caf10e9535160d90e874b45aa426de762f19f'},
             {'filename': 'b',
              'sha1': '745bab676c8f3cec8016e0c39ea61cf57e518865'}])

        # then
        self.assertEquals(actual_lookup, [
            {'filename': 'a',
             'sha1': '456caf10e9535160d90e874b45aa426de762f19f',
             'found': True},
            {'filename': 'b',
             'sha1': '745bab676c8f3cec8016e0c39ea61cf57e518865',
             'found': True}
        ])

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_multiple_hashes_some_missing(self, mock_backend):
        # given
        mock_backend.content_missing_per_sha1 = MagicMock(return_value=[
            hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')
        ])

        # when
        actual_lookup = service.lookup_multiple_hashes(
            [{'filename': 'a',
              'sha1': '456caf10e9535160d90e874b45aa426de762f19f'},
             {'filename': 'b',
              'sha1': '745bab676c8f3cec8016e0c39ea61cf57e518865'}])

        # then
        self.assertEquals(actual_lookup, [
            {'filename': 'a',
             'sha1': '456caf10e9535160d90e874b45aa426de762f19f',
             'found': False},
            {'filename': 'b',
             'sha1': '745bab676c8f3cec8016e0c39ea61cf57e518865',
             'found': True}
        ])

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_hash_does_not_exist(self, mock_backend):
        # given
        mock_backend.content_find = MagicMock(return_value=None)

        # when
        actual_lookup = service.lookup_hash(
            'sha1_git:123caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEquals({'found': None,
                           'algo': 'sha1_git'}, actual_lookup)

        # check the function has been called with parameters
        mock_backend.content_find.assert_called_with(
            'sha1_git',
            hex_to_hash('123caf10e9535160d90e874b45aa426de762f19f'))

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_hash_exist(self, mock_backend):
        # given
        stub_content = {
                'sha1': hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')
            }
        mock_backend.content_find = MagicMock(return_value=stub_content)

        # when
        actual_lookup = service.lookup_hash(
            'sha1:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEquals({'found': stub_content,
                           'algo': 'sha1'}, actual_lookup)

        mock_backend.content_find.assert_called_with(
            'sha1',
            hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f'),
        )

    @patch('swh.web.ui.service.backend')
    @istest
    def search_hash_does_not_exist(self, mock_backend):
        # given
        mock_backend.content_find = MagicMock(return_value=None)

        # when
        actual_lookup = service.search_hash(
            'sha1_git:123caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEquals({'found': False}, actual_lookup)

        # check the function has been called with parameters
        mock_backend.content_find.assert_called_with(
            'sha1_git',
            hex_to_hash('123caf10e9535160d90e874b45aa426de762f19f'))

    @patch('swh.web.ui.service.backend')
    @istest
    def search_hash_exist(self, mock_backend):
        # given
        stub_content = {
                'sha1': hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')
            }
        mock_backend.content_find = MagicMock(return_value=stub_content)

        # when
        actual_lookup = service.search_hash(
            'sha1:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEquals({'found': True}, actual_lookup)

        mock_backend.content_find.assert_called_with(
            'sha1',
            hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f'),
        )

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_filetype(self, mock_backend):
        # given
        mock_backend.content_filetype_get = MagicMock(
            return_value={
                'id': hex_to_hash(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'mimetype': b'text/x-c++',
                'encoding': b'us-ascii',
            })
        expected_filetype = {
                'id': '123caf10e9535160d90e874b45aa426de762f19f',
                'mimetype': 'text/x-c++',
                'encoding': 'us-ascii',
        }

        # when
        actual_filetype = service.lookup_content_filetype(
            'sha1:123caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual(actual_filetype, expected_filetype)

        mock_backend.content_filetype_get.assert_called_with(
            hex_to_hash('123caf10e9535160d90e874b45aa426de762f19f'))

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_filetype_2(self, mock_backend):
        # given
        mock_backend.content_find = MagicMock(
            return_value={
                'sha1': hex_to_hash(
                    '123caf10e9535160d90e874b45aa426de762f19f')
            }
        )
        mock_backend.content_filetype_get = MagicMock(
            return_value={
                'id': hex_to_hash(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'mimetype': b'text/x-python',
                'encoding': b'us-ascii',
            }
        )
        expected_filetype = {
                'id': '123caf10e9535160d90e874b45aa426de762f19f',
                'mimetype': 'text/x-python',
                'encoding': 'us-ascii',
        }

        # when
        actual_filetype = service.lookup_content_filetype(
            'sha1_git:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual(actual_filetype, expected_filetype)

        mock_backend.content_find(
            'sha1_git', hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')
        )
        mock_backend.content_filetype_get.assert_called_with(
            hex_to_hash('123caf10e9535160d90e874b45aa426de762f19f'))

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_language(self, mock_backend):
        # given
        mock_backend.content_language_get = MagicMock(
            return_value={
                'id': hex_to_hash(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'lang': 'python',
            })
        expected_language = {
                'id': '123caf10e9535160d90e874b45aa426de762f19f',
                'lang': 'python',
        }

        # when
        actual_language = service.lookup_content_language(
            'sha1:123caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual(actual_language, expected_language)

        mock_backend.content_language_get.assert_called_with(
            hex_to_hash('123caf10e9535160d90e874b45aa426de762f19f'))

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_language_2(self, mock_backend):
        # given
        mock_backend.content_find = MagicMock(
            return_value={
                'sha1': hex_to_hash(
                    '123caf10e9535160d90e874b45aa426de762f19f')
            }
        )
        mock_backend.content_language_get = MagicMock(
            return_value={
                'id': hex_to_hash(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'lang': 'haskell',
            }
        )
        expected_language = {
                'id': '123caf10e9535160d90e874b45aa426de762f19f',
                'lang': 'haskell',
        }

        # when
        actual_language = service.lookup_content_language(
            'sha1_git:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual(actual_language, expected_language)

        mock_backend.content_find(
            'sha1_git', hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')
        )
        mock_backend.content_language_get.assert_called_with(
            hex_to_hash('123caf10e9535160d90e874b45aa426de762f19f'))

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_expression(self, mock_backend):
        # given
        mock_backend.content_ctags_search = MagicMock(
            return_value=[{
                'id': hex_to_hash(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'name': 'foobar',
                'kind': 'variable',
                'lang': 'C',
                'line': 10
            }])
        expected_ctags = [{
            'sha1': '123caf10e9535160d90e874b45aa426de762f19f',
            'name': 'foobar',
            'kind': 'variable',
            'lang': 'C',
            'line': 10
        }]

        # when
        actual_ctags = list(service.lookup_expression('foobar'))

        # then
        self.assertEqual(actual_ctags, expected_ctags)

        mock_backend.content_ctags_search.assert_called_with('foobar')

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_expression_no_result(self, mock_backend):
        # given
        mock_backend.content_ctags_search = MagicMock(
            return_value=[])
        expected_ctags = []

        # when
        actual_ctags = list(service.lookup_expression('barfoo'))

        # then
        self.assertEqual(actual_ctags, expected_ctags)

        mock_backend.content_ctags_search.assert_called_with('barfoo')

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_license(self, mock_backend):
        # given
        mock_backend.content_license_get = MagicMock(
            return_value={
                'id': hex_to_hash(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'lang': 'python',
            })
        expected_license = {
                'id': '123caf10e9535160d90e874b45aa426de762f19f',
                'lang': 'python',
        }

        # when
        actual_license = service.lookup_content_license(
            'sha1:123caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual(actual_license, expected_license)

        mock_backend.content_license_get.assert_called_with(
            hex_to_hash('123caf10e9535160d90e874b45aa426de762f19f'))

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_license_2(self, mock_backend):
        # given
        mock_backend.content_find = MagicMock(
            return_value={
                'sha1': hex_to_hash(
                    '123caf10e9535160d90e874b45aa426de762f19f')
            }
        )
        mock_backend.content_license_get = MagicMock(
            return_value={
                'id': hex_to_hash(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'lang': 'haskell',
            }
        )
        expected_license = {
                'id': '123caf10e9535160d90e874b45aa426de762f19f',
                'lang': 'haskell',
        }

        # when
        actual_license = service.lookup_content_license(
            'sha1_git:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual(actual_license, expected_license)

        mock_backend.content_find(
            'sha1_git', hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f')
        )
        mock_backend.content_license_get.assert_called_with(
            hex_to_hash('123caf10e9535160d90e874b45aa426de762f19f'))

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_provenance(self, mock_backend):
        # given
        mock_backend.content_find_provenance = MagicMock(
            return_value=(p for p in [{
                'content': hex_to_hash(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'revision': hex_to_hash(
                    '456caf10e9535160d90e874b45aa426de762f19f'),
                'origin': 100,
                'visit': 1,
                'path': b'octavio-3.4.0/octave.html/doc_002dS_005fISREG.html'
            }]))
        expected_provenances = [{
            'content': '123caf10e9535160d90e874b45aa426de762f19f',
            'revision': '456caf10e9535160d90e874b45aa426de762f19f',
            'origin': 100,
            'visit': 1,
            'path': 'octavio-3.4.0/octave.html/doc_002dS_005fISREG.html'
        }]

        # when
        actual_provenances = service.lookup_content_provenance(
            'sha1_git:123caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual(list(actual_provenances), expected_provenances)

        mock_backend.content_find_provenance.assert_called_with(
            'sha1_git',
            hex_to_hash('123caf10e9535160d90e874b45aa426de762f19f'))

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_provenance_not_found(self, mock_backend):
        # given
        mock_backend.content_find_provenance = MagicMock(return_value=None)

        # when
        actual_provenances = service.lookup_content_provenance(
            'sha1_git:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertIsNone(actual_provenances)

        mock_backend.content_find_provenance.assert_called_with(
            'sha1_git',
            hex_to_hash('456caf10e9535160d90e874b45aa426de762f19f'))

    @patch('swh.web.ui.service.backend')
    @istest
    def stat_counters(self, mock_backend):
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
        mock_backend.stat_counters = MagicMock(return_value=input_stats)

        # when
        actual_stats = service.stat_counters()

        # then
        expected_stats = input_stats
        self.assertEqual(actual_stats, expected_stats)

        mock_backend.stat_counters.assert_called_with()

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_origin_visits(self, mock_backend):
        # given
        date_origin_visit2 = datetime.datetime(
            2013, 7, 1, 20, 0, 0,
            tzinfo=datetime.timezone.utc)

        date_origin_visit3 = datetime.datetime(
            2015, 1, 1, 21, 0, 0,
            tzinfo=datetime.timezone.utc)
        stub_result = [self.origin_visit1, {
            'date': date_origin_visit2,
            'origin': 1,
            'visit': 2,
            'target': hex_to_hash('65a55bbdf3629f916219feb3dcc7393ded1bc8db'),
            'branch': b'master',
            'target_type': 'release'
        }, {
            'date': date_origin_visit3,
            'origin': 1,
            'visit': 3
        }]
        mock_backend.lookup_origin_visits.return_value = stub_result

        # when
        expected_origin_visits = [{
            'date': self.origin_visit1['date'].timestamp(),
            'origin': self.origin_visit1['origin'],
            'visit': self.origin_visit1['visit']
        }, {
            'date': date_origin_visit2.timestamp(),
            'origin': 1,
            'visit': 2,
            'target': '65a55bbdf3629f916219feb3dcc7393ded1bc8db',
            'branch': 'master',
            'target_type': 'release'
        }, {
            'date': date_origin_visit3.timestamp(),
            'origin': 1,
            'visit': 3
        }]

        actual_origin_visits = service.lookup_origin_visits(6)

        # then
        self.assertEqual(list(actual_origin_visits), expected_origin_visits)

        mock_backend.lookup_origin_visits.assert_called_once_with(6)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_origin_visit(self, mock_backend):
        # given
        stub_result = self.origin_visit1
        mock_backend.lookup_origin_visit.return_value = stub_result

        expected_origin_visit = {
            'date': self.origin_visit1['date'].timestamp(),
            'origin': self.origin_visit1['origin'],
            'visit': self.origin_visit1['visit']
        }

        # when
        actual_origin_visit = service.lookup_origin_visit(1, 1)

        # then
        self.assertEqual(actual_origin_visit, expected_origin_visit)

        mock_backend.lookup_origin_visit.assert_called_once_with(1, 1)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_origin(self, mock_backend):
        # given
        mock_backend.origin_get = MagicMock(return_value={
            'id': 'origin-id',
            'lister': 'uuid-lister',
            'project': 'uuid-project',
            'url': 'ftp://some/url/to/origin',
            'type': 'ftp'})

        # when
        actual_origin = service.lookup_origin({'id': 'origin-id'})

        # then
        self.assertEqual(actual_origin, {'id': 'origin-id',
                                         'lister': 'uuid-lister',
                                         'project': 'uuid-project',
                                         'url': 'ftp://some/url/to/origin',
                                         'type': 'ftp'})

        mock_backend.origin_get.assert_called_with({'id': 'origin-id'})

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_release_ko_id_checksum_not_ok_because_not_a_sha1(self,
                                                                mock_backend):
        # given
        mock_backend.release_get = MagicMock()

        with self.assertRaises(BadInputExc) as cm:
            # when
            service.lookup_release('not-a-sha1')
            self.assertIn('invalid checksum', cm.exception.args[0])

        mock_backend.release_get.called = False

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_release_ko_id_checksum_ok_but_not_a_sha1(self, mock_backend):
        # given
        mock_backend.release_get = MagicMock()

        # when
        with self.assertRaises(BadInputExc) as cm:
            service.lookup_release(
                '13c1d34d138ec13b5ebad226dc2528dc7506c956e4646f62d4daf5'
                '1aea892abe')
            self.assertIn('sha1_git supported', cm.exception.args[0])

        mock_backend.release_get.called = False

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_directory_with_path_not_found(self, mock_backend):
        # given
        mock_backend.lookup_directory_with_path = MagicMock(return_value=None)

        sha1_git = '65a55bbdf3629f916219feb3dcc7393ded1bc8db'

        # when
        actual_directory = mock_backend.lookup_directory_with_path(
            sha1_git, 'some/path/here')

        self.assertIsNone(actual_directory)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_directory_with_path_found(self, mock_backend):
        # given
        sha1_git = '65a55bbdf3629f916219feb3dcc7393ded1bc8db'
        entry = {'id': 'dir-id',
                 'type': 'dir',
                 'name': 'some/path/foo'}

        mock_backend.lookup_directory_with_path = MagicMock(return_value=entry)

        # when
        actual_directory = mock_backend.lookup_directory_with_path(
            sha1_git, 'some/path/here')

        self.assertEqual(entry, actual_directory)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_release(self, mock_backend):
        # given
        mock_backend.release_get = MagicMock(return_value={
            'id': hex_to_hash('65a55bbdf3629f916219feb3dcc7393ded1bc8db'),
            'target': None,
            'date': {
                'timestamp': datetime.datetime(
                    2015, 1, 1, 22, 0, 0,
                    tzinfo=datetime.timezone.utc).timestamp(),
                'offset': 0,
                'negative_utc': True,
            },
            'name': b'v0.0.1',
            'message': b'synthetic release',
            'synthetic': True,
        })

        # when
        actual_release = service.lookup_release(
            '65a55bbdf3629f916219feb3dcc7393ded1bc8db')

        # then
        self.assertEqual(actual_release, {
            'id': '65a55bbdf3629f916219feb3dcc7393ded1bc8db',
            'target': None,
            'date': '2015-01-01T22:00:00-00:00',
            'name': 'v0.0.1',
            'message': 'synthetic release',
            'synthetic': True,
        })

        mock_backend.release_get.assert_called_with(
            hex_to_hash('65a55bbdf3629f916219feb3dcc7393ded1bc8db'))

    @istest
    def lookup_revision_with_context_ko_not_a_sha1_1(self):
        # given
        sha1_git = '13c1d34d138ec13b5ebad226dc2528dc7506c956e4646f62d4' \
                   'daf51aea892abe'
        sha1_git_root = '65a55bbdf3629f916219feb3dcc7393ded1bc8db'

        # when
        with self.assertRaises(BadInputExc) as cm:
            service.lookup_revision_with_context(sha1_git_root, sha1_git)
            self.assertIn('Only sha1_git is supported', cm.exception.args[0])

    @istest
    def lookup_revision_with_context_ko_not_a_sha1_2(self):
        # given
        sha1_git_root = '65a55bbdf3629f916219feb3dcc7393ded1bc8db'
        sha1_git = '13c1d34d138ec13b5ebad226dc2528dc7506c956e4646f6' \
                   '2d4daf51aea892abe'

        # when
        with self.assertRaises(BadInputExc) as cm:
            service.lookup_revision_with_context(sha1_git_root, sha1_git)
            self.assertIn('Only sha1_git is supported', cm.exception.args[0])

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_with_context_ko_sha1_git_does_not_exist(
            self,
            mock_backend):
        # given
        sha1_git_root = '65a55bbdf3629f916219feb3dcc7393ded1bc8db'
        sha1_git = '777777bdf3629f916219feb3dcc7393ded1bc8db'

        sha1_git_bin = hex_to_hash(sha1_git)

        mock_backend.revision_get.return_value = None

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_with_context(sha1_git_root, sha1_git)
            self.assertIn('Revision 777777bdf3629f916219feb3dcc7393ded1bc8db'
                          ' not found', cm.exception.args[0])

        mock_backend.revision_get.assert_called_once_with(
            sha1_git_bin)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_with_context_ko_root_sha1_git_does_not_exist(
            self,
            mock_backend):
        # given
        sha1_git_root = '65a55bbdf3629f916219feb3dcc7393ded1bc8db'
        sha1_git = '777777bdf3629f916219feb3dcc7393ded1bc8db'

        sha1_git_root_bin = hex_to_hash(sha1_git_root)
        sha1_git_bin = hex_to_hash(sha1_git)

        mock_backend.revision_get.side_effect = ['foo', None]

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_with_context(sha1_git_root, sha1_git)
            self.assertIn('Revision 65a55bbdf3629f916219feb3dcc7393ded1bc8db'
                          ' not found', cm.exception.args[0])

        mock_backend.revision_get.assert_has_calls([call(sha1_git_bin),
                                                    call(sha1_git_root_bin)])

    @patch('swh.web.ui.service.backend')
    @patch('swh.web.ui.service.query')
    @istest
    def lookup_revision_with_context(self, mock_query, mock_backend):
        # given
        sha1_git_root = '666'
        sha1_git = '883'

        sha1_git_root_bin = b'666'
        sha1_git_bin = b'883'

        sha1_git_root_dict = {
            'id': sha1_git_root_bin,
            'parents': [b'999'],
        }
        sha1_git_dict = {
            'id': sha1_git_bin,
            'parents': [],
            'directory': b'278',
        }

        stub_revisions = [
            sha1_git_root_dict,
            {
                'id': b'999',
                'parents': [b'777', b'883', b'888'],
            },
            {
                'id': b'777',
                'parents': [b'883'],
            },
            sha1_git_dict,
            {
                'id': b'888',
                'parents': [b'889'],
            },
            {
                'id': b'889',
                'parents': [],
            },
        ]

        # inputs ok
        mock_query.parse_hash_with_algorithms_or_throws.side_effect = [
            ('sha1', sha1_git_bin),
            ('sha1', sha1_git_root_bin)
        ]

        # lookup revision first 883, then 666 (both exists)
        mock_backend.revision_get.side_effect = [
            sha1_git_dict,
            sha1_git_root_dict
        ]

        mock_backend.revision_log = MagicMock(
            return_value=stub_revisions)

        # when

        actual_revision = service.lookup_revision_with_context(
            sha1_git_root,
            sha1_git)

        # then
        self.assertEquals(actual_revision, {
            'id': hash_to_hex(sha1_git_bin),
            'parents': [],
            'children': [hash_to_hex(b'999'), hash_to_hex(b'777')],
            'directory': hash_to_hex(b'278'),
            'merge': False
        })

        mock_query.parse_hash_with_algorithms_or_throws.assert_has_calls(
            [call(sha1_git, ['sha1'], 'Only sha1_git is supported.'),
             call(sha1_git_root, ['sha1'], 'Only sha1_git is supported.')])

        mock_backend.revision_log.assert_called_with(
            sha1_git_root_bin, 100)

    @patch('swh.web.ui.service.backend')
    @patch('swh.web.ui.service.query')
    @istest
    def lookup_revision_with_context_sha1_git_root_already_retrieved_as_dict(
            self, mock_query, mock_backend):
        # given
        sha1_git = '883'

        sha1_git_root_bin = b'666'
        sha1_git_bin = b'883'

        sha1_git_root_dict = {
            'id': sha1_git_root_bin,
            'parents': [b'999'],
        }

        sha1_git_dict = {
            'id': sha1_git_bin,
            'parents': [],
            'directory': b'278',
        }

        stub_revisions = [
            sha1_git_root_dict,
            {
                'id': b'999',
                'parents': [b'777', b'883', b'888'],
            },
            {
                'id': b'777',
                'parents': [b'883'],
            },
            sha1_git_dict,
            {
                'id': b'888',
                'parents': [b'889'],
            },
            {
                'id': b'889',
                'parents': [],
            },
        ]

        # inputs ok
        mock_query.parse_hash_with_algorithms_or_throws.return_value = (
            'sha1', sha1_git_bin)

        # lookup only on sha1
        mock_backend.revision_get.return_value = sha1_git_dict

        mock_backend.revision_log.return_value = stub_revisions

        # when
        actual_revision = service.lookup_revision_with_context(
            {'id': sha1_git_root_bin},
            sha1_git)

        # then
        self.assertEquals(actual_revision, {
            'id': hash_to_hex(sha1_git_bin),
            'parents': [],
            'children': [hash_to_hex(b'999'), hash_to_hex(b'777')],
            'directory': hash_to_hex(b'278'),
            'merge': False
        })

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with(  # noqa
            sha1_git, ['sha1'], 'Only sha1_git is supported.')

        mock_backend.revision_get.assert_called_once_with(sha1_git_bin)

        mock_backend.revision_log.assert_called_with(
            sha1_git_root_bin, 100)

    @patch('swh.web.ui.service.backend')
    @patch('swh.web.ui.service.query')
    @istest
    def lookup_directory_with_revision_ko_revision_not_found(self,
                                                             mock_query,
                                                             mock_backend):
        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')
        mock_backend.revision_get.return_value = None

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_directory_with_revision('123')
            self.assertIn('Revision 123 not found', cm.exception.args[0])

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with
        ('123', ['sha1'], 'Only sha1_git is supported.')
        mock_backend.revision_get.assert_called_once_with(b'123')

    @patch('swh.web.ui.service.backend')
    @patch('swh.web.ui.service.query')
    @istest
    def lookup_directory_with_revision_ko_revision_with_path_to_nowhere(
            self,
            mock_query,
            mock_backend):
        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')

        dir_id = b'dir-id-as-sha1'
        mock_backend.revision_get.return_value = {
            'directory': dir_id,
        }

        mock_backend.directory_entry_get_by_path.return_value = None

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_directory_with_revision(
                '123',
                'path/to/something/unknown')
            self.assertIn("Directory/File 'path/to/something/unknown' " +
                          "pointed to by revision 123 not found",
                          cm.exception.args[0])

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with
        ('123', ['sha1'], 'Only sha1_git is supported.')
        mock_backend.revision_get.assert_called_once_with(b'123')
        mock_backend.directory_entry_get_by_path.assert_called_once_with(
            b'dir-id-as-sha1', 'path/to/something/unknown')

    @patch('swh.web.ui.service.backend')
    @patch('swh.web.ui.service.query')
    @istest
    def lookup_directory_with_revision_ko_type_not_implemented(
            self,
            mock_query,
            mock_backend):

        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')

        dir_id = b'dir-id-as-sha1'
        mock_backend.revision_get.return_value = {
            'directory': dir_id,
        }

        mock_backend.directory_entry_get_by_path.return_value = {
            'type': 'rev',
            'name': b'some/path/to/rev',
            'target': b'456'
        }

        stub_content = {
            'id': b'12',
            'type': 'file'
        }

        mock_backend.content_get.return_value = stub_content

        # when
        with self.assertRaises(NotImplementedError) as cm:
            service.lookup_directory_with_revision(
                '123',
                'some/path/to/rev')
            self.assertIn("Entity of type 'rev' not implemented.",
                          cm.exception.args[0])

        # then
        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with
        ('123', ['sha1'], 'Only sha1_git is supported.')
        mock_backend.revision_get.assert_called_once_with(b'123')
        mock_backend.directory_entry_get_by_path.assert_called_once_with(
            b'dir-id-as-sha1', 'some/path/to/rev')

    @patch('swh.web.ui.service.backend')
    @patch('swh.web.ui.service.query')
    @istest
    def lookup_directory_with_revision_revision_without_path(self,
                                                             mock_query,
                                                             mock_backend):
        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')

        dir_id = b'dir-id-as-sha1'
        mock_backend.revision_get.return_value = {
            'directory': dir_id,
        }

        stub_dir_entries = [{
            'id': b'123',
            'type': 'dir'
        }, {
            'id': b'456',
            'type': 'file'
        }]

        mock_backend.directory_ls.return_value = stub_dir_entries

        # when
        actual_directory_entries = service.lookup_directory_with_revision(
            '123')

        self.assertEqual(actual_directory_entries['type'], 'dir')
        self.assertEqual(list(actual_directory_entries['content']),
                         stub_dir_entries)

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with
        ('123', ['sha1'], 'Only sha1_git is supported.')
        mock_backend.revision_get.assert_called_once_with(b'123')
        mock_backend.directory_ls.assert_called_once_with(dir_id)

    @patch('swh.web.ui.service.backend')
    @patch('swh.web.ui.service.query')
    @istest
    def lookup_directory_with_revision_revision_with_path_to_dir(self,
                                                                 mock_query,
                                                                 mock_backend):
        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')

        dir_id = b'dir-id-as-sha1'
        mock_backend.revision_get.return_value = {
            'directory': dir_id,
        }

        stub_dir_entries = [{
            'id': b'12',
            'type': 'dir'
        }, {
            'id': b'34',
            'type': 'file'
        }]

        mock_backend.directory_entry_get_by_path.return_value = {
            'type': 'dir',
            'name': b'some/path',
            'target': b'456'
        }
        mock_backend.directory_ls.return_value = stub_dir_entries

        # when
        actual_directory_entries = service.lookup_directory_with_revision(
            '123',
            'some/path')

        self.assertEqual(actual_directory_entries['type'], 'dir')
        self.assertEqual(actual_directory_entries['revision'], '123')
        self.assertEqual(actual_directory_entries['path'], 'some/path')
        self.assertEqual(list(actual_directory_entries['content']),
                         stub_dir_entries)

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with
        ('123', ['sha1'], 'Only sha1_git is supported.')
        mock_backend.revision_get.assert_called_once_with(b'123')
        mock_backend.directory_entry_get_by_path.assert_called_once_with(
            dir_id,
            'some/path')
        mock_backend.directory_ls.assert_called_once_with(b'456')

    @patch('swh.web.ui.service.backend')
    @patch('swh.web.ui.service.query')
    @istest
    def lookup_directory_with_revision_revision_with_path_to_file_without_data(
            self,
            mock_query,
            mock_backend):

        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')

        dir_id = b'dir-id-as-sha1'
        mock_backend.revision_get.return_value = {
            'directory': dir_id,
        }

        mock_backend.directory_entry_get_by_path.return_value = {
                'type': 'file',
                'name': b'some/path/to/file',
                'target': b'789'
            }

        stub_content = {
            'status': 'visible',
        }

        mock_backend.content_find.return_value = stub_content

        # when
        actual_content = service.lookup_directory_with_revision(
            '123',
            'some/path/to/file')

        # then
        self.assertEqual(actual_content, {'type': 'file',
                                          'revision': '123',
                                          'path': 'some/path/to/file',
                                          'content': stub_content})

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with
        ('123', ['sha1'], 'Only sha1_git is supported.')
        mock_backend.revision_get.assert_called_once_with(b'123')
        mock_backend.directory_entry_get_by_path.assert_called_once_with(
            b'dir-id-as-sha1', 'some/path/to/file')
        mock_backend.content_find.assert_called_once_with('sha1_git', b'789')

    @patch('swh.web.ui.service.backend')
    @patch('swh.web.ui.service.query')
    @istest
    def lookup_directory_with_revision_revision_with_path_to_file_with_data(
            self,
            mock_query,
            mock_backend):

        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')

        dir_id = b'dir-id-as-sha1'
        mock_backend.revision_get.return_value = {
            'directory': dir_id,
        }

        mock_backend.directory_entry_get_by_path.return_value = {
                'type': 'file',
                'name': b'some/path/to/file',
                'target': b'789'
            }

        stub_content = {
            'status': 'visible',
            'sha1': b'content-sha1'
        }

        mock_backend.content_find.return_value = stub_content
        mock_backend.content_get.return_value = {
            'sha1': b'content-sha1',
            'data': b'some raw data'
        }

        expected_content = {
            'status': 'visible',
            'sha1': hash_to_hex(b'content-sha1'),
            'data': b'some raw data'
        }

        # when
        actual_content = service.lookup_directory_with_revision(
            '123',
            'some/path/to/file',
            with_data=True)

        # then
        self.assertEqual(actual_content, {'type': 'file',
                                          'revision': '123',
                                          'path': 'some/path/to/file',
                                          'content': expected_content})

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with
        ('123', ['sha1'], 'Only sha1_git is supported.')
        mock_backend.revision_get.assert_called_once_with(b'123')
        mock_backend.directory_entry_get_by_path.assert_called_once_with(
            b'dir-id-as-sha1', 'some/path/to/file')
        mock_backend.content_find.assert_called_once_with('sha1_git', b'789')
        mock_backend.content_get.assert_called_once_with(b'content-sha1')

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision(self, mock_backend):
        # given
        mock_backend.revision_get = MagicMock(
            return_value=self.SAMPLE_REVISION_RAW)

        # when
        actual_revision = service.lookup_revision(
            self.SHA1_SAMPLE)

        # then
        self.assertEqual(actual_revision, self.SAMPLE_REVISION)

        mock_backend.revision_get.assert_called_with(
            self.SHA1_SAMPLE_BIN)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_invalid_msg(self, mock_backend):
        # given
        stub_rev = self.SAMPLE_REVISION_RAW
        stub_rev['message'] = b'elegant fix for bug \xff'

        expected_revision = self.SAMPLE_REVISION
        expected_revision['message'] = None
        expected_revision['message_decoding_failed'] = True
        mock_backend.revision_get = MagicMock(return_value=stub_rev)

        # when
        actual_revision = service.lookup_revision(
            self.SHA1_SAMPLE)

        # then
        self.assertEqual(actual_revision, expected_revision)

        mock_backend.revision_get.assert_called_with(
            self.SHA1_SAMPLE_BIN)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_msg_ok(self, mock_backend):
        # given
        mock_backend.revision_get.return_value = self.SAMPLE_REVISION_RAW

        # when
        rv = service.lookup_revision_message(
            self.SHA1_SAMPLE)

        # then
        self.assertEquals(rv, {'message': self.SAMPLE_MESSAGE_BIN})
        mock_backend.revision_get.assert_called_with(
            self.SHA1_SAMPLE_BIN)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_msg_absent(self, mock_backend):
        # given
        stub_revision = self.SAMPLE_REVISION_RAW
        del stub_revision['message']
        mock_backend.revision_get.return_value = stub_revision

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_message(
                self.SHA1_SAMPLE)

            # then
            mock_backend.revision_get.assert_called_with(
                self.SHA1_SAMPLE_BIN)
            self.assertEqual(cm.exception.args[0], 'No message for revision '
                             'with sha1_git '
                             '18d8be353ed3480476f032475e7c233eff7371d5.')

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_msg_norev(self, mock_backend):
        # given
        mock_backend.revision_get.return_value = None

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_message(
                self.SHA1_SAMPLE)

            # then
            mock_backend.revision_get.assert_called_with(
                self.SHA1_SAMPLE_BIN)
            self.assertEqual(cm.exception.args[0], 'Revision with sha1_git '
                             '18d8be353ed3480476f032475e7c233eff7371d5 '
                             'not found.')

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_multiple(self, mock_backend):
        # given
        sha1 = self.SHA1_SAMPLE
        sha1_other = 'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'

        stub_revisions = [
            self.SAMPLE_REVISION_RAW,
            {
                'id': hex_to_hash(sha1_other),
                'directory': 'abcdbe353ed3480476f032475e7c233eff7371d5',
                'author': {
                    'name': b'name',
                    'email': b'name@surname.org',
                },
                'committer': {
                    'name': b'name',
                    'email': b'name@surname.org',
                },
                'message': b'ugly fix for bug 42',
                'date': {
                    'timestamp': datetime.datetime(
                        2000, 1, 12, 5, 23, 54,
                        tzinfo=datetime.timezone.utc).timestamp(),
                    'offset': 0,
                    'negative_utc': False
                    },
                'date_offset': 0,
                'committer_date': {
                    'timestamp': datetime.datetime(
                        2000, 1, 12, 5, 23, 54,
                        tzinfo=datetime.timezone.utc).timestamp(),
                    'offset': 0,
                    'negative_utc': False
                    },
                'committer_date_offset': 0,
                'synthetic': False,
                'type': 'git',
                'parents': [],
                'metadata': [],
            }
        ]

        mock_backend.revision_get_multiple.return_value = stub_revisions

        # when
        actual_revisions = service.lookup_revision_multiple(
            [sha1, sha1_other])

        # then
        self.assertEqual(list(actual_revisions), [
            self.SAMPLE_REVISION,
            {
                'id': sha1_other,
                'directory': 'abcdbe353ed3480476f032475e7c233eff7371d5',
                'author': {
                    'name': 'name',
                    'email': 'name@surname.org',
                },
                'committer': {
                    'name': 'name',
                    'email': 'name@surname.org',
                },
                'message': 'ugly fix for bug 42',
                'date': '2000-01-12T05:23:54+00:00',
                'date_offset': 0,
                'committer_date': '2000-01-12T05:23:54+00:00',
                'committer_date_offset': 0,
                'synthetic': False,
                'type': 'git',
                'parents': [],
                'metadata': [],
                'merge': False
            }
        ])

        self.assertEqual(
            list(mock_backend.revision_get_multiple.call_args[0][0]),
            [hex_to_hash(sha1),
             hex_to_hash(sha1_other)])

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_multiple_none_found(self, mock_backend):
        # given
        sha1_bin = self.SHA1_SAMPLE
        sha1_other = 'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'

        mock_backend.revision_get_multiple.return_value = []

        # then
        actual_revisions = service.lookup_revision_multiple(
            [sha1_bin, sha1_other])

        self.assertEqual(list(actual_revisions), [])

        self.assertEqual(
            list(mock_backend.revision_get_multiple.call_args[0][0]),
            [hex_to_hash(self.SHA1_SAMPLE),
             hex_to_hash(sha1_other)])

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_log(self, mock_backend):
        # given
        stub_revision_log = [self.SAMPLE_REVISION_RAW]
        mock_backend.revision_log = MagicMock(return_value=stub_revision_log)

        # when
        actual_revision = service.lookup_revision_log(
            'abcdbe353ed3480476f032475e7c233eff7371d5',
            limit=25)

        # then
        self.assertEqual(list(actual_revision), [self.SAMPLE_REVISION])

        mock_backend.revision_log.assert_called_with(
            hex_to_hash('abcdbe353ed3480476f032475e7c233eff7371d5'), 25)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_log_by(self, mock_backend):
        # given
        stub_revision_log = [self.SAMPLE_REVISION_RAW]
        mock_backend.revision_log_by = MagicMock(
            return_value=stub_revision_log)

        # when
        actual_log = service.lookup_revision_log_by(
            1, 'refs/heads/master', None, limit=100)
        # then
        self.assertEqual(list(actual_log), [self.SAMPLE_REVISION])

        mock_backend.revision_log_by.assert_called_with(
            1, 'refs/heads/master', None, 100)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_log_by_nolog(self, mock_backend):
        # given
        mock_backend.revision_log_by = MagicMock(return_value=None)

        # when
        res = service.lookup_revision_log_by(
            1, 'refs/heads/master', None, limit=100)
        # then
        self.assertEquals(res, None)
        mock_backend.revision_log_by.assert_called_with(
            1, 'refs/heads/master', None, 100)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_raw_not_found(self, mock_backend):
        # given
        mock_backend.content_find = MagicMock(return_value=None)

        # when
        actual_content = service.lookup_content_raw(
            'sha1:18d8be353ed3480476f032475e7c233eff7371d5')

        # then
        self.assertIsNone(actual_content)

        mock_backend.content_find.assert_called_with(
            'sha1', hex_to_hash(self.SHA1_SAMPLE))

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_raw(self, mock_backend):
        # given
        mock_backend.content_find = MagicMock(return_value={
            'sha1': self.SHA1_SAMPLE,
        })
        mock_backend.content_get = MagicMock(return_value={
            'data': b'binary data'})

        # when
        actual_content = service.lookup_content_raw(
            'sha256:%s' % self.SHA256_SAMPLE)

        # then
        self.assertEquals(actual_content, {'data': b'binary data'})

        mock_backend.content_find.assert_called_once_with(
            'sha256', self.SHA256_SAMPLE_BIN)
        mock_backend.content_get.assert_called_once_with(
            self.SHA1_SAMPLE)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_not_found(self, mock_backend):
        # given
        mock_backend.content_find = MagicMock(return_value=None)

        # when
        actual_content = service.lookup_content(
            'sha1:%s' % self.SHA1_SAMPLE)

        # then
        self.assertIsNone(actual_content)

        mock_backend.content_find.assert_called_with(
            'sha1', self.SHA1_SAMPLE_BIN)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_with_sha1(self, mock_backend):
        # given
        mock_backend.content_find = MagicMock(
            return_value=self.SAMPLE_CONTENT_RAW)

        # when
        actual_content = service.lookup_content(
            'sha1:%s' % self.SHA1_SAMPLE)

        # then
        self.assertEqual(actual_content, self.SAMPLE_CONTENT)

        mock_backend.content_find.assert_called_with(
            'sha1', hex_to_hash(self.SHA1_SAMPLE))

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_content_with_sha256(self, mock_backend):
        # given
        stub_content = self.SAMPLE_CONTENT_RAW
        stub_content['status'] = 'visible'

        expected_content = self.SAMPLE_CONTENT
        expected_content['status'] = 'visible'
        mock_backend.content_find = MagicMock(
            return_value=stub_content)

        # when
        actual_content = service.lookup_content(
            'sha256:%s' % self.SHA256_SAMPLE)

        # then
        self.assertEqual(actual_content, expected_content)

        mock_backend.content_find.assert_called_with(
            'sha256', self.SHA256_SAMPLE_BIN)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_person(self, mock_backend):
        # given
        mock_backend.person_get = MagicMock(return_value={
            'id': 'person_id',
            'name': b'some_name',
            'email': b'some-email',
        })

        # when
        actual_person = service.lookup_person('person_id')

        # then
        self.assertEqual(actual_person, {
            'id': 'person_id',
            'name': 'some_name',
            'email': 'some-email',
        })

        mock_backend.person_get.assert_called_with('person_id')

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_directory_bad_checksum(self, mock_backend):
        # given
        mock_backend.directory_ls = MagicMock()

        # when
        with self.assertRaises(BadInputExc):
            service.lookup_directory('directory_id')

        # then
        mock_backend.directory_ls.called = False

    @patch('swh.web.ui.service.backend')
    @patch('swh.web.ui.service.query')
    @istest
    def lookup_directory_not_found(self, mock_query, mock_backend):
        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = (
            'sha1',
            'directory-id-bin')
        mock_backend.directory_get.return_value = None

        # when
        actual_dir = service.lookup_directory('directory_id')

        # then
        self.assertIsNone(actual_dir)

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_with(
            'directory_id', ['sha1'], 'Only sha1_git is supported.')
        mock_backend.directory_get.assert_called_with('directory-id-bin')
        mock_backend.directory_ls.called = False

    @patch('swh.web.ui.service.backend')
    @patch('swh.web.ui.service.query')
    @istest
    def lookup_directory(self, mock_query, mock_backend):
        mock_query.parse_hash_with_algorithms_or_throws.return_value = (
            'sha1',
            'directory-sha1-bin')

        # something that exists is all that matters here
        mock_backend.directory_get.return_value = {'id': b'directory-sha1-bin'}

        # given
        stub_dir_entries = [{
            'sha1': self.SHA1_SAMPLE_BIN,
            'sha256': self.SHA256_SAMPLE_BIN,
            'sha1_git': self.SHA1GIT_SAMPLE_BIN,
            'target': hex_to_hash('40e71b8614fcd89ccd17ca2b1d9e66'
                                  'c5b00a6d03'),
            'dir_id': self.DIRECTORY_ID_BIN,
            'name': b'bob',
            'type': 10,
        }]

        expected_dir_entries = [{
            'sha1': self.SHA1_SAMPLE,
            'sha256': self.SHA256_SAMPLE,
            'sha1_git': self.SHA1GIT_SAMPLE,
            'target': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'dir_id': self.DIRECTORY_ID,
            'name': 'bob',
            'type': 10,
        }]

        mock_backend.directory_ls.return_value = stub_dir_entries

        # when
        actual_directory_ls = list(service.lookup_directory(
            'directory-sha1'))

        # then
        self.assertEqual(actual_directory_ls, expected_dir_entries)

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_with(
            'directory-sha1', ['sha1'], 'Only sha1_git is supported.')
        mock_backend.directory_ls.assert_called_with(
            'directory-sha1-bin')

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_by_nothing_found(self, mock_backend):
        # given
        mock_backend.revision_get_by.return_value = None

        # when
        actual_revisions = service.lookup_revision_by(1)

        # then
        self.assertIsNone(actual_revisions)

        mock_backend.revision_get_by(1, 'master', None)

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_by(self, mock_backend):
        # given
        stub_rev = self.SAMPLE_REVISION_RAW

        expected_rev = self.SAMPLE_REVISION

        mock_backend.revision_get_by.return_value = stub_rev

        # when
        actual_revision = service.lookup_revision_by(10, 'master2', 'some-ts')

        # then
        self.assertEquals(actual_revision, expected_rev)

        mock_backend.revision_get_by(1, 'master2', 'some-ts')

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_by_nomerge(self, mock_backend):
        # given
        stub_rev = self.SAMPLE_REVISION_RAW
        stub_rev['parents'] = [
                hex_to_hash('adc83b19e793491b1c6ea0fd8b46cd9f32e592fc')]

        expected_rev = self.SAMPLE_REVISION
        expected_rev['parents'] = ['adc83b19e793491b1c6ea0fd8b46cd9f32e592fc']
        mock_backend.revision_get_by.return_value = stub_rev

        # when
        actual_revision = service.lookup_revision_by(10, 'master2', 'some-ts')

        # then
        self.assertEquals(actual_revision, expected_rev)

        mock_backend.revision_get_by(1, 'master2', 'some-ts')

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_by_merge(self, mock_backend):
        # given
        stub_rev = self.SAMPLE_REVISION_RAW
        stub_rev['parents'] = [
            hex_to_hash('adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'),
            hex_to_hash('ffff3b19e793491b1c6db0fd8b46cd9f32e592fc')
        ]

        expected_rev = self.SAMPLE_REVISION
        expected_rev['parents'] = [
            'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
            'ffff3b19e793491b1c6db0fd8b46cd9f32e592fc'
        ]
        expected_rev['merge'] = True

        mock_backend.revision_get_by.return_value = stub_rev

        # when
        actual_revision = service.lookup_revision_by(10, 'master2', 'some-ts')

        # then
        self.assertEquals(actual_revision, expected_rev)

        mock_backend.revision_get_by(1, 'master2', 'some-ts')

    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_with_context_by_ko(self, mock_backend):
        # given
        mock_backend.revision_get_by.return_value = None

        # when
        with self.assertRaises(NotFoundExc) as cm:
            origin_id = 1
            branch_name = 'master3'
            ts = None
            service.lookup_revision_with_context_by(origin_id, branch_name, ts,
                                                    'sha1')
            # then
            self.assertIn(
                'Revision with (origin_id: %s, branch_name: %s'
                ', ts: %s) not found.' % (origin_id,
                                          branch_name,
                                          ts), cm.exception.args[0])

            mock_backend.revision_get_by.assert_called_once_with(
                origin_id, branch_name, ts)

    @patch('swh.web.ui.service.lookup_revision_with_context')
    @patch('swh.web.ui.service.backend')
    @istest
    def lookup_revision_with_context_by(self, mock_backend,
                                        mock_lookup_revision_with_context):
        # given
        stub_root_rev = {'id': 'root-rev-id'}
        mock_backend.revision_get_by.return_value = {'id': 'root-rev-id'}
        stub_rev = {'id': 'rev-found'}
        mock_lookup_revision_with_context.return_value = stub_rev

        # when
        origin_id = 1
        branch_name = 'master3'
        ts = None
        sha1_git = 'sha1'
        actual_root_rev, actual_rev = service.lookup_revision_with_context_by(
            origin_id, branch_name, ts, sha1_git)

        # then
        self.assertEquals(actual_root_rev, stub_root_rev)
        self.assertEquals(actual_rev, stub_rev)

        mock_backend.revision_get_by.assert_called_once_with(
            origin_id, branch_name, ts)
        mock_lookup_revision_with_context.assert_called_once_with(
            stub_root_rev, sha1_git, 100)

    @patch('swh.web.ui.service.backend')
    @patch('swh.web.ui.service.query')
    @istest
    def lookup_entity_by_uuid(self, mock_query, mock_backend):
        # given
        uuid_test = 'correct-uuid'
        mock_query.parse_uuid4.return_value = uuid_test
        stub_entities = [{'uuid': uuid_test}]

        mock_backend.entity_get.return_value = stub_entities

        # when
        actual_entities = service.lookup_entity_by_uuid(uuid_test)

        # then
        self.assertEquals(actual_entities, stub_entities)

        mock_query.parse_uuid4.assert_called_once_with(uuid_test)
        mock_backend.entity_get.assert_called_once_with(uuid_test)

    @istest
    def lookup_revision_through_ko_not_implemented(self):
        # then
        with self.assertRaises(NotImplementedError):
            service.lookup_revision_through({
                'something-unknown': 10,
            })

    @patch('swh.web.ui.service.lookup_revision_with_context_by')
    @istest
    def lookup_revision_through_with_context_by(self, mock_lookup):
        # given
        stub_rev = {'id': 'rev'}
        mock_lookup.return_value = stub_rev

        # when
        actual_revision = service.lookup_revision_through({
            'origin_id': 1,
            'branch_name': 'master',
            'ts': None,
            'sha1_git': 'sha1-git'
        }, limit=1000)

        # then
        self.assertEquals(actual_revision, stub_rev)

        mock_lookup.assert_called_once_with(
            1, 'master', None, 'sha1-git', 1000)

    @patch('swh.web.ui.service.lookup_revision_by')
    @istest
    def lookup_revision_through_with_revision_by(self, mock_lookup):
        # given
        stub_rev = {'id': 'rev'}
        mock_lookup.return_value = stub_rev

        # when
        actual_revision = service.lookup_revision_through({
            'origin_id': 2,
            'branch_name': 'master2',
            'ts': 'some-ts',
        }, limit=10)

        # then
        self.assertEquals(actual_revision, stub_rev)

        mock_lookup.assert_called_once_with(
            2, 'master2', 'some-ts')

    @patch('swh.web.ui.service.lookup_revision_with_context')
    @istest
    def lookup_revision_through_with_context(self, mock_lookup):
        # given
        stub_rev = {'id': 'rev'}
        mock_lookup.return_value = stub_rev

        # when
        actual_revision = service.lookup_revision_through({
            'sha1_git_root': 'some-sha1-root',
            'sha1_git': 'some-sha1',
        })

        # then
        self.assertEquals(actual_revision, stub_rev)

        mock_lookup.assert_called_once_with(
            'some-sha1-root', 'some-sha1', 100)

    @patch('swh.web.ui.service.lookup_revision')
    @istest
    def lookup_revision_through_with_revision(self, mock_lookup):
        # given
        stub_rev = {'id': 'rev'}
        mock_lookup.return_value = stub_rev

        # when
        actual_revision = service.lookup_revision_through({
            'sha1_git': 'some-sha1',
        })

        # then
        self.assertEquals(actual_revision, stub_rev)

        mock_lookup.assert_called_once_with(
            'some-sha1')

    @patch('swh.web.ui.service.lookup_revision_through')
    @istest
    def lookup_directory_through_revision_ko_not_found(
            self, mock_lookup_rev):
        # given
        mock_lookup_rev.return_value = None

        # when
        with self.assertRaises(NotFoundExc):
            service.lookup_directory_through_revision(
                {'id': 'rev'}, 'some/path', 100)

        mock_lookup_rev.assert_called_once_with({'id': 'rev'}, 100)

    @patch('swh.web.ui.service.lookup_revision_through')
    @patch('swh.web.ui.service.lookup_directory_with_revision')
    @istest
    def lookup_directory_through_revision_ok_with_data(
            self, mock_lookup_dir, mock_lookup_rev):
        # given
        mock_lookup_rev.return_value = {'id': 'rev-id'}
        mock_lookup_dir.return_value = {'type': 'dir',
                                        'content': []}

        # when
        rev_id, dir_result = service.lookup_directory_through_revision(
            {'id': 'rev'}, 'some/path', 100)
        # then
        self.assertEquals(rev_id, 'rev-id')
        self.assertEquals(dir_result, {'type': 'dir',
                                       'content': []})

        mock_lookup_rev.assert_called_once_with({'id': 'rev'}, 100)
        mock_lookup_dir.assert_called_once_with('rev-id', 'some/path', False)

    @patch('swh.web.ui.service.lookup_revision_through')
    @patch('swh.web.ui.service.lookup_directory_with_revision')
    @istest
    def lookup_directory_through_revision_ok_with_content(
            self, mock_lookup_dir, mock_lookup_rev):
        # given
        mock_lookup_rev.return_value = {'id': 'rev-id'}
        stub_result = {'type': 'file',
                       'revision': 'rev-id',
                       'content': {'data': b'blah',
                                   'sha1': 'sha1'}}
        mock_lookup_dir.return_value = stub_result

        # when
        rev_id, dir_result = service.lookup_directory_through_revision(
            {'id': 'rev'}, 'some/path', 10, with_data=True)
        # then
        self.assertEquals(rev_id, 'rev-id')
        self.assertEquals(dir_result, stub_result)

        mock_lookup_rev.assert_called_once_with({'id': 'rev'}, 10)
        mock_lookup_dir.assert_called_once_with('rev-id', 'some/path', True)
