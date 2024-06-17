# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import uuid

import pytest

from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.helpers import check_api_post_response, check_http_get_response
from swh.web.utils import reverse

pytestmark = pytest.mark.django_db

NB_SUBMITTED_ORIGINS = 100


@pytest.fixture
def submitted_origins(api_client, save_bulk_user, swh_scheduler):
    api_client.force_login(save_bulk_user)
    url = reverse("api-1-save-origin-bulk")
    origins = [
        {
            "origin_url": f"https://git.example.org/project{i:02d}.git",
            "visit_type": "git",
        }
        for i in range(NB_SUBMITTED_ORIGINS)
    ]
    resp = check_api_post_response(api_client, url, data=origins, status_code=200)
    return origins, resp.data["request_id"]


def test_api_save_bulk_origins_list_request_not_found(client):
    unknown_request_id = str(uuid.uuid4())
    url = reverse(
        "save-origin-bulk-origins-list", url_args={"request_id": unknown_request_id}
    )
    resp = check_http_get_response(client, url, status_code=404)
    assert_contains(
        resp,
        f"Bulk save request with id {unknown_request_id} not found!",
        status_code=404,
    )


@pytest.mark.parametrize("per_page", [NB_SUBMITTED_ORIGINS, NB_SUBMITTED_ORIGINS // 10])
def test_api_save_bulk_origins_list(client, submitted_origins, per_page):
    origins, request_id = submitted_origins
    nb_pages = NB_SUBMITTED_ORIGINS // per_page
    origins_list = []
    for i in range(1, nb_pages + 1):
        url = reverse(
            "save-origin-bulk-origins-list",
            url_args={"request_id": request_id},
            query_params={"page": i, "per_page": per_page},
        )
        resp = check_http_get_response(client, url, status_code=200)
        origins_list += json.loads(resp.content)

    assert origins_list == origins

    url = reverse(
        "save-origin-bulk-origins-list",
        url_args={"request_id": request_id},
        query_params={"page": nb_pages + 1, "per_page": per_page},
    )
    resp = check_http_get_response(client, url, status_code=200)
    assert json.loads(resp.content) == []
