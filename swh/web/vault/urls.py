# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import re_path as url

# register Web API endpoints
from swh.web.vault.api_views import vault_api_urls


def vault_view(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "vault-ui.html",
        {"heading": "Download archive content from the Vault"},
    )


def browse_vault_view(request: HttpRequest) -> HttpResponse:
    return redirect("vault")


urlpatterns = [
    url(r"^vault/$", vault_view, name="vault"),
    # for backward compatibility
    url(r"^browse/vault/$", browse_vault_view, name="browse-vault"),
    *vault_api_urls.get_url_patterns(),
]
