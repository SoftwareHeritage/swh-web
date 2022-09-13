# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


import requests
from requests.auth import HTTPBasicAuth

from django.contrib.auth.decorators import user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import re_path as url

from swh.web.auth.utils import ADMIN_LIST_DEPOSIT_PERMISSION
from swh.web.config import get_config


def can_list_deposits(user):
    return user.is_staff or user.has_perm(ADMIN_LIST_DEPOSIT_PERMISSION)


@user_passes_test(can_list_deposits)
def admin_deposit(request):
    return render(request, "deposit-admin.html")


@user_passes_test(can_list_deposits)
def admin_deposit_list(request):
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


urlpatterns = [
    url(r"^admin/deposit/$", admin_deposit, name="admin-deposit"),
    url(r"^admin/deposit/list/$", admin_deposit_list, name="admin-deposit-list"),
]
