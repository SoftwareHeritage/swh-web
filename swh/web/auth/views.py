# Copyright (C) 2020-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from typing import Any, Dict, Optional, Union, cast

from cryptography.fernet import InvalidToken

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    JsonResponse,
)
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from swh.auth.django.models import OIDCUser
from swh.auth.django.utils import keycloak_oidc_client
from swh.auth.django.views import get_oidc_login_data, oidc_login_view
from swh.auth.keycloak import KeycloakError, keycloak_error_message
from swh.web.auth.models import OIDCUserOfflineTokens
from swh.web.auth.utils import decrypt_data, encrypt_data
from swh.web.config import get_config
from swh.web.utils import datatables_pagination_params, reverse
from swh.web.utils.exc import ForbiddenExc


def oidc_generate_bearer_token(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated or not isinstance(request.user, OIDCUser):
        return HttpResponseForbidden()
    redirect_uri = reverse("oidc-generate-bearer-token-complete", request=request)
    return oidc_login_view(
        request, redirect_uri=redirect_uri, scope="openid offline_access"
    )


def oidc_generate_bearer_token_complete(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated or not isinstance(request.user, OIDCUser):
        raise ForbiddenExc("You are not allowed to generate bearer tokens.")
    if "error" in request.GET:
        raise Exception(request.GET["error"])

    login_data = get_oidc_login_data(request)
    oidc_client = keycloak_oidc_client()
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

    length, page = datatables_pagination_params(request)

    paginator = Paginator(tokens, length)

    tokens_data = [
        {"id": t.id, "creation_date": t.creation_date.isoformat()}
        for t in paginator.page(int(page)).object_list
    ]

    table_data: Dict[str, Any] = {}
    table_data["recordsTotal"] = len(tokens_data)
    table_data["draw"] = int(request.GET.get("draw", 1))
    table_data["data"] = tokens_data
    table_data["recordsFiltered"] = len(tokens_data)
    return JsonResponse(table_data)


def _encrypted_token_bytes(token: Union[bytes, memoryview]) -> bytes:
    # token has been retrieved from a PostgreSQL database
    if isinstance(token, memoryview):
        return token.tobytes()
    else:
        return token


def _decrypt_user_token(
    token_data: OIDCUserOfflineTokens, salt: bytes
) -> Optional[bytes]:
    current_secret = get_config()["secret_key"].encode()
    fallback_secrets = [
        secret.encode() for secret in get_config()["secret_key_fallbacks"]
    ]
    decrypted_token = None
    for secret in [current_secret] + fallback_secrets:
        try:
            decrypted_token = decrypt_data(
                _encrypted_token_bytes(token_data.offline_token), secret, salt
            )
            if secret in fallback_secrets:
                # re-encrypt user token if django secret got rotated
                token_data.offline_token = encrypt_data(
                    decrypted_token, current_secret, salt
                )
                token_data.save()
            break
        except InvalidToken:
            pass
    return decrypted_token


@require_http_methods(["POST"])
def oidc_get_bearer_token(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated or not isinstance(request.user, OIDCUser):
        return HttpResponseForbidden()
    try:
        data = json.loads(request.body.decode("ascii"))
        user = cast(OIDCUser, request.user)
        token_data = OIDCUserOfflineTokens.objects.get(id=data["token_id"])
        decrypted_token = _decrypt_user_token(token_data, salt=user.sub.encode())
        if decrypted_token is None:
            return HttpResponseBadRequest(
                "Stored bearer token could not be decrypted, please generate a new one.",
                content_type="text/plain",
            )
        refresh_token = decrypted_token.decode("ascii")
        # check token is still valid
        oidc_client = keycloak_oidc_client()
        oidc_client.refresh_token(refresh_token)
        return HttpResponse(refresh_token, content_type="text/plain")
    except KeycloakError as ke:
        error_msg = keycloak_error_message(ke)
        if error_msg in (
            "invalid_grant: Offline session not active",
            "invalid_grant: Offline user session not found",
        ):
            error_msg = "Bearer token has expired, please generate a new one."
        return HttpResponseBadRequest(error_msg, content_type="text/plain")


@require_http_methods(["POST"])
def oidc_revoke_bearer_tokens(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated or not isinstance(request.user, OIDCUser):
        return HttpResponseForbidden()

    data = json.loads(request.body.decode("ascii"))
    user = cast(OIDCUser, request.user)
    for token_id in data["token_ids"]:
        token_data = OIDCUserOfflineTokens.objects.get(id=token_id)
        decrypted_token = _decrypt_user_token(token_data, salt=user.sub.encode())
        if decrypted_token is not None:
            oidc_client = keycloak_oidc_client()
            oidc_client.logout(decrypted_token.decode("ascii"))
        token_data.delete()
    return HttpResponse(status=200)


@login_required(login_url="oidc-login")
def oidc_profile_view(request: HttpRequest) -> HttpResponse:
    return render(request, "profile.html")
