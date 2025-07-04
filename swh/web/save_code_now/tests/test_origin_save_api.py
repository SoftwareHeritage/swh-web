# Copyright (C) 2018-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta, timezone
import uuid

import pytest

from django.core.exceptions import ObjectDoesNotExist

from swh.model.hashutil import hash_to_bytes
from swh.model.swhids import CoreSWHID, ObjectType
from swh.web.api.throttling import SwhWebUserRateThrottle
from swh.web.auth.utils import (
    API_SAVE_ORIGIN_PERMISSION,
    SWH_AMBASSADOR_PERMISSION,
    get_or_create_django_permission,
)
from swh.web.save_code_now.models import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_REQUEST_PENDING,
    SAVE_REQUEST_REJECTED,
    SAVE_TASK_FAILED,
    SAVE_TASK_NOT_CREATED,
    SAVE_TASK_PENDING,
    SAVE_TASK_RUNNING,
    SAVE_TASK_SCHEDULED,
    SAVE_TASK_SUCCEEDED,
    VISIT_STATUS_FAILED,
    VISIT_STATUS_FULL,
    SaveAuthorizedOrigin,
    SaveOriginRequest,
    SaveUnauthorizedOrigin,
)
from swh.web.settings.tests import save_origin_rate_post
from swh.web.tests.helpers import (
    check_api_get_responses,
    check_api_post_response,
    check_api_post_responses,
)
from swh.web.utils import reverse
from swh.web.utils.typing import OriginExistenceCheckInfo

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def populated_db():
    SaveAuthorizedOrigin.objects.create(url="https://github.com/"),
    SaveAuthorizedOrigin.objects.create(url="https://gitlab.com/"),
    SaveUnauthorizedOrigin.objects.create(url="https://github.com/user/illegal_repo")
    SaveUnauthorizedOrigin.objects.create(url="https://gitlab.com/user_to_exclude")


def _save_origin_api_url(
    visit_type: str, origin_url: str, use_query_params: bool
) -> str:
    params = {
        "visit_type": visit_type,
        "origin_url": origin_url,
    }
    if use_query_params:
        return reverse("api-1-save-origin", query_params=params)
    else:
        return reverse("api-1-save-origin", url_args=params)


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_invalid_visit_type(api_client, swh_scheduler, use_query_params):
    url = _save_origin_api_url(
        visit_type="foo",
        origin_url="https://github.com/torvalds/linux",
        use_query_params=use_query_params,
    )
    check_api_get_responses(api_client, url, status_code=400)


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_invalid_origin_url(api_client, swh_scheduler, use_query_params):
    url = _save_origin_api_url(
        visit_type="git",
        origin_url="bar",
        use_query_params=use_query_params,
    )
    check_api_get_responses(api_client, url, status_code=400)


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_url_url_in_origin_url(api_client, swh_scheduler, use_query_params):
    url = _save_origin_api_url(
        visit_type="git",
        origin_url="https://example.org/user/project/url/url/",
        use_query_params=use_query_params,
    )
    check_api_post_responses(api_client, url, status_code=200)


def check_created_save_request_status(
    api_client,
    mocker,
    origin_url,
    expected_request_status,
    expected_task_status=None,
    visit_date=None,
    use_query_params=False,
):
    mock_origin_exists = mocker.patch("swh.web.save_code_now.origin_save.origin_exists")
    mock_origin_exists.return_value = OriginExistenceCheckInfo(
        origin_url=origin_url, exists=True, last_modified=None, content_length=None
    )

    url = _save_origin_api_url(
        visit_type="git",
        origin_url=origin_url,
        use_query_params=use_query_params,
    )

    mock_visit_date = mocker.patch(
        ("swh.web.save_code_now.origin_save._get_visit_info_for_save_request")
    )
    mock_visit_date.return_value = (visit_date, None, None)

    if expected_request_status != SAVE_REQUEST_REJECTED:
        response = check_api_post_responses(api_client, url, data=None, status_code=200)
        assert response.data["save_request_status"] == expected_request_status
        assert response.data["save_task_status"] == expected_task_status
        assert response.data["from_webhook"] is False
        assert response.data["webhook_origin"] is None
        assert "id" in response.data
        assert response.data["request_url"] == reverse(
            "api-1-save-origin",
            url_args={"request_id": response.data["id"]},
            request=response.wsgi_request,
        )
    else:
        check_api_post_responses(api_client, url, data=None, status_code=403)


