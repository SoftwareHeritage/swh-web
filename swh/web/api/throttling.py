# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from ipaddress import ip_address, ip_network, IPv4Network, IPv6Network
from typing import Callable, List, TypeVar, Union

from django.core.exceptions import ImproperlyConfigured
import rest_framework
from rest_framework.throttling import ScopedRateThrottle
import sentry_sdk

from swh.web.config import get_config


APIView = TypeVar("APIView", bound="rest_framework.views.APIView")
Request = rest_framework.request.Request

API_THROTTLING_EXEMPTED_PERM = "swh.web.api.throttling_exempted"


class SwhWebRateThrottle(ScopedRateThrottle):
    """Custom request rate limiter for DRF enabling to exempt
    specific networks specified in swh-web configuration.

    Requests are grouped into scopes. It enables to apply different
    requests rate limiting based on the scope name but also the
    input HTTP request types.

    To associate a scope to requests, one must add a 'throttle_scope'
    attribute when using a class based view, or call the 'throttle_scope'
    decorator when using a function based view. By default, requests
    do not have an associated scope and are not rate limited.

    Rate limiting can also be configured according to the type
    of the input HTTP requests for fine grained tuning.

    For instance, the following YAML configuration section sets a rate of:
        - 1 per minute for POST requests
        - 60 per minute for other request types

    for the 'swh_api' scope while exempting those coming from the
    127.0.0.0/8 ip network.

    .. code-block:: yaml

        throttling:
            scopes:
                swh_api:
                    limiter_rate:
                        default: 60/m
                        POST: 1/m
                    exempted_networks:
                        - 127.0.0.0/8

    """

    scope = None

    def __init__(self):
        super().__init__()
        self.exempted_networks = None

    def get_exempted_networks(
        self, scope_name: str
    ) -> List[Union[IPv4Network, IPv6Network]]:
        if not self.exempted_networks:
            scopes = get_config()["throttling"]["scopes"]
            scope = scopes.get(scope_name)
            if scope:
                networks = scope.get("exempted_networks")
                if networks:
                    self.exempted_networks = [
                        ip_network(network) for network in networks
                    ]
        return self.exempted_networks

    def allow_request(self, request: Request, view: APIView) -> bool:
        # no throttling for staff users
        if request.user.is_authenticated and (
            request.user.is_staff or request.user.has_perm(API_THROTTLING_EXEMPTED_PERM)
        ):
            return True
        # class based view case
        if not self.scope:

            default_scope = getattr(view, self.scope_attr, None)
            request_allowed = None
            if default_scope is not None:
                # check if there is a specific rate limiting associated
                # to the request type
                assert request.method is not None
                request_scope = f"{default_scope}_{request.method.lower()}"
                setattr(view, self.scope_attr, request_scope)
                try:
                    request_allowed = super().allow_request(request, view)
                # use default rate limiting otherwise
                except ImproperlyConfigured as exc:
                    sentry_sdk.capture_exception(exc)

            setattr(view, self.scope_attr, default_scope)
            if request_allowed is None:
                request_allowed = super().allow_request(request, view)

        # function based view case
        else:
            default_scope = self.scope
            # check if there is a specific rate limiting associated
            # to the request type
            self.scope = default_scope + "_" + request.method.lower()
            try:
                self.rate = self.get_rate()
            # use default rate limiting otherwise
            except ImproperlyConfigured as exc:
                sentry_sdk.capture_exception(exc)
                self.scope = default_scope
                self.rate = self.get_rate()
            self.num_requests, self.duration = self.parse_rate(self.rate)

            request_allowed = super(ScopedRateThrottle, self).allow_request(
                request, view
            )
            self.scope = default_scope

        exempted_networks = self.get_exempted_networks(default_scope)
        exempted_ip = False

        if exempted_networks:
            remote_address = ip_address(self.get_ident(request))
            exempted_ip = any(
                remote_address in network for network in exempted_networks
            )
            request_allowed = exempted_ip or request_allowed

        # set throttling related data in the request metadata
        # in order for the ThrottlingHeadersMiddleware to
        # add X-RateLimit-* headers in the HTTP response
        if not exempted_ip and hasattr(self, "history"):
            hit_count = len(self.history)
            request.META["RateLimit-Limit"] = self.num_requests
            request.META["RateLimit-Remaining"] = self.num_requests - hit_count
            wait = self.wait()
            if wait is not None:
                request.META["RateLimit-Reset"] = int(self.now + wait)

        return request_allowed


def throttle_scope(scope: str) -> Callable[..., APIView]:
    """Decorator that allows the throttle scope of a DRF
    function based view to be set::

        @api_view(['GET', ])
        @throttle_scope('scope')
        def view(request):
            ...

    """

    def decorator(func: APIView) -> APIView:
        SwhScopeRateThrottle = type(
            "CustomScopeRateThrottle", (SwhWebRateThrottle,), {"scope": scope}
        )
        func.throttle_classes = (SwhScopeRateThrottle,)
        return func

    return decorator
