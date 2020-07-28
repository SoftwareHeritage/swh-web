# Copyright (C) 2018-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given

from swh.model.identifiers import CONTENT, DIRECTORY, RELEASE, REVISION, SNAPSHOT

from swh.web.common.utils import reverse
from swh.web.tests.data import random_sha1
from swh.web.tests.strategies import (
    content,
    directory,
    origin,
    release,
    revision,
    snapshot,
    unknown_content,
    unknown_directory,
    unknown_release,
    unknown_revision,
    unknown_snapshot,
)


@given(origin(), content(), directory(), release(), revision(), snapshot())
def test_swhid_resolve_success(
    api_client, origin, content, directory, release, revision, snapshot
):

    for obj_type_short, obj_type, obj_id in (
        ("cnt", CONTENT, content["sha1_git"]),
        ("dir", DIRECTORY, directory),
        ("rel", RELEASE, release),
        ("rev", REVISION, revision),
        ("snp", SNAPSHOT, snapshot),
    ):

        swhid = "swh:1:%s:%s;origin=%s" % (obj_type_short, obj_id, origin["url"])
        url = reverse("api-1-resolve-swhid", url_args={"swhid": swhid})

        resp = api_client.get(url)

        if obj_type == CONTENT:
            url_args = {"query_string": "sha1_git:%s" % obj_id}
        elif obj_type == SNAPSHOT:
            url_args = {"snapshot_id": obj_id}
        else:
            url_args = {"sha1_git": obj_id}

        browse_rev_url = reverse(
            "browse-%s" % obj_type,
            url_args=url_args,
            query_params={"origin_url": origin["url"]},
            request=resp.wsgi_request,
        )

        expected_result = {
            "browse_url": browse_rev_url,
            "metadata": {"origin": origin["url"]},
            "namespace": "swh",
            "object_id": obj_id,
            "object_type": obj_type,
            "scheme_version": 1,
        }

        assert resp.status_code == 200, resp.data
        assert resp.data == expected_result


def test_swhid_resolve_invalid(api_client):
    rev_id_invalid = "96db9023b8_foo_50d6c108e9a3"
    swhid = "swh:1:rev:%s" % rev_id_invalid
    url = reverse("api-1-resolve-swhid", url_args={"swhid": swhid})

    resp = api_client.get(url)

    assert resp.status_code == 400, resp.data


@given(
    unknown_content(),
    unknown_directory(),
    unknown_release(),
    unknown_revision(),
    unknown_snapshot(),
)
def test_swhid_resolve_not_found(
    api_client,
    unknown_content,
    unknown_directory,
    unknown_release,
    unknown_revision,
    unknown_snapshot,
):

    for obj_type_short, obj_id in (
        ("cnt", unknown_content["sha1_git"]),
        ("dir", unknown_directory),
        ("rel", unknown_release),
        ("rev", unknown_revision),
        ("snp", unknown_snapshot),
    ):

        swhid = "swh:1:%s:%s" % (obj_type_short, obj_id)

        url = reverse("api-1-resolve-swhid", url_args={"swhid": swhid})

        resp = api_client.get(url)

        assert resp.status_code == 404, resp.data


def test_swh_origin_id_not_resolvable(api_client):
    ori_swhid = "swh:1:ori:8068d0075010b590762c6cb5682ed53cb3c13deb"
    url = reverse("api-1-resolve-swhid", url_args={"swhid": ori_swhid})
    resp = api_client.get(url)
    assert resp.status_code == 400, resp.data


@given(content(), directory())
def test_api_known_swhid_some_present(api_client, content, directory):
    content_ = "swh:1:cnt:%s" % content["sha1_git"]
    directory_ = "swh:1:dir:%s" % directory
    unknown_revision_ = "swh:1:rev:%s" % random_sha1()
    unknown_release_ = "swh:1:rel:%s" % random_sha1()
    unknown_snapshot_ = "swh:1:snp:%s" % random_sha1()

    input_swhids = [
        content_,
        directory_,
        unknown_revision_,
        unknown_release_,
        unknown_snapshot_,
    ]

    url = reverse("api-1-known")

    resp = api_client.post(
        url, data=input_swhids, format="json", HTTP_ACCEPT="application/json"
    )

    assert resp.status_code == 200, resp.data
    assert resp["Content-Type"] == "application/json"
    assert resp.data == {
        content_: {"known": True},
        directory_: {"known": True},
        unknown_revision_: {"known": False},
        unknown_release_: {"known": False},
        unknown_snapshot_: {"known": False},
    }


def test_api_known_invalid_swhid(api_client):
    invalid_swhid_sha1 = ["swh:1:cnt:8068d0075010b590762c6cb5682ed53cb3c13de;"]
    invalid_swhid_type = ["swh:1:cnn:8068d0075010b590762c6cb5682ed53cb3c13deb"]

    url = reverse("api-1-known")

    resp = api_client.post(
        url, data=invalid_swhid_sha1, format="json", HTTP_ACCEPT="application/json"
    )

    assert resp.status_code == 400, resp.data

    resp2 = api_client.post(
        url, data=invalid_swhid_type, format="json", HTTP_ACCEPT="application/json"
    )

    assert resp2.status_code == 400, resp.data


def test_api_known_raises_large_payload_error(api_client):
    random_swhid = "swh:1:cnt:8068d0075010b590762c6cb5682ed53cb3c13deb"
    limit = 10000
    err_msg = "The maximum number of SWHIDs this endpoint can receive is 1000"

    swhids = [random_swhid for i in range(limit)]

    url = reverse("api-1-known")
    resp = api_client.post(
        url, data=swhids, format="json", HTTP_ACCEPT="application/json"
    )

    assert resp.status_code == 413, resp.data
    assert resp["Content-Type"] == "application/json"
    assert resp.data == {"exception": "LargePayloadExc", "reason": err_msg}