def check_save_request_status(
    api_client,
    mocker,
    swh_scheduler,
    origin_url,
    expected_request_status,
    expected_task_status,
    scheduler_task_status="next_run_not_scheduled",
    scheduler_task_run_status=None,
    visit_date=None,
    visit_status=None,
    snapshot_id=None,
    error_msg=None,
    use_query_params=False,
):
    if expected_task_status != SAVE_TASK_NOT_CREATED:
        task = swh_scheduler.search_tasks()[0]
        backend_id = str(uuid.uuid4())

    if scheduler_task_status != "next_run_not_scheduled":
        swh_scheduler.schedule_task_run(task.id, backend_id)

    if scheduler_task_run_status is not None:
        swh_scheduler.start_task_run(backend_id)
        metadata = {}
        if error_msg:
            metadata["error"] = error_msg
        task_run = swh_scheduler.end_task_run(
            backend_id, scheduler_task_run_status, metadata
        )

    url = _save_origin_api_url(
        visit_type="git",
        origin_url=origin_url,
        use_query_params=use_query_params,
    )

    mock_visit_date = mocker.patch(
        ("swh.web.save_code_now.origin_save._get_visit_info_for_save_request")
    )
    mock_visit_date.return_value = (visit_date, visit_status, snapshot_id)
    response = check_api_get_responses(api_client, url, status_code=200)
    save_request_data = response.data[0]

    assert save_request_data["save_request_status"] == expected_request_status
    assert save_request_data["save_task_status"] == expected_task_status
    assert save_request_data["visit_status"] == visit_status
    assert save_request_data["from_webhook"] is False
    assert save_request_data["webhook_origin"] is None
    assert "id" in save_request_data
    assert save_request_data["request_url"] == reverse(
        "api-1-save-origin",
        url_args={"request_id": save_request_data["id"]},
        request=response.wsgi_request,
    )

    if error_msg:
        assert save_request_data["metadata"] == {"error": error_msg}

    check_api_get_responses(
        api_client, save_request_data["request_url"], status_code=200
    )
    if snapshot_id:
        assert save_request_data["snapshot_swhid"] == str(
            CoreSWHID(
                object_type=ObjectType.SNAPSHOT, object_id=hash_to_bytes(snapshot_id)
            )
        )
        assert save_request_data["snapshot_url"] == reverse(
            "api-1-snapshot",
            url_args={"snapshot_id": snapshot_id},
            request=response.wsgi_request,
        )

    if scheduler_task_run_status is not None:
        # Check that save task status is still available when
        # the scheduler task has been archived
        swh_scheduler.delete_archived_tasks(
            [{"task_id": task.id, "task_run_id": task_run.id}]
        )
        response = check_api_get_responses(api_client, url, status_code=200)
        save_request_data = response.data[0]
        assert save_request_data["save_task_status"] == expected_task_status
        assert save_request_data["visit_status"] == visit_status


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_save_request_rejected(api_client, mocker, swh_scheduler, use_query_params):
    origin_url = "https://github.com/user/illegal_repo"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_REJECTED,
        use_query_params=use_query_params,
    )
    check_save_request_status(
        api_client,
        mocker,
        swh_scheduler,
        origin_url,
        expected_request_status=SAVE_REQUEST_REJECTED,
        expected_task_status=SAVE_TASK_NOT_CREATED,
        use_query_params=use_query_params,
    )


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_save_request_pending(api_client, mocker, swh_scheduler, use_query_params):
    origin_url = "https://unkwownforge.com/user/repo"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_PENDING,
        expected_task_status=SAVE_TASK_NOT_CREATED,
        use_query_params=use_query_params,
    )
    check_save_request_status(
        api_client,
        mocker,
        swh_scheduler,
        origin_url,
        expected_request_status=SAVE_REQUEST_PENDING,
        expected_task_status=SAVE_TASK_NOT_CREATED,
        use_query_params=use_query_params,
    )


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_save_request_scheduled(api_client, mocker, swh_scheduler, use_query_params):
    origin_url = "https://github.com/Kitware/CMake"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_PENDING,
        use_query_params=use_query_params,
    )
    check_save_request_status(
        api_client,
        mocker,
        swh_scheduler,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_SCHEDULED,
        scheduler_task_status="next_run_scheduled",
        scheduler_task_run_status="scheduled",
        use_query_params=use_query_params,
    )


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_save_request_completed(
    api_client, mocker, swh_scheduler, snapshot, use_query_params
):
    origin_url = "https://github.com/Kitware/CMake"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_PENDING,
        use_query_params=use_query_params,
    )
    visit_date = datetime.now(tz=timezone.utc) + timedelta(hours=1)
    check_save_request_status(
        api_client,
        mocker,
        swh_scheduler,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_SUCCEEDED,
        scheduler_task_status="completed",
        scheduler_task_run_status="eventful",
        visit_date=visit_date,
        visit_status=VISIT_STATUS_FULL,
        snapshot_id=snapshot,
        use_query_params=use_query_params,
    )


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_save_request_failed(api_client, mocker, swh_scheduler, use_query_params):
    origin_url = "https://gitlab.com/inkscape/inkscape"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_PENDING,
        use_query_params=use_query_params,
    )
    check_save_request_status(
        api_client,
        mocker,
        swh_scheduler,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_FAILED,
        scheduler_task_status="disabled",
        scheduler_task_run_status="failed",
        visit_status=VISIT_STATUS_FAILED,
        error_msg="Something went wrong",
        use_query_params=use_query_params,
    )


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_no_duplicate_if_already_scheduled(
    api_client, mocker, swh_scheduler, use_query_params
):
    origin_url = "https://github.com/webpack/webpack"

    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_PENDING,
        use_query_params=use_query_params,
    )

    sors = list(
        SaveOriginRequest.objects.filter(visit_type="git", origin_url=origin_url)
    )
    assert len(sors) == 1

    check_save_request_status(
        api_client,
        mocker,
        swh_scheduler,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_SCHEDULED,
        scheduler_task_status="next_run_scheduled",
        scheduler_task_run_status="scheduled",
        use_query_params=use_query_params,
    )

    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_SCHEDULED,
        use_query_params=use_query_params,
    )
    sors = list(
        SaveOriginRequest.objects.filter(visit_type="git", origin_url=origin_url)
    )
    assert len(sors) == 1


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_if_previous_one_is_running(
    api_client, mocker, swh_scheduler, use_query_params
):
    origin_url = "https://github.com/webpack/webpack"

    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_PENDING,
        use_query_params=use_query_params,
    )

    check_save_request_status(
        api_client,
        mocker,
        swh_scheduler,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_RUNNING,
        scheduler_task_status="next_run_scheduled",
        scheduler_task_run_status="started",
        use_query_params=use_query_params,
    )

    sors = list(
        SaveOriginRequest.objects.filter(visit_type="git", origin_url=origin_url)
    )
    assert len(sors) == 1

    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_PENDING,
        use_query_params=use_query_params,
    )

    sors = list(
        SaveOriginRequest.objects.filter(visit_type="git", origin_url=origin_url)
    )
    assert len(sors) == 2


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_get_save_requests_unknown_origin(api_client, swh_scheduler, use_query_params):
    unknown_origin_url = "https://gitlab.com/foo/bar"
    url = _save_origin_api_url(
        visit_type="git",
        origin_url=unknown_origin_url,
        use_query_params=use_query_params,
    )
    response = check_api_get_responses(api_client, url, status_code=404)
    assert response.data == {
        "exception": "NotFoundExc",
        "reason": (
            "No save requests found for visit of type git on origin with url %s."
        )
        % unknown_origin_url,
    }


