# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime
import unittest

from nose.tools import istest

from swh.core import hashutil
from swh.web.ui import converters


class ConvertersTestCase(unittest.TestCase):

    @istest
    def from_swh(self):
        some_input = {
            'a': 'something',
            'b': 'someone',
            'c': b'sharp-0.3.4.tgz',
            'd': hashutil.hex_to_hash(
                'b04caf10e9535160d90e874b45aa426de762f19f'),
            'e': b'sharp.html/doc_002dS_005fISREG.html',
            'g': [b'utf-8-to-decode', b'another-one'],
            'h': 'something filtered',
            'i': {'e': b'something'},
            'j': {
                'k': {
                    'l': [b'bytes thing', b'another thingy'],
                    'n': 'dont care either'
                },
                'm': 'dont care'
            }
        }

        expected_output = {
            'a': 'something',
            'b': 'someone',
            'c': 'sharp-0.3.4.tgz',
            'd': 'b04caf10e9535160d90e874b45aa426de762f19f',
            'e': 'sharp.html/doc_002dS_005fISREG.html',
            'g': ['utf-8-to-decode', 'another-one'],
            'i': {'e': 'something'},
            'j': {
                'k': {
                    'l': ['bytes thing', 'another thingy']
                }
            },
        }

        actual_output = converters.from_swh(some_input,
                                            hashess={'d'},
                                            bytess={'c', 'e', 'g', 'l'},
                                            blacklist={'h', 'm', 'n'})

        self.assertEquals(expected_output, actual_output)

    @istest
    def from_swh_edge_cases_do_no_conversion_if_none_or_not_bytes(self):
        some_input = {
            'a': 'something',
            'b': None,
            'c': 'someone',
            'd': None,
        }

        expected_output = {
            'a': 'something',
            'b': None,
            'c': 'someone',
            'd': None,
        }

        actual_output = converters.from_swh(some_input,
                                            hashess={'a', 'b'},
                                            bytess={'c', 'd'})

        self.assertEquals(expected_output, actual_output)

    @istest
    def from_swh_empty(self):
        # when
        self.assertEquals({}, converters.from_swh({}))

    @istest
    def from_swh_none(self):
        # when
        self.assertIsNone(converters.from_swh(None))

    @istest
    def from_origin(self):
        # given
        origin_input = {
            'origin_type': 'ftp',
            'origin_url': 'rsync://ftp.gnu.org/gnu/octave',
            'branch': 'octave-3.4.0.tar.gz',
            'revision': b'\xb0L\xaf\x10\xe9SQ`\xd9\x0e\x87KE\xaaBm\xe7b\xf1\x9f',  # noqa
            'path': b'octave-3.4.0/doc/interpreter/octave.html/doc_002dS_005fISREG.html'  # noqa
        }

        expected_origin = {
            'origin_type': 'ftp',
            'origin_url': 'rsync://ftp.gnu.org/gnu/octave',
            'branch': 'octave-3.4.0.tar.gz',
            'revision': 'b04caf10e9535160d90e874b45aa426de762f19f',
            'path': 'octave-3.4.0/doc/interpreter/octave.html/doc_002dS_005fISREG.html'  # noqa
        }

        # when
        actual_origin = converters.from_origin(origin_input)

        # then
        self.assertEqual(actual_origin, expected_origin)

    @istest
    def from_release(self):
        release_input = {
            'id': hashutil.hex_to_hash(
                'aad23fa492a0c5fed0708a6703be875448c86884'),
            'target': hashutil.hex_to_hash(
                '5e46d564378afc44b31bb89f99d5675195fbdf67'),
            'target_type': 'revision',
            'date': datetime.datetime(2015, 1, 1, 22, 0, 0,
                                      tzinfo=datetime.timezone.utc),
            'author': {
                'name': b'author name',
                'email': b'author@email',
            },
            'name': b'v0.0.1',
            'message': b'some comment on release',
            'synthetic': True,
        }

        expected_release = {
            'id': 'aad23fa492a0c5fed0708a6703be875448c86884',
            'target': '5e46d564378afc44b31bb89f99d5675195fbdf67',
            'target_type': 'revision',
            'date': datetime.datetime(2015, 1, 1, 22, 0, 0,
                                      tzinfo=datetime.timezone.utc),
            'author': {
                'name': 'author name',
                'email': 'author@email',
            },
            'name': 'v0.0.1',
            'message': 'some comment on release',
            'target_type': 'revision',
            'synthetic': True,
        }

        # when
        actual_release = converters.from_release(release_input)

        # then
        self.assertEqual(actual_release, expected_release)

    @istest
    def from_release_no_revision(self):
        release_input = {
            'id': hashutil.hex_to_hash(
                'b2171ee2bdf119cd99a7ec7eff32fa8013ef9a4e'),
            'target': None,
            'date': datetime.datetime(2016, 3, 2, 10, 0, 0,
                                      tzinfo=datetime.timezone.utc),
            'name': b'v0.1.1',
            'message': b'comment on release',
            'synthetic': False,
            'author': {
                'name': b'bob',
                'email': b'bob@alice.net',
            },
        }

        expected_release = {
            'id': 'b2171ee2bdf119cd99a7ec7eff32fa8013ef9a4e',
            'target': None,
            'date': datetime.datetime(2016, 3, 2, 10, 0, 0,
                                      tzinfo=datetime.timezone.utc),
            'name': 'v0.1.1',
            'message': 'comment on release',
            'synthetic': False,
            'author': {
                'name': 'bob',
                'email': 'bob@alice.net',
            },
        }

        # when
        actual_release = converters.from_release(release_input)

        # then
        self.assertEqual(actual_release, expected_release)

    @istest
    def from_revision(self):
        revision_input = {
            'id': hashutil.hex_to_hash(
                '18d8be353ed3480476f032475e7c233eff7371d5'),
            'directory': hashutil.hex_to_hash(
                '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6'),
            'author': {
                'name': b'Software Heritage',
                'email': b'robot@softwareheritage.org',
            },
            'committer': {
                'name': b'Software Heritage',
                'email': b'robot@softwareheritage.org',
            },
            'message': b'synthetic revision message',
            'date': datetime.datetime(2000, 1, 17, 11, 23, 54, tzinfo=None),
            'date_offset': 0,
            'committer_date': datetime.datetime(2000, 1, 17, 11, 23, 54,
                                                tzinfo=None),
            'committer_date_offset': 0,
            'synthetic': True,
            'type': 'tar',
            'parents': [
                hashutil.hex_to_hash(
                    '29d8be353ed3480476f032475e7c244eff7371d5'),
                hashutil.hex_to_hash(
                    '30d8be353ed3480476f032475e7c244eff7371d5')
            ],
            'metadata': {
                'original_artifact': [{
                    'archive_type': 'tar',
                    'name': 'webbase-5.7.0.tar.gz',
                    'sha1': '147f73f369733d088b7a6fa9c4e0273dcd3c7ccd',
                    'sha1_git': '6a15ea8b881069adedf11feceec35588f2cfe8f1',
                    'sha256': '401d0df797110bea805d358b85bcc1ced29549d3d73f'
                    '309d36484e7edf7bb912',

                }]
            },
        }

        expected_revision = {
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'author': {
                'name': 'Software Heritage',
                'email': 'robot@softwareheritage.org',
            },
            'committer': {
                'name': 'Software Heritage',
                'email': 'robot@softwareheritage.org',
            },
            'message': 'synthetic revision message',
            'date': datetime.datetime(2000, 1, 17, 11, 23, 54, tzinfo=None),
            'date_offset': 0,
            'committer_date': datetime.datetime(2000, 1, 17, 11, 23, 54,
                                                tzinfo=None),
            'committer_date_offset': 0,
            'parents': [
                '29d8be353ed3480476f032475e7c244eff7371d5',
                '30d8be353ed3480476f032475e7c244eff7371d5'
            ],
            'type': 'tar',
            'synthetic': True,
            'metadata': {
                'original_artifact': [{
                    'archive_type': 'tar',
                    'name': 'webbase-5.7.0.tar.gz',
                    'sha1': '147f73f369733d088b7a6fa9c4e0273dcd3c7ccd',
                    'sha1_git': '6a15ea8b881069adedf11feceec35588f2cfe8f1',
                    'sha256': '401d0df797110bea805d358b85bcc1ced29549d3d73f'
                    '309d36484e7edf7bb912'
                }]
            },
        }

        # when
        actual_revision = converters.from_revision(revision_input)

        # then
        self.assertEqual(actual_revision, expected_revision)

    @istest
    def from_content(self):
        content_input = {
            'sha1': hashutil.hex_to_hash('5c6f0e2750f48fa0bd0c4cf5976ba0b9e0'
                                         '2ebda5'),
            'sha256': hashutil.hex_to_hash('39007420ca5de7cb3cfc15196335507e'
                                           'e76c98930e7e0afa4d2747d3bf96c926'),
            'sha1_git': hashutil.hex_to_hash('40e71b8614fcd89ccd17ca2b1d9e66'
                                             'c5b00a6d03'),
            'data': b'data in bytes',
            'length': 10,
            'status': 'visible',
        }

        # 'status' is filtered
        expected_content = {
            'sha1': '5c6f0e2750f48fa0bd0c4cf5976ba0b9e02ebda5',
            'sha256': '39007420ca5de7cb3cfc15196335507ee76c98930e7e0afa4d274'
            '7d3bf96c926',
            'sha1_git': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'data': 'data in bytes',
            'length': 10,
        }

        # when
        actual_content = converters.from_content(content_input)

        # then
        self.assertEqual(actual_content, expected_content)

    @istest
    def from_person(self):
        person_input = {
            'id': 10,
            'anything': 'else',
            'name': b'bob',
            'email': b'bob@foo.alice',
        }

        expected_person = {
            'id': 10,
            'anything': 'else',
            'name': 'bob',
            'email': 'bob@foo.alice',
        }

        # when
        actual_person = converters.from_person(person_input)

        # then
        self.assertEqual(actual_person, expected_person)

    @istest
    def from_directory_entries(self):
        dir_entries_input = {
            'sha1': hashutil.hex_to_hash('5c6f0e2750f48fa0bd0c4cf5976ba0b9e0'
                                         '2ebda5'),
            'sha256': hashutil.hex_to_hash('39007420ca5de7cb3cfc15196335507e'
                                           'e76c98930e7e0afa4d2747d3bf96c926'),
            'sha1_git': hashutil.hex_to_hash('40e71b8614fcd89ccd17ca2b1d9e66'
                                             'c5b00a6d03'),
            'target': hashutil.hex_to_hash('40e71b8614fcd89ccd17ca2b1d9e66'
                                           'c5b00a6d03'),
            'dir_id': hashutil.hex_to_hash('40e71b8614fcd89ccd17ca2b1d9e66'
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

        # when
        actual_dir_entries = converters.from_directory_entry(dir_entries_input)

        # then
        self.assertEqual(actual_dir_entries, expected_dir_entries)
