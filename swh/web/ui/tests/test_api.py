# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import unittest
import yaml

from nose.tools import istest
from unittest.mock import patch, MagicMock

from swh.web.ui.tests import test_app
from swh.web.ui import api, exc
from swh.web.ui.exc import NotFoundExc, BadInputExc
from swh.storage.exc import StorageDBError, StorageAPIError


class ApiTestCase(test_app.SWHApiTestCase):
    @istest
    def generic_api_lookup_Nothing_is_found(self):
        # given
        def test_generic_lookup_fn(sha1, another_unused_arg):
            assert another_unused_arg == 'unused arg'
            assert sha1 == 'sha1'
            return None

        # when
        with self.assertRaises(NotFoundExc) as cm:
            api._api_lookup('sha1', test_generic_lookup_fn,
                            'This will be raised because None is returned.',
                            lambda x: x,
                            'unused arg')
            self.assertIn('This will be raised because None is returned.',
                          cm.exception.args[0])

    @istest
    def generic_api_map_are_enriched_and_transformed_to_list(self):
        # given
        def test_generic_lookup_fn_1(criteria0, param0, param1):
            assert criteria0 == 'something'
            return map(lambda x: x + 1, [1, 2, 3])

        # when
        actual_result = api._api_lookup(
            'something',
            test_generic_lookup_fn_1,
            'This is not the error message you are looking for. Move along.',
            lambda x: x * 2,
            'some param 0',
            'some param 1')

        self.assertEqual(actual_result, [4, 6, 8])

    @istest
    def generic_api_list_are_enriched_too(self):
        # given
        def test_generic_lookup_fn_2(crit):
            assert crit == 'something'
            return ['a', 'b', 'c']

        # when
        actual_result = api._api_lookup(
            'something',
            test_generic_lookup_fn_2,
            'Not the error message you are looking for, it is. '
            'Along, you move!',
            lambda x: ''. join(['=', x, '=']))

        self.assertEqual(actual_result, ['=a=', '=b=', '=c='])

    @istest
    def generic_api_generator_are_enriched_and_returned_as_list(self):
        # given
        def test_generic_lookup_fn_3(crit):
            assert crit == 'crit'
            return (i for i in [4, 5, 6])

        # when
        actual_result = api._api_lookup(
            'crit',
            test_generic_lookup_fn_3,
            'Move!',
            lambda x: x - 1)

        self.assertEqual(actual_result, [3, 4, 5])

    @istest
    def generic_api_simple_data_are_enriched_and_returned_too(self):
        # given
        def test_generic_lookup_fn_4(crit):
            assert crit == '123'
            return {'a': 10}

        def test_enrich_data(x):
            x['a'] = x['a'] * 10
            return x

        # when
        actual_result = api._api_lookup(
            '123',
            test_generic_lookup_fn_4,
            'Nothing to do',
            test_enrich_data)

        self.assertEqual(actual_result, {'a': 100})

    @patch('swh.web.ui.api.service')