_visit_type = "git"
_origin_url = "https://github.com/python/cpython"


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_save_requests_rate_limit(api_client, swh_scheduler, use_query_params):
    url = _save_origin_api_url(
        visit_type=_visit_type,
        origin_url=_origin_url,
        use_query_params=use_query_params,
    )

    for _ in range(save_origin_rate_post):
        check_api_post_response(api_client, url, status_code=200)

    check_api_post_response(api_client, url, status_code=429)


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_save_requests_no_rate_limit_if_permission(
    api_client, regular_user, swh_scheduler, use_query_params
):
    regular_user.user_permissions.add(
        get_or_create_django_permission(API_SAVE_ORIGIN_PERMISSION)
    )

    assert regular_user.has_perm(API_SAVE_ORIGIN_PERMISSION)

    api_client.force_login(regular_user)

    url = _save_origin_api_url(
        visit_type=_visit_type,
        origin_url=_origin_url,
        use_query_params=use_query_params,
    )

    for _ in range(save_origin_rate_post * SwhWebUserRateThrottle.NUM_REQUESTS_FACTOR):
        check_api_post_response(api_client, url, status_code=200)

    check_api_post_response(api_client, url, status_code=200)


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_save_request_unknown_repo_with_permission(
    api_client, regular_user, mocker, swh_scheduler, use_query_params
):
    regular_user.user_permissions.add(
        get_or_create_django_permission(API_SAVE_ORIGIN_PERMISSION)
    )

    assert regular_user.has_perm(API_SAVE_ORIGIN_PERMISSION)

    api_client.force_login(regular_user)

    origin_url = "https://unkwownforge.org/user/repo"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_PENDING,
        use_query_params=use_query_params,
    )
    check_save_request_status(
        api_client,
        mocker,
        swh_scheduler,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_PENDING,
        use_query_params=use_query_params,
    )


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_save_request_form_server_error(api_client, mocker, use_query_params):
    create_save_origin_request = mocker.patch(
        "swh.web.save_code_now.api_views.create_save_origin_request"
    )
    create_save_origin_request.side_effect = Exception("Server error")

    url = _save_origin_api_url(
        visit_type=_visit_type,
        origin_url=_origin_url,
        use_query_params=use_query_params,
    )

    check_api_post_responses(api_client, url, status_code=500)


