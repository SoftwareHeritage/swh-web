# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import sentry_sdk

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render

from swh.web.admin.adminurls import admin_route
from swh.web.auth.utils import ADMIN_LIST_DEPOSIT_PERMISSION
from swh.web.common.utils import (
    get_deposits_list,
    parse_swh_deposit_origin,
    parse_swh_metadata_provenance,
)


def _can_list_deposits(user):
    return user.is_staff or user.has_perm(ADMIN_LIST_DEPOSIT_PERMISSION)


@admin_route(r"deposit/", view_name="admin-deposit")
@user_passes_test(_can_list_deposits, login_url=settings.LOGIN_URL)
def _admin_origin_save(request):
    return render(request, "admin/deposit.html")


@admin_route(r"deposit/list/", view_name="admin-deposit-list")
@user_passes_test(_can_list_deposits, login_url=settings.LOGIN_URL)
def _admin_deposit_list(request):
    table_data = {}
    table_data["draw"] = int(request.GET["draw"])
    try:
        deposits = get_deposits_list(request.GET.get("username"))
        deposits_count = len(deposits)
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
        table_data["recordsTotal"] = deposits_count
        table_data["recordsFiltered"] = len(deposits)
        data_list = []
        for d in data:
            data_dict = {
                "id": d["id"],
                "type": d["type"],
                "external_id": d["external_id"],
                "reception_date": d["reception_date"],
                "status": d["status"],
                "status_detail": d["status_detail"],
                "swhid": d["swhid"],
                "swhid_context": d["swhid_context"],
            }
            provenance = None
            raw_metadata = d["raw_metadata"]
            # Try to determine provenance out of the raw metadata
            if raw_metadata and d["type"] == "meta":  # metadata provenance
                provenance = parse_swh_metadata_provenance(d["raw_metadata"])
            elif raw_metadata and d["type"] == "code":
                provenance = parse_swh_deposit_origin(raw_metadata)

            if not provenance and d["origin_url"]:
                provenance = d["origin_url"]

            # Finally, if still not found, we determine uri using the swhid
            if not provenance and d["swhid_context"]:
                # Trying to compute the origin as we did before in the js
                from swh.model.swhids import QualifiedSWHID

                swhid = QualifiedSWHID.from_string(d["swhid_context"])
                provenance = swhid.origin

            data_dict["uri"] = provenance  # could be None

            # This could be large. As this is not displayed yet, drop it to avoid
            # cluttering the data dict
            data_dict.pop("raw_metadata", None)

            data_list.append(data_dict)

        table_data["data"] = data_list

    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        table_data[
            "error"
        ] = "An error occurred while retrieving the list of deposits !"

    return JsonResponse(table_data)
