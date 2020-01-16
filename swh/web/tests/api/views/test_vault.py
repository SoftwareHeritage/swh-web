# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.model import hashutil
from swh.web.common.utils import reverse

TEST_OBJ_ID = 'd4905454cc154b492bd6afed48694ae3c579345e'

OBJECT_TYPES = ('directory', 'revision_gitfast')


def test_api_vault_cook(api_client, mocker):
    mock_service = mocker.patch('swh.web.api.views.vault.service')

    for obj_type in OBJECT_TYPES:

        fetch_url = reverse(f'api-1-vault-fetch-{obj_type}',
                            url_args={f'{obj_type[:3]}_id': TEST_OBJ_ID})
        stub_cook = {
            'fetch_url': fetch_url,
            'obj_id': TEST_OBJ_ID,
            'obj_type': obj_type,
            'progress_message': None,
            'status': 'done',
            'task_uuid': 'de75c902-5ee5-4739-996e-448376a93eff',
        }
        stub_fetch = b'content'

        mock_service.vault_cook.return_value = stub_cook
        mock_service.vault_fetch.return_value = stub_fetch

        url = reverse(f'api-1-vault-cook-{obj_type}',
                      url_args={f'{obj_type[:3]}_id': TEST_OBJ_ID})

        rv = api_client.post(url, {'email': 'test@test.mail'})

        assert rv.status_code == 200, rv.data
        assert rv['Content-Type'] == 'application/json'

        stub_cook['fetch_url'] = rv.wsgi_request.build_absolute_uri(
            stub_cook['fetch_url'])

        assert rv.data == stub_cook
        mock_service.vault_cook.assert_called_with(
            obj_type,
            hashutil.hash_to_bytes(TEST_OBJ_ID),
            'test@test.mail')

        rv = api_client.get(fetch_url)

        assert rv.status_code == 200
        assert rv['Content-Type'] == 'application/gzip'
        assert rv.content == stub_fetch
        mock_service.vault_fetch.assert_called_with(
            obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID))


def test_api_vault_cook_uppercase_hash(api_client):

    for obj_type in OBJECT_TYPES:

        url = reverse(f'api-1-vault-cook-{obj_type}-uppercase-checksum',
                      url_args={f'{obj_type[:3]}_id': TEST_OBJ_ID.upper()})
        rv = api_client.post(url, {'email': 'test@test.mail'})

        assert rv.status_code == 302

        redirect_url = reverse(f'api-1-vault-cook-{obj_type}',
                               url_args={f'{obj_type[:3]}_id': TEST_OBJ_ID})

        assert rv['location'] == redirect_url

        fetch_url = reverse(
            f'api-1-vault-fetch-{obj_type}-uppercase-checksum',
            url_args={f'{obj_type[:3]}_id': TEST_OBJ_ID.upper()})

        rv = api_client.get(fetch_url)

        assert rv.status_code == 302

        redirect_url = reverse(f'api-1-vault-fetch-{obj_type}',
                               url_args={f'{obj_type[:3]}_id': TEST_OBJ_ID})

        assert rv['location'] == redirect_url


def test_api_vault_cook_notfound(api_client, mocker):
    mock_service = mocker.patch('swh.web.api.views.vault.service')
    mock_service.vault_cook.return_value = None
    mock_service.vault_fetch.return_value = None

    for obj_type in OBJECT_TYPES:
        url = reverse(f'api-1-vault-cook-{obj_type}',
                      url_args={f'{obj_type[:3]}_id': TEST_OBJ_ID})
        rv = api_client.post(url)

        assert rv.status_code == 404, rv.data
        assert rv['Content-Type'] == 'application/json'

        assert rv.data['exception'] == 'NotFoundExc'
        mock_service.vault_cook.assert_called_with(
            obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID), None)

        fetch_url = reverse(f'api-1-vault-fetch-{obj_type}',
                            url_args={f'{obj_type[:3]}_id': TEST_OBJ_ID})

        rv = api_client.get(fetch_url)

        assert rv.status_code == 404, rv.data
        assert rv['Content-Type'] == 'application/json'
        assert rv.data['exception'] == 'NotFoundExc'
        mock_service.vault_fetch.assert_called_with(
            obj_type, hashutil.hash_to_bytes(TEST_OBJ_ID))
