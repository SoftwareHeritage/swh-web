# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.contrib.auth.views import LoginView, LogoutView
from django.urls import re_path as url

from swh.auth.django.views import urlpatterns as auth_urlpatterns
from swh.web.auth.views import (
    oidc_generate_bearer_token,
    oidc_generate_bearer_token_complete,
    oidc_get_bearer_token,
    oidc_list_bearer_tokens,
    oidc_profile_view,
    oidc_revoke_bearer_tokens,
)
from swh.web.config import get_config

config = get_config()

oidc_enabled = bool(config["keycloak"]["server_url"])

urlpatterns = []

if not oidc_enabled:
    urlpatterns = [
        url(
            r"^login/$",
            LoginView.as_view(template_name="login.html"),
            name="login",
        )
    ]

if oidc_enabled or config["e2e_tests_mode"]:
    urlpatterns += auth_urlpatterns + [
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
        url(
            r"^oidc/profile/$",
            oidc_profile_view,
            name="oidc-profile",
        ),
    ]

urlpatterns.append(
    url(
        r"^logout/$",
        LogoutView.as_view(template_name="logout.html"),
        name="logout",
    )
)
