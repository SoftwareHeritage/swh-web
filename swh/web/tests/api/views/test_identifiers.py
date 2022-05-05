# Copyright (C) 2018-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from swh.model.swhids import ObjectType
from swh.web.common.identifiers import gen_swhid
from swh.web.common.utils import reverse
from swh.web.tests.data import random_sha1
from swh.web.tests.utils import check_api_get_responses, check_api_post_responses


def test_swhid_resolve_success(
    api_client, content, directory, origin, release, revision, snapshot
):

    for obj_type, obj_id in (
        (ObjectType.CONTENT, content["sha1_git"]),
        (ObjectType.DIRECTORY, directory),
        (ObjectType.RELEASE, release),
        (ObjectType.REVISION, revision),
        (ObjectType.SNAPSHOT, snapshot),
    ):

        swhid = gen_swhid(obj_type, obj_id, metadata={"origin": origin["url"]})

        url = reverse("api-1-resolve-swhid", url_args={"swhid": swhid})

        resp = check_api_get_responses(api_client, url, status_code=200)

        if obj_type == ObjectType.CONTENT:
            url_args = {"query_string": "sha1_git:%s" % obj_id}
        elif obj_type == ObjectType.SNAPSHOT:
            url_args = {"snapshot_id": obj_id}
        else:
            url_args = {"sha1_git": obj_id}

        obj_type_str = obj_type.name.lower()

        browse_rev_url = reverse(
            f"browse-{obj_type_str}",
            url_args=url_args,
            query_params={"origin_url": origin["url"]},
            request=resp.wsgi_request,
        )

        expected_result = {
            "browse_url": browse_rev_url,
            "metadata": {"origin": origin["url"]},
            "namespace": "swh",
            "object_id": obj_id,
            "object_type": obj_type_str,
            "scheme_version": 1,
        }

        assert resp.data == expected_result


def test_swhid_resolve_invalid(api_client):
    rev_id_invalid = "96db9023b8_foo_50d6c108e9a3"
    swhid = "swh:1:rev:%s" % rev_id_invalid
    url = reverse("api-1-resolve-swhid", url_args={"swhid": swhid})
    check_api_get_responses(api_client, url, status_code=400)


def test_swhid_resolve_not_found(
    api_client,
    unknown_content,
    unknown_directory,
    unknown_release,
    unknown_revision,
    unknown_snapshot,
):

    for obj_type, obj_id in (
        (ObjectType.CONTENT, unknown_content["sha1_git"]),
        (ObjectType.DIRECTORY, unknown_directory),
        (ObjectType.RELEASE, unknown_release),
        (ObjectType.REVISION, unknown_revision),
        (ObjectType.SNAPSHOT, unknown_snapshot),
    ):

        swhid = gen_swhid(obj_type, obj_id)

        url = reverse("api-1-resolve-swhid", url_args={"swhid": swhid})

        check_api_get_responses(api_client, url, status_code=404)


def test_swh_origin_id_not_resolvable(api_client):
    ori_swhid = "swh:1:ori:8068d0075010b590762c6cb5682ed53cb3c13deb"
    url = reverse("api-1-resolve-swhid", url_args={"swhid": ori_swhid})
    check_api_get_responses(api_client, url, status_code=400)


def test_api_known_swhid_all_present(
    api_client, content, directory, release, revision, snapshot
):
    input_swhids = [
        gen_swhid(ObjectType.CONTENT, content["sha1_git"]),
        gen_swhid(ObjectType.DIRECTORY, directory),
        gen_swhid(ObjectType.REVISION, revision),
        gen_swhid(ObjectType.RELEASE, release),
        gen_swhid(ObjectType.SNAPSHOT, snapshot),
    ]

    url = reverse("api-1-known")

    resp = check_api_post_responses(api_client, url, data=input_swhids, status_code=200)

    assert resp.data == {swhid: {"known": True} for swhid in input_swhids}


def test_api_known_swhid_some_present(api_client, content, directory):
    content_ = gen_swhid(ObjectType.CONTENT, content["sha1_git"])
    directory_ = gen_swhid(ObjectType.DIRECTORY, directory)
    unknown_revision_ = gen_swhid(ObjectType.REVISION, random_sha1())
    unknown_release_ = gen_swhid(ObjectType.RELEASE, random_sha1())
    unknown_snapshot_ = gen_swhid(ObjectType.SNAPSHOT, random_sha1())

    input_swhids = [
        content_,
        directory_,
        unknown_revision_,
        unknown_release_,
        unknown_snapshot_,
    ]

    url = reverse("api-1-known")

    resp = check_api_post_responses(api_client, url, data=input_swhids, status_code=200)

    assert resp.data == {
        content_: {"known": True},
        directory_: {"known": True},
        unknown_revision_: {"known": False},
        unknown_release_: {"known": False},
        unknown_snapshot_: {"known": False},
    }


def test_api_known_swhid_same_hash(api_client, content):
    content_ = gen_swhid(ObjectType.CONTENT, content["sha1_git"])
    # Reuse hash to make invalid directory SHWID
    directory_ = gen_swhid(ObjectType.DIRECTORY, content["sha1_git"])

    input_swhids = [
        content_,
        directory_,
    ]

    url = reverse("api-1-known")

    resp = check_api_post_responses(api_client, url, data=input_swhids, status_code=200)

    assert resp.data == {
        content_: {"known": True},
        directory_: {"known": False},
    }


def test_api_known_invalid_swhid(api_client):
    invalid_swhid_sha1 = ["swh:1:cnt:8068d0075010b590762c6cb5682ed53cb3c13de;"]
    invalid_swhid_type = ["swh:1:cnn:8068d0075010b590762c6cb5682ed53cb3c13deb"]

    url = reverse("api-1-known")

    check_api_post_responses(api_client, url, data=invalid_swhid_sha1, status_code=400)

    check_api_post_responses(api_client, url, data=invalid_swhid_type, status_code=400)


def test_api_known_raises_large_payload_error(api_client):
    random_swhid = "swh:1:cnt:8068d0075010b590762c6cb5682ed53cb3c13deb"
    limit = 10000
    err_msg = "The maximum number of SWHIDs this endpoint can receive is 1000"

    swhids = [random_swhid for i in range(limit)]

    url = reverse("api-1-known")
    resp = check_api_post_responses(api_client, url, data=swhids, status_code=413)

    assert resp.data == {"exception": "LargePayloadExc", "reason": err_msg}
