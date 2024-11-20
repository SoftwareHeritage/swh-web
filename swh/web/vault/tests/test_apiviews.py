# Copyright (C) 2017-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re

import pytest

from swh.model.swhids import CoreSWHID
from swh.vault.exc import NotFoundExc
from swh.web.tests.helpers import (
    check_api_get_responses,
    check_api_post_responses,
    check_http_get_response,
    check_http_post_response,
)
from swh.web.utils import reverse

#####################
# Current API:


@pytest.mark.parametrize("fetch_redirect", [False, True])
def test_api_vault_cook_and_fetch(
    api_client, mocker, directory, revision, release, snapshot, fetch_redirect
):
    mock_archive = mocker.patch("swh.web.vault.api_views.archive")

    for (
        bundle_type,
        swhid,
        content_type,
    ) in (
        ("flat", f"swh:1:dir:{directory}", "application/gzip"),
        ("gitfast", f"swh:1:rev:{revision}", "application/gzip"),
        ("git_bare", f"swh:1:rev:{revision}", "application/x-tar"),
        ("git_bare", f"swh:1:dir:{directory}", "application/x-tar"),
        ("git_bare", f"swh:1:rel:{release}", "application/x-tar"),
        ("git_bare", f"swh:1:snp:{snapshot}", "application/x-tar"),
    ):
        swhid = CoreSWHID.from_string(swhid)

        fetch_url = reverse(
            f"api-1-vault-download-{bundle_type.replace('_', '-')}",
            url_args={"swhid": str(swhid)},
        )
        stub_cook = {
            "type": bundle_type,
            "progress_msg": None,
            "task_id": 1,
            "task_status": "done",
            "swhid": swhid,
        }
        stub_fetch = b"content"

        mock_archive.vault_cook.return_value = stub_cook
        mock_archive.vault_download.return_value = stub_fetch
        if fetch_redirect:
            redirect_url = f"http://example.org/vault/{bundle_type}/{swhid}"
            mock_archive.vault_download_url.return_value = redirect_url
        else:
            mock_archive.vault_download_url.return_value = None

        email = "test@test.mail"
        url = reverse(
            f"api-1-vault-cook-{bundle_type.replace('_', '-')}",
            url_args={"swhid": str(swhid)},
            query_params={"email": email},
        )

        rv = check_api_post_responses(api_client, url, data=None, status_code=200)
        assert rv.data == {
            "fetch_url": rv.wsgi_request.build_absolute_uri(fetch_url),
            "progress_message": None,
            "id": 1,
            "status": "done",
            "swhid": str(swhid),
        }
        mock_archive.vault_cook.assert_called_with(bundle_type, swhid, email)

        if fetch_redirect:
            rv = check_http_get_response(api_client, fetch_url, status_code=302)
            assert rv["Location"] == redirect_url
            mock_archive.vault_download_url.assert_called()
        else:
            rv = check_http_get_response(api_client, fetch_url, status_code=200)
            assert rv["Content-Type"] == content_type
            assert b"".join(rv.streaming_content) == stub_fetch
            mock_archive.vault_download.assert_called_with(bundle_type, swhid)


@pytest.mark.parametrize("fetch_redirect", [False, True])
def test_api_vault_cook_notfound(
    api_client,
    mocker,
    config_updater,
    directory,
    revision,
    release,
    snapshot,
    unknown_directory,
    unknown_revision,
    fetch_redirect,
):
    mocked_vault = mocker.MagicMock()
    mocked_vault.cook.side_effect = NotFoundExc("object not found")
    mocked_vault.fetch.side_effect = NotFoundExc("cooked archive not found")
    mocked_vault.progress.side_effect = NotFoundExc("cooking request not found")
    if fetch_redirect:
        mocked_vault.download_url.side_effect = NotFoundExc("cooking request not found")
    else:
        mocked_vault.download_url.return_value = None
    config_updater({"vault": mocked_vault})
    for bundle_type, swhid in (
        ("flat", f"swh:1:dir:{directory}"),
        ("gitfast", f"swh:1:rev:{revision}"),
        ("git_bare", f"swh:1:rev:{revision}"),
        ("git_bare", f"swh:1:dir:{directory}"),
        ("git_bare", f"swh:1:rel:{release}"),
        ("git_bare", f"swh:1:snp:{snapshot}"),
    ):
        swhid = CoreSWHID.from_string(swhid)

        url = reverse(
            f"api-1-vault-cook-{bundle_type.replace('_', '-')}",
            url_args={"swhid": str(swhid)},
        )

        rv = check_api_get_responses(api_client, url, status_code=404)

        assert rv.data["exception"] == "NotFoundExc"
        assert rv.data["reason"] == f"Cooking of {swhid} was never requested."
        mocked_vault.progress.assert_called_with(bundle_type, swhid)

    for bundle_type, swhid in (
        ("flat", f"swh:1:dir:{unknown_directory}"),
        ("gitfast", f"swh:1:rev:{unknown_revision}"),
        ("git_bare", f"swh:1:rev:{unknown_revision}"),
    ):
        swhid = CoreSWHID.from_string(swhid)
        url = reverse(
            f"api-1-vault-cook-{bundle_type.replace('_', '-')}",
            url_args={"swhid": str(swhid)},
        )
        rv = check_api_post_responses(api_client, url, data=None, status_code=404)

        assert rv.data["exception"] == "NotFoundExc"
        assert rv.data["reason"] == f"{swhid} not found."
        mocked_vault.cook.assert_called_with(bundle_type, swhid, email=None)

        fetch_url = reverse(
            f"api-1-vault-download-{bundle_type.replace('_', '-')}",
            url_args={"swhid": str(swhid)},
        )

        rv = check_api_get_responses(api_client, fetch_url, status_code=404)
        assert rv.data["exception"] == "NotFoundExc"
        assert rv.data["reason"] == f"Cooked archive for {swhid} not found."
        if fetch_redirect:
            mocked_vault.download_url.assert_called()
        else:
            mocked_vault.fetch.assert_called_with(bundle_type, swhid)


