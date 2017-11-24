# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from nose.tools import istest
from unittest.mock import patch

from swh.model import hashutil

from ..swh_api_testcase import SWHApiTestCase

TEST_OBJ_ID = 'd4905454cc154b492bd6afed48694ae3c579345e'


class VaultApiTestCase(SWHApiTestCase):
    @patch('swh.web.api.views.vault.service')
    @istest
    def api_vault_cook(self, mock_service):
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

        for obj_type in ('directory', 'revision_gitfast'):
            rv = self.client.get(('/api/1/vault/{}/{}/?email=test@test.mail')
                                 .format(obj_type, TEST_OBJ_ID))

            self.assertEquals(rv.status_code, 200)
            self.assertEquals(rv['Content-Type'], 'application/json')

            self.assertEquals(rv.data, stub_cook)
            mock_service.vault_cook.assert_called_with(
                obj_type,
                hashutil.hash_to_bytes(TEST_OBJ_ID),
                'test@test.mail')

            rv = self.client.get(('/api/1/vault/{}/{}/raw/')
                                 .format(obj_type, TEST_OBJ_ID))

            self.assertEquals(rv.status_code, 200)
            self.assertEquals(rv['Content-Type'], 'application/gzip')
            self.assertEquals(rv.content, stub_fetch)
            mock_service.vault_fetch.assert_called_with(
                obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID))

    @patch('swh.web.api.views.vault.service')
    @istest
    def api_vault_cook_notfound(self, mock_service):
        mock_service.vault_cook.return_value = None
        mock_service.vault_fetch.return_value = None

        for obj_type in ('directory', 'revision_gitfast'):
            rv = self.client.get(('/api/1/vault/{}/{}/')
                                 .format(obj_type, TEST_OBJ_ID))

            self.assertEquals(rv.status_code, 404)
            self.assertEquals(rv['Content-Type'], 'application/json')

            self.assertEquals(rv.data['exception'], 'NotFoundExc')
            mock_service.vault_cook.assert_called_with(
                obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID), None)

            rv = self.client.get(('/api/1/vault/{}/{}/raw/')
                                 .format(obj_type, TEST_OBJ_ID))

            self.assertEquals(rv.status_code, 404)
            self.assertEquals(rv['Content-Type'], 'application/json')
            self.assertEquals(rv.data['exception'], 'NotFoundExc')
            mock_service.vault_fetch.assert_called_with(
                obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID))
