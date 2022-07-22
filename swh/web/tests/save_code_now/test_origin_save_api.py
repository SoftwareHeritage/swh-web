# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime, timedelta
import uuid

import pytest

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from swh.web.api.throttling import SwhWebUserRateThrottle
from swh.web.auth.utils import API_SAVE_ORIGIN_PERMISSION, SWH_AMBASSADOR_PERMISSION
from swh.web.save_code_now.models import (
    SAVE_REQUEST_ACCEPTED,
    SAVE_REQUEST_PENDING,
    SAVE_REQUEST_REJECTED,
    SAVE_TASK_FAILED,
    SAVE_TASK_NOT_CREATED,
    SAVE_TASK_NOT_YET_SCHEDULED,
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
    create_django_permission,
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


def test_invalid_visit_type(api_client, swh_scheduler):
    url = reverse(
        "api-1-save-origin",
        url_args={
            "visit_type": "foo",
            "origin_url": "https://github.com/torvalds/linux",
        },
    )
    check_api_get_responses(api_client, url, status_code=400)


def test_invalid_origin_url(api_client, swh_scheduler):
    url = reverse(
        "api-1-save-origin", url_args={"visit_type": "git", "origin_url": "bar"}
    )
    check_api_get_responses(api_client, url, status_code=400)


def check_created_save_request_status(
    api_client,
    mocker,
    origin_url,
    expected_request_status,
    expected_task_status=None,
    visit_date=None,
):

    mock_origin_exists = mocker.patch("swh.web.save_code_now.origin_save.origin_exists")
    mock_origin_exists.return_value = OriginExistenceCheckInfo(
        origin_url=origin_url, exists=True, last_modified=None, content_length=None
    )

    url = reverse(
        "api-1-save-origin", url_args={"visit_type": "git", "origin_url": origin_url}
    )

    mock_visit_date = mocker.patch(
        ("swh.web.save_code_now.origin_save._get_visit_info_for_save_request")
    )
    mock_visit_date.return_value = (visit_date, None)

    if expected_request_status != SAVE_REQUEST_REJECTED:
        response = check_api_post_responses(api_client, url, data=None, status_code=200)
        assert response.data["save_request_status"] == expected_request_status
        assert response.data["save_task_status"] == expected_task_status
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
):

    if expected_task_status != SAVE_TASK_NOT_CREATED:
        task = dict(swh_scheduler.search_tasks()[0].items())
        backend_id = str(uuid.uuid4())

    if scheduler_task_status != "next_run_not_scheduled":
        swh_scheduler.schedule_task_run(task["id"], backend_id)

    if scheduler_task_run_status is not None:
        swh_scheduler.start_task_run(backend_id)
        task_run = dict(
            swh_scheduler.end_task_run(backend_id, scheduler_task_run_status).items()
        )

    url = reverse(
        "api-1-save-origin", url_args={"visit_type": "git", "origin_url": origin_url}
    )

    mock_visit_date = mocker.patch(
        ("swh.web.save_code_now.origin_save._get_visit_info_for_save_request")
    )
    mock_visit_date.return_value = (visit_date, visit_status)
    response = check_api_get_responses(api_client, url, status_code=200)
    save_request_data = response.data[0]

    assert save_request_data["save_request_status"] == expected_request_status
    assert save_request_data["save_task_status"] == expected_task_status
    assert save_request_data["visit_status"] == visit_status

    if scheduler_task_run_status is not None:
        # Check that save task status is still available when
        # the scheduler task has been archived
        swh_scheduler.delete_archived_tasks(
            [{"task_id": task["id"], "task_run_id": task_run["id"]}]
        )
        response = check_api_get_responses(api_client, url, status_code=200)
        save_request_data = response.data[0]
        assert save_request_data["save_task_status"] == expected_task_status
        assert save_request_data["visit_status"] == visit_status


def test_save_request_rejected(api_client, mocker, swh_scheduler):
    origin_url = "https://github.com/user/illegal_repo"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_REJECTED,
    )
    check_save_request_status(
        api_client,
        mocker,
        swh_scheduler,
        origin_url,
        expected_request_status=SAVE_REQUEST_REJECTED,
        expected_task_status=SAVE_TASK_NOT_CREATED,
    )


