# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime


from swh.model import hashutil

from swh.web.common import converters
from swh.web.tests.testcase import SWHWebTestCase


class ConvertersTestCase(SWHWebTestCase):

    def test_fmap(self):
        self.assertEqual([2, 3, None, 4],
                         converters.fmap(lambda x: x+1, [1, 2, None, 3]))
        self.assertEqual([11, 12, 13],
                         list(converters.fmap(lambda x: x+10,
                                              map(lambda x: x, [1, 2, 3]))))
        self.assertEqual({'a': 2, 'b': 4},
                         converters.fmap(lambda x: x*2, {'a': 1, 'b': 2}))
        self.assertEqual(100,
                         converters.fmap(lambda x: x*10, 10))
        self.assertEqual({'a': [2, 6], 'b': 4},
                          converters.fmap(lambda x: x*2, {'a': [1, 3], 'b': 2})) # noqa

        self.assertIsNone(converters.fmap(lambda x: x, None))

    def test_from_swh(self):
        some_input = {
            'a': 'something',
            'b': 'someone',
            'c': b'sharp-0.3.4.tgz',
            'd': hashutil.hash_to_bytes(
                'b04caf10e9535160d90e874b45aa426de762f19f'),
            'e': b'sharp.html/doc_002dS_005fISREG.html',
            'g': [b'utf-8-to-decode', b'another-one'],
            'h': 'something filtered',
            'i': {'e': b'something'},
            'j': {
                'k': {
                    'l': [b'bytes thing', b'another thingy', b''],
                    'n': 'dont care either'
                },
                'm': 'dont care'
            },
            'o': 'something',
            'p': b'foo',
            'q': {'extra-headers': [['a', b'intact']]},
            'w': None,
            'r': {'p': 'also intact',
                  'q': 'bar'},
            's': {
                'timestamp': 42,
                'offset': -420,
                'negative_utc': None,
            },
            's1': {
                'timestamp': {'seconds': 42, 'microseconds': 0},
                'offset': -420,
                'negative_utc': None,
            },
            's2': datetime.datetime(
                2013, 7, 1, 20, 0, 0,
                tzinfo=datetime.timezone.utc),
            't': None,
            'u': None,
            'v': None,
            'x': None,
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
                    'l': ['bytes thing', 'another thingy', '']
                }
            },
            'p': 'foo',
            'q': {'extra-headers': [['a', 'intact']]},
            'w': {},
            'r': {'p': 'also intact',
                  'q': 'bar'},
            's': '1969-12-31T17:00:42-07:00',
            's1': '1969-12-31T17:00:42-07:00',
            's2': '2013-07-01T20:00:00+00:00',
            'u': {},
            'v': [],
            'x': None,
        }

        actual_output = converters.from_swh(
            some_input,
            hashess={'d', 'o', 'x'},
            bytess={'c', 'e', 'g', 'l'},
            dates={'s', 's1', 's2'},
            blacklist={'h', 'm', 'n', 'o'},
            removables_if_empty={'t'},
            empty_dict={'u'},
            empty_list={'v'},
            convert={'p', 'q', 'w'},
            convert_fn=converters.convert_revision_metadata)

        self.assertEqual(expected_output, actual_output)

    def test_from_swh_edge_cases_do_no_conversion_if_none_or_not_bytes(self):
        some_input = {
            'a': 'something',
            'b': None,
            'c': 'someone',
            'd': None,
            'e': None
        }

        expected_output = {
            'a': 'something',
            'b': None,
            'c': 'someone',
            'd': None,
            'e': None
        }

        actual_output = converters.from_swh(some_input,
                                            hashess={'a', 'b'},
                                            bytess={'c', 'd'},
                                            dates={'e'})

        self.assertEqual(expected_output, actual_output)

    def test_from_swh_edge_cases_convert_invalid_utf8_bytes(self):
        some_input = {
            'a': 'something',
            'b': 'someone',
            'c': b'a name \xff',
            'd': b'an email \xff',
        }

        expected_output = {
            'a': 'something',
            'b': 'someone',
            'c': 'a name \\xff',
            'd': 'an email \\xff',
            'decoding_failures': ['c', 'd']
        }

        actual_output = converters.from_swh(some_input,
                                            hashess={'a', 'b'},
                                            bytess={'c', 'd'})
        for v in ['a', 'b', 'c', 'd']:
            self.assertEqual(expected_output[v], actual_output[v])
        self.assertEqual(len(expected_output['decoding_failures']),
                         len(actual_output['decoding_failures']))
        for v in expected_output['decoding_failures']:
            self.assertTrue(v in actual_output['decoding_failures'])

    def test_from_swh_empty(self):
        # when
        self.assertEqual({}, converters.from_swh({}))

    def test_from_swh_none(self):
        # when
        self.assertIsNone(converters.from_swh(None))

    def test_from_provenance(self):
        # given
        input_provenance = {
            'origin': 10,
            'visit': 1,
            'content': hashutil.hash_to_bytes(
                '321caf10e9535160d90e874b45aa426de762f19f'),
            'revision': hashutil.hash_to_bytes(
                '123caf10e9535160d90e874b45aa426de762f19f'),
            'path': b'octave-3.4.0/doc/interpreter/octave/doc_002dS_005fISREG'
        }

        expected_provenance = {
            'origin': 10,
            'visit': 1,
            'content': '321caf10e9535160d90e874b45aa426de762f19f',
            'revision': '123caf10e9535160d90e874b45aa426de762f19f',
            'path': 'octave-3.4.0/doc/interpreter/octave/doc_002dS_005fISREG'
        }

        # when
        actual_provenance = converters.from_provenance(input_provenance)

        # then
        self.assertEqual(actual_provenance, expected_provenance)

    def test_from_origin(self):
        # given
        origin_input = {
            'id': 9,
            'type': 'ftp',
            'url': 'rsync://ftp.gnu.org/gnu/octave',
        }

        expected_origin = {
            'id': 9,
            'type': 'ftp',
            'url': 'rsync://ftp.gnu.org/gnu/octave',
        }

        # when
        actual_origin = converters.from_origin(origin_input)

        # then
        self.assertEqual(actual_origin, expected_origin)

    def test_from_origin_visit(self):
        snap_hash = 'b5f0b7f716735ebffe38505c60145c4fd9da6ca3'

        for snap in [snap_hash, None]:
            # given
            visit = {
                'date': {
                    'timestamp': datetime.datetime(
                        2015, 1, 1, 22, 0, 0,
                        tzinfo=datetime.timezone.utc).timestamp(),
                    'offset': 0,
                    'negative_utc': False,
                },
                'origin': 10,
                'visit': 100,
                'metadata': None,
                'status': 'full',
                'snapshot': hashutil.hash_to_bytes(snap) if snap else snap,
            }

            expected_visit = {
                'date': '2015-01-01T22:00:00+00:00',
                'origin': 10,
                'visit': 100,
                'metadata': {},
                'status': 'full',
                'snapshot': snap_hash if snap else snap
            }

            # when
            actual_visit = converters.from_origin_visit(visit)

            # then
            self.assertEqual(actual_visit, expected_visit)

    def test_from_release(self):
        release_input = {
            'id': hashutil.hash_to_bytes(
                'aad23fa492a0c5fed0708a6703be875448c86884'),
            'target': hashutil.hash_to_bytes(
                '5e46d564378afc44b31bb89f99d5675195fbdf67'),
            'target_type': 'revision',
            'date': {
                'timestamp': datetime.datetime(
                    2015, 1, 1, 22, 0, 0,
                    tzinfo=datetime.timezone.utc).timestamp(),
                'offset': 0,
                'negative_utc': False,
            },
            'author': {
                'name': b'author name',
                'fullname': b'Author Name author@email',
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
            'date': '2015-01-01T22:00:00+00:00',
            'author': {
                'name': 'author name',
                'fullname': 'Author Name author@email',
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

    def test_from_release_no_revision(self):
        release_input = {
            'id': hashutil.hash_to_bytes(
                'b2171ee2bdf119cd99a7ec7eff32fa8013ef9a4e'),
            'target': None,
            'date': {
                'timestamp': datetime.datetime(
                    2016, 3, 2, 10, 0, 0,
                    tzinfo=datetime.timezone.utc).timestamp(),
                'offset': 0,
                'negative_utc': True,

            },
            'name': b'v0.1.1',
            'message': b'comment on release',
            'synthetic': False,
            'author': {
                'name': b'bob',
                'fullname': b'Bob bob@alice.net',
                'email': b'bob@alice.net',
            },
        }

        expected_release = {
            'id': 'b2171ee2bdf119cd99a7ec7eff32fa8013ef9a4e',
            'target': None,
            'date': '2016-03-02T10:00:00-00:00',
            'name': 'v0.1.1',
            'message': 'comment on release',
            'synthetic': False,
            'author': {
                'name': 'bob',
                'fullname': 'Bob bob@alice.net',
                'email': 'bob@alice.net',
            },
        }

        # when
        actual_release = converters.from_release(release_input)

        # then
        self.assertEqual(actual_release, expected_release)

    def test_from_revision(self):
        revision_input = {
            'id': hashutil.hash_to_bytes(
                '18d8be353ed3480476f032475e7c233eff7371d5'),
            'directory': hashutil.hash_to_bytes(
                '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6'),
            'author': {
                'name': b'Software Heritage',
                'fullname': b'robot robot@softwareheritage.org',
                'email': b'robot@softwareheritage.org',
            },
            'committer': {
                'name': b'Software Heritage',
                'fullname': b'robot robot@softwareheritage.org',
                'email': b'robot@softwareheritage.org',
            },
            'message': b'synthetic revision message',
            'date': {
                'timestamp': datetime.datetime(
                    2000, 1, 17, 11, 23, 54,
                    tzinfo=datetime.timezone.utc).timestamp(),
                'offset': 0,
                'negative_utc': False,
            },
            'committer_date': {
                'timestamp': datetime.datetime(
                    2000, 1, 17, 11, 23, 54,
                    tzinfo=datetime.timezone.utc).timestamp(),
                'offset': 0,
                'negative_utc': False,
            },
            'synthetic': True,
            'type': 'tar',
            'parents': [
                hashutil.hash_to_bytes(
                    '29d8be353ed3480476f032475e7c244eff7371d5'),
                hashutil.hash_to_bytes(
                    '30d8be353ed3480476f032475e7c244eff7371d5')
            ],
            'children': [
                hashutil.hash_to_bytes(
                    '123546353ed3480476f032475e7c244eff7371d5'),
            ],
            'metadata': {
                'extra_headers': [['gpgsig', b'some-signature']],
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
                'fullname': 'robot robot@softwareheritage.org',
                'email': 'robot@softwareheritage.org',
            },
            'committer': {
                'name': 'Software Heritage',
                'fullname': 'robot robot@softwareheritage.org',
                'email': 'robot@softwareheritage.org',
            },
            'message': 'synthetic revision message',
            'date': "2000-01-17T11:23:54+00:00",
            'committer_date': "2000-01-17T11:23:54+00:00",
            'children': [
                '123546353ed3480476f032475e7c244eff7371d5'
            ],
            'parents': [
                '29d8be353ed3480476f032475e7c244eff7371d5',
                '30d8be353ed3480476f032475e7c244eff7371d5'
            ],
            'type': 'tar',
            'synthetic': True,
            'metadata': {
                'extra_headers': [['gpgsig', 'some-signature']],
                'original_artifact': [{
                    'archive_type': 'tar',
                    'name': 'webbase-5.7.0.tar.gz',
                    'sha1': '147f73f369733d088b7a6fa9c4e0273dcd3c7ccd',
                    'sha1_git': '6a15ea8b881069adedf11feceec35588f2cfe8f1',
                    'sha256': '401d0df797110bea805d358b85bcc1ced29549d3d73f'
                    '309d36484e7edf7bb912'
                }]
            },
            'merge': True
        }

        # when
        actual_revision = converters.from_revision(revision_input)

        # then
        self.assertEqual(actual_revision, expected_revision)

    def test_from_revision_nomerge(self):
        revision_input = {
            'id': hashutil.hash_to_bytes(
                '18d8be353ed3480476f032475e7c233eff7371d5'),
            'parents': [
                hashutil.hash_to_bytes(
                    '29d8be353ed3480476f032475e7c244eff7371d5')
            ]
        }

        expected_revision = {
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'parents': [
                '29d8be353ed3480476f032475e7c244eff7371d5'
            ],
            'merge': False
        }

        # when
        actual_revision = converters.from_revision(revision_input)

        # then
        self.assertEqual(actual_revision, expected_revision)

    def test_from_revision_noparents(self):
        revision_input = {
            'id': hashutil.hash_to_bytes(
                '18d8be353ed3480476f032475e7c233eff7371d5'),
            'directory': hashutil.hash_to_bytes(
                '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6'),
            'author': {
                'name': b'Software Heritage',
                'fullname': b'robot robot@softwareheritage.org',
                'email': b'robot@softwareheritage.org',
            },
            'committer': {
                'name': b'Software Heritage',
                'fullname': b'robot robot@softwareheritage.org',
                'email': b'robot@softwareheritage.org',
            },
            'message': b'synthetic revision message',
            'date': {
                'timestamp': datetime.datetime(
                    2000, 1, 17, 11, 23, 54,
                    tzinfo=datetime.timezone.utc).timestamp(),
                'offset': 0,
                'negative_utc': False,
            },
            'committer_date': {
                'timestamp': datetime.datetime(
                    2000, 1, 17, 11, 23, 54,
                    tzinfo=datetime.timezone.utc).timestamp(),
                'offset': 0,
                'negative_utc': False,
            },
            'synthetic': True,
            'type': 'tar',
            'children': [
                hashutil.hash_to_bytes(
                    '123546353ed3480476f032475e7c244eff7371d5'),
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
                'fullname': 'robot robot@softwareheritage.org',
                'email': 'robot@softwareheritage.org',
            },
            'committer': {
                'name': 'Software Heritage',
                'fullname': 'robot robot@softwareheritage.org',
                'email': 'robot@softwareheritage.org',
            },
            'message': 'synthetic revision message',
            'date': "2000-01-17T11:23:54+00:00",
            'committer_date': "2000-01-17T11:23:54+00:00",
            'children': [
                '123546353ed3480476f032475e7c244eff7371d5'
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
            }
        }

        # when
        actual_revision = converters.from_revision(revision_input)

        # then
        self.assertEqual(actual_revision, expected_revision)

    def test_from_revision_invalid(self):
        revision_input = {
            'id': hashutil.hash_to_bytes(
                '18d8be353ed3480476f032475e7c233eff7371d5'),
            'directory': hashutil.hash_to_bytes(
                '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6'),
            'author': {
                'name': b'Software Heritage',
                'fullname': b'robot robot@softwareheritage.org',
                'email': b'robot@softwareheritage.org',
            },
            'committer': {
                'name': b'Software Heritage',
                'fullname': b'robot robot@softwareheritage.org',
                'email': b'robot@softwareheritage.org',
            },
            'message': b'invalid message \xff',
            'date': {
                'timestamp': datetime.datetime(
                    2000, 1, 17, 11, 23, 54,
                    tzinfo=datetime.timezone.utc).timestamp(),
                'offset': 0,
                'negative_utc': False,
            },
            'committer_date': {
                'timestamp': datetime.datetime(
                    2000, 1, 17, 11, 23, 54,
                    tzinfo=datetime.timezone.utc).timestamp(),
                'offset': 0,
                'negative_utc': False,
            },
            'synthetic': True,
            'type': 'tar',
            'parents': [
                hashutil.hash_to_bytes(
                    '29d8be353ed3480476f032475e7c244eff7371d5'),
                hashutil.hash_to_bytes(
                    '30d8be353ed3480476f032475e7c244eff7371d5')
            ],
            'children': [
                hashutil.hash_to_bytes(
                    '123546353ed3480476f032475e7c244eff7371d5'),
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
                'fullname': 'robot robot@softwareheritage.org',
                'email': 'robot@softwareheritage.org',
            },
            'committer': {
                'name': 'Software Heritage',
                'fullname': 'robot robot@softwareheritage.org',
                'email': 'robot@softwareheritage.org',
            },
            'message': None,
            'message_decoding_failed': True,
            'date': "2000-01-17T11:23:54+00:00",
            'committer_date': "2000-01-17T11:23:54+00:00",
            'children': [
                '123546353ed3480476f032475e7c244eff7371d5'
            ],
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
            'merge': True
        }

        # when
        actual_revision = converters.from_revision(revision_input)

        # then
        self.assertEqual(actual_revision, expected_revision)

    def test_from_content_none(self):
        self.assertIsNone(converters.from_content(None))

    def test_from_content(self):
        content_input = {
            'sha1': hashutil.hash_to_bytes(
                '5c6f0e2750f48fa0bd0c4cf5976ba0b9e02ebda5'),
            'sha256': hashutil.hash_to_bytes(
                '39007420ca5de7cb3cfc15196335507e'
                'e76c98930e7e0afa4d2747d3bf96c926'),
            'blake2s256': hashutil.hash_to_bytes(
                '49007420ca5de7cb3cfc15196335507e'
                'e76c98930e7e0afa4d2747d3bf96c926'),
            'sha1_git': hashutil.hash_to_bytes(
                '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'),
            'ctime': 'something-which-is-filtered-out',
            'data': b'data in bytes',
            'length': 10,
            'status': 'hidden',
        }

        # 'status' is filtered
        expected_content = {
            'checksums': {
                'sha1': '5c6f0e2750f48fa0bd0c4cf5976ba0b9e02ebda5',
                'sha256': '39007420ca5de7cb3cfc15196335507ee76c98'
                          '930e7e0afa4d2747d3bf96c926',
                'blake2s256': '49007420ca5de7cb3cfc15196335507ee7'
                              '6c98930e7e0afa4d2747d3bf96c926',
                'sha1_git': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            },
            'data': b'data in bytes',
            'length': 10,
            'status': 'absent',
        }

        # when
        actual_content = converters.from_content(content_input)

        # then
        self.assertEqual(actual_content, expected_content)

    def test_from_person(self):
        person_input = {
            'id': 10,
            'anything': 'else',
            'name': b'bob',
            'fullname': b'bob bob@alice.net',
            'email': b'bob@foo.alice',
        }

        expected_person = {
            'id': 10,
            'anything': 'else',
            'name': 'bob',
            'fullname': 'bob bob@alice.net',
            'email': 'bob@foo.alice',
        }

        # when
        actual_person = converters.from_person(person_input)

        # then
        self.assertEqual(actual_person, expected_person)

    def test_from_directory_entries(self):
        dir_entries_input = {
            'sha1': hashutil.hash_to_bytes(
                '5c6f0e2750f48fa0bd0c4cf5976ba0b9e02ebda5'),
            'sha256': hashutil.hash_to_bytes(
                '39007420ca5de7cb3cfc15196335507e'
                'e76c98930e7e0afa4d2747d3bf96c926'),
            'sha1_git': hashutil.hash_to_bytes(
                '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'),
            'blake2s256': hashutil.hash_to_bytes(
                '685395c5dc57cada459364f0946d3dd45bad5fcbab'
                'c1048edb44380f1d31d0aa'),
            'target': hashutil.hash_to_bytes(
                '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'),
            'dir_id': hashutil.hash_to_bytes(
                '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'),
            'name': b'bob',
            'type': 10,
            'status': 'hidden',
        }

        expected_dir_entries = {
            'checksums': {
                'sha1': '5c6f0e2750f48fa0bd0c4cf5976ba0b9e02ebda5',
                'sha256': '39007420ca5de7cb3cfc15196335507ee76c98'
                          '930e7e0afa4d2747d3bf96c926',
                'sha1_git': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
                'blake2s256': '685395c5dc57cada459364f0946d3dd45bad5f'
                              'cbabc1048edb44380f1d31d0aa',
            },
            'target': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'dir_id': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'name': 'bob',
            'type': 10,
            'status': 'absent',
        }

        # when
        actual_dir_entries = converters.from_directory_entry(dir_entries_input)

        # then
        self.assertEqual(actual_dir_entries, expected_dir_entries)

    def test_from_filetype(self):
        content_filetype = {
            'id': hashutil.hash_to_bytes(
                '5c6f0e2750f48fa0bd0c4cf5976ba0b9e02ebda5'),
            'encoding': 'utf-8',
            'mimetype': 'text/plain',
        }

        expected_content_filetype = {
            'id': '5c6f0e2750f48fa0bd0c4cf5976ba0b9e02ebda5',
            'encoding': 'utf-8',
            'mimetype': 'text/plain',
        }

        # when
        actual_content_filetype = converters.from_filetype(content_filetype)

        # then
        self.assertEqual(actual_content_filetype, expected_content_filetype)
