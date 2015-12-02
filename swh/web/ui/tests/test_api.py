# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import yaml

from nose.tools import istest
from unittest.mock import patch, MagicMock

from swh.web.ui.tests import test_app


class ApiTestCase(test_app.SWHApiTestCase):

    @patch('swh.web.ui.api.service')
    @istest
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
            '/api/1/browse/sha1:34571b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

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
    @istest
    def api_content_checksum_to_origin_sha_not_found(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = {'found': False}
        # when
        rv = self.app.get(
            '/api/1/browse/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

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
    def api_content_with_details(self, mock_service):
        # given
        mock_service.lookup_content.return_value = {
            'data': 'some content data',
            'sha1': '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03',
            'sha1_git': 'b4e8f472ffcb01a03875b26e462eb568739f6882',
            'sha256': '83c0e67cc80f60caf1fcbec2d84b0ccd7968b3be4735637006560'
            'cde9b067a4f',
            'length': 17,
            'status': 'visible'
        }

        # when
        rv = self.app.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'data': '/api/1/content/'
                    '40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/raw',
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
            'be4735637006560c')

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
            'be4735637006560c',
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
        stub_content = {'data': 'some content data'}
        mock_service.lookup_content_raw.return_value = stub_content

        # when
        rv = self.app.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/raw',
            headers={'Content-Type': 'text/plain'})

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'text/plain')
        self.assertEquals(rv.data.decode('utf-8'), stub_content['data'])

        mock_service.lookup_content_raw.assert_called_once_with(
            'sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03')

    @patch('swh.web.ui.api.service')
    @istest
    def api_content_raw_not_found(self, mock_service):
        # given
        mock_service.lookup_content_raw.return_value = None

        # when
        rv = self.app.get(
            '/api/1/content/sha1:40e71b8614fcd89ccd17ca2b1d9e66c5b00a6d03/raw',
            headers={'Content-Type': 'text/plain'})

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
        mock_service.lookup_hash.return_value = True

        # when
        rv = self.app.get('/api/1/search/sha1:blah')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {'found': True})

        mock_service.lookup_hash.assert_called_once_with('sha1:blah')

    @patch('swh.web.ui.api.service')
    @istest
    def api_search_as_yaml(self, mock_service):
        # given
        mock_service.lookup_hash.return_value = True

        # when
        rv = self.app.get('/api/1/search/sha1:halb',
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
        mock_service.lookup_hash.return_value = False

        # when
        rv = self.app.get('/api/1/search/sha1:halb')

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
        rv = self.app.get('/api/1/stat/counters')
        # then
        self.assertEquals(rv.status_code, 400)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'voluntary error to check the bad request middleware.'})

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
        rv = self.app.get('/api/1/stat/counters')

        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')
        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_stats)

        mock_service.stat_counters.assert_called_once_with()

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
        rv = self.app.post('/api/1/uploadnsearch')

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
        rv = self.app.get('/api/1/origin/1234')

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
        rv = self.app.get('/api/1/origin/4321')

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
            'revision': 'revision-sha1',
            'author_name': 'author release name',
            'author_email': 'author@email',
        }

        mock_service.lookup_release.return_value = stub_release

        # when
        rv = self.app.get('/api/1/release/release-0')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_release)

    @patch('swh.web.ui.api.service')
    @istest
    def api_release_not_found(self, mock_service):
        # given
        mock_service.lookup_release.return_value = None

        # when
        rv = self.app.get('/api/1/release/release-0')

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
        mock_service.lookup_revision.return_value = stub_revision

        # when
        rv = self.app.get('/api/1/revision/revision-0')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_revision)

    @patch('swh.web.ui.api.service')
    @istest
    def api_revision_not_found(self, mock_service):
        # given
        mock_service.lookup_revision.return_value = None

        # when
        rv = self.app.get('/api/1/revision/revision-0')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Revision with sha1_git revision-0 not found.'})

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
        rv = self.app.get('/api/1/person/198003')

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
        rv = self.app.get('/api/1/person/666')

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
        stub_directory = [{
            'sha1_git': '18d8be353ed3480476f032475e7c233eff7371d5',
        }]
        mock_service.lookup_directory.return_value = stub_directory

        # when
        rv = self.app.get('/api/1/directory/'
                          '18d8be353ed3480476f032475e7c233eff7371d5')

        # then
        self.assertEquals(rv.status_code, 200)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, stub_directory)

    @patch('swh.web.ui.api.service')
    @istest
    def api_directory_not_found(self, mock_service):
        # given
        mock_service.lookup_directory.return_value = []

        # when
        rv = self.app.get('/api/1/directory/'
                          '66618d8be353ed3480476f032475e7c233eff737')

        # then
        self.assertEquals(rv.status_code, 404)
        self.assertEquals(rv.mimetype, 'application/json')

        response_data = json.loads(rv.data.decode('utf-8'))
        self.assertEquals(response_data, {
            'error': 'Directory with sha1_git '
            '66618d8be353ed3480476f032475e7c233eff737 not found.'})
