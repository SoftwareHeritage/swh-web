# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


import requests
from requests.auth import HTTPBasicAuth

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.shortcuts import render

from swh.web.admin.adminurls import admin_route
from swh.web.auth.utils import ADMIN_LIST_DEPOSIT_PERMISSION
from swh.web.config import get_config


def _can_list_deposits(user):
    return user.is_staff or user.has_perm(ADMIN_LIST_DEPOSIT_PERMISSION)


@admin_route(r"deposit/", view_name="admin-deposit")
@user_passes_test(_can_list_deposits, login_url=settings.LOGIN_URL)
def _admin_origin_save(request):
    return render(request, "admin/deposit.html")


@admin_route(r"deposit/list/", view_name="admin-deposit-list")
@user_passes_test(_can_list_deposits, login_url=settings.LOGIN_URL)
def _admin_deposit_list(request):
    config = get_config()["deposit"]
    private_api_url = config["private_api_url"].rstrip("/") + "/"
    deposits_list_url = private_api_url + "deposits/datatables/"
    deposits_list_auth = HTTPBasicAuth(
        config["private_api_user"], config["private_api_password"]
    )

    deposits = requests.get(
        deposits_list_url, auth=deposits_list_auth, params=request.GET, timeout=30
    ).json()

    return JsonResponse(deposits)
