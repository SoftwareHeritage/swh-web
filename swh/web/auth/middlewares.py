# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.contrib.auth import BACKEND_SESSION_KEY
from django.http.response import HttpResponseRedirect

from swh.web.common.utils import reverse


class OIDCSessionExpiredMiddleware:
    """
    Middleware for checking OIDC user session expiration.
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

        # At that point, we know that a OIDC user was previously logged in
        # and his session has expired.
        # User will be redirected to logout page and a link will be offered to
        # login again.
        next_path = request.get_full_path()
        logout_url = reverse(
            "logout", query_params={"next_path": next_path, "remote_user": 1}
        )
        return HttpResponseRedirect(logout_url)
