# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import requests

from django.core.cache import cache
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render

from requests.auth import HTTPBasicAuth
import sentry_sdk

from swh.web.admin.adminurls import admin_route
from swh.web.config import get_config

config = get_config()["deposit"]


@admin_route(r"deposit/", view_name="admin-deposit")
@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def _admin_origin_save(request):
    return render(request, "admin/deposit.html")


@admin_route(r"deposit/list/", view_name="admin-deposit-list")
@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def _admin_deposit_list(request):
    table_data = {}
    table_data["draw"] = int(request.GET["draw"])
    deposits_list_url = config["private_api_url"] + "deposits"
    deposits_list_auth = HTTPBasicAuth(
        config["private_api_user"], config["private_api_password"]
    )
    try:
        nb_deposits = requests.get(
            "%s?page_size=1" % deposits_list_url, auth=deposits_list_auth, timeout=30
        ).json()["count"]

        deposits_data = cache.get("swh-deposit-list")
        if not deposits_data or deposits_data["count"] != nb_deposits:
            deposits_data = requests.get(
                "%s?page_size=%s" % (deposits_list_url, nb_deposits),
                auth=deposits_list_auth,
                timeout=30,
            ).json()
            cache.set("swh-deposit-list", deposits_data)

        deposits = deposits_data["results"]

        search_value = request.GET["search[value]"]
        if search_value:
            deposits = [
                d
                for d in deposits
                if any(
                    search_value.lower() in val
                    for val in [str(v).lower() for v in d.values()]
                )
            ]

        exclude_pattern = request.GET.get("excludePattern")
        if exclude_pattern:
            deposits = [
                d
                for d in deposits
                if all(
                    exclude_pattern.lower() not in val
                    for val in [str(v).lower() for v in d.values()]
                )
            ]

        column_order = request.GET["order[0][column]"]
        field_order = request.GET["columns[%s][name]" % column_order]
        order_dir = request.GET["order[0][dir]"]

        deposits = sorted(deposits, key=lambda d: d[field_order] or "")
        if order_dir == "desc":
            deposits = list(reversed(deposits))

        length = int(request.GET["length"])
        page = int(request.GET["start"]) / length + 1
        paginator = Paginator(deposits, length)
        data = paginator.page(page).object_list
        table_data["recordsTotal"] = deposits_data["count"]
        table_data["recordsFiltered"] = len(deposits)
        table_data["data"] = [
            {
                "id": d["id"],
                "external_id": d["external_id"],
                "reception_date": d["reception_date"],
                "status": d["status"],
                "status_detail": d["status_detail"],
                "swhid": d["swh_id"],
                "swhid_context": d["swh_id_context"],
            }
            for d in data
        ]

    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        table_data["error"] = (
            "An error occurred while retrieving " "the list of deposits !"
        )

    return HttpResponse(json.dumps(table_data), content_type="application/json")
