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
            'd': b'\xb0L\xaf\x10\xe9SQ`\xd9\x0e\x87KE\xaaBm\xe7b\xf1\x9f',
            'e': b'sharp.html/doc_002dS_005fISREG.html'
        }

        expected_output = {
            'a': 'something',
            'b': 'someone',
            'c': 'sharp-0.3.4.tgz',
            'd': 'b04caf10e9535160d90e874b45aa426de762f19f',
            'e': 'sharp.html/doc_002dS_005fISREG.html'
        }

        actual_output = converters.from_swh(some_input,
                                            hashess=set(['d']),
                                            bytess=set(['c', 'e']))

        self.assertEquals(expected_output, actual_output)

    @istest
    def from_swh_empty(self):
        # when
        self.assertEquals({}, converters.from_swh({}))

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
            'revision': hashutil.hex_to_hash(
                '5e46d564378afc44b31bb89f99d5675195fbdf67'),
            'date': datetime.datetime(2015, 1, 1, 22, 0, 0,
                                      tzinfo=datetime.timezone.utc),
            'date_offset': None,
            'name': 'v0.0.1',
            'comment': b'some comment on release',
            'synthetic': True,
        }

        expected_release = {
            'id': 'aad23fa492a0c5fed0708a6703be875448c86884',
            'revision': '5e46d564378afc44b31bb89f99d5675195fbdf67',
            'date': datetime.datetime(2015, 1, 1, 22, 0, 0,
                                      tzinfo=datetime.timezone.utc),
            'date_offset': None,
            'name': 'v0.0.1',
            'comment': 'some comment on release',
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
            'revision': None,
            'date': datetime.datetime(2016, 3, 2, 10, 0, 0,
                                      tzinfo=datetime.timezone.utc),
            'date_offset': 1,
            'name': 'v0.1.1',
            'comment': b'comment on release',
            'synthetic': False,
        }

        expected_release = {
            'id': 'b2171ee2bdf119cd99a7ec7eff32fa8013ef9a4e',
            'revision': None,
            'date': datetime.datetime(2016, 3, 2, 10, 0, 0,
                                      tzinfo=datetime.timezone.utc),
            'date_offset': 1,
            'name': 'v0.1.1',
            'comment': 'comment on release',
            'synthetic': False,
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
            'author_name': b'Software Heritage',
            'author_email': b'robot@softwareheritage.org',
            'committer_name': b'Software Heritage',
            'committer_email': b'robot@softwareheritage.org',
            'message': b'synthetic revision message',
            'date': datetime.datetime(2000, 1, 17, 11, 23, 54, tzinfo=None),
            'date_offset': 0,
            'committer_date': datetime.datetime(2000, 1, 17, 11, 23, 54,
                                                tzinfo=None),
            'committer_date_offset': 0,
            'synthetic': True,
            'type': 'tar',
            'parents': [],
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
            'author_name': 'Software Heritage',
            'author_email': 'robot@softwareheritage.org',
            'committer_name': 'Software Heritage',
            'committer_email': 'robot@softwareheritage.org',
            'message': 'synthetic revision message',
            'date': datetime.datetime(2000, 1, 17, 11, 23, 54, tzinfo=None),
            'date_offset': 0,
            'committer_date': datetime.datetime(2000, 1, 17, 11, 23, 54,
                                                tzinfo=None),
            'committer_date_offset': 0,
            'parents': [],
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

        expected_content = {
            'sha1': '5c6f0e2750f48fa0bd0c4cf5976ba0b9e02ebda5',
            'sha256': '39007420ca5de7cb3cfc15196335507ee76c98930e7e0afa4d274'
            '7d3bf96c926',
            'sha1_git': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'data': 'data in bytes',
            'length': 10,
            'status': 'visible',
        }

        # when
        actual_content = converters.from_content(content_input)

        # then
        self.assertEqual(actual_content, expected_content)
