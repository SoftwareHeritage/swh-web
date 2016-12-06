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

    def setUp(self):
        self.origin_visit1 = {
            'date': datetime.datetime(
                2015, 1, 1, 22, 0, 0,
                tzinfo=datetime.timezone.utc),
            'origin': 1,
            'visit': 1
        }

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
    def content_ctags_search_1(self):
        # given
        self.storage.content_ctags_search = MagicMock(
            return_value="some-result")

        # when
        actual_ctags = backend.content_ctags_search(
            'foo', last_sha1='some-hash', limit=1)

        # then
        self.assertEquals(actual_ctags, 'some-result')
        self.storage.content_ctags_search.assert_called_once_with(
            'foo', last_sha1='some-hash', limit=1)

    @istest
    def content_ctags_search_2(self):
        # given
        self.storage.content_ctags_search = MagicMock(
            return_value="some other result")

        # when
        actual_ctags = backend.content_ctags_search(
            'foo|bar', last_sha1='some-hash', limit=2)

        # then
        self.assertEquals(actual_ctags, 'some other result')
        self.storage.content_ctags_search.assert_called_once_with(
            'foo|bar', last_sha1='some-hash', limit=2)

    @istest
    def content_ctags_search_3(self):
        # given
        self.storage.content_ctags_search = MagicMock(
            return_value="yet another result")

        # when
        actual_ctags = backend.content_ctags_search(
            'bar', last_sha1='some-hash', limit=1000)

        # then
        self.assertEquals(actual_ctags, 'yet another result')
        self.storage.content_ctags_search.assert_called_once_with(
            'bar', last_sha1='some-hash', limit=50)

    @istest
    def content_get(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '123caf10e9535160d90e874b45aa426de762f19f')
        stub_contents = [{
            'sha1': sha1_bin,
            'data': b'binary data',
        }]

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
    def content_find_provenance_ko_no_result(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '123caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_find_provenance = MagicMock(
            return_value=(x for x in []))

        # when
        actual_lookup = backend.content_find_provenance('sha1_git', sha1_bin)

        # then
        self.assertEquals(list(actual_lookup), [])

        self.storage.content_find_provenance.assert_called_once_with(
            {'sha1_git': sha1_bin})

    @istest
    def content_ctags_get(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_ctags_get = MagicMock(
            return_value=[1, 2, 3])

        # when
        actual_content = backend.content_ctags_get(sha1_bin)

        # then
        self.assertEquals(actual_content, [1, 2, 3])

        self.storage.content_ctags_get.assert_called_with(
            [sha1_bin])

    @istest
    def content_ctags_get_no_result(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_ctags_get = MagicMock(
            return_value=[])

        # when
        actual_content = backend.content_ctags_get(sha1_bin)

        # then
        self.assertEquals(actual_content, [])

        self.storage.content_ctags_get.assert_called_with(
            [sha1_bin])

    @istest
    def content_filetype_get(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_mimetype_get = MagicMock(
            return_value=[1, 2, 3])

        # when
        actual_content = backend.content_filetype_get(sha1_bin)

        # then
        self.assertEquals(actual_content, 1)

        self.storage.content_mimetype_get.assert_called_with(
            [sha1_bin])

    @istest
    def content_filetype_get_no_result(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_mimetype_get = MagicMock(
            return_value=[])

        # when
        actual_content = backend.content_filetype_get(sha1_bin)

        # then
        self.assertIsNone(actual_content)

        self.storage.content_mimetype_get.assert_called_with(
            [sha1_bin])

    @istest
    def content_language_get(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_language_get = MagicMock(
            return_value=[1, 2, 3])

        # when
        actual_content = backend.content_language_get(sha1_bin)

        # then
        self.assertEquals(actual_content, 1)

        self.storage.content_language_get.assert_called_with(
            [sha1_bin])

    @istest
    def content_language_get_no_result(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_language_get = MagicMock(
            return_value=[])

        # when
        actual_content = backend.content_language_get(sha1_bin)

        # then
        self.assertIsNone(actual_content)

        self.storage.content_language_get.assert_called_with(
            [sha1_bin])

    @istest
    def content_license_get(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_fossology_license_get = MagicMock(
            return_value=[1, 2, 3])

        # when
        actual_content = backend.content_license_get(sha1_bin)

        # then
        self.assertEquals(actual_content, 1)

        self.storage.content_fossology_license_get.assert_called_with(
            [sha1_bin])

    @istest
    def content_license_get_no_result(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_fossology_license_get = MagicMock(
            return_value=[])

        # when
        actual_content = backend.content_license_get(sha1_bin)

        # then
        self.assertIsNone(actual_content)

        self.storage.content_fossology_license_get.assert_called_with(
            [sha1_bin])

    @istest
    def content_find_provenance(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f')
        self.storage.content_find_provenance = MagicMock(
            return_value=(x for x in (1, 2, 3)))

        # when
        actual_content = backend.content_find_provenance('sha1', sha1_bin)

        # then
        self.assertEquals(list(actual_content), [1, 2, 3])

        # check the function has been called with parameters
        self.storage.content_find_provenance.assert_called_with(
            {'sha1': sha1_bin})

    @istest
    def content_missing_per_sha1_none(self):
        # given
        sha1s_bin = [hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f'),
                     hashutil.hex_to_hash(
            '745bab676c8f3cec8016e0c39ea61cf57e518865'
                     )]
        self.storage.content_missing_per_sha1 = MagicMock(return_value=[])

        # when
        actual_content = backend.content_missing_per_sha1(sha1s_bin)

        # then
        self.assertEquals(actual_content, [])
        self.storage.content_missing_per_sha1.assert_called_with(sha1s_bin)

    @istest
    def content_missing_per_sha1_some(self):
        # given
        sha1s_bin = [hashutil.hex_to_hash(
            '456caf10e9535160d90e874b45aa426de762f19f'),
                     hashutil.hex_to_hash(
            '745bab676c8f3cec8016e0c39ea61cf57e518865'
                     )]
        self.storage.content_missing_per_sha1 = MagicMock(return_value=[
            hashutil.hex_to_hash(
                '745bab676c8f3cec8016e0c39ea61cf57e518865'
            )])

        # when
        actual_content = backend.content_missing_per_sha1(sha1s_bin)

        # then
        self.assertEquals(actual_content, [hashutil.hex_to_hash(
            '745bab676c8f3cec8016e0c39ea61cf57e518865'
            )])
        self.storage.content_missing_per_sha1.assert_called_with(sha1s_bin)

    @istest
    def origin_get_by_id(self):
        # given
        self.storage.origin_get = MagicMock(return_value={
            'id': 'origin-id',
            'lister': 'uuid-lister',
            'project': 'uuid-project',
            'url': 'ftp://some/url/to/origin',
            'type': 'ftp'})

        # when
        actual_origin = backend.origin_get({'id': 'origin-id'})

        # then
        self.assertEqual(actual_origin, {'id': 'origin-id',
                                         'lister': 'uuid-lister',
                                         'project': 'uuid-project',
                                         'url': 'ftp://some/url/to/origin',
                                         'type': 'ftp'})

        self.storage.origin_get.assert_called_with({'id': 'origin-id'})

    @istest
    def origin_get_by_type_url(self):
        # given
        self.storage.origin_get = MagicMock(return_value={
            'id': 'origin-id',
            'lister': 'uuid-lister',
            'project': 'uuid-project',
            'url': 'ftp://some/url/to/origin',
            'type': 'ftp'})

        # when
        actual_origin = backend.origin_get({'type': 'ftp',
                                            'url': 'ftp://some/url/to/origin'})

        # then
        self.assertEqual(actual_origin, {'id': 'origin-id',
                                         'lister': 'uuid-lister',
                                         'project': 'uuid-project',
                                         'url': 'ftp://some/url/to/origin',
                                         'type': 'ftp'})

        self.storage.origin_get.assert_called_with(
            {'type': 'ftp',
             'url': 'ftp://some/url/to/origin'})

    @istest
    def person_get(self):
        # given
        self.storage.person_get = MagicMock(return_value=[{
            'id': 'person-id',
            'name': 'blah'}])

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
        self.storage.directory_get = MagicMock(return_value=None)

        # when
        actual_directory = backend.directory_get(sha1_bin)

        # then
        self.assertEquals(actual_directory, None)

        self.storage.directory_get.assert_called_with([sha1_bin])

    @istest
    def directory_get(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '51f71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')
        sha1_bin2 = hashutil.hex_to_hash(
            '62071b8614fcd89ccd17ca2b1d9e66c5b00a6d03')
        stub_dir = {'id': sha1_bin, 'revision': b'sha1-blah'}
        stub_dir2 = {'id': sha1_bin2, 'revision': b'sha1-foobar'}
        self.storage.directory_get = MagicMock(return_value=[stub_dir,
                                                             stub_dir2])

        # when
        actual_directory = backend.directory_get(sha1_bin)

        # then
        self.assertEquals(actual_directory, stub_dir)

        self.storage.directory_get.assert_called_with([sha1_bin])

    @istest
    def directory_ls_empty_result(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')
        self.storage.directory_ls = MagicMock(return_value=[])

        # when
        actual_directory = backend.directory_ls(sha1_bin)

        # then
        self.assertEquals(actual_directory, [])

        self.storage.directory_ls.assert_called_with(sha1_bin, False)

    @istest
    def directory_ls(self):
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

        self.storage.directory_ls = MagicMock(
            return_value=stub_dir_entries)

        actual_directory = backend.directory_ls(sha1_bin, recursive=True)

        # then
        self.assertIsNotNone(actual_directory)
        self.assertEqual(list(actual_directory), stub_dir_entries)

        self.storage.directory_ls.assert_called_with(sha1_bin, True)

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
    def revision_get_by_not_found(self):
        # given
        self.storage.revision_get_by = MagicMock(return_value=[])

        # when
        actual_revision = backend.revision_get_by(10, 'master', 'ts2')

        # then
        self.assertIsNone(actual_revision)

        self.storage.revision_get_by.assert_called_with(10, 'master',
                                                        timestamp='ts2',
                                                        limit=1)

    @istest
    def revision_get_by(self):
        # given
        self.storage.revision_get_by = MagicMock(return_value=[{'id': 1}])

        # when
        actual_revisions = backend.revision_get_by(100, 'dev', 'ts')

        # then
        self.assertEquals(actual_revisions, {'id': 1})

        self.storage.revision_get_by.assert_called_with(100, 'dev',
                                                        timestamp='ts',
                                                        limit=1)

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
    def revision_get_multiple(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '18d8be353ed3480476f032475e7c233eff7371d5')
        sha1_other = hashutil.hex_to_hash(
            'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc')

        stub_revisions = [
            {
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
            },
            {
                'id': sha1_other,
                'directory': hashutil.hex_to_hash(
                    '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6'),
                'author': {
                    'name': b'name',
                    'email': b'name@surname.org',
                },
                'committer': {
                    'name': b'name',
                    'email': b'name@surname.org',
                },
                'message': b'ugly fix for bug 42',
                'date': datetime.datetime(2000, 1, 12, 5, 23, 54),
                'date_offset': 0,
                'committer_date': datetime.datetime(2000, 1, 12, 5, 23, 54),
                'committer_date_offset': 0,
                'synthetic': False,
                'type': 'git',
                'parents': [],
                'metadata': [],
            }
        ]
        self.storage.revision_get = MagicMock(
            return_value=stub_revisions)

        # when
        actual_revision = backend.revision_get_multiple([sha1_bin, sha1_other])

        # then
        self.assertEqual(actual_revision, stub_revisions)

        self.storage.revision_get.assert_called_with(
            [sha1_bin, sha1_other])

    @istest
    def revision_get_multiple_none_found(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '18d8be353ed3480476f032475e7c233eff7371d5')
        sha1_other = hashutil.hex_to_hash(
            'adc83b19e793491b1c6ea0fd8b46cd9f32e592fc')

        self.storage.revision_get = MagicMock(
            return_value=[])

        # when
        actual_revision = backend.revision_get_multiple([sha1_bin, sha1_other])

        # then
        self.assertEqual(actual_revision, [])

        self.storage.revision_get.assert_called_with(
            [sha1_bin, sha1_other])

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
        actual_revision = backend.revision_log(sha1_bin, limit=1)

        # then
        self.assertEqual(list(actual_revision), stub_revision_log)

        self.storage.revision_log.assert_called_with([sha1_bin], 1)

    @istest
    def revision_log_by(self):
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

        self.storage.revision_log_by = MagicMock(
            return_value=stub_revision_log)

        # when
        actual_log = backend.revision_log_by(1, 'refs/heads/master',
                                             None, limit=1)

        # then
        self.assertEqual(actual_log, stub_revision_log)
        self.storage.revision_log.assert_called_with([sha1_bin], 1)

    @istest
    def revision_log_by_norev(self):
        # given
        sha1_bin = hashutil.hex_to_hash(
            '28d8be353ed3480476f032475e7c233eff7371d5')

        self.storage.revision_log_by = MagicMock(return_value=None)

        # when
        actual_log = backend.revision_log_by(1, 'refs/heads/master',
                                             None, limit=1)

        # then
        self.assertEqual(actual_log, None)
        self.storage.revision_log.assert_called_with([sha1_bin], 1)

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

    @istest
    def lookup_origin_visits(self):
        # given
        expected_origin_visits = [
            self.origin_visit1, {
                'date': datetime.datetime(
                    2013, 7, 1, 20, 0, 0,
                    tzinfo=datetime.timezone.utc),
                'origin': 1,
                'visit': 2
            }, {
                'date': datetime.datetime(
                    2015, 1, 1, 21, 0, 0,
                    tzinfo=datetime.timezone.utc),
                'origin': 1,
                'visit': 3
            }]
        self.storage.origin_visit_get = MagicMock(
            return_value=expected_origin_visits)

        # when
        actual_origin_visits = backend.lookup_origin_visits(5)

        # then
        self.assertEqual(list(actual_origin_visits), expected_origin_visits)

        self.storage.origin_visit_get.assert_called_with(5)

    @istest
    def lookup_origin_visit(self):
        # given
        self.storage.origin_visit_get_by = MagicMock(
            return_value=self.origin_visit1)

        # when
        actual_origin_visit = backend.lookup_origin_visit(10, 1)

        # then
        self.assertEqual(actual_origin_visit, self.origin_visit1)

        self.storage.origin_visit_get_by.assert_called_with(10, 1)

    @istest
    def lookup_origin_visit_None(self):
        # given
        self.storage.origin_visit_get_by = MagicMock(
            return_value=None)

        # when
        actual_origin_visit = backend.lookup_origin_visit(1, 10)

        # then
        self.assertIsNone(actual_origin_visit)

        self.storage.origin_visit_get_by.assert_called_with(1, 10)

    @istest
    def directory_entry_get_by_path(self):
        # given
        stub_dir_entry = {'id': b'dir-id',
                          'type': 'dir',
                          'name': b'some/path/foo'}
        self.storage.directory_entry_get_by_path = MagicMock(
            return_value=stub_dir_entry)

        # when
        actual_dir_entry = backend.directory_entry_get_by_path(b'dir-sha1',
                                                               'some/path/foo')

        self.assertEquals(actual_dir_entry, stub_dir_entry)
        self.storage.directory_entry_get_by_path.assert_called_once_with(
            b'dir-sha1',
            [b'some', b'path', b'foo'])

    @istest
    def entity_get(self):
        # given
        stub_entities = [{'uuid': 'e8c3fc2e-a932-4fd7-8f8e-c40645eb35a7',
                          'parent': 'aee991a0-f8d7-4295-a201-d1ce2efc9fb2'},
                         {'uuid': 'aee991a0-f8d7-4295-a201-d1ce2efc9fb2',
                          'parent': None}]
        self.storage.entity_get = MagicMock(return_value=stub_entities)

        # when
        actual_entities = backend.entity_get(
            'e8c3fc2e-a932-4fd7-8f8e-c40645eb35a7')

        # then
        self.assertEquals(actual_entities, stub_entities)

        self.storage.entity_get.assert_called_once_with(
            'e8c3fc2e-a932-4fd7-8f8e-c40645eb35a7')