#    @istest
    def api_content_checksum_to_origin(self, mock_service):
        mock_service.lookup_hash.return_value = {'found': True}
        stub_origin = {
            "lister": None,
            "url": "rsync://ftp.gnu.org/old-gnu/webbase",
            "type": "ftp",
            "id": 2,
            "project": None
        }
        mock_service.lookup_hash_origin.return_value = stub_origin

        # when
        rv = self.app.get(
            '/api/1/browse/sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_origin)

        mock_service.lookup_hash.assert_called_once_with(
            'sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03')
        mock_service.lookup_hash_origin.assert_called_once_with(
            'sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.ui.api.service')
#    @istest
    def api_content_checksum_to_origin_sha_not_found(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {'found': False}
        # when
        rv = self.app.get(
            '/api/1/browse/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Content with sha1:40e71b8614fcd89ccd17ca2b1d9e6'
            '6c5b00a6d03 not found.'
        })
        mock_service.lookup_hash.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.ui.api.service')
    @istest
    def api_content_metadata(self, mock_service):
        # given
        mock_service.lookup_content.return_value = {
            'sha1': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'sha1_git': 'b4e8f472ffcb01a03875b26e462eb568739f6882',
            'sha256': '83c0e67cc80f60caf1fcbec2d84b0ccd7968b3be4735637006560'
            'cde9b067a4f',
            'length': 17,
            'status': 'visible'
        }

        # when
        rv = self.app.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'data_url': '/api/1/content/'
                        '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/raw/',
            'sha1': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'sha1_git': 'b4e8f472ffcb01a03875b26e462eb568739f6882',
            'sha256': '83c0e67cc80f60caf1fcbec2d84b0ccd7968b3be4735637006560c'
            'de9b067a4f',
            'length': 17,
            'status': 'visible'
        })

        mock_service.lookup_content.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.ui.api.service')
    @istest
    def api_content_not_found_as_json(self, mock_service):
        # given
        mock_service.lookup_content.return_value = None
        mock_service.lookup_hash_origin = MagicMock()

        # when
        rv = self.app.get(
            '/api/1/content/sha256:83c0e67cc80f60caf1fcbec2d84b0ccd7968b3'
            'be4735637006560c/')

        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Content with sha256:83c0e67cc80f60caf1fcbec2d84b0ccd79'
            '68b3be4735637006560c not found.'
        })

        mock_service.lookup_content.assert_called_once_with(
            'sha256:83c0e67cc80f60caf1fcbec2d84b0ccd7968b3'
            'be4735637006560c')
        mock_service.lookup_hash_origin.called = False

    @patch('swh.web.ui.api.service')
    @istest
    def api_content_not_found_as_yaml(self, mock_service):
        # given
        mock_service.lookup_content.return_value = None
        mock_service.lookup_hash_origin = MagicMock()

        # when
        rv = self.app.get(
            '/api/1/content/sha256:83c0e67cc80f60caf1fcbec2d84b0ccd7968b3'
            'be4735637006560c/',
            headers={'accept': 'application/yaml'})

        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/yaml')

        response_data = yaml.load(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Content with sha256:83c0e67cc80f60caf1fcbec2d84b0ccd79'
            '68b3be4735637006560c not found.'
        })

        mock_service.lookup_content.assert_called_once_with(
            'sha256:83c0e67cc80f60caf1fcbec2d84b0ccd7968b3'
            'be4735637006560c')
        mock_service.lookup_hash_origin.called = False

    @patch('swh.web.ui.api.service')
    @istest
    def api_content_raw(self, mock_service):
        # given
        stub_content = {'data': b'some content data'}
        mock_service.lookup_content_raw.return_value = stub_content

        # when
        rv = self.app.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'
            '/raw/',
            headers={'Content-type': 'application/octet-stream',
                     'Content-disposition': 'attachment'})

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/octet-stream')
        self.assertEquals(rv.data, stub_content['data'])

        mock_service.lookup_content_raw.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.ui.api.service')
    @istest
    def api_content_raw_not_found(self, mock_service):
        # given
        mock_service.lookup_content_raw.return_value = None

        # when
        rv = self.app.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03'
            '/raw/')

        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Content with sha1:40e71b8614fcd89ccd17ca2b1d9e6'
            '6c5b00a6d03 not found.'
        })

        mock_service.lookup_content_raw.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.ui.api.service')
    @istest
    def api_search(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {
            'found': {
                'sha1': 'or something'
            }
        }

        # when
        rv = self.app.get('/api/1/search/sha1:blah/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {'found': True})

        mock_service.lookup_hash.assert_called_once_with('sha1:blah')

    @patch('swh.web.ui.api.service')
    @istest
    def api_search_as_yaml(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {
            'found': {
                'sha1': 'sha1 hash'
            }
        }

        # when
        rv = self.app.get('/api/1/search/sha1:halb/',
                          headers={'Accept': 'application/yaml'})

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/yaml')

        response_data = yaml.load(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {'found': True})

        mock_service.lookup_hash.assert_called_once_with('sha1:halb')

    @patch('swh.web.ui.api.service')
    @istest
    def api_search_not_found(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {}

        # when
        rv = self.app.get('/api/1/search/sha1:halb/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {'found': False})

        mock_service.lookup_hash.assert_called_once_with('sha1:halb')

    @patch('swh.web.ui.api.service')
    @istest
    def api_1_stat_counters_raise_error(self, mock_service):
        # given
        mock_service.stat_counters.side_effect = ValueError(
            'voluntary error to check the bad request middleware.')
        # when
        rv = self.app.get('/api/1/stat/counters/')
        # then
        self.assertEquals(rv.status_code, 400)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'voluntary error to check the bad request middleware.'})

    @patch('swh.web.ui.api.service')
    @istest
    def api_1_stat_counters_raise_swh_storage_error_db(self, mock_service):
        # given
        mock_service.stat_counters.side_effect = StorageDBError(
            'SWH Storage exploded! Will be back online shortly!')
        # when
        rv = self.app.get('/api/1/stat/counters/')
        # then
        self.assertEquals(rv.status_code, 503)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error':
            'An unexpected error occurred in the backend: '
            'SWH Storage exploded! Will be back online shortly!'})

    @patch('swh.web.ui.api.service')
    @istest
    def api_1_stat_counters_raise_swh_storage_error_api(self, mock_service):
        # given
        mock_service.stat_counters.side_effect = StorageAPIError(
            'SWH Storage API dropped dead! Will resurrect from its ashes asap!'
        )
        # when
        rv = self.app.get('/api/1/stat/counters/')
        # then
        self.assertEquals(rv.status_code, 503)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error':
            'An unexpected error occurred in the api backend: '
            'SWH Storage API dropped dead! Will resurrect from its ashes asap!'
        })

    @patch('swh.web.ui.api.service')
    @istest
    def api_1_stat_counters(self, mock_service):
        # given
        stub_stats = {
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
        mock_service.stat_counters.return_value = stub_stats

        # when
        rv = self.app.get('/api/1/stat/counters/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_stats)

        mock_service.stat_counters.assert_called_once_with()

    @patch('swh.web.ui.api.service')
    @patch('swh.web.ui.api.request')
    @istest
    def api_uploadnsearch_bad_input(self, mock_request, mock_service):
        # given
        mock_request.files = {}

        # when
        rv = self.app.post('/api/1/uploadnsearch/')

        self.assertEquals(rv.status_code, 400)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': "Bad request, missing 'filename' entry in form."})

        mock_service.upload_and_search.called = False

    @patch('swh.web.ui.api.service')
    @patch('swh.web.ui.api.request')
    @istest
    def api_uploadnsearch(self, mock_request, mock_service):
        # given
        mock_request.files = {'filename': 'simple-filename'}
        mock_service.upload_and_search.return_value = {
            'filename': 'simple-filename',
            'sha1': 'some-hex-sha1',
            'found': False,
        }

        # when
        rv = self.app.post('/api/1/uploadnsearch/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {'filename': 'simple-filename',
                                          'sha1': 'some-hex-sha1',
                                          'found': False})

        mock_service.upload_and_search.assert_called_once_with(
            'simple-filename')

    @patch('swh.web.ui.api.service')
    @istest
    def api_origin(self, mock_service):
        # given
        stub_origin = {
            'id': 1234,
            'lister': 'uuid-lister-0',
            'project': 'uuid-project-0',
            'url': 'ftp://some/url/to/origin/0',
            'type': 'ftp'
        }
        mock_service.lookup_origin.return_value = stub_origin

        # when
        rv = self.app.get('/api/1/origin/1234/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_origin)

        mock_service.lookup_origin.assert_called_with(1234)

    @patch('swh.web.ui.api.service')
    @istest
    def api_origin_not_found(self, mock_service):
        # given
        mock_service.lookup_origin.return_value = None

        # when
        rv = self.app.get('/api/1/origin/4321/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Origin with id 4321 not found.'
        })

        mock_service.lookup_origin.assert_called_with(4321)

    @patch('swh.web.ui.api.service')
    @istest
    def api_release(self, mock_service):
        # given
        stub_release = {
            'id': 'release-0',
            'target_type': 'revision',
            'target': 'revision-sha1',
            "date": "Mon, 10 Mar 1997 08:00:00 GMT",
            "synthetic": True,
            'author': {
                'name': 'author release name',
                'email': 'author@email',
            },
        }

        expected_release = {
            'id': 'release-0',
            'target_type': 'revision',
            'target': 'revision-sha1',
            'target_url': '/api/1/revision/revision-sha1/',
            "date": "Mon, 10 Mar 1997 08:00:00 GMT",
            "synthetic": True,
            'author': {
                'name': 'author release name',
                'email': 'author@email',
            },
        }

        mock_service.lookup_release.return_value = stub_release

        # when
        rv = self.app.get('/api/1/release/release-0/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_release)

        mock_service.lookup_release.assert_called_once_with('release-0')

    @patch('swh.web.ui.api.service')
    @istest
    def api_release_target_type_not_a_revision(self, mock_service):
        # given
        stub_release = {
            'id': 'release-0',
            'target_type': 'other-stuff',
            'target': 'other-stuff-checksum',
            "date": "Mon, 10 Mar 1997 08:00:00 GMT",
            "synthetic": True,
            'author': {
                'name': 'author release name',
                'email': 'author@email',
            },
        }

        expected_release = {
            'id': 'release-0',
            'target_type': 'other-stuff',
            'target': 'other-stuff-checksum',
            "date": "Mon, 10 Mar 1997 08:00:00 GMT",
            "synthetic": True,
            'author': {
                'name': 'author release name',
                'email': 'author@email',
            },
        }

        mock_service.lookup_release.return_value = stub_release

        # when
        rv = self.app.get('/api/1/release/release-0/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_release)

        mock_service.lookup_release.assert_called_once_with('release-0')

    @patch('swh.web.ui.api.service')
    @istest
    def api_release_not_found(self, mock_service):
        # given
        mock_service.lookup_release.return_value = None

        # when
        rv = self.app.get('/api/1/release/release-0/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Release with sha1_git release-0 not found.'
        })

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision(self, mock_service):
        # given
        stub_revision = {
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'author_name': 'Software Heritage',
            'author_email': 'robot@softwareheritage.org',
            'committer_name': 'Software Heritage',
            'committer_email': 'robot@softwareheritage.org',
            'message': 'synthetic revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': ['8734ef7e7c357ce2af928115c6c6a42b7e2a44e7'],
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
        mock_service.lookup_revision.return_value = stub_revision

        expected_revision = {
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'url': '/api/1/revision/18d8be353ed3480476f032475e7c233eff7371d5/',
            'history_url': '/api/1/revision/18d8be353ed3480476f032475e7c233e'
                           'ff7371d5/log/',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'directory_url': '/api/1/directory/7834ef7e7c357ce2af928115c6c6'
                             'a42b7e2a44e6/',
            'author_name': 'Software Heritage',
            'author_email': 'robot@softwareheritage.org',
            'committer_name': 'Software Heritage',
            'committer_email': 'robot@softwareheritage.org',
            'message': 'synthetic revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': [
                '8734ef7e7c357ce2af928115c6c6a42b7e2a44e7'
            ],
            'parent_urls': [
                '/api/1/revision/18d8be353ed3480476f032475e7c233eff7371d5'
                '/history/8734ef7e7c357ce2af928115c6c6a42b7e2a44e7/'
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
        rv = self.app.get('/api/1/revision/'
                          '18d8be353ed3480476f032475e7c233eff7371d5/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_revision)

        mock_service.lookup_revision.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5')

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_not_found(self, mock_service):
        # given
        mock_service.lookup_revision.return_value = None

        # when
        rv = self.app.get('/api/1/revision/revision-0/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Revision with sha1_git revision-0 not found.'})

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_with_origin_not_found(self, mock_service):
        mock_service.lookup_revision_by.return_value = None

        rv = self.app.get('/api/1/revision/origin/123/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertIn('Revision with (origin_id: 123', response_data['error'])
        self.assertIn('not found', response_data['error'])

        mock_service.lookup_revision_by.assert_called_once_with(
            123,
            'refs/heads/master',
            None)

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_with_origin(self, mock_service):
        mock_revision = {
            'id': '32',
            'directory': '21',
            'message': 'message 1',
            'type': 'deb',
        }
        expected_revision = {
            'id': '32',
            'url': '/api/1/revision/32/',
            'history_url': '/api/1/revision/32/log/',
            'directory': '21',
            'directory_url': '/api/1/directory/21/',
            'message': 'message 1',
            'type': 'deb',
        }
        mock_service.lookup_revision_by.return_value = mock_revision

        rv = self.app.get('/api/1/revision/origin/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEqual(response_data, expected_revision)

        mock_service.lookup_revision_by.assert_called_once_with(
            1,
            'refs/heads/master',
            None)

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_with_origin_and_branch_name(self, mock_service):
        mock_revision = {
            'id': '12',
            'directory': '23',
            'message': 'message 2',
            'type': 'tar',
        }
        mock_service.lookup_revision_by.return_value = mock_revision

        expected_revision = {
            'id': '12',
            'url': '/api/1/revision/12/',
            'history_url': '/api/1/revision/12/log/',
            'directory': '23',
            'directory_url': '/api/1/directory/23/',
            'message': 'message 2',
            'type': 'tar',
        }

        rv = self.app.get('/api/1/revision/origin/1/branch/refs/origin/dev/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEqual(response_data, expected_revision)

        mock_service.lookup_revision_by.assert_called_once_with(
            1,
            'refs/origin/dev',
            None)

    @patch('swh.web.ui.api.service')
    @patch('swh.web.ui.api.utils')
    @istest
    def api_revision_with_origin_and_branch_name_and_timestamp(self,
                                                               mock_utils,
                                                               mock_service):
        mock_revision = {
            'id': '123',
            'directory': '456',
            'message': 'message 3',
            'type': 'tar',
        }
        mock_service.lookup_revision_by.return_value = mock_revision

        expected_revision = {
            'id': '123',
            'url': '/api/1/revision/123/',
            'history_url': '/api/1/revision/123/log/',
            'directory': '456',
            'directory_url': '/api/1/directory/456/',
            'message': 'message 3',
            'type': 'tar',
        }

        mock_utils.parse_timestamp.return_value = 'parsed-date'
        mock_utils.enrich_revision.return_value = expected_revision

        rv = self.app.get('/api/1/revision'
                          '/origin/1'
                          '/branch/refs/origin/dev'
                          '/ts/1452591542/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEqual(response_data, expected_revision)

        mock_service.lookup_revision_by.assert_called_once_with(
            1,
            'refs/origin/dev',
            'parsed-date')
        mock_utils.parse_timestamp.assert_called_once_with('1452591542')
        mock_utils.enrich_revision.assert_called_once_with(
            mock_revision)

    @patch('swh.web.ui.api.service')
    @patch('swh.web.ui.api.utils')
    @istest
    def api_revision_with_origin_and_branch_name_and_timestamp_with_escapes(
            self,
            mock_utils,
            mock_service):
        mock_revision = {
            'id': '999',
        }
        mock_service.lookup_revision_by.return_value = mock_revision

        expected_revision = {
            'id': '999',
            'url': '/api/1/revision/999/',
            'history_url': '/api/1/revision/999/log/',
        }

        mock_utils.parse_timestamp.return_value = 'parsed-date'
        mock_utils.enrich_revision.return_value = expected_revision

        rv = self.app.get('/api/1/revision'
                          '/origin/1'
                          '/branch/refs%2Forigin%2Fdev'
                          '/ts/Today%20is%20'
                          'January%201,%202047%20at%208:21:00AM/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEqual(response_data, expected_revision)

        mock_service.lookup_revision_by.assert_called_once_with(
            1,
            'refs/origin/dev',
            'parsed-date')
        mock_utils.parse_timestamp.assert_called_once_with(
            'Today is January 1, 2047 at 8:21:00AM')
        mock_utils.enrich_revision.assert_called_once_with(
            mock_revision)

    @patch('swh.web.ui.api.service')
    @istest
    def api_directory_through_rev_with_origin_history_with_rev_not_found_0(
            self, mock_service):
        # test both endpoint (path is useless here, still the endpoint
        # must be tested)
        for url in ['/api/1/revision'
                    '/origin/1'
                    '/history/4563'
                    '/directory/',
                    '/api/1/revision'
                    '/origin/1'
                    '/history/4563'
                    '/directory/some-path/']:
            # given
            mock_service.lookup_revision_with_context_by.return_value = {
                'id': 'root-rev-id'}, None

            # when
            rv = self.app.get(url)

            # then
            self.assertEquals(rv.status_code, 404)
            self.assertEquals(rv.mimetype, 'application/json')
            response_data = json.loads(rv.data.decode('utf-8'))

            self.assertEqual(response_data, {
                'error':
                "Possibly sha1_git '%s' is not an ancestor of sha1_git_root "
                "'%s' sha1_git_root being the revision's identifier pointed to"
                " by (origin_id: %s, branch_name: %s, ts: %s)." % (
                    '4563',
                    'root-rev-id',
                    1,
                    'refs/heads/master',
                    None)})

            mock_service.lookup_revision_with_context_by.assert_called(
                1, 'refs/heads/master', None, '4563', 100)

            # reset_mock
            mock_service.reset_mock()

    @patch('swh.web.ui.api.service')
    @istest
    def api_directory_through_rev_with_origin_history_rev_not_found_1(  # noqa
            self, mock_service):
        # test both endpoint (path is useless here, still the endpoint
        # must be tested)
        for url in ['/api/1/revision'
                    '/origin/10'
                    '/branch/origin/dev'
                    '/history/213'
                    '/directory/',
                    '/api/1/revision'
                    '/origin/10'
                    '/branch/origin/dev'
                    '/history/213'
                    '/directory/some/path/']:
            # given
            mock_service.lookup_revision_with_context_by.return_value = {
                'id': 'root-rev-id'}, None

            # when
            rv = self.app.get(url)

            # then
            self.assertEquals(rv.status_code, 404)
            self.assertEquals(rv.mimetype, 'application/json')
            response_data = json.loads(rv.data.decode('utf-8'))

            self.assertEqual(response_data, {
                'error':
                "Possibly sha1_git '%s' is not an ancestor of sha1_git_root "
                "'%s' sha1_git_root being the revision's identifier pointed to"
                " by (origin_id: %s, branch_name: %s, ts: %s)." % (
                    '213',
                    'root-rev-id',
                    10,
                    'origin/dev',
                    None)})

            mock_service.lookup_revision_with_context_by.assert_called(
                10, 'origin/dev', None, '213', 100)

            # for next turn
            mock_service.reset_mock()

    @patch('swh.web.ui.api.utils')
    @patch('swh.web.ui.api.service')
    @istest
    def api_directory_through_rev_with_origin_history_rev_found_2(
            self, mock_service, mock_utils):
        # test both endpoint (path is useless here, still the endpoint
        # must be tested)
        for url in ['/api/1/revision'
                    '/origin/100'
                    '/branch/master'
                    '/ts/2012-11-23'
                    '/history/876'
                    '/directory/',
                    '/api/1/revision'
                    '/origin/100'
                    '/branch/master'
                    '/ts/2012-11-23'
                    '/history/876'
                    '/directory/some-path/']:
            # given
            mock_service.lookup_revision_with_context_by.return_value = {
                'id': 'root-rev-id'}, None
            mock_utils.parse_timestamp.return_value = '2012-11-23 00:00:00'

            # when
            rv = self.app.get(url)

            # then
            self.assertEquals(rv.status_code, 404)
            self.assertEquals(rv.mimetype, 'application/json')
            response_data = json.loads(rv.data.decode('utf-8'))

            self.assertEqual(response_data, {
                'error':
                "Possibly sha1_git '%s' is not an ancestor of sha1_git_root "
                "'%s' sha1_git_root being the revision's identifier pointed to"
                " by (origin_id: %s, branch_name: %s, ts: %s)." % (
                    '876',
                    'root-rev-id',
                    100,
                    'master',
                    '2012-11-23 00:00:00')})

            mock_service.lookup_revision_with_context_by.assert_called(
                100, 'master', '2012-11-23 00:00:00', '876', 100)

            mock_utils.parse_timestamp.assert_called_once_with('2012-11-23')

            # rest
            mock_utils.reset_mock()
            mock_service.reset_mock()

    @patch('swh.web.ui.api.utils')
    @patch('swh.web.ui.api.service')
    @istest
    def api_directory_through_rev_with_origin_history_rev_ok_but_sha1_rev_not(
            self, mock_service, mock_utils):
        # test both endpoint (path is useless here, still the endpoint
        # must be tested)
        for url in ['/api/1/revision'
                    '/origin/666'
                    '/branch/refs/master'
                    '/ts/2016-11-23'
                    '/history/123-sha1-git'
                    '/directory/?limit=1000',
                    '/api/1/revision'
                    '/origin/666'
                    '/branch/refs/master'
                    '/ts/2016-11-23'
                    '/history/123-sha1-git'
                    '/directory/some/path/?limit=1000']:
            # given
            mock_service.lookup_revision_with_context_by.return_value = {
                'id': 'root-rev-id'}, None

            mock_utils.parse_timestamp.return_value = '2016-11-23 00:00:00'

            # when
            rv = self.app.get(url)

            # then
            self.assertEquals(rv.status_code, 404)
            self.assertEquals(rv.mimetype, 'application/json')
            response_data = json.loads(rv.data.decode('utf-8'))

            self.assertEqual(response_data, {
                'error':
                "Possibly sha1_git '%s' is not an ancestor of sha1_git_root "
                "'%s' sha1_git_root being the revision's identifier pointed to"
                " by (origin_id: %s, branch_name: %s, ts: %s)."
                % ('123-sha1-git',
                   'root-rev-id',
                   666,
                   'refs/master',
                   '2016-11-23 00:00:00')})

            mock_service.lookup_revision_with_context_by.assert_called(
                666, 'refs/master', '2016-11-23 00:00:00',
                '123-sha1-git', 1000)

            mock_utils.parse_timestamp.assert_called_once_with('2016-11-23')

            # reset_mock
            mock_service.reset_mock()
            mock_utils.reset_mock()

    @patch('swh.web.ui.api._revision_directory')
    @patch('swh.web.ui.api.utils')
    @patch('swh.web.ui.api.service')
    @istest
    def api_directory_through_revision_with_origin_history(
            self, mock_service, mock_utils, mock_revision_directory):
        # given
        stub_root_rev = {
            'id': '45-sha1-git-root'
        }
        stub_revision = {
            'id': 'revision-id',
        }
        mock_service.lookup_revision_with_context_by.return_value = (
            stub_root_rev,
            stub_revision)
        stub_dir_content = [
            {
                'type': 'dir'
            },
            {
                'type': 'file'
            },
        ]
        mock_revision_directory.return_value = stub_dir_content

        mock_utils.parse_timestamp.return_value = '2016-11-24 00:00:00'

        # when
        url = '/api/1/revision'  \
              '/origin/999' \
              '/branch/refs/dev' \
              '/ts/2016-11-24' \
              '/history/12-sha1-git' \
              '/directory/some/content/'
        rv = self.app.get(url)

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))

        self.assertEqual(response_data, stub_dir_content)

        mock_utils.parse_timestamp.assert_called_once_with('2016-11-24')

        mock_service.lookup_revision_with_context_by(999,
                                                     'refs/dev',
                                                     '2016-11-24 00:00:00'
                                                     '12-sha1-git',
                                                     100)

        mock_revision_directory.assert_called_once_with('revision-id',
                                                        'some/content',
                                                        url)

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_history_through_origin_rev_not_found_0(
            self, mock_service):
        mock_service.lookup_revision_with_context_by.return_value = {
            'id': 'root-rev-id'}, None

        # when
        rv = self.app.get('/api/1/revision'
                          '/origin/1'
                          '/history/4563/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))

        self.assertEqual(response_data, {
            'error':
            "Possibly sha1_git '%s' is not an ancestor of sha1_git_root '%s'"
            " sha1_git_root being the revision's identifier pointed to by "
            "(origin_id: %s, branch_name: %s, ts: %s)."
            % ('4563',
               'root-rev-id',
               1,
               'refs/heads/master',
               None)})

        mock_service.lookup_revision_with_context_by.assert_called_once_with(
            1, 'refs/heads/master', None, '4563', 100)

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_history_through_origin_rev_not_found_1(
            self, mock_service):
        # given
        mock_service.lookup_revision_with_context_by.return_value = {
            'id': 'root-rev-id'}, None

        # when
        rv = self.app.get('/api/1/revision'
                          '/origin/10'
                          '/branch/origin/dev'
                          '/history/213/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))

        self.assertEqual(response_data, {
            'error':
            "Possibly sha1_git '%s' is not an ancestor of sha1_git_root '%s'"
            " sha1_git_root being the revision's identifier pointed to by "
            "(origin_id: %s, branch_name: %s, ts: %s)."
            % ('213',
               'root-rev-id',
               10,
               'origin/dev',
               None)})

        mock_service.lookup_revision_with_context_by.assert_called_once_with(
            10, 'origin/dev', None, '213', 100)

    @patch('swh.web.ui.api.utils')
    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_history_through_origin_rev_not_found_2(
            self, mock_service, mock_utils):
        # given
        mock_service.lookup_revision_with_context_by.return_value = {
            'id': 'root-rev-id'}, None
        mock_utils.parse_timestamp.return_value = '2012-11-23 00:00:00'

        # when
        rv = self.app.get('/api/1/revision'
                          '/origin/100'
                          '/branch/master'
                          '/ts/2012-11-23'
                          '/history/876/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))

        self.assertEqual(response_data, {
            'error':
            "Possibly sha1_git '%s' is not an ancestor of sha1_git_root '%s'"
            " sha1_git_root being the revision's identifier pointed to by "
            "(origin_id: %s, branch_name: %s, ts: %s)."
            % ('876',
               'root-rev-id',
               100,
               'master',
               '2012-11-23 00:00:00')})

        mock_service.lookup_revision_with_context_by.assert_called_once_with(
            100, 'master', '2012-11-23 00:00:00', '876', 100)

        mock_utils.parse_timestamp.assert_called_once_with('2012-11-23')

    @patch('swh.web.ui.api.utils')
    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_history_through_origin_rev_not_found_3(
            self, mock_service, mock_utils):
        # given
        mock_service.lookup_revision_with_context_by.return_value = {
            'id': 'root-rev-id'}, None

        mock_service.lookup_revision_with_context.return_value = None

        mock_utils.parse_timestamp.return_value = '2016-11-23 00:00:00'

        # when
        rv = self.app.get('/api/1/revision'
                          '/origin/666'
                          '/branch/refs/master'
                          '/ts/2016-11-23'
                          '/history/123-sha1-git/?limit=1000')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))

        self.assertEqual(response_data, {
            'error':
            "Possibly sha1_git '%s' is not an ancestor of sha1_git_root '%s'"
            " sha1_git_root being the revision's identifier pointed to by "
            "(origin_id: %s, branch_name: %s, ts: %s)."
            % ('123-sha1-git',
               'root-rev-id',
               666,
               'refs/master',
               '2016-11-23 00:00:00')})

        mock_service.lookup_revision_with_context_by.assert_called_once_with(
            666, 'refs/master', '2016-11-23 00:00:00', '123-sha1-git', 1000)

        mock_utils.parse_timestamp.assert_called_once_with('2016-11-23')

        mock_service.lookup_revision_with_context('456-sha1-git-root',
                                                  '123-sha1-git',
                                                  1000)

    @patch('swh.web.ui.api.utils')
    @patch('swh.web.ui.api.service')
    @istest
    def api_history_through_revision(self, mock_service, mock_utils):
        # given
        stub_root_rev = {
            'id': '45-sha1-git-root'
        }

        stub_revision = {
            'children': [],
        }
        mock_service.lookup_revision_with_context_by.return_value = (
            stub_root_rev,
            stub_revision)

        mock_utils.enrich_revision.return_value = 'some-result'

        mock_utils.parse_timestamp.return_value = '2016-11-24 00:00:00'

        # when
        rv = self.app.get('/api/1/revision'
                          '/origin/999'
                          '/branch/refs/dev'
                          '/ts/2016-11-24'
                          '/history/12-sha1-git/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))

        self.assertEqual(response_data, 'some-result')

        mock_service.lookup_revision_with_context_by.assert_called_once_with(
            999,
            'refs/dev',
            '2016-11-24 00:00:00',
            '12-sha1-git',
            100)

        mock_utils.parse_timestamp.assert_called_once_with('2016-11-24')

        mock_utils.enrich_revision.assert_called_once_with(
            stub_revision,
            context='45-sha1-git-root')

    @patch('swh.web.ui.api.utils')
    @patch('swh.web.ui.api.service')
    @istest
    def api_directory_through_revision_with_origin_rev_not_found(self,
                                                                 mock_service,
                                                                 mock_utils):
        mock_service.lookup_revision_by.return_value = None
        mock_utils.parse_timestamp.return_value = '2012-10-20 00:00:00'

        rv = self.app.get('/api/1/revision'
                          '/origin/10'
                          '/branch/refs/remote/origin/dev'
                          '/ts/2012-10-20'
                          '/directory/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEqual(response_data, {
            'error': 'Revision with (origin_id: 10, branch_name: '
            'refs/remote/origin/dev, ts: 2012-10-20 00:00:00) not found.'})

        mock_service.lookup_revision_by.assert_called_once_with(
            10,
            'refs/remote/origin/dev',
            '2012-10-20 00:00:00')

    @patch('swh.web.ui.api.service')
    @patch('swh.web.ui.api._revision_directory')
    @istest
    def api_directory_through_origin(self,
                                     mock_revision_dir,
                                     mock_service):
        mock_revision = {
            'id': '998',
        }
        expected_res = [{
            'id': '123'
        }]
        mock_revision_dir.return_value = expected_res

        mock_service.lookup_revision_by.return_value = mock_revision

        rv = self.app.get('/api/1/revision/origin/3/directory/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEqual(response_data, expected_res)

        mock_service.lookup_revision_by.assert_called_once_with(
            3,
            'refs/heads/master',
            None)
        mock_revision_dir.assert_called_once_with(
            '998',
            None,
            '/api/1/revision/origin/3/directory/')

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_log(self, mock_service):
        # given
        stub_revisions = [{
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'author_name': 'Software Heritage',
            'author_email': 'robot@softwareheritage.org',
            'committer_name': 'Software Heritage',
            'committer_email': 'robot@softwareheritage.org',
            'message': 'synthetic revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': ['7834ef7e7c357ce2af928115c6c6a42b7e2a4345'],
            'type': 'tar',
            'synthetic': True,
        }]
        mock_service.lookup_revision_log.return_value = stub_revisions

        expected_revisions = [{
            'id': '18d8be353ed3480476f032475e7c233eff7371d5',
            'url': '/api/1/revision/18d8be353ed3480476f032475e7c233eff7371d5/',
            'history_url': '/api/1/revision/18d8be353ed3480476f032475e7c233ef'
                           'f7371d5/log/',
            'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'directory_url': '/api/1/directory/7834ef7e7c357ce2af928115c6c6a'
                             '42b7e2a44e6/',
            'author_name': 'Software Heritage',
            'author_email': 'robot@softwareheritage.org',
            'committer_name': 'Software Heritage',
            'committer_email': 'robot@softwareheritage.org',
            'message': 'synthetic revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': [
                '7834ef7e7c357ce2af928115c6c6a42b7e2a4345'
            ],
            'parent_urls': [
                '/api/1/revision/18d8be353ed3480476f032475e7c233eff7371d5'
                '/history/7834ef7e7c357ce2af928115c6c6a42b7e2a4345/'
            ],
            'type': 'tar',
            'synthetic': True,
        }]

        # when
        rv = self.app.get('/api/1/revision/8834ef7e7c357ce2af928115c6c6a42'
                          'b7e2a44e6/log/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_revisions)

        mock_service.lookup_revision_log.assert_called_once_with(
            '8834ef7e7c357ce2af928115c6c6a42b7e2a44e6', 100)

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_log_not_found(self, mock_service):
        # given
        mock_service.lookup_revision_log.return_value = None

        # when
        rv = self.app.get('/api/1/revision/8834ef7e7c357ce2af928115c6c6a42b7'
                          'e2a44e6/log/?limit=10')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Revision with sha1_git'
            ' 8834ef7e7c357ce2af928115c6c6a42b7e2a44e6 not found.'})

        mock_service.lookup_revision_log.assert_called_once_with(
            '8834ef7e7c357ce2af928115c6c6a42b7e2a44e6', 10)

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_history_not_found(self, mock_service):
        # given
        mock_service.lookup_revision_with_context.return_value = None

        # then
        rv = self.app.get('/api/1/revision/999/history/338/?limit=5')

        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        mock_service.lookup_revision_with_context.assert_called_once_with(
                        '999', '338', 5)

    @istest
    def api_revision_history_sha1_same_so_redirect(self):
        # when
        rv = self.app.get('/api/1/revision/123/history/123?limit=10')
        # then
        self.assertEquals(rv.status_code, 301)
        # Ideally we'd like to be able to check the resulting url path
        # but does not work, this returns the current url
        # also following the redirect would mean to yet mock again the
        # destination url... So for now cannot test it

        # self.assertEquals(rv.location,
        #                   'http://localhost/api/1/revision/123?limit=10')

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_history(self, mock_service):
        # for readability purposes, we use:
        # - sha1 as 3 letters (url are way too long otherwise to respect pep8)
        # - only keys with modification steps (all other keys are kept as is)

        # given
        stub_revision = {
            'id': '883',
            'children': ['777', '999'],
            'parents': [],
            'directory': '272'
        }

        mock_service.lookup_revision_with_context.return_value = stub_revision

        # then
        rv = self.app.get('/api/1/revision/666/history/883/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))

        self.assertEquals(response_data, {
            'id': '883',
            'url': '/api/1/revision/883/',
            'history_url': '/api/1/revision/883/log/',
            'children': ['777', '999'],
            'children_urls': ['/api/1/revision/666/history/777/',
                              '/api/1/revision/666/history/999/'],
            'parents': [],
            'parent_urls': [],
            'directory': '272',
            'directory_url': '/api/1/directory/272/'
        })

        mock_service.lookup_revision_with_context.assert_called_once_with(
            '666', '883', 100)

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_directory_not_found(self, mock_service):
        # given
        mock_service.lookup_directory_with_revision.return_value = None

        # then
        rv = self.app.get('/api/1/revision/999/directory/some/path/to/dir/')

        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        mock_service.lookup_directory_with_revision.assert_called_once_with(
                        '999', 'some/path/to/dir')

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_directory_not_found_2(self, mock_service):
        # given
        mock_service.lookup_directory_with_revision.return_value = None

        # then
        rv = self.app.get('/api/1/revision/123/directory/')

        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        mock_service.lookup_directory_with_revision.assert_called_once_with(
                        '123', None)

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_directory_ok_returns_dir_entries(self, mock_service):
        stub_dir = {
            'type': 'dir',
            'content': [
                {
                    'sha1_git': '789',
                    'type': 'file',
                    'target': '101',
                    'name': 'somefile'
                },
                {
                    'sha1_git': '123',
                    'type': 'dir',
                    'target': '456',
                    'name': 'to-subdir',
                }
            ]
        }

        expected_dir = {
            'type': 'dir',
            'revision': '999',
            'content': [
                {
                    'sha1_git': '789',
                    'type': 'file',
                    'target': '101',
                    'target_url': '/api/1/content/sha1_git:101/',
                    'name': 'somefile',
                    'file_url': '/api/1/revision/999/directory/some/path/'
                    'somefile/'
                },
                {
                    'sha1_git': '123',
                    'type': 'dir',
                    'target': '456',
                    'target_url': '/api/1/directory/456/',
                    'name': 'to-subdir',
                    'dir_url': '/api/1/revision/999/directory/some/path/'
                    'to-subdir/',
                }]
        }

        # given
        mock_service.lookup_directory_with_revision.return_value = stub_dir

        # then
        rv = self.app.get('/api/1/revision/999/directory/some/path/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_dir)

        mock_service.lookup_directory_with_revision.assert_called_once_with(
            '999', 'some/path')

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_directory_ok_returns_content(self, mock_service):
        stub_content = {
            'type': 'file',
            'content': {
                'sha1_git': '789',
                'sha1': '101',
            }
        }

        expected_content = {
            'type': 'file',
            'revision': '999',
            'content': {
                'sha1_git': '789',
                'sha1': '101',
                'data_url': '/api/1/content/101/raw/',
            }
        }

        # given
        mock_service.lookup_directory_with_revision.return_value = stub_content

        # then
        rv = self.app.get('/api/1/revision/999/directory/some/path/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_content)

        mock_service.lookup_directory_with_revision.assert_called_once_with(
            '999', 'some/path')

    @istest
    def api_revision_history_directory_sha1_same_so_redirect(self):
        # when
        rv = self.app.get(
            '/api/1/revision/123/history/123/directory/path/to/?limit=1')

        # then
        self.assertEquals(rv.status_code, 301)

        # self.assertEquals(rv.location,
        #                   'http://localhost/api/1/revision/123/directory/path/to/')

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_history_directory_ko_revision_not_found(self,
                                                             mock_service):
        # given
        mock_service.lookup_revision_with_context.return_value = None

        # then
        rv = self.app.get('/api/1/revision/456/history/987/directory/path/to/')

        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': "Possibly sha1_git '987' is not " +
                     "an ancestor of sha1_git_root '456'"})

        mock_service.lookup_revision_with_context.assert_called_once_with(
                        '456', '987', 100)

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_history_directory(self,
                                       mock_service):
        # given
        mock_service.lookup_revision_with_context.return_value = {
            'id': 'rev-id'
        }

        stub_dir = {
            'type': 'dir',
            'content': [
                {
                    'sha1_git': '879',
                    'type': 'file',
                    'target': '110',
                    'name': 'subfile'
                },
                {
                    'sha1_git': '213',
                    'type': 'dir',
                    'target': '546',
                    'name': 'subdir',
                }
            ]
        }

        expected_dir = {
            'type': 'dir',
            'revision': 'rev-id',
            'content': [
                {
                    'sha1_git': '879',
                    'type': 'file',
                    'target': '110',
                    'target_url': '/api/1/content/sha1_git:110/',
                    'name': 'subfile',
                    'file_url': '/api/1/revision/354/history/867/directory/'
                    'debian/'
                    'subfile/',
                },
                {
                    'sha1_git': '213',
                    'type': 'dir',
                    'target': '546',
                    'target_url': '/api/1/directory/546/',
                    'name': 'subdir',
                    'dir_url':
                    '/api/1/revision/354/history/867/directory/debian/subdir/'
                }]
        }

        # given
        mock_service.lookup_directory_with_revision.return_value = stub_dir

        # then
        rv = self.app.get('/api/1/revision/354'
                          '/history/867'
                          '/directory/debian/?limit=4')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_dir)

        mock_service.lookup_revision_with_context.assert_called_once_with(
            '354', '867', 4)

        mock_service.lookup_directory_with_revision('rev-id', 'debian')

    @patch('swh.web.ui.api.service')
    @istest
    def api_person(self, mock_service):
        # given
        stub_person = {
            'id': '198003',
            'name': 'Software Heritage',
            'email': 'robot@softwareheritage.org',
        }
        mock_service.lookup_person.return_value = stub_person

        # when
        rv = self.app.get('/api/1/person/198003/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_person)

    @patch('swh.web.ui.api.service')
    @istest
    def api_person_not_found(self, mock_service):
        # given
        mock_service.lookup_person.return_value = None

        # when
        rv = self.app.get('/api/1/person/666/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Person with id 666 not found.'})

    @patch('swh.web.ui.api.service')
    @istest
    def api_directory(self, mock_service):
        # given
        stub_directories = [
            {
                'sha1_git': '18d8be353ed3480476f032475e7c233eff7371d5',
                'type': 'file',
                'target': '4568be353ed3480476f032475e7c233eff737123',
            },
            {
                'sha1_git': '1d518d8be353ed3480476f032475e7c233eff737',
                'type': 'dir',
                'target': '8be353ed3480476f032475e7c233eff737123456',
            }]

        expected_directories = [
            {
                'sha1_git': '18d8be353ed3480476f032475e7c233eff7371d5',
                'type': 'file',
                'target': '4568be353ed3480476f032475e7c233eff737123',
                'target_url': '/api/1/content/'
                'sha1_git:4568be353ed3480476f032475e7c233eff737123/',
            },
            {
                'sha1_git': '1d518d8be353ed3480476f032475e7c233eff737',
                'type': 'dir',
                'target': '8be353ed3480476f032475e7c233eff737123456',
                'target_url':
                '/api/1/directory/8be353ed3480476f032475e7c233eff737123456/',
            }]

        mock_service.lookup_directory.return_value = stub_directories

        # when
        rv = self.app.get('/api/1/directory/'
                          '18d8be353ed3480476f032475e7c233eff7371d5/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_directories)

        mock_service.lookup_directory.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5')

    @patch('swh.web.ui.api.service')
    @istest
    def api_directory_not_found(self, mock_service):
        # given
        mock_service.lookup_directory.return_value = []

        # when
        rv = self.app.get('/api/1/directory/'
                          '66618d8be353ed3480476f032475e7c233eff737/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Directory with sha1_git '
            '66618d8be353ed3480476f032475e7c233eff737 not found.'})

    @patch('swh.web.ui.api.service')
    @istest
    def api_lookup_entity_by_uuid_not_found(self, mock_service):
        # when
        mock_service.lookup_entity_by_uuid.return_value = []

        # when
        rv = self.app.get('/api/1/entity/')

        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error':
            "Entity with uuid '5f4d4c51-498a-4e28-88b3-b3e4e8396cba' not " +
            "found."})

        mock_service.lookup_entity_by_uuid.assert_called_once_with(
            '5f4d4c51-498a-4e28-88b3-b3e4e8396cba')

    @patch('swh.web.ui.api.service')
    @istest
    def api_lookup_entity_by_uuid_bad_request(self, mock_service):
        # when
        mock_service.lookup_entity_by_uuid.side_effect = BadInputExc(
            'bad input: uuid malformed!')

        # when
        rv = self.app.get('/api/1/entity/uuid malformed/')

        self.assertEquals(rv.status_code, 400)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'bad input: uuid malformed!'})
        mock_service.lookup_entity_by_uuid.assert_called_once_with(
            'uuid malformed')

    @patch('swh.web.ui.api.service')
    @istest
    def api_lookup_entity_by_uuid(self, mock_service):
        # when
        stub_entities = [
            {
                'uuid': '34bd6b1b-463f-43e5-a697-785107f598e4',
                'parent': 'aee991a0-f8d7-4295-a201-d1ce2efc9fb2'
            },
            {
                'uuid': 'aee991a0-f8d7-4295-a201-d1ce2efc9fb2'
            }
        ]
        mock_service.lookup_entity_by_uuid.return_value = stub_entities

        expected_entities = [
            {
                'uuid': '34bd6b1b-463f-43e5-a697-785107f598e4',
                'uuid_url': '/api/1/entity/34bd6b1b-463f-43e5-a697-'
                            '785107f598e4/',
                'parent': 'aee991a0-f8d7-4295-a201-d1ce2efc9fb2',
                'parent_url': '/api/1/entity/aee991a0-f8d7-4295-a201-'
                              'd1ce2efc9fb2/'
            },
            {
                'uuid': 'aee991a0-f8d7-4295-a201-d1ce2efc9fb2',
                'uuid_url': '/api/1/entity/aee991a0-f8d7-4295-a201-'
                            'd1ce2efc9fb2/'
            }
        ]

        # when
        rv = self.app.get('/api/1/entity'
                          '/34bd6b1b-463f-43e5-a697-785107f598e4/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_entities)
        mock_service.lookup_entity_by_uuid.assert_called_once_with(
            '34bd6b1b-463f-43e5-a697-785107f598e4')


class ApiUtils(unittest.TestCase):

    @istest
    def api_lookup_not_found(self):
        # when
        with self.assertRaises(exc.NotFoundExc) as e:
            api._api_lookup('something',
                            lambda x: None,
                            'this is the error message raised as it is None')

        self.assertEqual(e.exception.args[0],
                         'this is the error message raised as it is None')

    @istest
    def api_lookup_with_result(self):
        # when
        actual_result = api._api_lookup('something',
                                        lambda x: x + '!',
                                        'this is the error which won\'t be '
                                        'used here')

        self.assertEqual(actual_result, 'something!')

    @istest
    def api_lookup_with_result_as_map(self):
        # when
        actual_result = api._api_lookup([1, 2, 3],
                                        lambda x: map(lambda y: y+1, x),
                                        'this is the error which won\'t be '
                                        'used here')

        self.assertEqual(actual_result, [2, 3, 4])
