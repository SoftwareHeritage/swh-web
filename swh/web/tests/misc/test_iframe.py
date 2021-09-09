# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given

from swh.model.hashutil import hash_to_bytes
from swh.model.identifiers import CoreSWHID, ObjectType
from swh.web.common.utils import reverse
from swh.web.tests.strategies import (
    content_swhid,
    directory_swhid,
    revision_swhid,
    unknown_directory,
)
from swh.web.tests.utils import check_html_get_response


@given(content_swhid())
def test_content_swhid_iframe(client, content_swhid):
    url = reverse("swhid-iframe", url_args={"swhid": str(content_swhid)})
    check_html_get_response(
        client, url, status_code=200, template_used="misc/iframe.html"
    )


@given(content_swhid())
def test_content_core_swhid_iframe(client, content_swhid):
    content_core_swhid = CoreSWHID(
        object_type=content_swhid.object_type, object_id=content_swhid.object_id
    )
    url = reverse("swhid-iframe", url_args={"swhid": str(content_core_swhid)})
    check_html_get_response(
        client, url, status_code=200, template_used="misc/iframe.html"
    )


@given(directory_swhid())
def test_directory_swhid_iframe(client, directory_swhid):
    url = reverse("swhid-iframe", url_args={"swhid": str(directory_swhid)})
    check_html_get_response(
        client, url, status_code=200, template_used="misc/iframe.html"
    )


@given(directory_swhid())
def test_directory_core_swhid_iframe(client, directory_swhid):
    directory_core_swhid = CoreSWHID(
        object_type=directory_swhid.object_type, object_id=directory_swhid.object_id
    )
    url = reverse("swhid-iframe", url_args={"swhid": str(directory_core_swhid)})
    check_html_get_response(
        client, url, status_code=200, template_used="misc/iframe.html"
    )


@given(revision_swhid())
def test_iframe_unsupported_object(client, revision_swhid):
    url = reverse("swhid-iframe", url_args={"swhid": str(revision_swhid)})
    check_html_get_response(
        client, url, status_code=400, template_used="misc/iframe.html"
    )


@given(unknown_directory())
def test_iframe_object_not_found(client, unknown_directory):
    swhid = CoreSWHID(
        object_type=ObjectType.DIRECTORY, object_id=hash_to_bytes(unknown_directory)
    )
    url = reverse("swhid-iframe", url_args={"swhid": str(swhid)})
    check_html_get_response(
        client, url, status_code=404, template_used="misc/iframe.html"
    )


@given(content_swhid())
def test_swhid_iframe_unknown_error(client, mocker, content_swhid):
    mocker.patch("swh.web.misc.iframe.get_swhid").side_effect = Exception("Error")
    url = reverse("swhid-iframe", url_args={"swhid": str(content_swhid)})
    check_html_get_response(
        client, url, status_code=500, template_used="misc/iframe.html"
    )