@pytest.mark.parametrize("bundle_type", ["flat", "gitfast", "git_bare"])
def test_api_vault_cook_error_content(api_client, mocker, bundle_type):
    swhid = "swh:1:cnt:" + "0" * 40

    email = "test@test.mail"
    url = reverse(
        f"api-1-vault-cook-{bundle_type.replace('_', '-')}",
        url_args={"swhid": swhid},
        query_params={"email": email},
    )

    rv = check_api_post_responses(api_client, url, data=None, status_code=400)
    if bundle_type != "git_bare":
        assert rv.data == {
            "exception": "BadInputExc",
            "reason": (
                "Content objects do not need to be cooked, "
                "use `/api/1/content/raw/` instead."
            ),
        }
    else:
        assert rv.data == {
            "exception": "BadInputExc",
            "reason": "Object type CONTENT cannot be cooked as 'git-bare' bundle.",
        }


@pytest.mark.parametrize(
    "bundle_type,swhid_type,hint",
    [
        ("flat", "rev", True),
        ("flat", "rel", False),
        ("flat", "snp", False),
        ("gitfast", "dir", True),
        ("gitfast", "rel", False),
        ("gitfast", "snp", False),
        ("git_bare", "cnt", False),
    ],
)
def test_api_vault_cook_error(api_client, mocker, bundle_type, swhid_type, hint):
    swhid = f"swh:1:{swhid_type}:" + "0" * 40

    email = "test@test.mail"
    url = reverse(
        f"api-1-vault-cook-{bundle_type.replace('_', '-')}",
        url_args={"swhid": swhid},
        query_params={"email": email},
    )

    rv = check_api_post_responses(api_client, url, data=None, status_code=400)
    assert rv.data["exception"] == "BadInputExc"
    if hint:
        assert re.match(
            r"Only .* can be cooked as .* bundles\. Use .*", rv.data["reason"]
        )
    else:
        if bundle_type != "git_bare":
            assert re.match(r"Only .* can be cooked as .* bundles\.", rv.data["reason"])
        else:
            assert re.match(
                r"Object type .* cannot be cooked as 'git-bare' bundle\.",
                rv.data["reason"],
            )


#####################
# Legacy API:


def test_api_vault_cook_legacy(api_client, mocker, directory, revision):
    mock_archive = mocker.patch("swh.web.vault.api_views.archive")

    for obj_type, bundle_type, response_obj_type, obj_id in (
        ("directory", "flat", "directory", directory),
        ("revision_gitfast", "gitfast", "revision", revision),
    ):
        swhid = CoreSWHID.from_string(f"swh:1:{obj_type[:3]}:{obj_id}")

        fetch_url = reverse(
            f"api-1-vault-download-{bundle_type}",
            url_args={"swhid": str(swhid)},
        )
        stub_cook = {
            "type": obj_type,
            "progress_msg": None,
            "task_id": 1,
            "task_status": "done",
            "swhid": swhid,
            "obj_type": response_obj_type,
            "obj_id": obj_id,
        }
        stub_fetch = b"content"

        mock_archive.vault_cook.return_value = stub_cook
        mock_archive.vault_download.return_value = stub_fetch
        mock_archive.vault_download_url.return_value = None

        email = "test@test.mail"
        url = reverse(
            f"api-1-vault-cook-{obj_type}",
            url_args={f"{obj_type[:3]}_id": obj_id},
            query_params={"email": email},
        )

        rv = check_api_post_responses(api_client, url, data=None, status_code=200)
        assert rv.data == {
            "fetch_url": rv.wsgi_request.build_absolute_uri(fetch_url),
            "progress_message": None,
            "id": 1,
            "status": "done",
            "swhid": str(swhid),
            "obj_type": response_obj_type,
            "obj_id": obj_id,
        }
        mock_archive.vault_cook.assert_called_with(bundle_type, swhid, email)

        rv = check_http_get_response(api_client, fetch_url, status_code=200)
        assert rv["Content-Type"] == "application/gzip"
        assert b"".join(rv.streaming_content) == stub_fetch
        mock_archive.vault_download.assert_called_with(bundle_type, swhid)


