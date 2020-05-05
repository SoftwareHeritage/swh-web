# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given

from swh.model import hashutil
from swh.vault.exc import NotFoundExc
from swh.web.common.utils import reverse
from swh.web.tests.strategies import (
    directory,
    revision,
    unknown_directory,
    unknown_revision,
)


@given(directory(), revision())
def test_api_vault_cook(api_client, mocker, directory, revision):
    mock_service = mocker.patch("swh.web.api.views.vault.service")

    for obj_type, obj_id in (
        ("directory", directory),
        ("revision_gitfast", revision),
    ):

        fetch_url = reverse(
            f"api-1-vault-fetch-{obj_type}", url_args={f"{obj_type[:3]}_id": obj_id},
        )
        stub_cook = {
            "fetch_url": fetch_url,
            "obj_id": obj_id,
            "obj_type": obj_type,
            "progress_message": None,
            "status": "done",
            "task_uuid": "de75c902-5ee5-4739-996e-448376a93eff",
        }
        stub_fetch = b"content"

        mock_service.vault_cook.return_value = stub_cook
        mock_service.vault_fetch.return_value = stub_fetch

        url = reverse(
            f"api-1-vault-cook-{obj_type}", url_args={f"{obj_type[:3]}_id": obj_id}
        )

        rv = api_client.post(url, {"email": "test@test.mail"})

        assert rv.status_code == 200, rv.data
        assert rv["Content-Type"] == "application/json"

        stub_cook["fetch_url"] = rv.wsgi_request.build_absolute_uri(
            stub_cook["fetch_url"]
        )

        assert rv.data == stub_cook
        mock_service.vault_cook.assert_called_with(
            obj_type, hashutil.hash_to_bytes(obj_id), "test@test.mail"
        )

        rv = api_client.get(fetch_url)

        assert rv.status_code == 200
        assert rv["Content-Type"] == "application/gzip"
        assert rv.content == stub_fetch
        mock_service.vault_fetch.assert_called_with(
            obj_type, hashutil.hash_to_bytes(obj_id)
        )


@given(directory(), revision())
def test_api_vault_cook_uppercase_hash(api_client, directory, revision):

    for obj_type, obj_id in (
        ("directory", directory),
        ("revision_gitfast", revision),
    ):

        url = reverse(
            f"api-1-vault-cook-{obj_type}-uppercase-checksum",
            url_args={f"{obj_type[:3]}_id": obj_id.upper()},
        )
        rv = api_client.post(url, {"email": "test@test.mail"})

        assert rv.status_code == 302

        redirect_url = reverse(
            f"api-1-vault-cook-{obj_type}", url_args={f"{obj_type[:3]}_id": obj_id}
        )

        assert rv["location"] == redirect_url

        fetch_url = reverse(
            f"api-1-vault-fetch-{obj_type}-uppercase-checksum",
            url_args={f"{obj_type[:3]}_id": obj_id.upper()},
        )

        rv = api_client.get(fetch_url)

        assert rv.status_code == 302

        redirect_url = reverse(
            f"api-1-vault-fetch-{obj_type}", url_args={f"{obj_type[:3]}_id": obj_id},
        )

        assert rv["location"] == redirect_url


@given(directory(), revision(), unknown_directory(), unknown_revision())
def test_api_vault_cook_notfound(
    api_client, mocker, directory, revision, unknown_directory, unknown_revision
):
    mock_vault = mocker.patch("swh.web.common.service.vault")
    mock_vault.cook.side_effect = NotFoundExc("object not found")
    mock_vault.fetch.side_effect = NotFoundExc("cooked archive not found")
    mock_vault.progress.side_effect = NotFoundExc("cooking request not found")

    for obj_type, obj_id in (
        ("directory", directory),
        ("revision_gitfast", revision),
    ):

        obj_name = obj_type.split("_")[0]

        url = reverse(
            f"api-1-vault-cook-{obj_type}", url_args={f"{obj_type[:3]}_id": obj_id},
        )

        rv = api_client.get(url)

        assert rv.status_code == 404, rv.data
        assert rv["Content-Type"] == "application/json"
        assert rv.data["exception"] == "NotFoundExc"
        assert (
            rv.data["reason"]
            == f"Cooking of {obj_name} '{obj_id}' was never requested."
        )
        mock_vault.progress.assert_called_with(obj_type, hashutil.hash_to_bytes(obj_id))

    for obj_type, obj_id in (
        ("directory", unknown_directory),
        ("revision_gitfast", unknown_revision),
    ):
        obj_name = obj_type.split("_")[0]

        url = reverse(
            f"api-1-vault-cook-{obj_type}", url_args={f"{obj_type[:3]}_id": obj_id}
        )
        rv = api_client.post(url)

        assert rv.status_code == 404, rv.data
        assert rv["Content-Type"] == "application/json"

        assert rv.data["exception"] == "NotFoundExc"
        assert rv.data["reason"] == f"{obj_name.title()} '{obj_id}' not found."
        mock_vault.cook.assert_called_with(
            obj_type, hashutil.hash_to_bytes(obj_id), email=None
        )

        fetch_url = reverse(
            f"api-1-vault-fetch-{obj_type}", url_args={f"{obj_type[:3]}_id": obj_id},
        )

        rv = api_client.get(fetch_url)

        assert rv.status_code == 404, rv.data
        assert rv["Content-Type"] == "application/json"
        assert rv.data["exception"] == "NotFoundExc"
        assert (
            rv.data["reason"] == f"Cooked archive for {obj_name} '{obj_id}' not found."
        )
        mock_vault.fetch.assert_called_with(obj_type, hashutil.hash_to_bytes(obj_id))
