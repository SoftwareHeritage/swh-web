# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import unittest

from nose.tools import istest

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
