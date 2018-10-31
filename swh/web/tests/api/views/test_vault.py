# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.test import APITestCase
from unittest.mock import patch

from swh.model import hashutil

from swh.web.tests.testcase import SWHWebTestCase

TEST_OBJ_ID = 'd4905454cc154b492bd6afed48694ae3c579345e'

OBJECT_TYPES = {'directory': ('directory', None),
                'revision_gitfast': ('revision', 'gitfast')}


class VaultApiTestCase(SWHWebTestCase, APITestCase):
    @patch('swh.web.api.views.vault.service')
    def test_api_vault_cook(self, mock_service):
        stub_cook = {
            'fetch_url': ('http://127.0.0.1:5004/api/1/vault/directory/{}/raw/'
                          .format(TEST_OBJ_ID)),
            'obj_id': 'd4905454cc154b492bd6afed48694ae3c579345e',
            'obj_type': 'test_type',
            'progress_message': None,
            'status': 'done',
            'task_uuid': 'de75c902-5ee5-4739-996e-448376a93eff',
        }
        stub_fetch = b'content'

        mock_service.vault_cook.return_value = stub_cook
        mock_service.vault_fetch.return_value = stub_fetch

        for obj_type, (obj_type_name, obj_type_format) in OBJECT_TYPES.items():
            url = '/api/1/vault/{}/{}/'.format(obj_type_name, TEST_OBJ_ID)
            if obj_type_format:
                url += '{}/'.format(obj_type_format)
            rv = self.client.post(url, {'email': 'test@test.mail'})

            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv['Content-Type'], 'application/json')

            self.assertEqual(rv.data, stub_cook)
            mock_service.vault_cook.assert_called_with(
                obj_type,
                hashutil.hash_to_bytes(TEST_OBJ_ID),
                'test@test.mail')

            rv = self.client.get(url + 'raw/')

            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv['Content-Type'], 'application/gzip')
            self.assertEqual(rv.content, stub_fetch)
            mock_service.vault_fetch.assert_called_with(
                obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID))

    @patch('swh.web.api.views.vault.service')
    def test_api_vault_cook_notfound(self, mock_service):
        mock_service.vault_cook.return_value = None
        mock_service.vault_fetch.return_value = None

        for obj_type, (obj_type_name, obj_type_format) in OBJECT_TYPES.items():
            url = '/api/1/vault/{}/{}/'.format(obj_type_name, TEST_OBJ_ID)
            if obj_type_format:
                url += '{}/'.format(obj_type_format)
            rv = self.client.post(url)

            self.assertEqual(rv.status_code, 404)
            self.assertEqual(rv['Content-Type'], 'application/json')

            self.assertEqual(rv.data['exception'], 'NotFoundExc')
            mock_service.vault_cook.assert_called_with(
                obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID), None)

            rv = self.client.get(url + 'raw/')

            self.assertEqual(rv.status_code, 404)
            self.assertEqual(rv['Content-Type'], 'application/json')
            self.assertEqual(rv.data['exception'], 'NotFoundExc')
            mock_service.vault_fetch.assert_called_with(
                obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID))
