# Copyright (C) 2019-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from corsheaders.middleware import ACCESS_CONTROL_ALLOW_ORIGIN
from hypothesis import given

from swh.model.hashutil import hash_to_bytes
from swh.model.swhids import ObjectType, QualifiedSWHID
from swh.web.badges import badge_config, get_logo_data
from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.helpers import check_http_get_response
from swh.web.tests.strategies import new_origin
from swh.web.utils import archive, reverse
from swh.web.utils.identifiers import resolve_swhid


def test_content_badge(client, content):
    _test_badge_endpoints(client, "content", content["sha1_git"])


def test_directory_badge(client, directory):
    _test_badge_endpoints(client, "directory", directory)


def test_origin_badge(client, origin):
    _test_badge_endpoints(client, "origin", origin["url"])


def test_release_badge(client, release):
    _test_badge_endpoints(client, "release", release)


def test_revision_badge(client, revision):
    _test_badge_endpoints(client, "revision", revision)


def test_snapshot_badge(client, snapshot):
    _test_badge_endpoints(client, "snapshot", snapshot)


@given(
    new_origin(),
)
def test_badge_errors(
    client,
    unknown_content,
    unknown_directory,
    unknown_release,
    unknown_revision,
    unknown_snapshot,
    invalid_sha1,
    new_origin,
):
    for object_type, object_id in (
        ("content", unknown_content["sha1_git"]),
        ("directory", unknown_directory),
        ("origin", new_origin),
        ("release", unknown_release),
        ("revision", unknown_revision),
        ("snapshot", unknown_snapshot),
    ):
        url_args = {"object_type": object_type, "object_id": object_id}
        url = reverse("swh-badge", url_args=url_args)
        resp = check_http_get_response(
            client, url, status_code=200, content_type="image/svg+xml"
        )
        _check_generated_badge(resp, **url_args, error="not found")

    for object_type, object_id in (
        (ObjectType.CONTENT, invalid_sha1),
        (ObjectType.DIRECTORY, invalid_sha1),
        (ObjectType.RELEASE, invalid_sha1),
        (ObjectType.REVISION, invalid_sha1),
        (ObjectType.SNAPSHOT, invalid_sha1),
    ):
        url_args = {"object_type": object_type.name.lower(), "object_id": object_id}
        url = reverse("swh-badge", url_args=url_args)

        resp = check_http_get_response(
            client, url, status_code=200, content_type="image/svg+xml"
        )
        _check_generated_badge(resp, **url_args, error="invalid id")

        object_swhid = f"swh:1:{object_type.value}:{object_id}"
        url = reverse("swh-badge-swhid", url_args={"object_swhid": object_swhid})
        resp = check_http_get_response(
            client, url, status_code=200, content_type="image/svg+xml"
        )
        _check_generated_badge(resp, "", "", error="invalid id")


def test_badge_endpoints_have_cors_header(client, origin, release):
    url = reverse(
        "swh-badge", url_args={"object_type": "origin", "object_id": origin["url"]}
    )

    resp = check_http_get_response(
        client,
        url,
        status_code=200,
        content_type="image/svg+xml",
        http_origin="https://example.org",
    )
    assert ACCESS_CONTROL_ALLOW_ORIGIN in resp

    release_swhid = str(
        QualifiedSWHID(object_type=ObjectType.RELEASE, object_id=hash_to_bytes(release))
    )
    url = reverse("swh-badge-swhid", url_args={"object_swhid": release_swhid})
    resp = check_http_get_response(
        client,
        url,
        status_code=200,
        content_type="image/svg+xml",
        http_origin="https://example.org",
    )
    assert ACCESS_CONTROL_ALLOW_ORIGIN in resp


def _test_badge_endpoints(client, object_type: str, object_id: str):
    url_args = {"object_type": object_type, "object_id": object_id}
    url = reverse("swh-badge", url_args=url_args)
    resp = check_http_get_response(
        client, url, status_code=200, content_type="image/svg+xml"
    )
    _check_generated_badge(resp, **url_args)

    if object_type != "origin":
        obj_swhid = str(
            QualifiedSWHID(
                object_type=ObjectType[object_type.upper()],
                object_id=hash_to_bytes(object_id),
            )
        )
        url = reverse("swh-badge-swhid", url_args={"object_swhid": obj_swhid})
        resp = check_http_get_response(
            client, url, status_code=200, content_type="image/svg+xml"
        )
        _check_generated_badge(resp, **url_args)


def _check_generated_badge(response, object_type, object_id, error=None):
    assert response.status_code == 200, response.content
    assert response["Content-Type"] == "image/svg+xml"

    if not object_type:
        object_type = "object"

    if object_type == "origin" and error is None:
        link = reverse("browse-origin", query_params={"origin_url": object_id})
        text = "repository"
    elif error is None:
        text = str(
            QualifiedSWHID(
                object_type=ObjectType[object_type.upper()],
                object_id=hash_to_bytes(object_id),
            )
        )
        link = resolve_swhid(text)["browse_url"]
        if object_type == "release":
            release = archive.lookup_release(object_id)
            text = release["name"]
    elif error == "invalid id":
        text = "error"
        link = f"invalid {object_type} id"
        object_type = "error"
    elif error == "not found":
        text = "error"
        link = f"{object_type} not found"
        object_type = "error"

    assert_contains(response, "<svg ")
    assert_contains(response, "</svg>")
    assert_contains(response, get_logo_data())
    assert_contains(response, badge_config[object_type]["color"])
    assert_contains(response, badge_config[object_type]["title"])
    assert_contains(response, text)
    assert_contains(response, link)