def test_api_vault_cook_uppercase_hash_legacy(api_client, directory, revision):
    for obj_type, obj_id in (
        ("directory", directory),
        ("revision_gitfast", revision),
    ):
        url = reverse(
            f"api-1-vault-cook-{obj_type}-uppercase-checksum",
            url_args={f"{obj_type[:3]}_id": obj_id.upper()},
        )
        rv = check_http_post_response(
            api_client, url, data={"email": "test@test.mail"}, status_code=302
        )

        redirect_url = reverse(
            f"api-1-vault-cook-{obj_type}", url_args={f"{obj_type[:3]}_id": obj_id}
        )

        assert rv["location"] == redirect_url

        fetch_url = reverse(
            f"api-1-vault-download-{obj_type}-uppercase-checksum",
            url_args={f"{obj_type[:3]}_id": obj_id.upper()},
        )

        rv = check_http_get_response(api_client, fetch_url, status_code=302)

        redirect_url = reverse(
            f"api-1-vault-download-{obj_type}",
            url_args={f"{obj_type[:3]}_id": obj_id},
        )

        assert rv["location"] == redirect_url


def test_api_vault_cook_notfound_legacy(
    api_client,
    mocker,
    config_updater,
    directory,
    revision,
    unknown_directory,
    unknown_revision,
):
    mocked_vault = mocker.MagicMock()
    mocked_vault.cook.side_effect = NotFoundExc("object not found")
    mocked_vault.fetch.side_effect = NotFoundExc("cooked archive not found")
    mocked_vault.progress.side_effect = NotFoundExc("cooking request not found")
    mocked_vault.download_url.return_value = None
    config_updater({"vault": mocked_vault})

    for obj_type, bundle_type, obj_id in (
        ("directory", "flat", directory),
        ("revision_gitfast", "gitfast", revision),
    ):
        url = reverse(
            f"api-1-vault-cook-{obj_type}",
            url_args={f"{obj_type[:3]}_id": obj_id},
        )

        swhid = CoreSWHID.from_string(f"swh:1:{obj_type[:3]}:{obj_id}")

        rv = check_api_get_responses(api_client, url, status_code=404)

        assert rv.data["exception"] == "NotFoundExc"
        assert rv.data["reason"] == f"Cooking of {swhid} was never requested."
        mocked_vault.progress.assert_called_with(bundle_type, swhid)

    for obj_type, bundle_type, obj_id in (
        ("directory", "flat", unknown_directory),
        ("revision_gitfast", "gitfast", unknown_revision),
    ):
        swhid = CoreSWHID.from_string(f"swh:1:{obj_type[:3]}:{obj_id}")

        url = reverse(
            f"api-1-vault-cook-{obj_type}", url_args={f"{obj_type[:3]}_id": obj_id}
        )
        rv = check_api_post_responses(api_client, url, data=None, status_code=404)

        assert rv.data["exception"] == "NotFoundExc"
        assert rv.data["reason"] == f"{swhid} not found."
        mocked_vault.cook.assert_called_with(bundle_type, swhid, email=None)

        fetch_url = reverse(
            f"api-1-vault-download-{obj_type}",
            url_args={f"{obj_type[:3]}_id": obj_id},
        )

        # Redirected to the current 'fetch' url
        rv = check_http_get_response(api_client, fetch_url, status_code=302)
        redirect_url = reverse(
            f"api-1-vault-download-{bundle_type}",
            url_args={"swhid": str(swhid)},
        )
        assert rv["location"] == redirect_url

        rv = check_api_get_responses(api_client, redirect_url, status_code=404)
        assert rv.data["exception"] == "NotFoundExc"
        assert rv.data["reason"] == f"Cooked archive for {swhid} not found."
        mocked_vault.fetch.assert_called_with(bundle_type, swhid)
