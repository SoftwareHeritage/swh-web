# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.model import hashutil

TEST_OBJ_ID = 'd4905454cc154b492bd6afed48694ae3c579345e'

OBJECT_TYPES = {'directory': ('directory', None),
                'revision_gitfast': ('revision', 'gitfast')}


def test_api_vault_cook(api_client, mocker):
    mock_service = mocker.patch('swh.web.api.views.vault.service')
    stub_cook = {
        'fetch_url': ('http://127.0.0.1:5004/api/1/vault/directory/{}/raw/'
                      .format(TEST_OBJ_ID)),
        'obj_id': TEST_OBJ_ID,
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
        rv = api_client.post(url, {'email': 'test@test.mail'})

        assert rv.status_code == 200, rv.data
        assert rv['Content-Type'] == 'application/json'

        assert rv.data == stub_cook
        mock_service.vault_cook.assert_called_with(
            obj_type,
            hashutil.hash_to_bytes(TEST_OBJ_ID),
            'test@test.mail')

        rv = api_client.get(url + 'raw/')

        assert rv.status_code == 200
        assert rv['Content-Type'] == 'application/gzip'
        assert rv.content == stub_fetch
        mock_service.vault_fetch.assert_called_with(
            obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID))


def test_api_vault_cook_uppercase_hash(api_client, mocker):
    mock_service = mocker.patch('swh.web.api.views.vault.service')
    stub_cook = {
        'fetch_url': ('http://127.0.0.1:5004/api/1/vault/directory/{}/raw/'
                      .format(TEST_OBJ_ID.upper())),
        'obj_id': TEST_OBJ_ID.upper(),
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
        rv = api_client.post(url, {'email': 'test@test.mail'})

        assert rv.status_code == 200, rv.data
        assert rv['Content-Type'] == 'application/json'

        assert rv.data == stub_cook
        mock_service.vault_cook.assert_called_with(
            obj_type,
            hashutil.hash_to_bytes(TEST_OBJ_ID),
            'test@test.mail')

        rv = api_client.get(url + 'raw/')

        assert rv.status_code == 200
        assert rv['Content-Type'] == 'application/gzip'
        assert rv.content == stub_fetch
        mock_service.vault_fetch.assert_called_with(
            obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID))


def test_api_vault_cook_notfound(api_client, mocker):
    mock_service = mocker.patch('swh.web.api.views.vault.service')
    mock_service.vault_cook.return_value = None
    mock_service.vault_fetch.return_value = None

    for obj_type, (obj_type_name, obj_type_format) in OBJECT_TYPES.items():
        url = '/api/1/vault/{}/{}/'.format(obj_type_name, TEST_OBJ_ID)
        if obj_type_format:
            url += '{}/'.format(obj_type_format)
        rv = api_client.post(url)

        assert rv.status_code == 404, rv.data
        assert rv['Content-Type'] == 'application/json'

        assert rv.data['exception'] == 'NotFoundExc'
        mock_service.vault_cook.assert_called_with(
            obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID), None)

        rv = api_client.get(url + 'raw/')

        assert rv.status_code == 404, rv.data
        assert rv['Content-Type'] == 'application/json'
        assert rv.data['exception'] == 'NotFoundExc'
        mock_service.vault_fetch.assert_called_with(
            obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID))
