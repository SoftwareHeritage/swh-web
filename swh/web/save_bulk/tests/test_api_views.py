# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import timedelta
import json
import random
import uuid

import pytest
import yaml

from swh.scheduler.model import LastVisitStatus, ListedOrigin, OriginVisitStats
from swh.storage.utils import now
from swh.web.save_bulk.models import SaveBulkOrigin, SaveBulkRequest
from swh.web.tests.data import random_sha1_bytes
from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.helpers import (
    check_api_get_responses,
    check_api_post_responses,
    check_http_get_response,
)
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


def test_save_bulk_post_valid_duplicated_origins(
    api_client,
    save_bulk_user,
    swh_scheduler,
):
    origins_data = [
        {
            "origin_url": "https://git.example.org/user/project",
            "visit_type": "git",
        },
        {
            "origin_url": "https://svn.example.org/user/project",
            "visit_type": "svn",
        },
    ]
    api_client.force_login(save_bulk_user)
    url = reverse("api-1-save-origin-bulk")
    api_resp = check_api_post_responses(
        api_client,
        url,
        HTTP_CONTENT_TYPE="application/json",
        data=json.dumps(origins_data + origins_data),
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


def test_save_bulk_request_info_anonymous(api_client):
    url = reverse(
        "api-1-save-origin-bulk-request-info",
        url_args={"request_id": str(uuid.uuid4())},
    )
    resp = check_api_get_responses(api_client, url, status_code=401)
    assert resp.data == {
        "exception": "UnauthorizedExc",
        "reason": "This API endpoint requires authentication.",
    }


def test_save_bulk_request_info_user_without_permission(api_client, regular_user):
    api_client.force_login(regular_user)
    url = reverse(
        "api-1-save-origin-bulk-request-info",
        url_args={"request_id": str(uuid.uuid4())},
    )
    resp = check_api_get_responses(api_client, url, status_code=403)
    assert resp.data == {
        "exception": "ForbiddenExc",
        "reason": "This API endpoint requires a special user permission.",
    }


def test_save_bulk_request_info_not_found(api_client, save_bulk_user):
    api_client.force_login(save_bulk_user)
    unknown_request_id = str(uuid.uuid4())
    url = reverse(
        "api-1-save-origin-bulk-request-info",
        url_args={"request_id": unknown_request_id},
    )
    resp = check_api_get_responses(api_client, url, status_code=404)

    assert resp.data == {
        "exception": "NotFoundExc",
        "reason": (f"Save bulk request with id {unknown_request_id} not found!"),
    }


def test_save_bulk_request_info_invalid_user(api_client, save_bulk_user):
    save_bulk_request = SaveBulkRequest.objects.create(user_id=str(1234))
    api_client.force_login(save_bulk_user)
    url = reverse(
        "api-1-save-origin-bulk-request-info",
        url_args={"request_id": str(save_bulk_request.id)},
    )
    resp = check_api_get_responses(api_client, url, status_code=403)

    assert resp.data == {
        "exception": "ForbiddenExc",
        "reason": (
            f"Save bulk request with id {save_bulk_request.id} was not "
            "created with your user account!"
        ),
    }


NB_SUBMITTED_ORIGINS = 2000


@pytest.fixture
def save_bulk_request_info_submitted_origins(save_bulk_user):
    """Simulate a save bulk request was submitted and the bulk save lister processed
    the origins list (rejecting some origins due to HTTP errors)."""

    save_bulk_request = SaveBulkRequest.objects.create(user_id=str(save_bulk_user.id))
    request_id = str(save_bulk_request.id)

    submitted_origins = [
        {
            "origin_url": f"https://git.example.org/user/project{i:03d}",
            "visit_type": "git",
        }
        for i in range(NB_SUBMITTED_ORIGINS)
    ]

    save_bulk_origins = SaveBulkOrigin.objects.bulk_create(
        [SaveBulkOrigin(**origin) for origin in submitted_origins]
    )
    SaveBulkOrigin.requests.through.objects.bulk_create(
        [
            SaveBulkOrigin.requests.through(
                savebulkorigin_id=save_bulk_origin.id,
                savebulkrequest_id=save_bulk_request.id,
            )
            for save_bulk_origin in save_bulk_origins
        ]
    )
    return request_id, submitted_origins


@pytest.fixture
def save_bulk_request_info_lister_data(
    swh_scheduler, save_bulk_request_info_submitted_origins
):
    """Simulate a save bulk request was submitted and the bulk save lister processed
    the origins list (rejecting some origins due to HTTP errors)."""

    request_id, submitted_origins = save_bulk_request_info_submitted_origins

    rejected_origins = random.sample(submitted_origins, k=100)
    rejected_origin_urls = {origin["origin_url"] for origin in rejected_origins}

    lister = swh_scheduler.get_or_create_lister(
        name="save-bulk", instance_name=request_id
    )

    lister.current_state = {
        "rejected_origins": [
            {
                **origin,
                "reason": "An HTTP error occurred when requesting origin URL: 404 - Not Found",
            }
            for origin in rejected_origins
        ]
    }

    swh_scheduler.update_lister(lister)

    accepted_origins = [
        origin
        for origin in submitted_origins
        if origin["origin_url"] not in rejected_origin_urls
    ]

    for origin in accepted_origins:
        swh_scheduler.record_listed_origins(
            [
                ListedOrigin(
                    lister_id=lister.id,
                    url=origin["origin_url"],
                    visit_type=origin["visit_type"],
                )
            ]
        )
        scheduling_date = now()
        visit_date = scheduling_date + timedelta(hours=1)
        swh_scheduler.origin_visit_stats_upsert(
            [
                OriginVisitStats(
                    url=origin["origin_url"],
                    visit_type=origin["visit_type"],
                    last_successful=visit_date,
                    last_visit=visit_date,
                    last_scheduled=scheduling_date,
                    last_snapshot=random_sha1_bytes(),
                    last_visit_status=LastVisitStatus.successful,
                )
            ]
        )

    return request_id, accepted_origins, rejected_origins


def test_save_bulk_request_info_successful_before_lister_processing(
    api_client, save_bulk_user, save_bulk_request_info_submitted_origins, swh_scheduler
):
    request_id, submitted_origins = save_bulk_request_info_submitted_origins
    api_client.force_login(save_bulk_user)
    url = reverse(
        "api-1-save-origin-bulk-request-info",
        url_args={"request_id": request_id},
        query_params={"per_page": NB_SUBMITTED_ORIGINS},
    )
    resp = check_api_get_responses(api_client, url, status_code=200)

    assert len(resp.data) == len(submitted_origins)
    assert all(
        submitted_origin["status"] == "pending"
        and submitted_origin["last_scheduling_date"] is None
        and submitted_origin["last_visit_date"] is None
        and submitted_origin["last_visit_status"] is None
        and submitted_origin["last_snapshot_swhid"] is None
        and submitted_origin["rejection_reason"] is None
        and submitted_origin["browse_url"] is None
        for submitted_origin in resp.data
    )


@pytest.fixture(params=["save_bulk_user", "staff_user"])
def save_bulk_request_info_user(request):
    return request.getfixturevalue(request.param)


def test_save_bulk_request_info_successful_after_lister_processing_no_pagination(
    api_client, save_bulk_request_info_user, save_bulk_request_info_lister_data
):
    api_client.force_login(save_bulk_request_info_user)
    request_id, accepted_origins, rejected_origins = save_bulk_request_info_lister_data

    url = reverse(
        "api-1-save-origin-bulk-request-info",
        url_args={"request_id": request_id},
        query_params={"per_page": NB_SUBMITTED_ORIGINS},
    )
    resp = check_api_get_responses(api_client, url, status_code=200)
    submitted_origins_info = resp.data

    assert len(submitted_origins_info) == len(accepted_origins) + len(rejected_origins)

    assert {
        origin_info["origin_url"]
        for origin_info in submitted_origins_info
        if origin_info["status"] == "accepted"
    } == {origin["origin_url"] for origin in accepted_origins}

    assert {
        origin_info["origin_url"]
        for origin_info in submitted_origins_info
        if origin_info["status"] == "rejected"
    } == {origin["origin_url"] for origin in rejected_origins}


def test_save_bulk_request_info_successful_after_lister_processing_pagination(
    api_client, save_bulk_request_info_user, save_bulk_request_info_lister_data
):
    request_id, accepted_origins, rejected_origins = save_bulk_request_info_lister_data

    api_client.force_login(save_bulk_request_info_user)

    nb_pages = 10
    per_page = NB_SUBMITTED_ORIGINS // nb_pages

    submitted_origins_info = []

    for i in range(1, nb_pages + 2):
        url = reverse(
            "api-1-save-origin-bulk-request-info",
            url_args={"request_id": request_id},
            query_params={"page": i, "per_page": per_page},
        )
        resp = check_api_get_responses(api_client, url, status_code=200)
        submitted_origins_info += resp.data
        if i < nb_pages:
            assert (
                reverse(
                    "api-1-save-origin-bulk-request-info",
                    url_args={"request_id": request_id},
                    query_params={"page": i + 1, "per_page": per_page},
                    request=resp.wsgi_request,
                )
                in resp["Link"]
            )
        if i > 1 and i <= nb_pages:
            assert (
                reverse(
                    "api-1-save-origin-bulk-request-info",
                    url_args={"request_id": request_id},
                    query_params={"page": i - 1, "per_page": per_page},
                    request=resp.wsgi_request,
                )
                in resp["Link"]
            )
        if i > nb_pages:
            assert "Link" not in resp

    assert len(submitted_origins_info) == len(accepted_origins) + len(rejected_origins)

    assert {
        origin_info["origin_url"]
        for origin_info in submitted_origins_info
        if origin_info["status"] == "accepted"
    } == {origin["origin_url"] for origin in accepted_origins}

    assert {
        origin_info["origin_url"]
        for origin_info in submitted_origins_info
        if origin_info["status"] == "rejected"
    } == {origin["origin_url"] for origin in rejected_origins}

    for origin in submitted_origins_info:
        if origin["status"] == "rejected":
            assert origin["rejection_reason"] is not None


def test_save_bulk_request_info_visit_date_before_request_date(
    api_client, save_bulk_user, swh_scheduler
):
    save_bulk_request = SaveBulkRequest.objects.create(user_id=str(save_bulk_user.id))
    request_id = str(save_bulk_request.id)

    origin_url = "https://git.example.org/user/project"
    visit_type = "git"
    save_bulk_origin = SaveBulkOrigin.objects.create(
        origin_url=origin_url,
        visit_type=visit_type,
    )
    save_bulk_origin.requests.set([save_bulk_request])

    lister = swh_scheduler.get_or_create_lister(
        name="save-bulk", instance_name=request_id
    )

    swh_scheduler.record_listed_origins(
        [
            ListedOrigin(
                lister_id=lister.id,
                url=origin_url,
                visit_type=visit_type,
            )
        ]
    )

    scheduling_date = now()
    visit_date = save_bulk_request.request_date - timedelta(days=10)
    swh_scheduler.origin_visit_stats_upsert(
        [
            OriginVisitStats(
                url=save_bulk_origin.origin_url,
                visit_type=save_bulk_origin.visit_type,
                last_successful=visit_date,
                last_visit=visit_date,
                last_scheduled=scheduling_date,
                last_snapshot=random_sha1_bytes(),
                last_visit_status=LastVisitStatus.successful,
            )
        ]
    )

    api_client.force_login(save_bulk_user)
    url = reverse(
        "api-1-save-origin-bulk-request-info",
        url_args={"request_id": request_id},
    )
    resp = check_api_get_responses(api_client, url, status_code=200)
    assert resp.data == [
        {
            "origin_url": origin_url,
            "visit_type": visit_type,
            "status": "accepted",
            "last_scheduling_date": scheduling_date.isoformat(),
            "last_visit_date": None,
            "last_visit_status": None,
            "last_snapshot_swhid": None,
            "rejection_reason": None,
            "browse_url": None,
        }
    ]


NB_SAVE_BULK_REQUESTS = 100


@pytest.fixture
def user_save_bulk_requests(save_bulk_user):
    SaveBulkRequest.objects.bulk_create(
        [
            SaveBulkRequest(user_id=str(save_bulk_user.id))
            for _ in range(NB_SAVE_BULK_REQUESTS)
        ]
    )
    return SaveBulkRequest.objects


def test_list_save_bulk_requests_anonymous(api_client):
    url = reverse("api-1-save-origin-bulk-requests")
    resp = check_api_get_responses(api_client, url, status_code=401)
    assert resp.data == {
        "exception": "UnauthorizedExc",
        "reason": "This API endpoint requires authentication.",
    }


def test_list_save_bulk_requests_user_without_permission(api_client, regular_user):
    api_client.force_login(regular_user)
    url = reverse("api-1-save-origin-bulk-requests")
    resp = check_api_get_responses(api_client, url, status_code=403)
    assert resp.data == {
        "exception": "ForbiddenExc",
        "reason": "This API endpoint requires a special user permission.",
    }


def test_list_save_bulk_requests(api_client, save_bulk_user, user_save_bulk_requests):
    api_client.force_login(save_bulk_user)

    per_page = 10
    nb_pages = NB_SAVE_BULK_REQUESTS // per_page

    user_save_bulk_requests = user_save_bulk_requests.order_by("-request_date")

    for page in range(1, nb_pages + 2):
        url = reverse(
            "api-1-save-origin-bulk-requests",
            query_params={"per_page": per_page, "page": page},
        )

        resp = check_api_get_responses(api_client, url, status_code=200)

        expected_data = [
            {
                "request_id": str(save_bulk_request.id),
                "request_date": save_bulk_request.request_date.isoformat(),
                "request_info_url": reverse(
                    "api-1-save-origin-bulk-request-info",
                    url_args={"request_id": str(save_bulk_request.id)},
                    request=resp.wsgi_request,
                ),
            }
            for save_bulk_request in user_save_bulk_requests[
                (page - 1) * per_page : page * per_page
            ]
        ]

        assert resp.data == expected_data