def test_save_request_pending(api_client, mocker, swh_scheduler):
    origin_url = "https://unkwownforge.com/user/repo"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_PENDING,
        expected_task_status=SAVE_TASK_NOT_CREATED,
    )
    check_save_request_status(
        api_client,
        mocker,
        swh_scheduler,
        origin_url,
        expected_request_status=SAVE_REQUEST_PENDING,
        expected_task_status=SAVE_TASK_NOT_CREATED,
    )


def test_save_request_scheduled(api_client, mocker, swh_scheduler):
    origin_url = "https://github.com/Kitware/CMake"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
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
    )


def test_save_request_completed(api_client, mocker, swh_scheduler):
    origin_url = "https://github.com/Kitware/CMake"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
    )
    check_save_request_status(
        api_client,
        mocker,
        swh_scheduler,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_SUCCEEDED,
        scheduler_task_status="completed",
        scheduler_task_run_status="eventful",
        visit_date=None,
    )


def test_save_request_completed_visit_status(api_client, mocker, swh_scheduler):
    origin_url = "https://github.com/Kitware/CMake"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
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
    )


def test_save_request_failed(api_client, mocker, swh_scheduler):
    origin_url = "https://gitlab.com/inkscape/inkscape"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
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
    )


def test_create_save_request_no_duplicate(api_client, mocker, swh_scheduler):
    origin_url = "https://github.com/webpack/webpack"

    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
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
    )

    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_SCHEDULED,
    )
    sors = list(
        SaveOriginRequest.objects.filter(visit_type="git", origin_url=origin_url)
    )
    assert len(sors) == 1


def test_get_save_requests_unknown_origin(api_client, swh_scheduler):
    unknown_origin_url = "https://gitlab.com/foo/bar"
    url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": "git", "origin_url": unknown_origin_url},
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


def test_save_requests_rate_limit(api_client, swh_scheduler):

    url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": _visit_type, "origin_url": _origin_url},
    )

    for _ in range(save_origin_rate_post):
        check_api_post_response(api_client, url, status_code=200)

    check_api_post_response(api_client, url, status_code=429)


def test_save_requests_no_rate_limit_if_permission(
    api_client, regular_user, swh_scheduler
):

    regular_user.user_permissions.add(
        create_django_permission(API_SAVE_ORIGIN_PERMISSION)
    )

    assert regular_user.has_perm(API_SAVE_ORIGIN_PERMISSION)

    api_client.force_login(regular_user)

    url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": _visit_type, "origin_url": _origin_url},
    )

    for _ in range(save_origin_rate_post * SwhWebUserRateThrottle.NUM_REQUESTS_FACTOR):
        check_api_post_response(api_client, url, status_code=200)

    check_api_post_response(api_client, url, status_code=200)


def test_save_request_unknown_repo_with_permission(
    api_client, regular_user, mocker, swh_scheduler
):

    regular_user.user_permissions.add(
        create_django_permission(API_SAVE_ORIGIN_PERMISSION)
    )

    assert regular_user.has_perm(API_SAVE_ORIGIN_PERMISSION)

    api_client.force_login(regular_user)

    origin_url = "https://unkwownforge.org/user/repo"
    check_created_save_request_status(
        api_client,
        mocker,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
    )
    check_save_request_status(
        api_client,
        mocker,
        swh_scheduler,
        origin_url,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
    )


def test_save_request_form_server_error(api_client, mocker):
    create_save_origin_request = mocker.patch(
        "swh.web.save_code_now.api_views.create_save_origin_request"
    )
    create_save_origin_request.side_effect = Exception("Server error")

    url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": _visit_type, "origin_url": _origin_url},
    )

    check_api_post_responses(api_client, url, status_code=500)


@pytest.fixture
def origin_to_review():
    return "https://git.example.org/user/project"


def test_create_save_request_pending_review_anonymous_user(
    api_client, origin_to_review, swh_scheduler
):

    url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": "git", "origin_url": origin_to_review},
    )

    response = check_api_post_responses(api_client, url, status_code=200)

    assert response.data["save_request_status"] == SAVE_REQUEST_PENDING

    with pytest.raises(ObjectDoesNotExist):
        SaveAuthorizedOrigin.objects.get(url=origin_to_review)


