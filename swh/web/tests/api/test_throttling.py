# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.conf.urls import url
from django.contrib.auth.models import Permission, User
from django.contrib.contenttypes.models import ContentType
from django.test.utils import override_settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from swh.web.api.throttling import (
    API_THROTTLING_EXEMPTED_PERM,
    SwhWebRateThrottle,
    throttle_scope,
)
from swh.web.settings.tests import (
    scope1_limiter_rate,
    scope1_limiter_rate_post,
    scope2_limiter_rate,
    scope2_limiter_rate_post,
    scope3_limiter_rate,
    scope3_limiter_rate_post,
)
from swh.web.urls import urlpatterns


class MockViewScope1(APIView):
    throttle_classes = (SwhWebRateThrottle,)
    throttle_scope = "scope1"

    def get(self, request):
        return Response("foo_get")

    def post(self, request):
        return Response("foo_post")


@api_view(["GET", "POST"])
@throttle_scope("scope2")
def mock_view_scope2(request):
    if request.method == "GET":
        return Response("bar_get")
    elif request.method == "POST":
        return Response("bar_post")


class MockViewScope3(APIView):
    throttle_classes = (SwhWebRateThrottle,)
    throttle_scope = "scope3"

    def get(self, request):
        return Response("foo_get")

    def post(self, request):
        return Response("foo_post")


@api_view(["GET", "POST"])
@throttle_scope("scope3")
def mock_view_scope3(request):
    if request.method == "GET":
        return Response("bar_get")
    elif request.method == "POST":
        return Response("bar_post")


urlpatterns += [
    url(r"^scope1_class$", MockViewScope1.as_view()),
    url(r"^scope2_func$", mock_view_scope2),
    url(r"^scope3_class$", MockViewScope3.as_view()),
    url(r"^scope3_func$", mock_view_scope3),
]


def check_response(response, status_code, limit=None, remaining=None):
    assert response.status_code == status_code
    if limit is not None:
        assert response["X-RateLimit-Limit"] == str(limit)
    else:
        assert "X-RateLimit-Limit" not in response
    if remaining is not None:
        assert response["X-RateLimit-Remaining"] == str(remaining)
    else:
        assert "X-RateLimit-Remaining" not in response


@override_settings(ROOT_URLCONF=__name__)
def test_scope1_requests_are_throttled(api_client):
    """
    Ensure request rate is limited in scope1
    """
    for i in range(scope1_limiter_rate):
        response = api_client.get("/scope1_class")
        check_response(response, 200, scope1_limiter_rate, scope1_limiter_rate - i - 1)

    response = api_client.get("/scope1_class")
    check_response(response, 429, scope1_limiter_rate, 0)

    for i in range(scope1_limiter_rate_post):
        response = api_client.post("/scope1_class")
        check_response(
            response, 200, scope1_limiter_rate_post, scope1_limiter_rate_post - i - 1
        )

    response = api_client.post("/scope1_class")
    check_response(response, 429, scope1_limiter_rate_post, 0)


@override_settings(ROOT_URLCONF=__name__)
def test_scope2_requests_are_throttled(api_client):
    """
    Ensure request rate is limited in scope2
    """
    for i in range(scope2_limiter_rate):
        response = api_client.get("/scope2_func")
        check_response(response, 200, scope2_limiter_rate, scope2_limiter_rate - i - 1)

    response = api_client.get("/scope2_func")
    check_response(response, 429, scope2_limiter_rate, 0)

    for i in range(scope2_limiter_rate_post):
        response = api_client.post("/scope2_func")
        check_response(
            response, 200, scope2_limiter_rate_post, scope2_limiter_rate_post - i - 1
        )

    response = api_client.post("/scope2_func")
    check_response(response, 429, scope2_limiter_rate_post, 0)


@override_settings(ROOT_URLCONF=__name__)
def test_scope3_requests_are_throttled_exempted(api_client):
    """
    Ensure request rate is not limited in scope3 as
    requests coming from localhost are exempted from rate limit.
    """
    for _ in range(scope3_limiter_rate + 1):
        response = api_client.get("/scope3_class")
        check_response(response, 200)

    for _ in range(scope3_limiter_rate_post + 1):
        response = api_client.post("/scope3_class")
        check_response(response, 200)

    for _ in range(scope3_limiter_rate + 1):
        response = api_client.get("/scope3_func")
        check_response(response, 200)

    for _ in range(scope3_limiter_rate_post + 1):
        response = api_client.post("/scope3_func")
        check_response(response, 200)


@override_settings(ROOT_URLCONF=__name__)
@pytest.mark.django_db
def test_staff_users_are_not_rate_limited(api_client):
    staff_user = User.objects.create_user(
        username="johndoe", password="", is_staff=True
    )

    api_client.force_login(staff_user)

    for _ in range(scope2_limiter_rate + 1):
        response = api_client.get("/scope2_func")
        check_response(response, 200)

    for _ in range(scope2_limiter_rate_post + 1):
        response = api_client.post("/scope2_func")
        check_response(response, 200)


@override_settings(ROOT_URLCONF=__name__)
@pytest.mark.django_db
def test_non_staff_users_are_rate_limited(api_client):
    user = User.objects.create_user(username="johndoe", password="", is_staff=False)

    api_client.force_login(user)

    for i in range(scope2_limiter_rate):
        response = api_client.get("/scope2_func")
        check_response(response, 200, scope2_limiter_rate, scope2_limiter_rate - i - 1)

    response = api_client.get("/scope2_func")
    check_response(response, 429, scope2_limiter_rate, 0)

    for i in range(scope2_limiter_rate_post):
        response = api_client.post("/scope2_func")
        check_response(
            response, 200, scope2_limiter_rate_post, scope2_limiter_rate_post - i - 1
        )

    response = api_client.post("/scope2_func")
    check_response(response, 429, scope2_limiter_rate_post, 0)


@override_settings(ROOT_URLCONF=__name__)
@pytest.mark.django_db
def test_users_with_throttling_exempted_perm_are_not_rate_limited(api_client):
    user = User.objects.create_user(username="johndoe", password="")
    perm_splitted = API_THROTTLING_EXEMPTED_PERM.split(".")
    app_label = ".".join(perm_splitted[:-1])
    perm_name = perm_splitted[-1]
    content_type = ContentType.objects.create(app_label=app_label, model="dummy")
    permission = Permission.objects.create(
        codename=perm_name, name=perm_name, content_type=content_type,
    )
    user.user_permissions.add(permission)

    assert user.has_perm(API_THROTTLING_EXEMPTED_PERM)

    api_client.force_login(user)

    for _ in range(scope2_limiter_rate + 1):
        response = api_client.get("/scope2_func")
        check_response(response, 200)

    for _ in range(scope2_limiter_rate_post + 1):
        response = api_client.post("/scope2_func")
        check_response(response, 200)
