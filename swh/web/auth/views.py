# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from typing import Any, Dict, cast
import uuid

from cryptography.fernet import InvalidToken

from django.conf.urls import url
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.http.response import (
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from swh.web.auth.models import OIDCUser, OIDCUserOfflineTokens
from swh.web.auth.utils import (
    decrypt_data,
    encrypt_data,
    gen_oidc_pkce_codes,
    get_oidc_client,
)
from swh.web.common.exc import BadInputExc, ForbiddenExc
from swh.web.common.utils import reverse
from swh.web.config import get_config


def _oidc_login(request: HttpRequest, redirect_uri: str, scope: str = "openid"):
    # generate a CSRF token
    state = str(uuid.uuid4())

    code_verifier, code_challenge = gen_oidc_pkce_codes()

    request.session["login_data"] = {
        "code_verifier": code_verifier,
        "state": state,
        "redirect_uri": redirect_uri,
        "next_path": request.GET.get("next_path", ""),
    }

    authorization_url_params = {
        "state": state,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": scope,
    }

    oidc_client = get_oidc_client()
    authorization_url = oidc_client.authorization_url(
        redirect_uri, **authorization_url_params
    )

    return HttpResponseRedirect(authorization_url)


def oidc_login(request: HttpRequest) -> HttpResponse:
    """
    Django view to initiate login process using OpenID Connect.
    """

    redirect_uri = reverse("oidc-login-complete", request=request)

    return _oidc_login(request, redirect_uri=redirect_uri)


def _get_login_data(request: HttpRequest) -> Dict[str, Any]:
    if "login_data" not in request.session:
        raise Exception("Login process has not been initialized.")

    return request.session["login_data"]


def _check_login_data(request: HttpRequest, login_data: Dict[str, Any]):

    if "code" not in request.GET or "state" not in request.GET:
        raise BadInputExc("Missing query parameters for authentication.")

    # get CSRF token returned by OIDC server
    state = request.GET["state"]

    if state != login_data["state"]:
        raise BadInputExc("Wrong CSRF token, aborting login process.")


def oidc_login_complete(request: HttpRequest) -> HttpResponse:
    """
    Django view to finalize login process using OpenID Connect.
    """
    login_data = _get_login_data(request)
    next_path = login_data["next_path"] or request.build_absolute_uri("/")

    if "error" in request.GET:
        raise Exception(request.GET["error"])

    _check_login_data(request, login_data)

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


def oidc_logout(request: HttpRequest) -> HttpResponse:
    """
    Django view to logout using OpenID Connect.
    """
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


def oidc_generate_bearer_token(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated or not isinstance(request.user, OIDCUser):
        return HttpResponseForbidden()
    redirect_uri = reverse("oidc-generate-bearer-token-complete", request=request)
    return _oidc_login(
        request, redirect_uri=redirect_uri, scope="openid offline_access"
    )


def oidc_generate_bearer_token_complete(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated or not isinstance(request.user, OIDCUser):
        raise ForbiddenExc("You are not allowed to generate bearer tokens.")
    if "error" in request.GET:
        raise Exception(request.GET["error"])

    oidc_client = get_oidc_client()
    login_data = _get_login_data(request)
    _check_login_data(request, login_data)
    oidc_profile = oidc_client.authorization_code(
        code=request.GET["code"],
        code_verifier=login_data["code_verifier"],
        redirect_uri=login_data["redirect_uri"],
    )
    user = cast(OIDCUser, request.user)
    token = oidc_profile["refresh_token"]
    secret = get_config()["secret_key"].encode()
    salt = user.sub.encode()
    encrypted_token = encrypt_data(token.encode(), secret, salt)
    OIDCUserOfflineTokens.objects.create(
        user_id=str(user.id), offline_token=encrypted_token
    ).save()
    return HttpResponseRedirect(reverse("oidc-profile") + "#tokens")


def oidc_list_bearer_tokens(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated or not isinstance(request.user, OIDCUser):
        return HttpResponseForbidden()

    tokens = OIDCUserOfflineTokens.objects.filter(user_id=str(request.user.id))
    tokens = tokens.order_by("-creation_date")

    length = int(request.GET["length"])
    page = int(request.GET["start"]) / length + 1

    paginator = Paginator(tokens, length)

    tokens_data = [
        {"id": t.id, "creation_date": t.creation_date.isoformat()}
        for t in paginator.page(int(page)).object_list
    ]

    table_data: Dict[str, Any] = {}
    table_data["recordsTotal"] = len(tokens_data)
    table_data["draw"] = int(request.GET["draw"])
    table_data["data"] = tokens_data
    table_data["recordsFiltered"] = len(tokens_data)
    return JsonResponse(table_data)


@require_http_methods(["POST"])
def oidc_get_bearer_token(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated or not isinstance(request.user, OIDCUser):
        return HttpResponseForbidden()
    try:
        data = json.loads(request.body.decode("ascii"))
        user = cast(OIDCUser, request.user)
        token_data = OIDCUserOfflineTokens.objects.get(id=data["token_id"])
        secret = get_config()["secret_key"].encode()
        salt = user.sub.encode()
        decrypted_token = decrypt_data(token_data.offline_token, secret, salt)
        return HttpResponse(decrypted_token.decode("ascii"), content_type="text/plain")
    except InvalidToken:
        return HttpResponse(status=401)


@require_http_methods(["POST"])
def oidc_revoke_bearer_tokens(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated or not isinstance(request.user, OIDCUser):
        return HttpResponseForbidden()
    try:
        data = json.loads(request.body.decode("ascii"))
        user = cast(OIDCUser, request.user)
        for token_id in data["token_ids"]:
            token_data = OIDCUserOfflineTokens.objects.get(id=token_id)
            secret = get_config()["secret_key"].encode()
            salt = user.sub.encode()
            decrypted_token = decrypt_data(token_data.offline_token, secret, salt)
            oidc_client = get_oidc_client()
            oidc_client.logout(decrypted_token.decode("ascii"))
            token_data.delete()
        return HttpResponse(status=200)
    except InvalidToken:
        return HttpResponse(status=401)


@login_required(login_url="/oidc/login/", redirect_field_name="next_path")
def _oidc_profile_view(request: HttpRequest) -> HttpResponse:
    return render(request, "auth/profile.html")


urlpatterns = [
    url(r"^oidc/login/$", oidc_login, name="oidc-login"),
    url(r"^oidc/login-complete/$", oidc_login_complete, name="oidc-login-complete"),
    url(r"^oidc/logout/$", oidc_logout, name="oidc-logout"),
    url(
        r"^oidc/generate-bearer-token/$",
        oidc_generate_bearer_token,
        name="oidc-generate-bearer-token",
    ),
    url(
        r"^oidc/generate-bearer-token-complete/$",
        oidc_generate_bearer_token_complete,
        name="oidc-generate-bearer-token-complete",
    ),
    url(
        r"^oidc/list-bearer-token/$",
        oidc_list_bearer_tokens,
        name="oidc-list-bearer-tokens",
    ),
    url(
        r"^oidc/get-bearer-token/$",
        oidc_get_bearer_token,
        name="oidc-get-bearer-token",
    ),
    url(
        r"^oidc/revoke-bearer-tokens/$",
        oidc_revoke_bearer_tokens,
        name="oidc-revoke-bearer-tokens",
    ),
    url(r"^oidc/profile/$", _oidc_profile_view, name="oidc-profile",),
]
