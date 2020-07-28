# Copyright (C) 2019-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from corsheaders.middleware import ACCESS_CONTROL_ALLOW_ORIGIN
from hypothesis import given

from swh.model.identifiers import (
    swhid,
    CONTENT,
    DIRECTORY,
    ORIGIN,
    RELEASE,
    REVISION,
    SNAPSHOT,
)
from swh.web.common import service
from swh.web.common.identifiers import resolve_swhid
from swh.web.common.utils import reverse
from swh.web.misc.badges import _badge_config, _get_logo_data
from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.strategies import (
    content,
    directory,
    origin,
    release,
    revision,
    snapshot,
    unknown_content,
    unknown_directory,
    new_origin,
    unknown_release,
    unknown_revision,
    unknown_snapshot,
    invalid_sha1,
)


@given(content())
def test_content_badge(client, content):
    _test_badge_endpoints(client, CONTENT, content["sha1_git"])


@given(directory())
def test_directory_badge(client, directory):
    _test_badge_endpoints(client, DIRECTORY, directory)


@given(origin())
def test_origin_badge(client, origin):
    _test_badge_endpoints(client, ORIGIN, origin["url"])


@given(release())
def test_release_badge(client, release):
    _test_badge_endpoints(client, RELEASE, release)


@given(revision())
def test_revision_badge(client, revision):
    _test_badge_endpoints(client, REVISION, revision)


@given(snapshot())
def test_snapshot_badge(client, snapshot):
    _test_badge_endpoints(client, SNAPSHOT, snapshot)


@given(
    unknown_content(),
    unknown_directory(),
    new_origin(),
    unknown_release(),
    unknown_revision(),
    unknown_snapshot(),
    invalid_sha1(),
)
def test_badge_errors(
    client,
    unknown_content,
    unknown_directory,
    new_origin,
    unknown_release,
    unknown_revision,
    unknown_snapshot,
    invalid_sha1,
):
    for object_type, object_id in (
        (CONTENT, unknown_content["sha1_git"]),
        (DIRECTORY, unknown_directory),
        (ORIGIN, new_origin.url),
        (RELEASE, unknown_release),
        (REVISION, unknown_revision),
        (SNAPSHOT, unknown_snapshot),
    ):
        url_args = {"object_type": object_type, "object_id": object_id}
        url = reverse("swh-badge", url_args=url_args)
        resp = client.get(url)
        _check_generated_badge(resp, **url_args, error="not found")

        if object_type != ORIGIN:
            object_swhid = swhid(object_type, object_id)
            url = reverse("swh-badge-swhid", url_args={"object_swhid": object_swhid})
            resp = client.get(url)
            _check_generated_badge(resp, **url_args, error="not found")

    for object_type, object_id in (
        (CONTENT, invalid_sha1),
        (DIRECTORY, invalid_sha1),
        (RELEASE, invalid_sha1),
        (REVISION, invalid_sha1),
        (SNAPSHOT, invalid_sha1),
    ):
        url_args = {"object_type": object_type, "object_id": object_id}
        url = reverse("swh-badge", url_args=url_args)
        resp = client.get(url)
        _check_generated_badge(resp, **url_args, error="invalid id")

        object_swhid = f"swh:1:{object_type[:3]}:{object_id}"
        url = reverse("swh-badge-swhid", url_args={"object_swhid": object_swhid})
        resp = client.get(url)
        _check_generated_badge(resp, "", "", error="invalid id")


@given(origin(), release())
def test_badge_endpoints_have_cors_header(client, origin, release):
    url = reverse(
        "swh-badge", url_args={"object_type": ORIGIN, "object_id": origin["url"]}
    )
    resp = client.get(url, HTTP_ORIGIN="https://example.org")
    assert resp.status_code == 200, resp.content
    assert ACCESS_CONTROL_ALLOW_ORIGIN in resp

    release_swhid = swhid(RELEASE, release)
    url = reverse("swh-badge-swhid", url_args={"object_swhid": release_swhid})
    resp = client.get(url, HTTP_ORIGIN="https://example.org")
    assert resp.status_code == 200, resp.content
    assert ACCESS_CONTROL_ALLOW_ORIGIN in resp


def _test_badge_endpoints(client, object_type, object_id):
    url_args = {"object_type": object_type, "object_id": object_id}
    url = reverse("swh-badge", url_args=url_args)
    resp = client.get(url)
    _check_generated_badge(resp, **url_args)
    if object_type != ORIGIN:
        obj_swhid = swhid(object_type, object_id)
        url = reverse("swh-badge-swhid", url_args={"object_swhid": obj_swhid})
        resp = client.get(url)
        _check_generated_badge(resp, **url_args)


def _check_generated_badge(response, object_type, object_id, error=None):
    assert response.status_code == 200, response.content
    assert response["Content-Type"] == "image/svg+xml"

    if not object_type:
        object_type = "object"

    if object_type == ORIGIN and error is None:
        link = reverse("browse-origin", query_params={"origin_url": object_id})
        text = "repository"
    elif error is None:
        text = swhid(object_type, object_id)
        link = resolve_swhid(text)["browse_url"]
        if object_type == RELEASE:
            release = service.lookup_release(object_id)
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
    assert_contains(response, _get_logo_data())
    assert_contains(response, _badge_config[object_type]["color"])
    assert_contains(response, _badge_config[object_type]["title"])
    assert_contains(response, text)
    assert_contains(response, link)
