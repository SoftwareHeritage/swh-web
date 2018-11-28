# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime

from unittest.mock import MagicMock, patch, call

from swh.model.hashutil import hash_to_bytes, hash_to_hex

from swh.web.common import service
from swh.web.common.exc import BadInputExc, NotFoundExc
from swh.web.tests.testcase import SWHWebTestCase


class ServiceTestCase(SWHWebTestCase):

    def setUp(self):
        self.BLAKE2S256_SAMPLE = ('685395c5dc57cada459364f0946d3dd45b'
                                  'ad5fcbabc1048edb44380f1d31d0aa')
        self.BLAKE2S256_SAMPLE_BIN = hash_to_bytes(self.BLAKE2S256_SAMPLE)
        self.SHA1_SAMPLE = '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'
        self.SHA1_SAMPLE_BIN = hash_to_bytes(self.SHA1_SAMPLE)
        self.SHA256_SAMPLE = ('8abb0aa566452620ecce816eecdef4792d77a'
                              '293ad8ea82a4d5ecb4d36f7e560')
        self.SHA256_SAMPLE_BIN = hash_to_bytes(self.SHA256_SAMPLE)
        self.SHA1GIT_SAMPLE = '25d1a2e8f32937b0f498a5ca87f823d8df013c01'
        self.SHA1GIT_SAMPLE_BIN = hash_to_bytes(self.SHA1GIT_SAMPLE)
        self.DIRECTORY_ID = '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6'
        self.DIRECTORY_ID_BIN = hash_to_bytes(self.DIRECTORY_ID)
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
            'metadata': {},
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
            'checksums': {
                'blake2s256': self.BLAKE2S256_SAMPLE,
                'sha1': self.SHA1_SAMPLE,
                'sha256': self.SHA256_SAMPLE,
                'sha1_git': self.SHA1GIT_SAMPLE,
            },
            'length': 190,
            'status': 'absent'
        }
        self.SAMPLE_CONTENT_RAW = {
            'blake2s256': self.BLAKE2S256_SAMPLE_BIN,
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

    @patch('swh.web.common.service.storage')
    def test_lookup_multiple_hashes_ball_missing(self, mock_storage):
        # given
        mock_storage.content_missing_per_sha1 = MagicMock(return_value=[])

        # when
        actual_lookup = service.lookup_multiple_hashes(
            [{'filename': 'a',
              'sha1': '456caf10e9535160d90e874b45aa426de762f19f'},
             {'filename': 'b',
              'sha1': '745bab676c8f3cec8016e0c39ea61cf57e518865'}])

        # then
        self.assertEqual(actual_lookup, [
            {'filename': 'a',
             'sha1': '456caf10e9535160d90e874b45aa426de762f19f',
             'found': True},
            {'filename': 'b',
             'sha1': '745bab676c8f3cec8016e0c39ea61cf57e518865',
             'found': True}
        ])

    @patch('swh.web.common.service.storage')
    def test_lookup_multiple_hashes_some_missing(self, mock_storage):
        # given
        mock_storage.content_missing_per_sha1 = MagicMock(return_value=[
            hash_to_bytes('456caf10e9535160d90e874b45aa426de762f19f')
        ])

        # when
        actual_lookup = service.lookup_multiple_hashes(
            [{'filename': 'a',
              'sha1': '456caf10e9535160d90e874b45aa426de762f19f'},
             {'filename': 'b',
              'sha1': '745bab676c8f3cec8016e0c39ea61cf57e518865'}])

        # then
        self.assertEqual(actual_lookup, [
            {'filename': 'a',
             'sha1': '456caf10e9535160d90e874b45aa426de762f19f',
             'found': False},
            {'filename': 'b',
             'sha1': '745bab676c8f3cec8016e0c39ea61cf57e518865',
             'found': True}
        ])

    @patch('swh.web.common.service.storage')
    def test_lookup_hash_does_not_exist(self, mock_storage):
        # given
        mock_storage.content_find = MagicMock(return_value=None)

        # when
        actual_lookup = service.lookup_hash(
            'sha1_git:123caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual({'found': None,
                          'algo': 'sha1_git'}, actual_lookup)

        # check the function has been called with parameters
        mock_storage.content_find.assert_called_with(
            {'sha1_git':
             hash_to_bytes('123caf10e9535160d90e874b45aa426de762f19f')})

    @patch('swh.web.common.service.storage')
    def test_lookup_hash_exist(self, mock_storage):
        # given
        stub_content = {
                'sha1': hash_to_bytes(
                    '456caf10e9535160d90e874b45aa426de762f19f')
            }
        mock_storage.content_find = MagicMock(return_value=stub_content)

        # when
        actual_lookup = service.lookup_hash(
            'sha1:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual({'found': stub_content,
                          'algo': 'sha1'}, actual_lookup)

        mock_storage.content_find.assert_called_with(
            {'sha1':
             hash_to_bytes('456caf10e9535160d90e874b45aa426de762f19f')}
        )

    @patch('swh.web.common.service.storage')
    def test_search_hash_does_not_exist(self, mock_storage):
        # given
        mock_storage.content_find = MagicMock(return_value=None)

        # when
        actual_lookup = service.search_hash(
            'sha1_git:123caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual({'found': False}, actual_lookup)

        # check the function has been called with parameters
        mock_storage.content_find.assert_called_with(
            {'sha1_git':
             hash_to_bytes('123caf10e9535160d90e874b45aa426de762f19f')})

    @patch('swh.web.common.service.storage')
    def test_search_hash_exist(self, mock_storage):
        # given
        stub_content = {
                'sha1': hash_to_bytes(
                    '456caf10e9535160d90e874b45aa426de762f19f')
            }
        mock_storage.content_find = MagicMock(return_value=stub_content)

        # when
        actual_lookup = service.search_hash(
            'sha1:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual({'found': True}, actual_lookup)

        mock_storage.content_find.assert_called_with(
            {'sha1':
             hash_to_bytes('456caf10e9535160d90e874b45aa426de762f19f')},
        )

    @patch('swh.web.common.service.idx_storage')
    def test_lookup_content_ctags(self, mock_idx_storage):
        # given
        mock_idx_storage.content_ctags_get = MagicMock(
            return_value=[{
                'id': hash_to_bytes(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'line': 100,
                'name': 'hello',
                'kind': 'function',
                'tool_name': 'ctags',
                'tool_version': 'some-version',
            }])
        expected_ctags = [{
            'id': '123caf10e9535160d90e874b45aa426de762f19f',
            'line': 100,
            'name': 'hello',
            'kind': 'function',
            'tool_name': 'ctags',
            'tool_version': 'some-version',
        }]

        # when
        actual_ctags = list(service.lookup_content_ctags(
            'sha1:123caf10e9535160d90e874b45aa426de762f19f'))

        # then
        self.assertEqual(actual_ctags, expected_ctags)

        mock_idx_storage.content_ctags_get.assert_called_with(
            [hash_to_bytes('123caf10e9535160d90e874b45aa426de762f19f')])

    @patch('swh.web.common.service.idx_storage')
    def test_lookup_content_ctags_no_hash(self, mock_idx_storage):
        # given
        mock_idx_storage.content_ctags_get = MagicMock(return_value=[])

        # when
        actual_ctags = list(service.lookup_content_ctags(
            'sha1:123caf10e9535160d90e874b45aa426de762f19f'))

        # then
        self.assertEqual(actual_ctags, [])

    @patch('swh.web.common.service.idx_storage')
    def test_lookup_content_filetype(self, mock_idx_storage):
        # given
        mock_idx_storage.content_mimetype_get = MagicMock(
            return_value=[{
                'id': hash_to_bytes(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'mimetype': 'text/x-c++',
                'encoding': 'us-ascii',
            }])
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

        mock_idx_storage.content_mimetype_get.assert_called_with(
            [hash_to_bytes('123caf10e9535160d90e874b45aa426de762f19f')])

    @patch('swh.web.common.service.idx_storage')
    @patch('swh.web.common.service.storage')
    def test_lookup_content_filetype_2(self, mock_storage, mock_idx_storage):
        # given
        mock_storage.content_find = MagicMock(
            return_value={
                'sha1': hash_to_bytes(
                    '123caf10e9535160d90e874b45aa426de762f19f')
            }
        )
        mock_idx_storage.content_mimetype_get = MagicMock(
            return_value=[{
                'id': hash_to_bytes(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'mimetype': 'text/x-python',
                'encoding': 'us-ascii',
            }]
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

        mock_storage.content_find(
            'sha1_git', hash_to_bytes(
                '456caf10e9535160d90e874b45aa426de762f19f')
        )
        mock_idx_storage.content_mimetype_get.assert_called_with(
            [hash_to_bytes('123caf10e9535160d90e874b45aa426de762f19f')])

    @patch('swh.web.common.service.idx_storage')
    def test_lookup_content_language(self, mock_idx_storage):
        # given
        mock_idx_storage.content_language_get = MagicMock(
            return_value=[{
                'id': hash_to_bytes(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'lang': 'python',
            }])
        expected_language = {
                'id': '123caf10e9535160d90e874b45aa426de762f19f',
                'lang': 'python',
        }

        # when
        actual_language = service.lookup_content_language(
            'sha1:123caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual(actual_language, expected_language)

        mock_idx_storage.content_language_get.assert_called_with(
            [hash_to_bytes('123caf10e9535160d90e874b45aa426de762f19f')])

    @patch('swh.web.common.service.idx_storage')
    @patch('swh.web.common.service.storage')
    def test_lookup_content_language_2(self, mock_storage, mock_idx_storage):
        # given
        mock_storage.content_find = MagicMock(
            return_value={
                'sha1': hash_to_bytes(
                    '123caf10e9535160d90e874b45aa426de762f19f')
            }
        )
        mock_idx_storage.content_language_get = MagicMock(
            return_value=[{
                'id': hash_to_bytes(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'lang': 'haskell',
            }]
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

        mock_storage.content_find(
            'sha1_git', hash_to_bytes(
                '456caf10e9535160d90e874b45aa426de762f19f')
        )
        mock_idx_storage.content_language_get.assert_called_with(
            [hash_to_bytes('123caf10e9535160d90e874b45aa426de762f19f')])

    @patch('swh.web.common.service.idx_storage')
    def test_lookup_expression(self, mock_idx_storage):
        # given
        mock_idx_storage.content_ctags_search = MagicMock(
            return_value=[{
                'id': hash_to_bytes(
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
        actual_ctags = list(service.lookup_expression(
            'foobar', last_sha1='hash', per_page=10))

        # then
        self.assertEqual(actual_ctags, expected_ctags)

        mock_idx_storage.content_ctags_search.assert_called_with(
            'foobar', last_sha1='hash', limit=10)

    @patch('swh.web.common.service.idx_storage')
    def test_lookup_expression_no_result(self, mock_idx_storage):
        # given
        mock_idx_storage.content_ctags_search = MagicMock(
            return_value=[])
        expected_ctags = []

        # when
        actual_ctags = list(service.lookup_expression(
            'barfoo', last_sha1='hash', per_page=10))

        # then
        self.assertEqual(actual_ctags, expected_ctags)

        mock_idx_storage.content_ctags_search.assert_called_with(
            'barfoo', last_sha1='hash', limit=10)

    @patch('swh.web.common.service.idx_storage')
    def test_lookup_content_license(self, mock_idx_storage):
        # given
        mock_idx_storage.content_fossology_license_get = MagicMock(
            return_value=[{
                hash_to_bytes('123caf10e9535160d90e874b45aa426de762f19f'): [{
                    'licenses': ['GPL-3.0+'],
                    'tool': {}
                }]
            }])
        expected_license = {
                'id': '123caf10e9535160d90e874b45aa426de762f19f',
                'facts': [{
                    'licenses': ['GPL-3.0+'],
                    'tool': {}
                }]
        }

        # when
        actual_license = service.lookup_content_license(
            'sha1:123caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual(actual_license, expected_license)

        mock_idx_storage.content_fossology_license_get.assert_called_with(
            [hash_to_bytes('123caf10e9535160d90e874b45aa426de762f19f')])

    @patch('swh.web.common.service.idx_storage')
    @patch('swh.web.common.service.storage')
    def test_lookup_content_license_2(self, mock_storage, mock_idx_storage):
        # given
        mock_storage.content_find = MagicMock(
            return_value={
                'sha1': hash_to_bytes(
                    '123caf10e9535160d90e874b45aa426de762f19f')
            }
        )
        mock_idx_storage.content_fossology_license_get = MagicMock(
            return_value=[{
                hash_to_bytes('123caf10e9535160d90e874b45aa426de762f19f'): [{
                    'licenses': ['BSD-2-Clause'],
                    'tool': {}
                }]

            }]
        )
        expected_license = {
                'id': '123caf10e9535160d90e874b45aa426de762f19f',
                'facts': [{
                    'licenses': ['BSD-2-Clause'],
                    'tool': {}
                }]
        }

        # when
        actual_license = service.lookup_content_license(
            'sha1_git:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertEqual(actual_license, expected_license)

        mock_storage.content_find(
            'sha1_git', hash_to_bytes(
                '456caf10e9535160d90e874b45aa426de762f19f')
        )
        mock_idx_storage.content_fossology_license_get.assert_called_with(
            [hash_to_bytes('123caf10e9535160d90e874b45aa426de762f19f')])

    @patch('swh.web.common.service.storage')
    def test_lookup_content_provenance(self, mock_storage):
        # given
        mock_storage.content_find_provenance = MagicMock(
            return_value=(p for p in [{
                'content': hash_to_bytes(
                    '123caf10e9535160d90e874b45aa426de762f19f'),
                'revision': hash_to_bytes(
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

        mock_storage.content_find_provenance.assert_called_with(
            {'sha1_git':
             hash_to_bytes('123caf10e9535160d90e874b45aa426de762f19f')})

    @patch('swh.web.common.service.storage')
    def test_lookup_content_provenance_not_found(self, mock_storage):
        # given
        mock_storage.content_find_provenance = MagicMock(return_value=None)

        # when
        actual_provenances = service.lookup_content_provenance(
            'sha1_git:456caf10e9535160d90e874b45aa426de762f19f')

        # then
        self.assertIsNone(actual_provenances)

        mock_storage.content_find_provenance.assert_called_with(
            {'sha1_git':
             hash_to_bytes('456caf10e9535160d90e874b45aa426de762f19f')})

    @patch('swh.web.common.service.storage')
    def test_stat_counters(self, mock_storage):
        # given
        input_stats = {
            "content": 1770830,
            "directory": 211683,
            "directory_entry_dir": 209167,
            "directory_entry_file": 1807094,
            "directory_entry_rev": 0,
            "entity": 0,
            "entity_history": 0,
            "origin": 1096,
            "person": 0,
            "release": 8584,
            "revision": 7792,
            "revision_history": 0,
            "skipped_content": 0
        }
        mock_storage.stat_counters = MagicMock(return_value=input_stats)

        # when
        actual_stats = service.stat_counters()

        # then
        expected_stats = input_stats
        self.assertEqual(actual_stats, expected_stats)

        mock_storage.stat_counters.assert_called_with()

    @patch('swh.web.common.service._lookup_origin_visits')
    def test_lookup_origin_visits(self, mock_lookup_visits):
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
            'target': hash_to_bytes(
                '65a55bbdf3629f916219feb3dcc7393ded1bc8db'),
            'branch': b'master',
            'target_type': 'release',
            'metadata': None,
        }, {
            'date': date_origin_visit3,
            'origin': 1,
            'visit': 3
        }]
        mock_lookup_visits.return_value = stub_result

        # when
        expected_origin_visits = [{
            'date': self.origin_visit1['date'].isoformat(),
            'origin': self.origin_visit1['origin'],
            'visit': self.origin_visit1['visit']
        }, {
            'date': date_origin_visit2.isoformat(),
            'origin': 1,
            'visit': 2,
            'target': '65a55bbdf3629f916219feb3dcc7393ded1bc8db',
            'branch': 'master',
            'target_type': 'release',
            'metadata': {},
        }, {
            'date': date_origin_visit3.isoformat(),
            'origin': 1,
            'visit': 3
        }]

        actual_origin_visits = service.lookup_origin_visits(6)

        # then
        self.assertEqual(list(actual_origin_visits), expected_origin_visits)

        mock_lookup_visits.assert_called_once_with(
            6, last_visit=None, limit=10)

    @patch('swh.web.common.service.storage')
    def test_lookup_origin_visit(self, mock_storage):
        # given
        stub_result = self.origin_visit1
        mock_storage.origin_visit_get_by.return_value = stub_result

        expected_origin_visit = {
            'date': self.origin_visit1['date'].isoformat(),
            'origin': self.origin_visit1['origin'],
            'visit': self.origin_visit1['visit']
        }

        # when
        actual_origin_visit = service.lookup_origin_visit(1, 1)

        # then
        self.assertEqual(actual_origin_visit, expected_origin_visit)

        mock_storage.origin_visit_get_by.assert_called_once_with(1, 1)

    @patch('swh.web.common.service.storage')
    def test_lookup_origin(self, mock_storage):
        # given
        mock_storage.origin_get = MagicMock(return_value={
            'id': 'origin-id',
            'url': 'ftp://some/url/to/origin',
            'type': 'ftp'})

        # when
        actual_origin = service.lookup_origin({'id': 'origin-id'})

        # then
        self.assertEqual(actual_origin, {'id': 'origin-id',
                                         'url': 'ftp://some/url/to/origin',
                                         'type': 'ftp'})

        mock_storage.origin_get.assert_called_with({'id': 'origin-id'})

    @patch('swh.web.common.service.storage')
    def test_lookup_release_ko_id_checksum_not_a_sha1(self, mock_storage):
        # given
        mock_storage.release_get = MagicMock()

        with self.assertRaises(BadInputExc) as cm:
            # when
            service.lookup_release('not-a-sha1')
        self.assertIn('invalid checksum', cm.exception.args[0].lower())

        mock_storage.release_get.called = False

    @patch('swh.web.common.service.storage')
    def test_lookup_release_ko_id_checksum_too_long(self, mock_storage):
        # given
        mock_storage.release_get = MagicMock()

        # when
        with self.assertRaises(BadInputExc) as cm:
            service.lookup_release(
                '13c1d34d138ec13b5ebad226dc2528dc7506c956e4646f62d4daf5'
                '1aea892abe')
        self.assertEqual('Only sha1_git is supported.', cm.exception.args[0])

        mock_storage.release_get.called = False

    @patch('swh.web.common.service.storage')
    def test_lookup_directory_with_path_not_found(self, mock_storage):
        # given
        mock_storage.lookup_directory_with_path = MagicMock(return_value=None)

        sha1_git = '65a55bbdf3629f916219feb3dcc7393ded1bc8db'

        # when
        actual_directory = mock_storage.lookup_directory_with_path(
            sha1_git, 'some/path/here')

        self.assertIsNone(actual_directory)

    @patch('swh.web.common.service.storage')
    def test_lookup_directory_with_path_found(self, mock_storage):
        # given
        sha1_git = '65a55bbdf3629f916219feb3dcc7393ded1bc8db'
        entry = {'id': 'dir-id',
                 'type': 'dir',
                 'name': 'some/path/foo'}

        mock_storage.lookup_directory_with_path = MagicMock(return_value=entry)

        # when
        actual_directory = mock_storage.lookup_directory_with_path(
            sha1_git, 'some/path/here')

        self.assertEqual(entry, actual_directory)

    @patch('swh.web.common.service.storage')
    def test_lookup_release(self, mock_storage):
        # given
        mock_storage.release_get = MagicMock(return_value=[{
            'id': hash_to_bytes('65a55bbdf3629f916219feb3dcc7393ded1bc8db'),
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
        }])

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

        mock_storage.release_get.assert_called_with(
            [hash_to_bytes('65a55bbdf3629f916219feb3dcc7393ded1bc8db')])

    def test_lookup_revision_with_context_ko_not_a_sha1_1(self):
        # given
        sha1_git = '13c1d34d138ec13b5ebad226dc2528dc7506c956e4646f62d4' \
                   'daf51aea892abe'
        sha1_git_root = '65a55bbdf3629f916219feb3dcc7393ded1bc8db'

        # when
        with self.assertRaises(BadInputExc) as cm:
            service.lookup_revision_with_context(sha1_git_root, sha1_git)
        self.assertIn('Only sha1_git is supported', cm.exception.args[0])

    def test_lookup_revision_with_context_ko_not_a_sha1_2(self):
        # given
        sha1_git_root = '65a55bbdf3629f916219feb3dcc7393ded1bc8db'
        sha1_git = '13c1d34d138ec13b5ebad226dc2528dc7506c956e4646f6' \
                   '2d4daf51aea892abe'

        # when
        with self.assertRaises(BadInputExc) as cm:
            service.lookup_revision_with_context(sha1_git_root, sha1_git)
        self.assertIn('Only sha1_git is supported', cm.exception.args[0])

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_with_context_ko_sha1_git_does_not_exist(
            self,
            mock_storage):
        # given
        sha1_git_root = '65a55bbdf3629f916219feb3dcc7393ded1bc8db'
        sha1_git = '777777bdf3629f916219feb3dcc7393ded1bc8db'

        sha1_git_bin = hash_to_bytes(sha1_git)

        mock_storage.revision_get.return_value = None

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_with_context(sha1_git_root, sha1_git)
        self.assertIn('Revision 777777bdf3629f916219feb3dcc7393ded1bc8db'
                      ' not found', cm.exception.args[0])

        mock_storage.revision_get.assert_called_once_with(
            [sha1_git_bin])

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_with_context_ko_root_sha1_git_does_not_exist(
            self,
            mock_storage):
        # given
        sha1_git_root = '65a55bbdf3629f916219feb3dcc7393ded1bc8db'
        sha1_git = '777777bdf3629f916219feb3dcc7393ded1bc8db'

        sha1_git_root_bin = hash_to_bytes(sha1_git_root)
        sha1_git_bin = hash_to_bytes(sha1_git)

        mock_storage.revision_get.side_effect = ['foo', None]

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_with_context(sha1_git_root, sha1_git)
        self.assertIn('Revision root 65a55bbdf3629f916219feb3dcc7393ded1bc8db'
                      ' not found', cm.exception.args[0])

        mock_storage.revision_get.assert_has_calls([call([sha1_git_bin]),
                                                    call([sha1_git_root_bin])])

    @patch('swh.web.common.service.storage')
    @patch('swh.web.common.service.query')
    def test_lookup_revision_with_context(self, mock_query, mock_storage):
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
        mock_storage.revision_get.return_value = [
            sha1_git_dict,
            sha1_git_root_dict
        ]

        mock_storage.revision_log = MagicMock(
            return_value=stub_revisions)

        # when

        actual_revision = service.lookup_revision_with_context(
            sha1_git_root,
            sha1_git)

        # then
        self.assertEqual(actual_revision, {
            'id': hash_to_hex(sha1_git_bin),
            'parents': [],
            'children': [hash_to_hex(b'999'), hash_to_hex(b'777')],
            'directory': hash_to_hex(b'278'),
            'merge': False
        })

        mock_query.parse_hash_with_algorithms_or_throws.assert_has_calls(
            [call(sha1_git, ['sha1'], 'Only sha1_git is supported.'),
             call(sha1_git_root, ['sha1'], 'Only sha1_git is supported.')])

        mock_storage.revision_log.assert_called_with(
            [sha1_git_root_bin], 100)

    @patch('swh.web.common.service.storage')
    @patch('swh.web.common.service.query')
    def test_lookup_revision_with_context_retrieved_as_dict(
            self, mock_query, mock_storage):
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
        mock_storage.revision_get.return_value = [sha1_git_dict]

        mock_storage.revision_log.return_value = stub_revisions

        # when
        actual_revision = service.lookup_revision_with_context(
            {'id': sha1_git_root_bin},
            sha1_git)

        # then
        self.assertEqual(actual_revision, {
            'id': hash_to_hex(sha1_git_bin),
            'parents': [],
            'children': [hash_to_hex(b'999'), hash_to_hex(b'777')],
            'directory': hash_to_hex(b'278'),
            'merge': False
        })

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with(  # noqa
            sha1_git, ['sha1'], 'Only sha1_git is supported.')

        mock_storage.revision_get.assert_called_once_with([sha1_git_bin])

        mock_storage.revision_log.assert_called_with(
            [sha1_git_root_bin], 100)

    @patch('swh.web.common.service.storage')
    @patch('swh.web.common.service.query')
    def test_lookup_directory_with_revision_not_found(self,
                                                      mock_query,
                                                      mock_storage):
        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')
        mock_storage.revision_get.return_value = None

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_directory_with_revision('123')
        self.assertIn('Revision 123 not found', cm.exception.args[0])

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with
        ('123', ['sha1'], 'Only sha1_git is supported.')
        mock_storage.revision_get.assert_called_once_with([b'123'])

    @patch('swh.web.common.service.storage')
    @patch('swh.web.common.service.query')
    def test_lookup_directory_with_revision_ko_revision_with_path_to_nowhere(
            self,
            mock_query,
            mock_storage):
        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')

        dir_id = b'dir-id-as-sha1'
        mock_storage.revision_get.return_value = [{
            'directory': dir_id,
        }]

        mock_storage.directory_entry_get_by_path.return_value = None

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_directory_with_revision(
                '123',
                'path/to/something/unknown')
        exception_text = cm.exception.args[0].lower()
        self.assertIn('directory or file', exception_text)
        self.assertIn('path/to/something/unknown', exception_text)
        self.assertIn('revision 123', exception_text)
        self.assertIn('not found', exception_text)

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with
        ('123', ['sha1'], 'Only sha1_git is supported.')
        mock_storage.revision_get.assert_called_once_with([b'123'])
        mock_storage.directory_entry_get_by_path.assert_called_once_with(
            b'dir-id-as-sha1', [b'path', b'to', b'something', b'unknown'])

    @patch('swh.web.common.service.storage')
    @patch('swh.web.common.service.query')
    def test_lookup_directory_with_revision_ko_type_not_implemented(
            self,
            mock_query,
            mock_storage):

        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')

        dir_id = b'dir-id-as-sha1'
        mock_storage.revision_get.return_value = [{
            'directory': dir_id,
        }]

        mock_storage.directory_entry_get_by_path.return_value = {
            'type': 'rev',
            'name': b'some/path/to/rev',
            'target': b'456'
        }

        stub_content = {
            'id': b'12',
            'type': 'file'
        }

        mock_storage.content_get.return_value = stub_content

        # when
        with self.assertRaises(NotImplementedError) as cm:
            service.lookup_directory_with_revision(
                '123',
                'some/path/to/rev')
        self.assertIn("Entity of type rev not implemented.",
                      cm.exception.args[0])

        # then
        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with
        ('123', ['sha1'], 'Only sha1_git is supported.')
        mock_storage.revision_get.assert_called_once_with([b'123'])
        mock_storage.directory_entry_get_by_path.assert_called_once_with(
            b'dir-id-as-sha1', [b'some', b'path', b'to', b'rev'])

    @patch('swh.web.common.service.storage')
    @patch('swh.web.common.service.query')
    def test_lookup_directory_with_revision_revision_without_path(
        self, mock_query, mock_storage,
    ):
        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')

        dir_id = b'dir-id-as-sha1'
        mock_storage.revision_get.return_value = [{
            'directory': dir_id,
        }]

        stub_dir_entries = [{
            'id': b'123',
            'type': 'dir'
        }, {
            'id': b'456',
            'type': 'file'
        }]

        mock_storage.directory_ls.return_value = stub_dir_entries

        # when
        actual_directory_entries = service.lookup_directory_with_revision(
            '123')

        self.assertEqual(actual_directory_entries['type'], 'dir')
        self.assertEqual(list(actual_directory_entries['content']),
                         stub_dir_entries)

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_once_with
        ('123', ['sha1'], 'Only sha1_git is supported.')
        mock_storage.revision_get.assert_called_once_with([b'123'])
        mock_storage.directory_ls.assert_called_once_with(dir_id)

    @patch('swh.web.common.service.storage')
    @patch('swh.web.common.service.query')
    def test_lookup_directory_with_revision_with_path_to_dir(self,
                                                             mock_query,
                                                             mock_storage):
        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')

        dir_id = b'dir-id-as-sha1'
        mock_storage.revision_get.return_value = [{
            'directory': dir_id,
        }]

        stub_dir_entries = [{
            'id': b'12',
            'type': 'dir'
        }, {
            'id': b'34',
            'type': 'file'
        }]

        mock_storage.directory_entry_get_by_path.return_value = {
            'type': 'dir',
            'name': b'some/path',
            'target': b'456'
        }
        mock_storage.directory_ls.return_value = stub_dir_entries

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
        mock_storage.revision_get.assert_called_once_with([b'123'])
        mock_storage.directory_entry_get_by_path.assert_called_once_with(
            dir_id,
            [b'some', b'path'])
        mock_storage.directory_ls.assert_called_once_with(b'456')

    @patch('swh.web.common.service.storage')
    @patch('swh.web.common.service.query')
    def test_lookup_directory_with_revision_with_path_to_file_wo_data(
            self,
            mock_query,
            mock_storage):

        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')

        dir_id = b'dir-id-as-sha1'
        mock_storage.revision_get.return_value = [{
            'directory': dir_id,
        }]

        mock_storage.directory_entry_get_by_path.return_value = {
                'type': 'file',
                'name': b'some/path/to/file',
                'target': b'789'
            }

        stub_content = {
            'status': 'visible',
        }

        mock_storage.content_find.return_value = stub_content

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
        mock_storage.revision_get.assert_called_once_with([b'123'])
        mock_storage.directory_entry_get_by_path.assert_called_once_with(
            b'dir-id-as-sha1', [b'some', b'path', b'to', b'file'])
        mock_storage.content_find.assert_called_once_with({'sha1_git': b'789'})

    @patch('swh.web.common.service.storage')
    @patch('swh.web.common.service.query')
    def test_lookup_directory_with_revision_with_path_to_file_w_data(
            self,
            mock_query,
            mock_storage):

        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = ('sha1',
                                                                        b'123')

        dir_id = b'dir-id-as-sha1'
        mock_storage.revision_get.return_value = [{
            'directory': dir_id,
        }]

        mock_storage.directory_entry_get_by_path.return_value = {
                'type': 'file',
                'name': b'some/path/to/file',
                'target': b'789'
            }

        stub_content = {
            'status': 'visible',
            'sha1': b'content-sha1'
        }

        mock_storage.content_find.return_value = stub_content
        mock_storage.content_get.return_value = [{
            'sha1': b'content-sha1',
            'data': b'some raw data'
        }]

        expected_content = {
            'status': 'visible',
            'checksums': {
                'sha1': hash_to_hex(b'content-sha1'),
            },
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
        mock_storage.revision_get.assert_called_once_with([b'123'])
        mock_storage.directory_entry_get_by_path.assert_called_once_with(
            b'dir-id-as-sha1', [b'some', b'path', b'to', b'file'])
        mock_storage.content_find.assert_called_once_with({'sha1_git': b'789'})
        mock_storage.content_get.assert_called_once_with([b'content-sha1'])

    @patch('swh.web.common.service.storage')
    def test_lookup_revision(self, mock_storage):
        # given
        mock_storage.revision_get = MagicMock(
            return_value=[self.SAMPLE_REVISION_RAW])

        # when
        actual_revision = service.lookup_revision(
            self.SHA1_SAMPLE)

        # then
        self.assertEqual(actual_revision, self.SAMPLE_REVISION)

        mock_storage.revision_get.assert_called_with(
            [self.SHA1_SAMPLE_BIN])

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_invalid_msg(self, mock_storage):
        # given
        stub_rev = self.SAMPLE_REVISION_RAW
        stub_rev['message'] = b'elegant fix for bug \xff'

        expected_revision = self.SAMPLE_REVISION
        expected_revision['message'] = None
        expected_revision['message_decoding_failed'] = True
        mock_storage.revision_get = MagicMock(return_value=[stub_rev])

        # when
        actual_revision = service.lookup_revision(
            self.SHA1_SAMPLE)

        # then
        self.assertEqual(actual_revision, expected_revision)

        mock_storage.revision_get.assert_called_with(
            [self.SHA1_SAMPLE_BIN])

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_msg_ok(self, mock_storage):
        # given
        mock_storage.revision_get.return_value = [self.SAMPLE_REVISION_RAW]

        # when
        rv = service.lookup_revision_message(
            self.SHA1_SAMPLE)

        # then
        self.assertEqual(rv, {'message': self.SAMPLE_MESSAGE_BIN})
        mock_storage.revision_get.assert_called_with(
            [self.SHA1_SAMPLE_BIN])

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_msg_absent(self, mock_storage):
        # given
        stub_revision = self.SAMPLE_REVISION_RAW
        del stub_revision['message']
        mock_storage.revision_get.return_value = stub_revision

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_message(
                self.SHA1_SAMPLE)

        # then
        mock_storage.revision_get.assert_called_with(
            [self.SHA1_SAMPLE_BIN])
        self.assertEqual(
            cm.exception.args[0],
            'No message for revision with sha1_git %s.' % self.SHA1_SAMPLE,
        )

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_msg_norev(self, mock_storage):
        # given
        mock_storage.revision_get.return_value = None

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_message(
                self.SHA1_SAMPLE)

        # then
        mock_storage.revision_get.assert_called_with(
            [self.SHA1_SAMPLE_BIN])
        self.assertEqual(
            cm.exception.args[0],
            'Revision with sha1_git %s not found.' % self.SHA1_SAMPLE,
        )

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_multiple(self, mock_storage):
        # given
        sha1 = self.SHA1_SAMPLE
        sha1_other = 'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'

        stub_revisions = [
            self.SAMPLE_REVISION_RAW,
            {
                'id': hash_to_bytes(sha1_other),
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

        mock_storage.revision_get.return_value = stub_revisions

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
                'metadata': {},
                'merge': False
            }
        ])

        self.assertEqual(
            list(mock_storage.revision_get.call_args[0][0]),
            [hash_to_bytes(sha1),
             hash_to_bytes(sha1_other)])

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_multiple_none_found(self, mock_storage):
        # given
        sha1_bin = self.SHA1_SAMPLE
        sha1_other = 'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'

        mock_storage.revision_get.return_value = []

        # then
        actual_revisions = service.lookup_revision_multiple(
            [sha1_bin, sha1_other])

        self.assertEqual(list(actual_revisions), [])

        self.assertEqual(
            list(mock_storage.revision_get.call_args[0][0]),
            [hash_to_bytes(self.SHA1_SAMPLE),
             hash_to_bytes(sha1_other)])

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_log(self, mock_storage):
        # given
        stub_revision_log = [self.SAMPLE_REVISION_RAW]
        mock_storage.revision_log = MagicMock(return_value=stub_revision_log)

        # when
        actual_revision = service.lookup_revision_log(
            'abcdbe353ed3480476f032475e7c233eff7371d5',
            limit=25)

        # then
        self.assertEqual(list(actual_revision), [self.SAMPLE_REVISION])

        mock_storage.revision_log.assert_called_with(
            [hash_to_bytes('abcdbe353ed3480476f032475e7c233eff7371d5')], 25)

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_log_by(self, mock_storage):
        # given
        stub_revision_log = [self.SAMPLE_REVISION_RAW]
        mock_storage.revision_log_by = MagicMock(
            return_value=stub_revision_log)

        # when
        actual_log = service.lookup_revision_log_by(
            1, 'refs/heads/master', None, limit=100)
        # then
        self.assertEqual(list(actual_log), [self.SAMPLE_REVISION])

        mock_storage.revision_log_by.assert_called_with(
            1, 'refs/heads/master', None, limit=100)

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_log_by_nolog(self, mock_storage):
        # given
        mock_storage.revision_log_by = MagicMock(return_value=None)

        # when
        res = service.lookup_revision_log_by(
            1, 'refs/heads/master', None, limit=100)
        # then
        self.assertEqual(res, None)
        mock_storage.revision_log_by.assert_called_with(
            1, 'refs/heads/master', None, limit=100)

    @patch('swh.web.common.service.storage')
    def test_lookup_content_raw_not_found(self, mock_storage):
        # given
        mock_storage.content_find = MagicMock(return_value=None)

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_content_raw('sha1:' + self.SHA1_SAMPLE)
        self.assertIn(cm.exception.args[0],
                      'Content with %s checksum equals to %s not found!' %
                      ('sha1', self.SHA1_SAMPLE))

        mock_storage.content_find.assert_called_with(
            {'sha1': hash_to_bytes(self.SHA1_SAMPLE)})

    @patch('swh.web.common.service.storage')
    def test_lookup_content_raw(self, mock_storage):
        # given
        mock_storage.content_find = MagicMock(return_value={
            'sha1': self.SHA1_SAMPLE,
        })
        mock_storage.content_get = MagicMock(return_value=[{
            'data': b'binary data'}])

        # when
        actual_content = service.lookup_content_raw(
            'sha256:%s' % self.SHA256_SAMPLE)

        # then
        self.assertEqual(actual_content, {'data': b'binary data'})

        mock_storage.content_find.assert_called_once_with(
            {'sha256': self.SHA256_SAMPLE_BIN})
        mock_storage.content_get.assert_called_once_with(
            [self.SHA1_SAMPLE])

    @patch('swh.web.common.service.storage')
    def test_lookup_content_not_found(self, mock_storage):
        # given
        mock_storage.content_find = MagicMock(return_value=None)

        # when
        with self.assertRaises(NotFoundExc) as cm:
            # then
            service.lookup_content('sha1:%s' % self.SHA1_SAMPLE)
        self.assertIn(cm.exception.args[0],
                      'Content with %s checksum equals to %s not found!' %
                      ('sha1', self.SHA1_SAMPLE))

        mock_storage.content_find.assert_called_with(
            {'sha1': self.SHA1_SAMPLE_BIN})

    @patch('swh.web.common.service.storage')
    def test_lookup_content_with_sha1(self, mock_storage):
        # given
        mock_storage.content_find = MagicMock(
            return_value=self.SAMPLE_CONTENT_RAW)

        # when
        actual_content = service.lookup_content(
            'sha1:%s' % self.SHA1_SAMPLE)

        # then
        self.assertEqual(actual_content, self.SAMPLE_CONTENT)

        mock_storage.content_find.assert_called_with(
            {'sha1': hash_to_bytes(self.SHA1_SAMPLE)})

    @patch('swh.web.common.service.storage')
    def test_lookup_content_with_sha256(self, mock_storage):
        # given
        stub_content = self.SAMPLE_CONTENT_RAW
        stub_content['status'] = 'visible'

        expected_content = self.SAMPLE_CONTENT
        expected_content['status'] = 'visible'
        mock_storage.content_find = MagicMock(
            return_value=stub_content)

        # when
        actual_content = service.lookup_content(
            'sha256:%s' % self.SHA256_SAMPLE)

        # then
        self.assertEqual(actual_content, expected_content)

        mock_storage.content_find.assert_called_with(
            {'sha256': self.SHA256_SAMPLE_BIN})

    @patch('swh.web.common.service.storage')
    def test_lookup_person(self, mock_storage):
        # given
        mock_storage.person_get = MagicMock(return_value=[{
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

        mock_storage.person_get.assert_called_with(['person_id'])

    @patch('swh.web.common.service.storage')
    def test_lookup_directory_bad_checksum(self, mock_storage):
        # given
        mock_storage.directory_ls = MagicMock()

        # when
        with self.assertRaises(BadInputExc):
            service.lookup_directory('directory_id')

        # then
        mock_storage.directory_ls.called = False

    @patch('swh.web.common.service.storage')
    @patch('swh.web.common.service.query')
    def test_lookup_directory_not_found(self, mock_query, mock_storage):
        # given
        mock_query.parse_hash_with_algorithms_or_throws.return_value = (
            'sha1',
            'directory-id-bin')
        mock_storage.directory_ls.return_value = []

        # when
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_directory('directory_id')

        self.assertIn('Directory with sha1_git directory_id not found',
                      cm.exception.args[0])

        # then
        mock_query.parse_hash_with_algorithms_or_throws.assert_called_with(
            'directory_id', ['sha1'], 'Only sha1_git is supported.')
        mock_storage.directory_ls.assert_called_with('directory-id-bin')

    @patch('swh.web.common.service.storage')
    @patch('swh.web.common.service.query')
    def test_lookup_directory(self, mock_query, mock_storage):
        mock_query.parse_hash_with_algorithms_or_throws.return_value = (
            'sha1',
            'directory-sha1-bin')

        # given
        stub_dir_entries = [{
            'sha1': self.SHA1_SAMPLE_BIN,
            'sha256': self.SHA256_SAMPLE_BIN,
            'sha1_git': self.SHA1GIT_SAMPLE_BIN,
            'blake2s256': self.BLAKE2S256_SAMPLE_BIN,
            'target': hash_to_bytes(
                '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'),
            'dir_id': self.DIRECTORY_ID_BIN,
            'name': b'bob',
            'type': 10,
        }]

        expected_dir_entries = [{
            'checksums': {
                'sha1': self.SHA1_SAMPLE,
                'sha256': self.SHA256_SAMPLE,
                'sha1_git': self.SHA1GIT_SAMPLE,
                'blake2s256': self.BLAKE2S256_SAMPLE
            },
            'target': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'dir_id': self.DIRECTORY_ID,
            'name': 'bob',
            'type': 10,
        }]

        mock_storage.directory_ls.return_value = stub_dir_entries

        # when
        actual_directory_ls = list(service.lookup_directory(
            'directory-sha1'))

        # then
        self.assertEqual(actual_directory_ls, expected_dir_entries)

        mock_query.parse_hash_with_algorithms_or_throws.assert_called_with(
            'directory-sha1', ['sha1'], 'Only sha1_git is supported.')
        mock_storage.directory_ls.assert_called_with(
            'directory-sha1-bin')

    @patch('swh.web.common.service.storage')
    def test_lookup_directory_empty(self, mock_storage):
        empty_dir_sha1 = '4b825dc642cb6eb9a060e54bf8d69288fbee4904'
        mock_storage.directory_ls.return_value = []

        # when
        actual_directory_ls = list(service.lookup_directory(empty_dir_sha1))

        # then
        self.assertEqual(actual_directory_ls, [])

        self.assertFalse(mock_storage.directory_ls.called)

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_by_nothing_found(self, mock_storage):
        # given
        mock_storage.revision_get_by.return_value = None

        # when
        with self.assertRaises(NotFoundExc):
            service.lookup_revision_by(1)

            # then
            mock_storage.revision_get_by.assert_called_with(1, 'refs/heads/master', # noqa
                                                            limit=1,
                                                            timestamp=None)

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_by(self, mock_storage):
        # given
        stub_rev = self.SAMPLE_REVISION_RAW

        expected_rev = self.SAMPLE_REVISION

        mock_storage.revision_get_by.return_value = [stub_rev]

        # when
        actual_revision = service.lookup_revision_by(10, 'master2', 'some-ts')

        # then
        self.assertEqual(actual_revision, expected_rev)

        mock_storage.revision_get_by.assert_called_with(10, 'master2',
                                                        limit=1,
                                                        timestamp='some-ts')

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_by_nomerge(self, mock_storage):
        # given
        stub_rev = self.SAMPLE_REVISION_RAW
        stub_rev['parents'] = [
                hash_to_bytes('adc83b19e793491b1c6ea0fd8b46cd9f32e592fc')]

        expected_rev = self.SAMPLE_REVISION
        expected_rev['parents'] = ['adc83b19e793491b1c6ea0fd8b46cd9f32e592fc']
        mock_storage.revision_get_by.return_value = [stub_rev]

        # when
        actual_revision = service.lookup_revision_by(10, 'master2', 'some-ts')

        # then
        self.assertEqual(actual_revision, expected_rev)

        mock_storage.revision_get_by.assert_called_with(10, 'master2',
                                                        limit=1,
                                                        timestamp='some-ts')

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_by_merge(self, mock_storage):
        # given
        stub_rev = self.SAMPLE_REVISION_RAW
        stub_rev['parents'] = [
            hash_to_bytes('adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'),
            hash_to_bytes('ffff3b19e793491b1c6db0fd8b46cd9f32e592fc')
        ]

        expected_rev = self.SAMPLE_REVISION
        expected_rev['parents'] = [
            'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
            'ffff3b19e793491b1c6db0fd8b46cd9f32e592fc'
        ]
        expected_rev['merge'] = True

        mock_storage.revision_get_by.return_value = [stub_rev]

        # when
        actual_revision = service.lookup_revision_by(10, 'master2', 'some-ts')

        # then
        self.assertEqual(actual_revision, expected_rev)

        mock_storage.revision_get_by.assert_called_with(10, 'master2',
                                                        limit=1,
                                                        timestamp='some-ts')

    @patch('swh.web.common.service.storage')
    def test_lookup_revision_with_context_by_ko(self, mock_storage):
        # given
        mock_storage.revision_get_by.return_value = None

        # when
        origin_id = 1
        branch_name = 'master3'
        ts = None
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_with_context_by(origin_id, branch_name, ts,
                                                    'sha1')
        # then
        self.assertIn(
            'Revision with (origin_id: %s, branch_name: %s'
            ', ts: %s) not found.' % (origin_id,
                                      branch_name,
                                      ts), cm.exception.args[0])

        mock_storage.revision_get_by.assert_called_once_with(
            origin_id, branch_name, limit=1, timestamp=ts)

    @patch('swh.web.common.service.lookup_revision_with_context')
    @patch('swh.web.common.service.storage')
    def test_lookup_revision_with_context_by(
            self, mock_storage, mock_lookup_revision_with_context,
    ):
        # given
        stub_root_rev = {'id': 'root-rev-id'}
        mock_storage.revision_get_by.return_value = [{'id': 'root-rev-id'}]
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
        self.assertEqual(actual_root_rev, stub_root_rev)
        self.assertEqual(actual_rev, stub_rev)

        mock_storage.revision_get_by.assert_called_once_with(
            origin_id, branch_name, limit=1, timestamp=ts)
        mock_lookup_revision_with_context.assert_called_once_with(
            stub_root_rev, sha1_git, 100)

    @patch('swh.web.common.service.storage')
    @patch('swh.web.common.service.query')
    def test_lookup_entity_by_uuid(self, mock_query, mock_storage):
        # given
        uuid_test = 'correct-uuid'
        mock_query.parse_uuid4.return_value = uuid_test
        stub_entities = [{'uuid': uuid_test}]

        mock_storage.entity_get.return_value = stub_entities

        # when
        actual_entities = list(service.lookup_entity_by_uuid(uuid_test))

        # then
        self.assertEqual(actual_entities, stub_entities)

        mock_query.parse_uuid4.assert_called_once_with(uuid_test)
        mock_storage.entity_get.assert_called_once_with(uuid_test)

    def test_lookup_revision_through_ko_not_implemented(self):
        # then
        with self.assertRaises(NotImplementedError):
            service.lookup_revision_through({
                'something-unknown': 10,
            })

    @patch('swh.web.common.service.lookup_revision_with_context_by')
    def test_lookup_revision_through_with_context_by(self, mock_lookup):
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
        self.assertEqual(actual_revision, stub_rev)

        mock_lookup.assert_called_once_with(
            1, 'master', None, 'sha1-git', 1000)

    @patch('swh.web.common.service.lookup_revision_by')
    def test_lookup_revision_through_with_revision_by(self, mock_lookup):
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
        self.assertEqual(actual_revision, stub_rev)

        mock_lookup.assert_called_once_with(
            2, 'master2', 'some-ts')

    @patch('swh.web.common.service.lookup_revision_with_context')
    def test_lookup_revision_through_with_context(self, mock_lookup):
        # given
        stub_rev = {'id': 'rev'}
        mock_lookup.return_value = stub_rev

        # when
        actual_revision = service.lookup_revision_through({
            'sha1_git_root': 'some-sha1-root',
            'sha1_git': 'some-sha1',
        })

        # then
        self.assertEqual(actual_revision, stub_rev)

        mock_lookup.assert_called_once_with(
            'some-sha1-root', 'some-sha1', 100)

    @patch('swh.web.common.service.lookup_revision')
    def test_lookup_revision_through_with_revision(self, mock_lookup):
        # given
        stub_rev = {'id': 'rev'}
        mock_lookup.return_value = stub_rev

        # when
        actual_revision = service.lookup_revision_through({
            'sha1_git': 'some-sha1',
        })

        # then
        self.assertEqual(actual_revision, stub_rev)

        mock_lookup.assert_called_once_with(
            'some-sha1')

    @patch('swh.web.common.service.lookup_revision_through')
    def test_lookup_directory_through_revision_ko_not_found(
            self, mock_lookup_rev):
        # given
        mock_lookup_rev.return_value = None

        # when
        with self.assertRaises(NotFoundExc):
            service.lookup_directory_through_revision(
                {'id': 'rev'}, 'some/path', 100)

        mock_lookup_rev.assert_called_once_with({'id': 'rev'}, 100)

    @patch('swh.web.common.service.lookup_revision_through')
    @patch('swh.web.common.service.lookup_directory_with_revision')
    def test_lookup_directory_through_revision_ok_with_data(
            self, mock_lookup_dir, mock_lookup_rev):
        # given
        mock_lookup_rev.return_value = {'id': 'rev-id'}
        mock_lookup_dir.return_value = {'type': 'dir',
                                        'content': []}

        # when
        rev_id, dir_result = service.lookup_directory_through_revision(
            {'id': 'rev'}, 'some/path', 100)
        # then
        self.assertEqual(rev_id, 'rev-id')
        self.assertEqual(dir_result, {'type': 'dir',
                                      'content': []})

        mock_lookup_rev.assert_called_once_with({'id': 'rev'}, 100)
        mock_lookup_dir.assert_called_once_with('rev-id', 'some/path', False)

    @patch('swh.web.common.service.lookup_revision_through')
    @patch('swh.web.common.service.lookup_directory_with_revision')
    def test_lookup_directory_through_revision_ok_with_content(
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
        self.assertEqual(rev_id, 'rev-id')
        self.assertEqual(dir_result, stub_result)

        mock_lookup_rev.assert_called_once_with({'id': 'rev'}, 10)
        mock_lookup_dir.assert_called_once_with('rev-id', 'some/path', True)
