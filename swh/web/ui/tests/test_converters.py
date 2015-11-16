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
