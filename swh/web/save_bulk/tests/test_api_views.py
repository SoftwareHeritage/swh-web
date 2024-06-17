# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

import pytest
import yaml

from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.helpers import check_api_post_responses, check_http_get_response
from swh.web.utils import reverse

pytestmark = pytest.mark.django_db


def test_save_bulk_post_anonymous(api_client):
    url = reverse("api-1-save-origin-bulk")
    resp = check_api_post_responses(api_client, url, status_code=401)
    assert resp.data == {
        "status": "rejected",
        "reason": "This API endpoint requires authentication.",
    }


def test_save_bulk_post_user_without_permission(api_client, regular_user):
    api_client.force_login(regular_user)
    url = reverse("api-1-save-origin-bulk")
    resp = check_api_post_responses(api_client, url, status_code=403)
    assert resp.data == {
        "status": "rejected",
        "reason": "This API endpoint requires a special user permission.",
    }


def test_save_bulk_post_no_origins_data(api_client, save_bulk_user):
    api_client.force_login(save_bulk_user)
    url = reverse("api-1-save-origin-bulk")
    resp = check_api_post_responses(api_client, url, status_code=400)
    assert resp.data == {
        "status": "rejected",
        "reason": "No origins data were provided in POST request body.",
    }


@pytest.mark.parametrize(
    "content_type,invalid_data",
    [
        ("text/csv", b"a,b\rc,d"),
        ("application/json", b"{123}"),
        ("application/yaml", b"a\tb"),
    ],
    ids=["invalid CSV data", "invalid JSON data", "invalid YAML data"],
)
def test_save_bulk_post_not_parsable_data(
    api_client, save_bulk_user, content_type, invalid_data
):
    api_client.force_login(save_bulk_user)
    url = reverse("api-1-save-origin-bulk")
    resp = check_api_post_responses(
        api_client,
        url,
        HTTP_CONTENT_TYPE=content_type,
        data=invalid_data,
        status_code=400,
    )
    assert_contains(resp, "ParseError", status_code=400)


def test_save_bulk_post_invalid_content_type(api_client, save_bulk_user):
    api_client.force_login(save_bulk_user)
    url = reverse("api-1-save-origin-bulk")
    resp = check_api_post_responses(
        api_client,
        url,
        HTTP_CONTENT_TYPE="application/xml",
        data=b"foo",
        status_code=415,
    )
    assert_contains(resp, "UnsupportedMediaType", status_code=415)


@pytest.mark.parametrize(
    "content_type,malformed_data",
    [
        ("text/csv", b"https://git.example.org/user/project,git\n,svn"),
        (
            "application/json",
            b'[{"origin_url": "https://git.example.org/user/project", "visit_type": 123}]',
        ),
        (
            "application/yaml",
            b"- origin_url: https://git.example.org/user/project\n  visit_type: 123\n\n",
        ),
    ],
    ids=["malformed CSV data", "malformed JSON data", "malformed YAML data"],
)
def test_save_bulk_post_malformed_origins_data(
    api_client, save_bulk_user, content_type, malformed_data
):
    api_client.force_login(save_bulk_user)
    url = reverse("api-1-save-origin-bulk")

    resp = check_api_post_responses(
        api_client,
        url,
        HTTP_CONTENT_TYPE=content_type,
        data=malformed_data,
        status_code=400,
    )
    assert_contains(resp, "malformed, please check provided values.", status_code=400)


def test_save_bulk_post_invalid_origin_url(api_client, save_bulk_user):
    api_client.force_login(save_bulk_user)
    url = reverse("api-1-save-origin-bulk")
    invalid_origin_url = "https//git.example.org/user/project"
    resp = check_api_post_responses(
        api_client,
        url,
        HTTP_CONTENT_TYPE="text/csv",
        data=f"{invalid_origin_url},git\n",
        status_code=400,
    )
    assert resp.data == {
        "status": "rejected",
        "reason": "Some origins data could not be validated.",
        "rejected_origins": [
            {
                "origin": {
                    "origin_url": invalid_origin_url,
                    "visit_type": "git",
                },
                "rejection_reason": (
                    f"The provided origin URL '{invalid_origin_url}' " "is not valid!"
                ),
            }
        ],
    }


