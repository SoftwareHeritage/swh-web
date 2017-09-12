# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import ipaddress

from rest_framework.throttling import ScopedRateThrottle

from swh.web.config import get_config


class SwhWebRateThrottle(ScopedRateThrottle):
    """Custom request rate limiter for DRF enabling to exempt
    specific networks specified in swh-web configuration.

    Requests are grouped into scopes. It enables to apply different
    requests rate limiting based on the scope name.

    To associate a scope to requests, one must add a 'throttle_scope'
    attribute when using a class based view, or call the 'throttle_scope'
    decorator when using a function based view. By default, requests
    do not have an associated scope and are not rate limited.

    For instance, the following YAML configuration section sets a rate of
    60 requests per minute for the 'swh_api' scope while exempting those
    comming from the 127.0.0.0/8 ip network.

    throttling:
        scopes:
            swh_api:
                limiter_rate: 60/min
                exempted_networks:
                    - 127.0.0.0/8
    """

    scope = None

    def __init__(self):
        super().__init__()
        self.exempted_networks = None
        scopes = get_config()['throttling']['scopes']
        scope = scopes.get(self.scope)
        if scope:
            networks = scope.get('exempted_networks')
            if networks:
                self.exempted_networks = [ipaddress.ip_network(network)
                                          for network in networks]

    def allow_request(self, request, view):
        # class based view case
        if not self.scope:
            request_allowed = \
                super(SwhWebRateThrottle, self).allow_request(request, view)
        # function based view case
        else:
            self.rate = self.get_rate()
            self.num_requests, self.duration = self.parse_rate(self.rate)
            request_allowed = \
                super(ScopedRateThrottle, self).allow_request(request, view)

        if self.exempted_networks:
            remote_address = ipaddress.ip_address(self.get_ident(request))
            return any(remote_address in network
                       for network in self.exempted_networks) or \
                request_allowed

        return request_allowed


def throttle_scope(scope):
    """Decorator that allows the throttle scope of a DRF
    function based view to be set:

    @api_view(['GET', ])
    @throttle_scope('scope')
    def view(request):
         ...
    """
    def decorator(func):
        SwhScopeRateThrottle = type(
            'CustomScopeRateThrottle',
            (SwhWebRateThrottle,),
            {'scope': scope}
        )
        func.throttle_classes = (SwhScopeRateThrottle, )
        return func
    return decorator
