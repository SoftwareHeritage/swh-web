# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import datetime

from nose.tools import istest
from unittest.mock import MagicMock

from swh.core import hashutil
from swh.web.ui import backend
from swh.web.ui.tests import test_app


class BackendTestCase(test_app.SWHApiTestCase):

    @istest
    def content_get_ko_not_found_1(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f777')
        self.storage.content_get = MagicMock(return_value=None)

        # when
        actual_content = backend.content_get(sha1_bin)

        # then
        self.assertIsNone(actual_content)

        self.storage.content_get.assert_called_once_with(
            [sha1_bin])

    @istest
    def content_get_ko_not_found_empty_result(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_get = MagicMock(return_value=[])

        # when
        actual_content = backend.content_get(sha1_bin)

        # then
        self.assertIsNone(actual_content)

        self.storage.content_get.assert_called_once_with(
            [sha1_bin])

    @istest
    def content_get(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '123caf10e9535160d90e874b45aa426de762f19f')
        stub_contents = [{
            'sha1': sha1_bin,
            'data': b'binary data',
        },
                        {}]

        self.storage.content_get = MagicMock(return_value=stub_contents)

        # when
        actual_content = backend.content_get(sha1_bin)

        # then
        self.assertEquals(actual_content, stub_contents[0])
        self.storage.content_get.assert_called_once_with(
            [sha1_bin])

    @istest
    def content_find_ko_no_result(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '123caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_find = MagicMock(return_value=None)

        # when
        actual_lookup = backend.content_find('sha1_git', sha1_bin)

        # then
        self.assertIsNone(actual_lookup)

        self.storage.content_find.assert_called_once_with(
            {'sha1_git': sha1_bin})

    @istest
    def content_find(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_find = MagicMock(return_value=(1, 2, 3))

        # when
        actual_content = backend.content_find('sha1', sha1_bin)

        # then
        self.assertEquals(actual_content, (1, 2, 3))

        # check the function has been called with parameters
        self.storage.content_find.assert_called_with({'sha1': sha1_bin})

    @istest
    def content_find_occurrence_ko_no_result(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '123caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_find_occurrence = MagicMock(return_value=None)

        # when
        actual_lookup = backend.content_find_occurrence('sha1_git', sha1_bin)

        # then
        self.assertIsNone(actual_lookup)

        self.storage.content_find_occurrence.assert_called_once_with(
            {'sha1_git': sha1_bin})

    @istest
    def content_find_occurrence(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_find_occurrence = MagicMock(
            return_value=(1, 2, 3))

        # when
        actual_content = backend.content_find_occurrence('sha1', sha1_bin)

        # then
        self.assertEquals(actual_content, (1, 2, 3))

        # check the function has been called with parameters
        self.storage.content_find_occurrence.assert_called_with(
            {'sha1': sha1_bin})

    @istest
    def origin_get(self):
        # given
        self.storage.origin_get = MagicMock(return_value={
            'id': 'origin-id',
            'lister': 'uuid-lister',
            'project': 'uuid-project',
            'url': 'ftp://some/url/to/origin',
            'type': 'ftp'})

        # when
        actual_origin = backend.origin_get('origin-id')

        # then
        self.assertEqual(actual_origin, {'id': 'origin-id',
                                         'lister': 'uuid-lister',
                                         'project': 'uuid-project',
                                         'url': 'ftp://some/url/to/origin',
                                         'type': 'ftp'})

        self.storage.origin_get.assert_called_with({'id': 'origin-id'})

    @istest
    def person_get(self):
        # given
        self.storage.person_get = MagicMock(return_value={
            'id': 'person-id',
            'name': 'blah'})

        # when
        actual_person = backend.person_get('person-id')

        # then
        self.assertEqual(actual_person, {'id': 'person-id',
                                         'name': 'blah'})

        self.storage.person_get.assert_called_with(['person-id'])

    @istest
    def directory_get_not_found(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')
        self.storage.directory_get = MagicMock(return_value=[])

        # when
        actual_directory = backend.directory_get(sha1_bin)

        # then
        self.assertIsNone(actual_directory)

        self.storage.directory_get.assert_called_with(sha1_bin, False)

    @istest
    def directory_get(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')
        stub_dir_entries = [{
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
        }]

        self.storage.directory_get = MagicMock(
            return_value=stub_dir_entries)

        actual_directory = backend.directory_get(sha1_bin, recursive=True)

        # then
        self.assertIsNotNone(actual_directory)
        self.assertEqual(list(actual_directory), stub_dir_entries)

        self.storage.directory_get.assert_called_with(sha1_bin, True)

    @istest
    def release_get_not_found(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '65a55bbdf3629f916219feb3dcc7393ded1bc8db')

        self.storage.release_get = MagicMock(return_value=[])

        # when
        actual_release = backend.release_get(sha1_bin)

        # then
        self.assertIsNone(actual_release)
        self.storage.release_get.assert_called_with([sha1_bin])

    @istest
    def release_get(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '65a55bbdf3629f916219feb3dcc7393ded1bc8db')

        stub_releases = [{
            'id': sha1_bin,
            'target': None,
            'date': datetime.datetime(2015, 1, 1, 22, 0, 0,
                                      tzinfo=datetime.timezone.utc),
            'name': b'v0.0.1',
            'message': b'synthetic release',
            'synthetic': True,
        }]
        self.storage.release_get = MagicMock(return_value=stub_releases)

        # when
        actual_release = backend.release_get(sha1_bin)

        # then
        self.assertEqual(actual_release, stub_releases[0])

        self.storage.release_get.assert_called_with([sha1_bin])

    @istest
    def revision_get_not_found(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '18d8be353ed3480476f032475e7c233eff7371d5')

        self.storage.revision_get = MagicMock(return_value=[])

        # when
        actual_revision = backend.revision_get(sha1_bin)

        # then
        self.assertIsNone(actual_revision)

        self.storage.revision_get.assert_called_with([sha1_bin])

    @istest
    def revision_get(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '18d8be353ed3480476f032475e7c233eff7371d5')

        stub_revisions = [{
            'id': sha1_bin,
            'directory': hashutil.hex_to_hash(
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
        self.storage.revision_get = MagicMock(return_value=stub_revisions)

        # when
        actual_revision = backend.revision_get(sha1_bin)

        # then
        self.assertEqual(actual_revision, stub_revisions[0])

        self.storage.revision_get.assert_called_with([sha1_bin])

    @istest
    def revision_log(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '28d8be353ed3480476f032475e7c233eff7371d5')
        stub_revision_log = [{
            'id': sha1_bin,
            'directory': hashutil.hex_to_hash(
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
        actual_revision = backend.revision_log(sha1_bin)

        # then
        self.assertEqual(list(actual_revision), stub_revision_log)

        self.storage.revision_log.assert_called_with(sha1_bin, 100)

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
        actual_stats = backend.stat_counters()

        # then
        expected_stats = input_stats
        self.assertEqual(actual_stats, expected_stats)

        self.storage.stat_counters.assert_called_with()