def test_save_bulk_post_invalid_visit_type(api_client, save_bulk_user):
    api_client.force_login(save_bulk_user)
    url = reverse("api-1-save-origin-bulk")
    origin_url = "https://git.example.org/user/project"
    invalid_visit_type = "foo"
    resp = check_api_post_responses(
        api_client,
        url,
        HTTP_CONTENT_TYPE="text/csv",
        data=f"{origin_url},{invalid_visit_type}\n",
        status_code=400,
    )
    assert resp.data == {
        "status": "rejected",
        "reason": "Some origins data could not be validated.",
        "rejected_origins": [
            {
                "origin": {
                    "origin_url": origin_url,
                    "visit_type": invalid_visit_type,
                },
                "rejection_reason": f"Visit type '{invalid_visit_type}' is not supported.",
            }
        ],
    }


@pytest.mark.parametrize(
    "content_type, origins_data",
    [
        (
            "text/csv",
            b"https://git.example.org/user/project,git\nhttps://svn.example.org/user/project,svn",
        ),
        (
            "application/json",
            json.dumps(
                [
                    {
                        "origin_url": "https://git.example.org/user/project",
                        "visit_type": "git",
                    },
                    {
                        "origin_url": "https://svn.example.org/user/project",
                        "visit_type": "svn",
                    },
                ]
            ),
        ),
        (
            "application/yaml",
            yaml.dump(
                [
                    {
                        "origin_url": "https://git.example.org/user/project",
                        "visit_type": "git",
                    },
                    {
                        "origin_url": "https://svn.example.org/user/project",
                        "visit_type": "svn",
                    },
                ]
            ),
        ),
    ],
    ids=["CSV data", "JSON data", "YAML data"],
)
def test_save_bulk_post_valid_origins(
    api_client, save_bulk_user, swh_scheduler, content_type, origins_data
):
    api_client.force_login(save_bulk_user)
    url = reverse("api-1-save-origin-bulk")
    api_resp = check_api_post_responses(
        api_client,
        url,
        HTTP_CONTENT_TYPE=content_type,
        data=origins_data,
        status_code=200,
    )

    assert api_resp.data["status"] == "accepted"

    origins_list_url = reverse(
        "save-origin-bulk-origins-list",
        url_args={"request_id": api_resp.data["request_id"]},
    )

    resp = check_http_get_response(api_client, origins_list_url, status_code=200)

    expected_origins = [
        {"origin_url": "https://git.example.org/user/project", "visit_type": "git"},
        {"origin_url": "https://svn.example.org/user/project", "visit_type": "svn"},
    ]

    assert json.loads(resp.content) == expected_origins

    resp = check_http_get_response(api_client, origins_list_url, status_code=200)


def test_save_bulk_post_with_invalid_origins(api_client, save_bulk_user):
    origins_data = [
        {
            "origin_url": "https://git.example.org/user/project",
            "visit_type": "gi",
        },
        {
            "origin_url": "https://svn.example.org/user/project",
            "visit_type": "svn",
        },
        {
            "origin_url": "https//hg.example.org/user/project",
            "visit_type": "hg",
        },
    ]

    api_client.force_login(save_bulk_user)
    url = reverse("api-1-save-origin-bulk")
    api_resp = check_api_post_responses(
        api_client,
        url,
        data=origins_data,
        status_code=400,
    )

    assert api_resp.data == {
        "status": "rejected",
        "reason": "Some origins data could not be validated.",
        "rejected_origins": [
            {
                "origin": {
                    "origin_url": "https//hg.example.org/user/project",
                    "visit_type": "hg",
                },
                "rejection_reason": (
                    "The provided origin URL 'https//hg.example.org/user/project' is not valid!"
                ),
            },
            {
                "origin": {
                    "origin_url": "https://git.example.org/user/project",
                    "visit_type": "gi",
                },
                "rejection_reason": "Visit type 'gi' is not supported.",
            },
        ],
    }