@pytest.fixture
def origin_to_review():
    return "https://git.example.org/user/project"


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_pending_review_anonymous_user(
    api_client, origin_to_review, swh_scheduler, use_query_params
):
    url = _save_origin_api_url(
        visit_type="git",
        origin_url=origin_to_review,
        use_query_params=use_query_params,
    )

    response = check_api_post_responses(api_client, url, status_code=200)

    assert response.data["save_request_status"] == SAVE_REQUEST_PENDING

    with pytest.raises(ObjectDoesNotExist):
        SaveAuthorizedOrigin.objects.get(url=origin_to_review)


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_archives_with_ambassador_user(
    api_client,
    keycloak_oidc,
    requests_mock,
    swh_scheduler,
    use_query_params,
):
    swh_scheduler.add_load_archive_task_type()

    keycloak_oidc.realm_permissions = [SWH_AMBASSADOR_PERMISSION]
    oidc_profile = keycloak_oidc.login()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {oidc_profile['refresh_token']}")

    origin_url = "https://somewhere.org/simple"
    artifact_version = "1.2.3"
    artifact_filename = f"tarball-{artifact_version}.tar.gz"
    artifact_url = f"{origin_url}/{artifact_filename}"
    content_length = "100"
    last_modified = "Sun, 21 Aug 2011 16:26:32 GMT"

    requests_mock.head(
        artifact_url,
        status_code=200,
        headers={
            "content-length": content_length,
            "last-modified": last_modified,
        },
    )

    url = _save_origin_api_url(
        visit_type="archives",
        origin_url=origin_url,
        use_query_params=use_query_params,
    )

    response = check_api_post_response(
        api_client,
        url,
        status_code=200,
        data={
            "archives_data": [
                {
                    "artifact_url": artifact_url,
                    "artifact_version": artifact_version,
                }
            ]
        },
    )

    assert response.data["save_request_status"] == SAVE_REQUEST_ACCEPTED

    assert SaveAuthorizedOrigin.objects.get(url=origin_url)


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_archives_missing_artifacts_data(
    api_client, keycloak_oidc, swh_scheduler, use_query_params
):
    swh_scheduler.add_load_archive_task_type()

    keycloak_oidc.realm_permissions = [SWH_AMBASSADOR_PERMISSION]
    oidc_profile = keycloak_oidc.login()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {oidc_profile['refresh_token']}")

    origin_url = "https://somewhere.org/simple"

    url = _save_origin_api_url(
        visit_type="archives",
        origin_url=origin_url,
        use_query_params=use_query_params,
    )

    response = check_api_post_response(
        api_client,
        url,
        status_code=400,
        data={},
    )
    assert "Artifacts data are missing" in response.data["reason"]

    response = check_api_post_response(
        api_client,
        url,
        status_code=400,
        data={"archives_data": [{"artifact_url": "", "arttifact_version": "1.0"}]},
    )
    assert "Missing url or version for an artifact to load" in response.data["reason"]


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_archives_accepted_ambassador_user(
    api_client, origin_to_review, keycloak_oidc, mocker, swh_scheduler, use_query_params
):
    keycloak_oidc.realm_permissions = [SWH_AMBASSADOR_PERMISSION]
    oidc_profile = keycloak_oidc.login()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {oidc_profile['refresh_token']}")

    check_created_save_request_status(
        api_client,
        mocker,
        origin_to_review,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_PENDING,
        use_query_params=use_query_params,
    )

    assert SaveAuthorizedOrigin.objects.get(url=origin_to_review)


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_anonymous_user_no_user_id(
    api_client, swh_scheduler, use_query_params
):
    origin_url = "https://some.git.hosters/user/repo"

    url = _save_origin_api_url(
        visit_type="git",
        origin_url=origin_url,
        use_query_params=use_query_params,
    )

    check_api_post_responses(api_client, url, status_code=200)

    sor = SaveOriginRequest.objects.get(origin_url=origin_url)

    assert sor.user_ids is None


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_authenticated_user_id(
    api_client, keycloak_oidc, swh_scheduler, use_query_params
):
    oidc_profile = keycloak_oidc.login()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {oidc_profile['refresh_token']}")

    origin_url = "https://some.git.hosters/user/repo2"

    url = _save_origin_api_url(
        visit_type="git",
        origin_url=origin_url,
        use_query_params=use_query_params,
    )

    response = check_api_post_response(api_client, url, status_code=200)

    assert response.wsgi_request.user.id is not None

    user_id = str(response.wsgi_request.user.id)
    sor = SaveOriginRequest.objects.get(user_ids=f'"{user_id}"')
    assert sor.user_ids == f'"{user_id}"'


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_pending_save_request_multiple_authenticated_users(
    api_client, swh_scheduler, regular_user, regular_user2, use_query_params
):
    origin_url = "https://some.git.hosters/user/repo3"

    url = _save_origin_api_url(
        visit_type="git",
        origin_url=origin_url,
        use_query_params=use_query_params,
    )

    api_client.force_login(regular_user)
    check_api_post_response(api_client, url, status_code=200)

    api_client.force_login(regular_user2)
    check_api_post_response(api_client, url, status_code=200)

    assert SaveOriginRequest.objects.get(user_ids__contains=f'"{regular_user.id}"')
    assert SaveOriginRequest.objects.get(user_ids__contains=f'"{regular_user2.id}"')


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_reject_origin_url_with_password(api_client, swh_scheduler, use_query_params):
    url = _save_origin_api_url(
        visit_type="git",
        origin_url="https://user:pass@git.example.org/user/repo",
        use_query_params=use_query_params,
    )
    resp = check_api_post_responses(api_client, url, status_code=400)

    assert resp.data == {
        "exception": "BadInputExc",
        "reason": (
            "The provided origin URL contains a password and cannot "
            "be accepted for security reasons."
        ),
    }


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_accept_origin_url_with_username_but_without_password(
    api_client, swh_scheduler, use_query_params
):
    url = _save_origin_api_url(
        visit_type="git",
        origin_url="https://user@git.example.org/user/repo",
        use_query_params=use_query_params,
    )
    check_api_post_responses(api_client, url, status_code=200)


