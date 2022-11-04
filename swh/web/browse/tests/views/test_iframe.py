# Copyright (C) 2021-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from swh.model.hashutil import hash_to_bytes
from swh.model.swhids import CoreSWHID, ObjectType, QualifiedSWHID
from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.helpers import check_html_get_response
from swh.web.utils import reverse


def test_content_swhid_iframe(client, content_swhid):
    url = reverse("browse-swhid-iframe", url_args={"swhid": str(content_swhid)})
    check_html_get_response(
        client, url, status_code=200, template_used="browse-iframe.html"
    )


def test_content_core_swhid_iframe(client, content_swhid):
    content_core_swhid = CoreSWHID(
        object_type=content_swhid.object_type, object_id=content_swhid.object_id
    )
    url = reverse("browse-swhid-iframe", url_args={"swhid": str(content_core_swhid)})
    check_html_get_response(
        client, url, status_code=200, template_used="browse-iframe.html"
    )


def test_directory_swhid_iframe(client, directory_swhid):
    url = reverse("browse-swhid-iframe", url_args={"swhid": str(directory_swhid)})
    check_html_get_response(
        client, url, status_code=200, template_used="browse-iframe.html"
    )


def test_directory_core_swhid_iframe(client, directory_swhid):
    directory_core_swhid = CoreSWHID(
        object_type=directory_swhid.object_type, object_id=directory_swhid.object_id
    )
    url = reverse("browse-swhid-iframe", url_args={"swhid": str(directory_core_swhid)})
    check_html_get_response(
        client, url, status_code=200, template_used="browse-iframe.html"
    )


def test_iframe_unsupported_object(client, revision_swhid):
    url = reverse("browse-swhid-iframe", url_args={"swhid": str(revision_swhid)})
    check_html_get_response(
        client, url, status_code=400, template_used="browse-iframe.html"
    )


def test_iframe_object_not_found(client, unknown_directory):
    swhid = CoreSWHID(
        object_type=ObjectType.DIRECTORY, object_id=hash_to_bytes(unknown_directory)
    )
    url = reverse("browse-swhid-iframe", url_args={"swhid": str(swhid)})
    check_html_get_response(
        client, url, status_code=404, template_used="browse-iframe.html"
    )


def test_swhid_iframe_unknown_error(client, mocker, content_swhid):
    mocker.patch("swh.web.browse.views.iframe.get_swhid").side_effect = Exception(
        "Error"
    )
    url = reverse("browse-swhid-iframe", url_args={"swhid": str(content_swhid)})
    check_html_get_response(
        client, url, status_code=500, template_used="browse-iframe.html"
    )


def test_iframe_directory_no_snapshot_context(
    client, archive_data, directory_with_subdirs
):
    dir_content = archive_data.directory_ls(directory_with_subdirs)
    subdir = random.choice([e for e in dir_content if e["type"] == "dir"])
    path = f"/{subdir['name']}/"

    root_swhid = CoreSWHID(
        object_type=ObjectType.DIRECTORY,
        object_id=hash_to_bytes(directory_with_subdirs),
    )
    swhid = CoreSWHID(
        object_type=ObjectType.DIRECTORY, object_id=hash_to_bytes(subdir["target"])
    )
    qualified_swhid = QualifiedSWHID(
        object_type=ObjectType.DIRECTORY,
        object_id=hash_to_bytes(subdir["target"]),
        anchor=root_swhid,
        path=path,
    )

    url = reverse(
        "browse-swhid-iframe",
        url_args={"swhid": f"{str(swhid)};path={path}"},
        query_params={"focus_swhid": str(root_swhid)},
    )
    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-iframe.html"
    )

    archive_url = reverse("browse-swhid", url_args={"swhid": str(qualified_swhid)})

    assert_contains(resp, archive_url)


def test_iframe_legacy_url_redirection(client, directory_swhid):
    directory_core_swhid = CoreSWHID(
        object_type=directory_swhid.object_type, object_id=directory_swhid.object_id
    )
    url = reverse(
        "browse-swhid-iframe-legacy", url_args={"swhid": str(directory_core_swhid)}
    )
    resp = check_html_get_response(
        client,
        url,
        status_code=302,
    )

    assert resp["Location"] == reverse(
        "browse-swhid-iframe", url_args={"swhid": str(directory_core_swhid)}
    )