def test_create_save_request_archives_with_ambassador_user(
    api_client,
    keycloak_oidc,
    requests_mock,
    swh_scheduler,
):
    swh_scheduler.add_load_archive_task_type()

    keycloak_oidc.realm_permissions = [SWH_AMBASSADOR_PERMISSION]
    oidc_profile = keycloak_oidc.login()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {oidc_profile['refresh_token']}")

    originUrl = "https://somewhere.org/simple"
    artifact_version = "1.2.3"
    artifact_filename = f"tarball-{artifact_version}.tar.gz"
    artifact_url = f"{originUrl}/{artifact_filename}"
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

    url = reverse(
        "api-1-save-origin",
        url_args={
            "visit_type": "archives",
            "origin_url": originUrl,
        },
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

    assert SaveAuthorizedOrigin.objects.get(url=originUrl)


def test_create_save_request_archives_missing_artifacts_data(
    api_client, keycloak_oidc, swh_scheduler
):

    swh_scheduler.add_load_archive_task_type()

    keycloak_oidc.realm_permissions = [SWH_AMBASSADOR_PERMISSION]
    oidc_profile = keycloak_oidc.login()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {oidc_profile['refresh_token']}")

    originUrl = "https://somewhere.org/simple"

    url = reverse(
        "api-1-save-origin",
        url_args={
            "visit_type": "archives",
            "origin_url": originUrl,
        },
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


def test_create_save_request_archives_accepted_ambassador_user(
    api_client, origin_to_review, keycloak_oidc, mocker, swh_scheduler
):

    keycloak_oidc.realm_permissions = [SWH_AMBASSADOR_PERMISSION]
    oidc_profile = keycloak_oidc.login()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {oidc_profile['refresh_token']}")

    check_created_save_request_status(
        api_client,
        mocker,
        origin_to_review,
        expected_request_status=SAVE_REQUEST_ACCEPTED,
        expected_task_status=SAVE_TASK_NOT_YET_SCHEDULED,
    )

    assert SaveAuthorizedOrigin.objects.get(url=origin_to_review)


def test_create_save_request_anonymous_user_no_user_id(api_client, swh_scheduler):
    origin_url = "https://some.git.hosters/user/repo"
    url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": "git", "origin_url": origin_url},
    )

    check_api_post_responses(api_client, url, status_code=200)

    sor = SaveOriginRequest.objects.get(origin_url=origin_url)

    assert sor.user_ids is None


def test_create_save_request_authenticated_user_id(
    api_client, keycloak_oidc, swh_scheduler
):
    oidc_profile = keycloak_oidc.login()
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {oidc_profile['refresh_token']}")

    origin_url = "https://some.git.hosters/user/repo2"
    url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": "git", "origin_url": origin_url},
    )

    response = check_api_post_response(api_client, url, status_code=200)

    assert response.wsgi_request.user.id is not None

    user_id = str(response.wsgi_request.user.id)
    sor = SaveOriginRequest.objects.get(user_ids=f'"{user_id}"')
    assert sor.user_ids == f'"{user_id}"'


def test_create_pending_save_request_multiple_authenticated_users(
    api_client, swh_scheduler, regular_user, regular_user2
):
    origin_url = "https://some.git.hosters/user/repo3"

    url = reverse(
        "api-1-save-origin",
        url_args={"visit_type": "git", "origin_url": origin_url},
    )

    api_client.force_login(regular_user)
    check_api_post_response(api_client, url, status_code=200)

    api_client.force_login(regular_user2)
    check_api_post_response(api_client, url, status_code=200)

    assert SaveOriginRequest.objects.get(user_ids__contains=f'"{regular_user.id}"')
    assert SaveOriginRequest.objects.get(user_ids__contains=f'"{regular_user2.id}"')


def test_reject_origin_url_with_password(api_client, swh_scheduler):
    url = reverse(
        "api-1-save-origin",
        url_args={
            "visit_type": "git",
            "origin_url": "https://user:password@git.example.org/user/repo",
        },
    )
    resp = check_api_post_responses(api_client, url, status_code=400)

    assert resp.data == {
        "exception": "BadInputExc",
        "reason": (
            "The provided origin url contains a password and cannot "
            "be accepted for security reasons."
        ),
    }


def test_accept_origin_url_with_username_but_without_password(
    api_client, swh_scheduler
):
    url = reverse(
        "api-1-save-origin",
        url_args={
            "visit_type": "git",
            "origin_url": "https://user@git.example.org/user/repo",
        },
    )
    check_api_post_responses(api_client, url, status_code=200)


@pytest.mark.parametrize(
    "origin_url",
    [
        "https://anonymous:anonymous@git.example.org/user/repo",
        "https://anonymous:@git.example.org/user/repo",
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
