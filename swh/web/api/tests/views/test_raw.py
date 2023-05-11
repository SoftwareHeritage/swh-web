# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import hashlib

import pytest

from swh.model.hashutil import hash_to_bytes
from swh.web.api.throttling import SwhWebUserRateThrottle
from swh.web.settings.tests import api_raw_object_rate
from swh.web.tests.helpers import check_api_get_responses, check_http_get_response
from swh.web.utils import reverse


@pytest.mark.django_db
def test_api_raw_not_found(api_client, unknown_core_swhid, staff_user):
    api_client.force_login(staff_user)
    url = reverse("api-1-raw-object", url_args={"swhid": str(unknown_core_swhid)})
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": f"Object with id {unknown_core_swhid} not found.",
    }


def _test_api_raw_hash(api_client, regular_user, archive_data, object_id, object_ty):
    api_client.force_login(regular_user)
    url = reverse(
        "api-1-raw-object",
        url_args={"swhid": f"swh:1:{object_ty}:{object_id}"},
    )

    rv = check_http_get_response(api_client, url, status_code=200)
    assert rv["Content-Type"] == "application/octet-stream"
    assert (
        rv["Content-disposition"]
        == f"attachment; filename=swh_1_{object_ty}_{object_id}_raw"
    )
    sha1_git = hashlib.new("sha1", rv.content).digest()
    assert sha1_git == hash_to_bytes(object_id)


@pytest.mark.django_db
def test_api_raw_content(api_client, archive_data, content, regular_user):
    _test_api_raw_hash(
        api_client, regular_user, archive_data, content["sha1_git"], "cnt"
    )


@pytest.mark.django_db
def test_api_raw_directory(api_client, archive_data, directory, regular_user):
    _test_api_raw_hash(api_client, regular_user, archive_data, directory, "dir")


@pytest.mark.django_db
def test_api_raw_revision(api_client, archive_data, revision, regular_user):
    _test_api_raw_hash(api_client, regular_user, archive_data, revision, "rev")


@pytest.mark.django_db
def test_api_raw_release(api_client, archive_data, release, regular_user):
    _test_api_raw_hash(api_client, regular_user, archive_data, release, "rel")


@pytest.mark.django_db
def test_api_raw_snapshot(api_client, archive_data, snapshot, regular_user):
    _test_api_raw_hash(api_client, regular_user, archive_data, snapshot, "snp")


@pytest.mark.django_db
def test_api_raw_rate_limit(api_client, revision, regular_user):

    api_client.force_login(regular_user)

    url = reverse(
        "api-1-raw-object",
        url_args={"swhid": f"swh:1:rev:{revision}"},
    )

    for _ in range(api_raw_object_rate * SwhWebUserRateThrottle.NUM_REQUESTS_FACTOR):
        check_http_get_response(api_client, url, status_code=200)

    check_http_get_response(api_client, url, status_code=429)
