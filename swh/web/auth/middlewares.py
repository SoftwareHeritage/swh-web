# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.contrib.auth import BACKEND_SESSION_KEY
from django.http.response import HttpResponseRedirect

from swh.web.common.utils import reverse


class OIDCSessionRefreshMiddleware:
    """
    Middleware for silently refreshing on OpenID Connect session from
    the browser and get new access token.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response
        self.exempted_urls = [
            reverse(v)
            for v in ("logout", "oidc-login", "oidc-login-complete", "oidc-logout")
        ]

    def __call__(self, request):
        if (
            request.method != "GET"
            or request.user.is_authenticated
            or BACKEND_SESSION_KEY not in request.session
            or "OIDC" not in request.session[BACKEND_SESSION_KEY]
            or request.path in self.exempted_urls
        ):
            return self.get_response(request)

        # At that point, we know that a OIDC user was previously logged in.
        # Access token has expired so we attempt a silent OIDC session refresh.
        # If the latter failed because the session expired, user will be
        # redirected to logout page and a link will be offered to login again.
        # See implementation of "oidc-login-complete" view for more details.
        next_path = request.get_full_path()
        redirect_url = reverse(
            "oidc-login", query_params={"next_path": next_path, "prompt": "none"}
        )
        return HttpResponseRedirect(redirect_url)
