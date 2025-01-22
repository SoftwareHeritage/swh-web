# Copyright (C) 2018-2024 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import annotations

from typing import TYPE_CHECKING

import requests
from requests.auth import HTTPBasicAuth

from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import re_path as url

from swh.web.auth.utils import ADMIN_LIST_DEPOSIT_PERMISSION
from swh.web.config import get_config

if TYPE_CHECKING:
    from django.http import HttpResponse
    from django.http.request import HttpRequest


def can_list_deposits(user) -> bool:
    return user.is_staff or user.has_perm(ADMIN_LIST_DEPOSIT_PERMISSION)


@user_passes_test(can_list_deposits)
def admin_deposit(request: HttpRequest) -> HttpResponse:
    return render(request, "deposit-admin.html")


@user_passes_test(can_list_deposits)
def admin_deposit_list(request: HttpRequest) -> JsonResponse:
    config = get_config()["deposit"]
    if not config:
        return JsonResponse({})
    private_api_url = config["private_api_url"].rstrip("/") + "/"
    deposits_list_url = private_api_url + "deposits/datatables/"
    deposits_list_auth = HTTPBasicAuth(
        config["private_api_user"], config["private_api_password"]
    )
    deposits = requests.get(
        deposits_list_url,
        auth=deposits_list_auth,
        params=request.GET.dict(),
        timeout=30,
    ).json()
    return JsonResponse(deposits)


urlpatterns = [
    url(r"^admin/deposit/$", admin_deposit, name="admin-deposit"),
    url(r"^admin/deposit/list/$", admin_deposit_list, name="admin-deposit-list"),
]
