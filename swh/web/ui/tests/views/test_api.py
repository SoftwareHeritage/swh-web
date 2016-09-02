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
from swh.web.ui import exc
from swh.web.ui.views import api
from swh.web.ui.exc import NotFoundExc, BadInputExc
from swh.storage.exc import StorageDBError, StorageAPIError


class ApiTestCase(test_app.SWHApiTestCase):

    @istest
    def generic_api_lookup_nothing_is_found(self):
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

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_content_provenance(self, mock_service):
        stub_provenances = [{
            'origin': 1,
            'visit': 2,
            'revision': 'b04caf10e9535160d90e874b45aa426de762f19f',
            'content': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'path': 'octavio-3.4.0/octave.html/doc_002dS_005fISREG.html'
        }]
        mock_service.lookup_content_provenance.return_value = stub_provenances

        # when
        rv = self.app.get(
            '/api/1/provenance/'
            'sha1_git:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, [{
            'origin': 1,
            'visit': 2,
            'origin_url': '/api/1/origin/1/',
            'origin_visits_url': '/api/1/origin/1/visits/',
            'origin_visit_url': '/api/1/origin/1/visits/2/',
            'revision': 'b04caf10e9535160d90e874b45aa426de762f19f',
            'revision_url': '/api/1/revision/'
                            'b04caf10e9535160d90e874b45aa426de762f19f/',
            'content': '34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'content_url': '/api/1/content/'
            'sha1_git:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03/',
            'path': 'octavio-3.4.0/octave.html/doc_002dS_005fISREG.html'
        }])

        mock_service.lookup_content_provenance.assert_called_once_with(
            'sha1_git:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_content_provenance_sha_not_found(self, mock_service):
        # given
        mock_service.lookup_content_provenance.return_value = None

        # when
        rv = self.app.get(
            '/api/1/provenance/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Content with sha1:40e71b8614fcd89ccd17ca2b1d9e6'
            '6c5b00a6d03 not found.'
        })

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_content_not_found_as_json(self, mock_service):
        # given
        mock_service.lookup_content.return_value = None
        mock_service.lookup_content_provenance = MagicMock()

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
        mock_service.lookup_content_provenance.called = False

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_content_not_found_as_yaml(self, mock_service):
        # given
        mock_service.lookup_content.return_value = None
        mock_service.lookup_content_provenance = MagicMock()

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
        mock_service.lookup_content_provenance.called = False

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_content_raw_ko_not_found(self, mock_service):
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

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_search(self, mock_service):
        # given
        mock_service.search_hash.return_value = {'found': True}

        expected_result = {
            'search_stats': {'nbfiles': 1, 'pct': 100},
            'search_res': [{'filename': None,
                            'sha1': 'sha1:blah',
                            'found': True}]
        }

        # when
        rv = self.app.get('/api/1/content/search/sha1:blah/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_result)
        mock_service.search_hash.assert_called_once_with('sha1:blah')

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_search_as_yaml(self, mock_service):
        # given
        mock_service.search_hash.return_value = {'found': True}
        expected_result = {
            'search_stats': {'nbfiles': 1, 'pct': 100},
            'search_res': [{'filename': None,
                            'sha1': 'sha1:halb',
                            'found': True}]
        }

        # when
        rv = self.app.get('/api/1/content/search/sha1:halb/',
                          headers={'Accept': 'application/yaml'})

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/yaml')

        response_data = yaml.load(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_result)

        mock_service.search_hash.assert_called_once_with('sha1:halb')

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_search_not_found(self, mock_service):
        # given
        mock_service.search_hash.return_value = {'found': False}

        expected_result = {
            'search_stats': {'nbfiles': 1, 'pct': 0},
            'search_res': [{'filename': None,
                            'sha1': 'sha1:halb',
                            'found': False}]
        }

        # when
        rv = self.app.get('/api/1/content/search/sha1:halb/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_result)

        mock_service.search_hash.assert_called_once_with('sha1:halb')

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_1_lookup_origin_visits_raise_error(self, mock_service):
        # given
        mock_service.lookup_origin_visits.side_effect = ValueError(
            'voluntary error to check the bad request middleware.')
        # when
        rv = self.app.get('/api/1/origin/2/visits/')
        # then
        self.assertEquals(rv.status_code, 400)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'voluntary error to check the bad request middleware.'})

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_1_lookup_origin_visits_raise_swh_storage_error_db(
            self, mock_service):
        # given
        mock_service.lookup_origin_visits.side_effect = StorageDBError(
            'SWH Storage exploded! Will be back online shortly!')
        # when
        rv = self.app.get('/api/1/origin/2/visits/')
        # then
        self.assertEquals(rv.status_code, 503)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error':
            'An unexpected error occurred in the backend: '
            'SWH Storage exploded! Will be back online shortly!'})

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_1_lookup_origin_visits_raise_swh_storage_error_api(
            self, mock_service):
        # given
        mock_service.lookup_origin_visits.side_effect = StorageAPIError(
            'SWH Storage API dropped dead! Will resurrect from its ashes asap!'
        )
        # when
        rv = self.app.get('/api/1/origin/2/visits/')
        # then
        self.assertEquals(rv.status_code, 503)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error':
            'An unexpected error occurred in the api backend: '
            'SWH Storage API dropped dead! Will resurrect from its ashes asap!'
        })

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_1_lookup_origin_visits(self, mock_service):
        # given
        stub_visits = [
            {
                'date': 1104616800.0,
                'origin': 1,
                'visit': 1
            },
            {
                'date': 1293919200.0,
                'origin': 1,
                'visit': 2
            },
            {
                'date': 1420149600.0,
                'origin': 1,
                'visit': 3
            }
        ]
        mock_service.lookup_origin_visits.return_value = stub_visits

        # when
        rv = self.app.get('/api/1/origin/2/visits/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_visits)

        mock_service.lookup_origin_visits.assert_called_once_with(2)

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_1_lookup_origin_visit(self, mock_service):
        # given
        stub_origin_visit = {
            'date': 1104616800.0,
            'origin': 10,
            'visit': 100,
            'metadata': None,
            'status': 'full',
        }
        mock_service.lookup_origin_visit.return_value = stub_origin_visit

        # when
        rv = self.app.get('/api/1/origin/10/visits/100/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_origin_visit)

        mock_service.lookup_origin_visit.assert_called_once_with(10, 100)

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_1_lookup_origin_visit_not_found(self, mock_service):
        # given
        mock_service.lookup_origin_visit.return_value = None

        # when
        rv = self.app.get('/api/1/origin/1/visits/1000/')

        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'No visit 1000 for origin 1 found'
        })

        mock_service.lookup_origin_visit.assert_called_once_with(1, 1000)

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_origin_by_id(self, mock_service):
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

        mock_service.lookup_origin.assert_called_with({'id': 1234})

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_origin_by_type_url(self, mock_service):
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
        rv = self.app.get('/api/1/origin/ftp/url/ftp://some/url/to/origin/0/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_origin)

        mock_service.lookup_origin.assert_called_with(
            {'url': 'ftp://some/url/to/origin/0',
             'type': 'ftp'})

    @patch('swh.web.ui.views.api.service')
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

        mock_service.lookup_origin.assert_called_with({'id': 4321})

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
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
                '/api/1/revision/8734ef7e7c357ce2af928115c6c6a42b7e2a44e7'
                '/prev/18d8be353ed3480476f032475e7c233eff7371d5/'
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

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_revision_raw_ok(self, mock_service):
        # given
        stub_revision = {'message': 'synthetic revision message'}

        mock_service.lookup_revision_message.return_value = stub_revision

        # when
        rv = self.app.get('/api/1/revision/18d8be353ed3480476f032475e7c2'
                          '33eff7371d5/raw/')
        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/octet-stream')
        self.assertEquals(rv.data, b'synthetic revision message')

        mock_service.lookup_revision_message.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5')

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_revision_raw_ok_no_msg(self, mock_service):
        # given
        mock_service.lookup_revision_message.side_effect = NotFoundExc(
            'No message for revision')

        # when
        rv = self.app.get('/api/1/revision/'
                          '18d8be353ed3480476f032475e7c233eff7371d5/raw/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'No message for revision'})

        self.assertEquals
        mock_service.lookup_revision_message.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5')

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_revision_raw_ko_no_rev(self, mock_service):
        # given
        mock_service.lookup_revision_message.side_effect = NotFoundExc(
            'No revision found')

        # when
        rv = self.app.get('/api/1/revision/'
                          '18d8be353ed3480476f032475e7c233eff7371d5/raw/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'No revision found'})

        mock_service.lookup_revision_message.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5')

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
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

        rv = self.app.get('/api/1/revision/origin/1/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEqual(response_data, expected_revision)

        mock_service.lookup_revision_by.assert_called_once_with(
            1,
            'refs/heads/master',
            None)

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
    @patch('swh.web.ui.views.api.utils')
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

    @patch('swh.web.ui.views.api.service')
    @patch('swh.web.ui.views.api.utils')
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

    @patch('swh.web.ui.views.api.service')
    @istest
    def revision_directory_by_ko_raise(self, mock_service):
        # given
        mock_service.lookup_directory_through_revision.side_effect = NotFoundExc('not')  # noqa

        # when
        with self.assertRaises(NotFoundExc):
            api._revision_directory_by(
                {'sha1_git': 'id'},
                None,
                '/api/1/revision/sha1/directory/')

        # then
        mock_service.lookup_directory_through_revision.assert_called_once_with(
            {'sha1_git': 'id'},
            None, limit=100, with_data=False)

    @patch('swh.web.ui.views.api.service')
    @istest
    def revision_directory_by_type_dir(self, mock_service):
        # given
        mock_service.lookup_directory_through_revision.return_value = (
            'rev-id',
            {
                'type': 'dir',
                'revision': 'rev-id',
                'path': 'some/path',
                'content': []
            })
        # when
        actual_dir_content = api._revision_directory_by(
            {'sha1_git': 'blah-id'},
            'some/path', '/api/1/revision/sha1/directory/')

        # then
        self.assertEquals(actual_dir_content, {
            'type': 'dir',
            'revision': 'rev-id',
            'path': 'some/path',
            'content': []
        })

        mock_service.lookup_directory_through_revision.assert_called_once_with(
            {'sha1_git': 'blah-id'},
            'some/path', limit=100, with_data=False)

    @patch('swh.web.ui.views.api.service')
    @istest
    def revision_directory_by_type_file(self, mock_service):
        # given
        mock_service.lookup_directory_through_revision.return_value = (
            'rev-id',
            {
                'type': 'file',
                'revision': 'rev-id',
                'path': 'some/path',
                'content': {'blah': 'blah'}
            })
        # when
        actual_dir_content = api._revision_directory_by(
            {'sha1_git': 'sha1'},
            'some/path',
            '/api/1/revision/origin/2/directory/',
            limit=1000, with_data=True)

        # then
        self.assertEquals(actual_dir_content, {
                'type': 'file',
                'revision': 'rev-id',
                'path': 'some/path',
                'content': {'blah': 'blah'}
            })

        mock_service.lookup_directory_through_revision.assert_called_once_with(
            {'sha1_git': 'sha1'},
            'some/path', limit=1000, with_data=True)

    @patch('swh.web.ui.views.api.utils')
    @patch('swh.web.ui.views.api._revision_directory_by')
    @istest
    def api_directory_through_revision_origin_ko_not_found(self,
                                                           mock_rev_dir,
                                                           mock_utils):
        mock_rev_dir.side_effect = NotFoundExc('not found')
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
            'error': 'not found'})

        mock_rev_dir.assert_called_once_with(
            {'origin_id': 10,
             'branch_name': 'refs/remote/origin/dev',
             'ts': '2012-10-20 00:00:00'}, None,
            '/api/1/revision'
            '/origin/10'
            '/branch/refs/remote/origin/dev'
            '/ts/2012-10-20'
            '/directory/',
            with_data=False)

    @patch('swh.web.ui.views.api._revision_directory_by')
    @istest
    def api_directory_through_revision_origin(self,
                                              mock_revision_dir):
        expected_res = [{
            'id': '123'
        }]
        mock_revision_dir.return_value = expected_res

        rv = self.app.get('/api/1/revision/origin/3/directory/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEqual(response_data, expected_res)

        mock_revision_dir.assert_called_once_with({
            'origin_id': 3,
            'branch_name': 'refs/heads/master',
            'ts': None}, None, '/api/1/revision/origin/3/directory/',
                                                  with_data=False)

    @patch('swh.web.ui.views.api.service')
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
                '/api/1/revision/7834ef7e7c357ce2af928115c6c6a42b7e2a4345'
                '/prev/18d8be353ed3480476f032475e7c233eff7371d5/'
            ],
            'type': 'tar',
            'synthetic': True,
        }]

        expected_response = {
            'revisions': expected_revisions,
            'next_revs_url': None
        }

        # when
        rv = self.app.get('/api/1/revision/8834ef7e7c357ce2af928115c6c6a42'
                          'b7e2a44e6/log/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_response)

        mock_service.lookup_revision_log.assert_called_once_with(
            '8834ef7e7c357ce2af928115c6c6a42b7e2a44e6', 26)

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_revision_log_with_next(self, mock_service):
        # given
        stub_revisions = []
        for i in range(27):
            stub_revisions.append({'id': i})

        mock_service.lookup_revision_log.return_value = stub_revisions[:26]

        expected_revisions = [x for x in stub_revisions if x['id'] < 25]
        for e in expected_revisions:
            e['url'] = '/api/1/revision/%s/' % e['id']
            e['history_url'] = '/api/1/revision/%s/log/' % e['id']

        expected_response = {
            'revisions': expected_revisions,
            'next_revs_url': '/api/1/revision/25/log/'
        }

        # when
        rv = self.app.get('/api/1/revision/8834ef7e7c357ce2af928115c6c6a42'
                          'b7e2a44e6/log/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_response)

        mock_service.lookup_revision_log.assert_called_once_with(
            '8834ef7e7c357ce2af928115c6c6a42b7e2a44e6', 26)

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_revision_log_not_found(self, mock_service):
        # given
        mock_service.lookup_revision_log.return_value = None

        # when
        rv = self.app.get('/api/1/revision/8834ef7e7c357ce2af928115c6c6a42b7'
                          'e2a44e6/log/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Revision with sha1_git'
            ' 8834ef7e7c357ce2af928115c6c6a42b7e2a44e6 not found.'})

        mock_service.lookup_revision_log.assert_called_once_with(
            '8834ef7e7c357ce2af928115c6c6a42b7e2a44e6', 26)

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_revision_log_context(self, mock_service):
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
        mock_service.lookup_revision_multiple.return_value = [{
            'id': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
            'directory': '18d8be353ed3480476f032475e7c233eff7371d5',
            'author_name': 'Name Surname',
            'author_email': 'name@surname.com',
            'committer_name': 'Name Surname',
            'committer_email': 'name@surname.com',
            'message': 'amazing revision message',
            'date_offset': 0,
            'committer_date_offset': 0,
            'parents': ['adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'],
            'type': 'tar',
            'synthetic': True,
        }]

        expected_revisions = [
            {
                'url': '/api/1/revision/'
                '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6/',
                'history_url': '/api/1/revision/'
                '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6/log/',
                'id': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
                'directory': '18d8be353ed3480476f032475e7c233eff7371d5',
                'directory_url': '/api/1/directory/'
                '18d8be353ed3480476f032475e7c233eff7371d5/',
                'author_name': 'Name Surname',
                'author_email': 'name@surname.com',
                'committer_name': 'Name Surname',
                'committer_email': 'name@surname.com',
                'message': 'amazing revision message',
                'date_offset': 0,
                'committer_date_offset': 0,
                'parents': ['adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'],
                'parent_urls': [
                    '/api/1/revision/adc83b19e793491b1c6ea0fd8b46cd9f32e592fc'
                    '/prev/7834ef7e7c357ce2af928115c6c6a42b7e2a44e6/'
                ],
                'type': 'tar',
                'synthetic': True,
            },
            {
                'url': '/api/1/revision/'
                '18d8be353ed3480476f032475e7c233eff7371d5/',
                'history_url': '/api/1/revision/'
                '18d8be353ed3480476f032475e7c233eff7371d5/log/',
                'id': '18d8be353ed3480476f032475e7c233eff7371d5',
                'directory': '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6',
                'directory_url': '/api/1/directory/'
                '7834ef7e7c357ce2af928115c6c6a42b7e2a44e6/',
                'author_name': 'Software Heritage',
                'author_email': 'robot@softwareheritage.org',
                'committer_name': 'Software Heritage',
                'committer_email': 'robot@softwareheritage.org',
                'message': 'synthetic revision message',
                'date_offset': 0,
                'committer_date_offset': 0,
                'parents': ['7834ef7e7c357ce2af928115c6c6a42b7e2a4345'],
                'parent_urls': [
                    '/api/1/revision/7834ef7e7c357ce2af928115c6c6a42b7e2a4345'
                    '/prev/18d8be353ed3480476f032475e7c233eff7371d5/'
                ],
                'type': 'tar',
                'synthetic': True,
            }]

        expected_response = {
            'revisions': expected_revisions,
            'next_revs_url': None
        }

        # when
        rv = self.app.get('/api/1/revision/18d8be353ed3480476f0'
                          '32475e7c233eff7371d5/prev/prev-rev/log/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_response)

        mock_service.lookup_revision_log.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5', 26)
        mock_service.lookup_revision_multiple.assert_called_once_with(
            ['prev-rev'])

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_revision_log_by(self, mock_service):
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
        mock_service.lookup_revision_log_by.return_value = stub_revisions

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
                '/api/1/revision/7834ef7e7c357ce2af928115c6c6a42b7e2a4345'
                '/prev/18d8be353ed3480476f032475e7c233eff7371d5/'
            ],
            'type': 'tar',
            'synthetic': True,
        }]

        expected_result = {
            'revisions': expected_revisions,
            'next_revs_url': None
        }

        # when
        rv = self.app.get('/api/1/revision/origin/1/log/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_result)

        mock_service.lookup_revision_log_by.assert_called_once_with(
            1, 'refs/heads/master', None, 26)

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_revision_log_by_with_next(self, mock_service):
        # given
        stub_revisions = []
        for i in range(27):
            stub_revisions.append({'id': i})

        mock_service.lookup_revision_log_by.return_value = stub_revisions[:26]

        expected_revisions = [x for x in stub_revisions if x['id'] < 25]
        for e in expected_revisions:
            e['url'] = '/api/1/revision/%s/' % e['id']
            e['history_url'] = '/api/1/revision/%s/log/' % e['id']

        expected_response = {
            'revisions': expected_revisions,
            'next_revs_url': '/api/1/revision/25/log/'
        }

        # when
        rv = self.app.get('/api/1/revision/origin/1/log/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_response)

        mock_service.lookup_revision_log_by.assert_called_once_with(
            1, 'refs/heads/master', None, 26)

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_revision_log_by_norev(self, mock_service):
        # given
        mock_service.lookup_revision_log_by.side_effect = NotFoundExc(
            'No revision')

        # when
        rv = self.app.get('/api/1/revision/origin/1/log/')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {'error': 'No revision'})

        mock_service.lookup_revision_log_by.assert_called_once_with(
            1, 'refs/heads/master', None, 26)

    @patch('swh.web.ui.views.api.service')
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

        mock_service.lookup_revision.return_value = stub_revision

        # then
        rv = self.app.get('/api/1/revision/883/prev/999/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))

        self.assertEquals(response_data, {
            'id': '883',
            'url': '/api/1/revision/883/',
            'history_url': '/api/1/revision/883/log/',
            'history_context_url': '/api/1/revision/883/prev/999/log/',
            'children': ['777', '999'],
            'children_urls': ['/api/1/revision/777/',
                              '/api/1/revision/999/'],
            'parents': [],
            'parent_urls': [],
            'directory': '272',
            'directory_url': '/api/1/directory/272/'
        })

        mock_service.lookup_revision.assert_called_once_with('883')

    @patch('swh.web.ui.views.api._revision_directory_by')
    @istest
    def api_revision_directory_ko_not_found(self, mock_rev_dir):
        # given
        mock_rev_dir.side_effect = NotFoundExc('Not found')

        # then
        rv = self.app.get('/api/1/revision/999/directory/some/path/to/dir/')

        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Not found'})

        mock_rev_dir.assert_called_once_with(
            {'sha1_git': '999'},
            'some/path/to/dir',
            '/api/1/revision/999/directory/some/path/to/dir/',
            with_data=False)

    @patch('swh.web.ui.views.api._revision_directory_by')
    @istest
    def api_revision_directory_ok_returns_dir_entries(self, mock_rev_dir):
        stub_dir = {
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
        mock_rev_dir.return_value = stub_dir

        # then
        rv = self.app.get('/api/1/revision/999/directory/some/path/')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_dir)

        mock_rev_dir.assert_called_once_with(
            {'sha1_git': '999'},
            'some/path',
            '/api/1/revision/999/directory/some/path/',
            with_data=False)

    @patch('swh.web.ui.views.api._revision_directory_by')
    @istest
    def api_revision_directory_ok_returns_content(self, mock_rev_dir):
        stub_content = {
            'type': 'file',
            'revision': '999',
            'content': {
                'sha1_git': '789',
                'sha1': '101',
                'data_url': '/api/1/content/101/raw/',
            }
        }

        # given
        mock_rev_dir.return_value = stub_content

        # then
        url = '/api/1/revision/666/directory/some/other/path/'
        rv = self.app.get(url)

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_content)

        mock_rev_dir.assert_called_once_with(
            {'sha1_git': '666'}, 'some/other/path', url, with_data=False)

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_directory_with_path_found(self, mock_service):
        # given
        expected_dir = {
                'sha1_git': '18d8be353ed3480476f032475e7c233eff7371d5',
                'type': 'file',
                'name': 'bla',
                'target': '4568be353ed3480476f032475e7c233eff737123',
                'target_url': '/api/1/content/'
                'sha1_git:4568be353ed3480476f032475e7c233eff737123/',
            }

        mock_service.lookup_directory_with_path.return_value = expected_dir

        # when
        rv = self.app.get('/api/1/directory/'
                          '18d8be353ed3480476f032475e7c233eff7371d5/bla/')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, expected_dir)

        mock_service.lookup_directory_with_path.assert_called_once_with(
            '18d8be353ed3480476f032475e7c233eff7371d5', 'bla')

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_directory_with_path_not_found(self, mock_service):
        # given
        mock_service.lookup_directory_with_path.return_value = None
        path = 'some/path/to/dir/'

        # when
        rv = self.app.get(('/api/1/directory/'
                          '66618d8be353ed3480476f032475e7c233eff737/%s')
                          % path)
        path = path.strip('/')  # Path stripped of lead/trail separators

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': (('Entry with path %s relative to '
                       'directory with sha1_git '
                       '66618d8be353ed3480476f032475e7c233eff737 not found.')
                      % path)})

    @patch('swh.web.ui.views.api.service')
    @istest
    def api_lookup_entity_by_uuid_not_found(self, mock_service):
        # when
        mock_service.lookup_entity_by_uuid.return_value = []

        # when
        rv = self.app.get('/api/1/entity/'
                          '5f4d4c51-498a-4e28-88b3-b3e4e8396cba/')

        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error':
            "Entity with uuid '5f4d4c51-498a-4e28-88b3-b3e4e8396cba' not " +
            "found."})

        mock_service.lookup_entity_by_uuid.assert_called_once_with(
            '5f4d4c51-498a-4e28-88b3-b3e4e8396cba')

    @patch('swh.web.ui.views.api.service')
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

    @patch('swh.web.ui.views.api.service')
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
