# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.settings.tests import (
    scope1_limiter_rate, scope1_limiter_rate_post,
    scope2_limiter_rate, scope2_limiter_rate_post,
    scope3_limiter_rate, scope3_limiter_rate_post
)

from django.conf.urls import url
from django.core.cache import cache
from django.test.utils import override_settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.decorators import api_view


from swh.web.common.throttling import (
    SwhWebRateThrottle, throttle_scope
)
from swh.web.tests.testcase import SWHWebTestCase


class MockViewScope1(APIView):
    throttle_classes = (SwhWebRateThrottle,)
    throttle_scope = 'scope1'

    def get(self, request):
        return Response('foo_get')

    def post(self, request):
        return Response('foo_post')


@api_view(['GET', 'POST'])
@throttle_scope('scope2')
def mock_view_scope2(request):
    if request.method == 'GET':
        return Response('bar_get')
    elif request.method == 'POST':
        return Response('bar_post')


class MockViewScope3(APIView):
    throttle_classes = (SwhWebRateThrottle,)
    throttle_scope = 'scope3'

    def get(self, request):
        return Response('foo_get')

    def post(self, request):
        return Response('foo_post')


@api_view(['GET', 'POST'])
@throttle_scope('scope3')
def mock_view_scope3(request):
    if request.method == 'GET':
        return Response('bar_get')
    elif request.method == 'POST':
        return Response('bar_post')


urlpatterns = [
    url(r'^scope1_class$', MockViewScope1.as_view()),
    url(r'^scope2_func$', mock_view_scope2),
    url(r'^scope3_class$', MockViewScope3.as_view()),
    url(r'^scope3_func$', mock_view_scope3)
]


@override_settings(ROOT_URLCONF=__name__)
class ThrottlingTests(SWHWebTestCase):
    def setUp(self):
        """
        Reset the cache so that no throttles will be active
        """
        cache.clear()
        self.factory = APIRequestFactory()

    def check_response(self, response, status_code,
                       limit=None, remaining=None):
        assert response.status_code == status_code
        if limit is not None:
            assert response['X-RateLimit-Limit'] == str(limit)
        else:
            assert 'X-RateLimit-Limit' not in response
        if remaining is not None:
            assert response['X-RateLimit-Remaining'] == str(remaining)
        else:
            assert 'X-RateLimit-Remaining' not in response

    def test_scope1_requests_are_throttled(self):
        """
        Ensure request rate is limited in scope1
        """
        for i in range(scope1_limiter_rate):
            response = self.client.get('/scope1_class')
            self.check_response(response, 200, scope1_limiter_rate,
                                scope1_limiter_rate - i - 1)

        response = self.client.get('/scope1_class')
        self.check_response(response, 429, scope1_limiter_rate, 0)

        for i in range(scope1_limiter_rate_post):
            response = self.client.post('/scope1_class')
            self.check_response(response, 200, scope1_limiter_rate_post,
                                scope1_limiter_rate_post - i - 1)

        response = self.client.post('/scope1_class')
        self.check_response(response, 429, scope1_limiter_rate_post, 0)

    def test_scope2_requests_are_throttled(self):
        """
        Ensure request rate is limited in scope2
        """
        for i in range(scope2_limiter_rate):
            response = self.client.get('/scope2_func')
            self.check_response(response, 200, scope2_limiter_rate,
                                scope2_limiter_rate - i - 1)

        response = self.client.get('/scope2_func')
        self.check_response(response, 429, scope2_limiter_rate, 0)

        for i in range(scope2_limiter_rate_post):
            response = self.client.post('/scope2_func')
            self.check_response(response, 200, scope2_limiter_rate_post,
                                scope2_limiter_rate_post - i - 1)

        response = self.client.post('/scope2_func')
        self.check_response(response, 429, scope2_limiter_rate_post, 0)

    def test_scope3_requests_are_throttled_exempted(self):
        """
        Ensure request rate is not limited in scope3 as
        requests coming from localhost are exempted from rate limit.
        """
        for _ in range(scope3_limiter_rate+1):
            response = self.client.get('/scope3_class')
            self.check_response(response, 200)

        for _ in range(scope3_limiter_rate_post+1):
            response = self.client.post('/scope3_class')
            self.check_response(response, 200)

        for _ in range(scope3_limiter_rate+1):
            response = self.client.get('/scope3_func')
            self.check_response(response, 200)

        for _ in range(scope3_limiter_rate_post+1):
            response = self.client.post('/scope3_func')
            self.check_response(response, 200)
