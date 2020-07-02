# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import uuid

from typing import cast

from django.conf.urls import url
from django.core.cache import cache
from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest
from django.http.response import (
    HttpResponse,
    HttpResponseRedirect,
    HttpResponseServerError,
)

from swh.web.auth.models import OIDCUser
from swh.web.auth.utils import gen_oidc_pkce_codes, get_oidc_client
from swh.web.common.exc import handle_view_exception, BadInputExc
from swh.web.common.utils import reverse


def oidc_login(request: HttpRequest) -> HttpResponse:
    """
    Django view to initiate login process using OpenID Connect.
    """
    # generate a CSRF token
    state = str(uuid.uuid4())
    redirect_uri = reverse("oidc-login-complete", request=request)

    code_verifier, code_challenge = gen_oidc_pkce_codes()

    request.session["login_data"] = {
        "code_verifier": code_verifier,
        "state": state,
        "redirect_uri": redirect_uri,
        "next_path": request.GET.get("next_path", ""),
        "prompt": request.GET.get("prompt", ""),
    }

    authorization_url_params = {
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": "openid",
        "prompt": request.GET.get("prompt", ""),
    }

    try:
        oidc_client = get_oidc_client()
        authorization_url = oidc_client.authorization_url(
            redirect_uri, **authorization_url_params
        )

        return HttpResponseRedirect(authorization_url)
    except Exception as e:
        return handle_view_exception(request, e)


def oidc_login_complete(request: HttpRequest) -> HttpResponse:
    """
    Django view to finalize login process using OpenID Connect.
    """
    try:
        if "login_data" not in request.session:
            raise Exception("Login process has not been initialized.")

        login_data = request.session["login_data"]
        next_path = login_data["next_path"] or request.build_absolute_uri("/")

        if "error" in request.GET:
            if login_data["prompt"] == "none":
                # Silent login failed because OIDC session expired.
                # Redirect to logout page and inform user.
                logout(request)
                logout_url = reverse(
                    "logout", query_params={"next_path": next_path, "remote_user": 1}
                )
                return HttpResponseRedirect(logout_url)
            return HttpResponseServerError(request.GET["error"])

        if "code" not in request.GET or "state" not in request.GET:
            raise BadInputExc("Missing query parameters for authentication.")

        # get CSRF token returned by OIDC server
        state = request.GET["state"]

        if state != login_data["state"]:
            raise BadInputExc("Wrong CSRF token, aborting login process.")

        user = authenticate(
            request=request,
            code=request.GET["code"],
            code_verifier=login_data["code_verifier"],
            redirect_uri=login_data["redirect_uri"],
        )

        if user is None:
            raise Exception("User authentication failed.")

        login(request, user)

        return HttpResponseRedirect(next_path)
    except Exception as e:
        return handle_view_exception(request, e)


def oidc_logout(request: HttpRequest) -> HttpResponse:
    """
    Django view to logout using OpenID Connect.
    """
    try:
        user = request.user
        logout(request)
        if hasattr(user, "refresh_token"):
            oidc_client = get_oidc_client()
            user = cast(OIDCUser, user)
            refresh_token = cast(str, user.refresh_token)
            # end OpenID Connect session
            oidc_client.logout(refresh_token)
            # remove user data from cache
            cache.delete(f"oidc_user_{user.id}")

        logout_url = reverse("logout", query_params={"remote_user": 1})
        return HttpResponseRedirect(request.build_absolute_uri(logout_url))
    except Exception as e:
        return handle_view_exception(request, e)


urlpatterns = [
    url(r"^oidc/login/$", oidc_login, name="oidc-login"),
    url(r"^oidc/login-complete/$", oidc_login_complete, name="oidc-login-complete"),
    url(r"^oidc/logout/$", oidc_logout, name="oidc-logout"),
]
