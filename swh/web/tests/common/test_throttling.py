# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.settings.tests import (
    scope1_limiter_rate, scope1_limiter_rate_post,
    scope2_limiter_rate, scope2_limiter_rate_post,
    scope3_limiter_rate, scope3_limiter_rate_post
)

from django.test import TestCase
from django.core.cache import cache

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
from rest_framework.decorators import api_view

from nose.tools import istest

from swh.web.common.throttling import (
    SwhWebRateThrottle, throttle_scope
)


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


class ThrottlingTests(TestCase):
    def setUp(self):
        """
        Reset the cache so that no throttles will be active
        """
        cache.clear()
        self.factory = APIRequestFactory()

    @istest
    def scope1_requests_are_throttled(self):
        """
        Ensure request rate is limited in scope1
        """
        request = self.factory.get('/')
        for _ in range(scope1_limiter_rate):
            response = MockViewScope1.as_view()(request)
            assert response.status_code == 200
        response = MockViewScope1.as_view()(request)
        assert response.status_code == 429

        request = self.factory.post('/')
        for _ in range(scope1_limiter_rate_post):
            response = MockViewScope1.as_view()(request)
            assert response.status_code == 200
        response = MockViewScope1.as_view()(request)
        assert response.status_code == 429

    @istest
    def scope2_requests_are_throttled(self):
        """
        Ensure request rate is limited in scope2
        """
        request = self.factory.get('/')
        for _ in range(scope2_limiter_rate):
            response = mock_view_scope2(request)
            assert response.status_code == 200
        response = mock_view_scope2(request)
        assert response.status_code == 429

        request = self.factory.post('/')
        for _ in range(scope2_limiter_rate_post):
            response = mock_view_scope2(request)
            assert response.status_code == 200
        response = mock_view_scope2(request)
        assert response.status_code == 429

    @istest
    def scope3_requests_are_throttled_exempted(self):
        """
        Ensure request rate is not limited in scope3 as
        requests coming from localhost are exempted from rate limit.
        """
        request = self.factory.get('/')
        for _ in range(scope3_limiter_rate+1):
            response = MockViewScope3.as_view()(request)
            assert response.status_code == 200

        request = self.factory.post('/')
        for _ in range(scope3_limiter_rate_post+1):
            response = MockViewScope3.as_view()(request)
            assert response.status_code == 200

        request = self.factory.get('/')
        for _ in range(scope3_limiter_rate+1):
            response = mock_view_scope3(request)
            assert response.status_code == 200

        request = self.factory.post('/')
        for _ in range(scope3_limiter_rate_post+1):
            response = mock_view_scope3(request)
            assert response.status_code == 200