@pytest.mark.parametrize(
    "origin_url",
    [
        "https://anonymous:anonymous@git.example.org/user/repo",
        "https://anonymous:@git.example.org/user/repo",
        "https://anonymous:password@git.example.org/user/repo",
    ],
)
def test_accept_origin_url_with_anonymous_credentials(
    api_client, swh_scheduler, origin_url
):
    url = reverse(
        "api-1-save-origin",
        url_args={
            "visit_type": "git",
            "origin_url": origin_url,
        },
    )
    check_api_post_responses(api_client, url, status_code=200)


def test_get_save_request_not_found(api_client):
    url = reverse("api-1-save-origin", url_args={"request_id": 1})
    check_api_get_responses(api_client, url, status_code=404)


def test_create_save_request_mangled_origin_url(api_client, swh_scheduler):
    origin_url = "https://some.git.hosters/user/repo"
    url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": "git", "origin_url": origin_url.replace("://", ":/")},
    )

    check_api_post_responses(api_client, url, status_code=200)

    sor = SaveOriginRequest.objects.get(origin_url=origin_url)

    assert sor.user_ids is None


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_origin_url_to_quote(api_client, use_query_params):
    origin_url = "https://example.org/user/project name"

    url = _save_origin_api_url(
        visit_type="git",
        origin_url=origin_url,
        use_query_params=use_query_params,
    )

    resp = check_api_post_responses(api_client, url, status_code=200)

    assert resp.data["origin_url"] == "https://example.org/user/project%20name"


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_origin_url_quoted(api_client, use_query_params):
    origin_url = "https://example.org/user/project%20name"
    url = _save_origin_api_url(
        visit_type="git",
        origin_url=origin_url,
        use_query_params=use_query_params,
    )

    resp = check_api_post_responses(api_client, url, status_code=200)

    assert resp.data["origin_url"] == "https://example.org/user/project%20name"


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_origin_url_no_plus_quote(api_client, use_query_params):
    origin_url = "https://example.org/+user/project"
    url = _save_origin_api_url(
        visit_type="git",
        origin_url=origin_url,
        use_query_params=use_query_params,
    )

    resp = check_api_post_responses(api_client, url, status_code=200)

    assert resp.data["origin_url"] == origin_url


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_origin_url_with_query_parameter_ko(
    api_client, swh_scheduler, use_query_params
):
    origin_url = "https://example.org/user/project?format=zip"

    # not using reverse as it automatically percent-encode special characters
    url = f"/api/1/origin/save/git/url/{origin_url}/"

    # as the ? was not percent-encoded, django wrongly attempts to redirect to
    # truncated URL /api/1/origin/save/git/url/https://example.org/user/project/
    # as trailing slash is missing
    with pytest.raises(
        RuntimeError,
        match="You called this URL via POST, but the URL doesn't end in a slash",
    ):
        check_api_post_response(api_client, url, status_code=200)


@pytest.mark.parametrize(
    "use_query_params", [False, True], ids=["URL arguments", "Query parameters"]
)
def test_create_save_request_origin_url_with_query_parameter_ok(
    api_client, swh_scheduler, use_query_params
):
    origin_url = "https://example.org/user/project?format=zip"

    # compute correct URL with special characters percent-encoded
    url = _save_origin_api_url(
        visit_type="git",
        origin_url=origin_url,
        use_query_params=use_query_params,
    )

    assert "%3Fformat" in url

    # request should succeed
    resp = check_api_post_responses(api_client, url, status_code=200)
    # origin URL in response data should be unquoted
    assert resp.data["origin_url"] == origin_url
