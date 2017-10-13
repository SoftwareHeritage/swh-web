# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.settings.tests import (
    scope1_limiter_rate, scope2_limiter_rate
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


class MockView(APIView):
    throttle_classes = (SwhWebRateThrottle,)
    throttle_scope = 'scope1'

    def get(self, request):
        return Response('foo')


@api_view(['GET', ])
@throttle_scope('scope2')
def mock_view(request):
    return Response('bar')


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
        for dummy in range(scope1_limiter_rate+1):
            response = MockView.as_view()(request)
        assert response.status_code == 429

    @istest
    def scope2_requests_are_throttled(self):
        """
        Ensure request rate is not limited in scope2 as
        requests coming from localhost are exempted from rate limit.
        """
        request = self.factory.get('/')
        for dummy in range(scope2_limiter_rate+1):
            response = mock_view(request)
        assert response.status_code == 200
