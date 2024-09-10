# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.model.hashutil import hash_to_bytes
from swh.model.model import ExtID
from swh.model.swhids import CoreSWHID, ObjectType
from swh.web.tests.helpers import check_api_get_responses
from swh.web.utils import reverse
from swh.web.utils.archive import decode_extid


def test_api_extid_not_found(api_client):
    url = reverse(
        "api-1-extid",
        url_args={"extid_type": "foo", "extid_format": "raw", "extid": "bar"},
    )
    resp = check_api_get_responses(api_client, url, status_code=404)
    assert resp.data == {
        "exception": "NotFoundExc",
        "reason": "ExtID of type foo and value bar not found.",
    }


def test_api_extid_invalid_extid_format(api_client):
    url = reverse(
        "api-1-extid",
        url_args={"extid_type": "foo", "extid_format": "baz", "extid": "bar"},
    )
    resp = check_api_get_responses(api_client, url, status_code=400)
    assert resp.data == {
        "exception": "BadInputExc",
        "reason": "Invalid external identifier format: baz",
    }


@pytest.mark.parametrize(
    "extid_data",
    [
        ("hg-nodeid", "hex", "1ce49c60732c9020ce2f98d03a7a71ec8d5be191"),
        ("bzr-nodeid", "raw", "user@example.org-20090512192901-f22ja60nsgq9j5a4"),
    ],
    ids=["hex", "raw"],
)
def test_api_extid_success(api_client, archive_data, revision, extid_data):
    extid_type, extid_format, extid = extid_data
    target = CoreSWHID(
        object_type=ObjectType.REVISION, object_id=hash_to_bytes(revision)
    )

    archive_data.extid_add(
        [
            ExtID(
                extid_type=extid_type,
                extid=decode_extid(extid_format, extid),
                target=target,
            )
        ]
    )
    url = reverse(
        "api-1-extid",
        url_args={
            "extid_type": extid_type,
            "extid_format": extid_format,
            "extid": extid,
        },
    )
    resp = check_api_get_responses(api_client, url, status_code=200)
    assert resp.data == {
        "extid": extid,
        "extid_type": extid_type,
        "extid_version": 0,
        "target": str(target),
        "target_url": f"http://testserver/{str(target)}",
    }


@pytest.mark.parametrize(
    "extid_format,extid_str",
    [
        ("base64url", "c29tZS1leHRpZA"),
        ("hex", "736f6d652d6578746964"),
        ("raw", "some-extid"),
    ],
    ids=["base64url", "hex", "raw"],
)
def test_api_extid_success_version_filtering(
    api_client, archive_data, revision, extid_format, extid_str
):
    extid_type = "some-extid-type"
    extid = b"some-extid"

    target = CoreSWHID(
        object_type=ObjectType.REVISION, object_id=hash_to_bytes(revision)
    )

    for i in range(2):
        archive_data.extid_add(
            [
                ExtID(
                    extid_type=extid_type,
                    extid_version=i,
                    extid=extid,
                    target=target,
                )
            ]
        )

    for i in range(2):
        url = reverse(
            "api-1-extid",
            url_args={
                "extid_type": extid_type,
                "extid_format": extid_format,
                "extid": extid_str,
            },
            query_params={"extid_version": i},
        )
        resp = check_api_get_responses(api_client, url, status_code=200)
        assert resp.data == {
            "extid": extid_str,
            "extid_type": extid_type,
            "extid_version": i,
            "target": str(target),
            "target_url": f"http://testserver/{str(target)}",
        }


def test_api_extid_target_not_found(api_client, archive_data):
    unknown_target = "swh:1:rev:" + "3" * 40
    url = reverse("api-1-extid-target", url_args={"swhid": unknown_target})
    resp = check_api_get_responses(api_client, url, status_code=404)
    assert resp.data == {
        "exception": "NotFoundExc",
        "reason": f"ExtID targeting {unknown_target} not found.",
    }


@pytest.mark.parametrize(
    "extid_data",
    [
        ("hg-nodeid", "hex", "1ce49c60732c9020ce2f98d03a7a71ec8d5be191"),
        ("bzr-nodeid", "raw", "user@example.org-20090512192901-f22ja60nsgq9j5a4"),
    ],
    ids=["hex", "raw"],
)
def test_api_extid_target_success(api_client, archive_data, revision, extid_data):
    extid_type, extid_format, extid_str = extid_data
    target = CoreSWHID(
        object_type=ObjectType.REVISION, object_id=hash_to_bytes(revision)
    )

    archive_data.extid_add(
        [
            ExtID(
                extid_type=extid_type,
                extid=decode_extid(extid_format, extid_str),
                target=target,
            )
        ]
    )
    url = reverse(
        "api-1-extid-target",
        url_args={"swhid": str(target)},
        query_params={"extid_format": extid_format},
    )
    resp = check_api_get_responses(api_client, url, status_code=200)
    assert resp.data == [
        {
            "extid": extid_str,
            "extid_type": extid_type,
            "extid_version": 0,
            "target": str(target),
            "target_url": f"http://testserver/{str(target)}",
        },
    ]


def test_api_extid_target_invalid_parameters(api_client, revision):
    target = CoreSWHID(
        object_type=ObjectType.REVISION, object_id=hash_to_bytes(revision)
    )
    expected_data = {
        "exception": "BadInputExc",
        "reason": "Both extid_type and extid_version query parameters must be provided",
    }

    url = reverse(
        "api-1-extid-target",
        url_args={"swhid": str(target)},
        query_params={"extid_type": "foo"},
    )
    resp = check_api_get_responses(api_client, url, status_code=400)
    assert resp.data == expected_data

    url = reverse(
        "api-1-extid-target",
        url_args={"swhid": str(target)},
        query_params={"extid_version": 1},
    )
    resp = check_api_get_responses(api_client, url, status_code=400)
    assert resp.data == expected_data


@pytest.mark.parametrize(
    "extid_format,extid_str",
    [
        ("base64url", "c29tZS1leHRpZA"),
        ("hex", "736f6d652d6578746964"),
        ("raw", "some-extid"),
    ],
    ids=["base64url", "hex", "raw"],
)
def test_api_extid_target_success_with_filtering(
    api_client, archive_data, revision, extid_format, extid_str
):
    extid_type = "some-extid-type"
    extid = b"some-extid"

    target = CoreSWHID(
        object_type=ObjectType.REVISION, object_id=hash_to_bytes(revision)
    )

    archive_data.extid_add(
        [
            ExtID(
                extid_type=extid_type,
                extid=extid,
                target=target,
            )
        ]
    )

    url = reverse(
        "api-1-extid-target",
        url_args={"swhid": str(target)},
        query_params={
            "extid_type": extid_type,
            "extid_version": 0,
            "extid_format": extid_format,
        },
    )
    resp = check_api_get_responses(api_client, url, status_code=200)
    assert resp.data == [
        {
            "extid": extid_str,
            "extid_type": extid_type,
            "extid_version": 0,
            "target": str(target),
            "target_url": f"http://testserver/{str(target)}",
        },
    ]

    url = reverse(
        "api-1-extid-target",
        url_args={"swhid": str(target)},
        query_params={
            "extid_type": "foobar",
            "extid_version": 0,
            "extid_format": extid_format,
        },
    )
    resp = check_api_get_responses(api_client, url, status_code=404)
    assert resp.data == {
        "exception": "NotFoundExc",
        "reason": f"ExtID targeting {target} not found.",
    }
