# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render

from swh.web.auth.utils import SWH_AMBASSADOR_PERMISSION, privileged_user
from swh.web.save_code_now.models import SaveOriginRequest
from swh.web.save_code_now.origin_save import (
    get_savable_visit_types,
    get_save_origin_task_info,
)


def origin_save_help_view(request):
    return render(
        request,
        "origin-save-help.html",
        {
            "heading": ("Request the saving of a software origin into the archive"),
            "visit_types": get_savable_visit_types(
                privileged_user(request, permissions=[SWH_AMBASSADOR_PERMISSION])
            ),
        },
    )


def origin_save_list_view(request):
    return render(
        request,
        "origin-save-list.html",
        {
            "heading": ("Request the saving of a software origin into the archive"),
            "visit_types": get_savable_visit_types(
                privileged_user(request, permissions=[SWH_AMBASSADOR_PERMISSION])
            ),
        },
    )


def origin_save_requests_list(request, status):

    if status != "all":
        save_requests = SaveOriginRequest.objects.filter(status=status)
    else:
        save_requests = SaveOriginRequest.objects.all()

    table_data = {}
    table_data["recordsTotal"] = save_requests.count()
    table_data["draw"] = int(request.GET["draw"])

    search_value = request.GET["search[value]"]

    column_order = request.GET["order[0][column]"]
    field_order = request.GET["columns[%s][name]" % column_order]
    order_dir = request.GET["order[0][dir]"]
    if order_dir == "desc":
        field_order = "-" + field_order

    save_requests = save_requests.order_by(field_order)

    length = int(request.GET["length"])
    page = int(request.GET["start"]) / length + 1

    if search_value:
        save_requests = save_requests.filter(
            Q(status__icontains=search_value)
            | Q(loading_task_status__icontains=search_value)
            | Q(visit_type__icontains=search_value)
            | Q(origin_url__icontains=search_value)
        )

    if (
        int(request.GET.get("user_requests_only", "0"))
        and request.user.is_authenticated
    ):
        save_requests = save_requests.filter(user_ids__contains=f'"{request.user.id}"')

    table_data["recordsFiltered"] = save_requests.count()
    paginator = Paginator(save_requests, length)
    table_data["data"] = [sor.to_dict() for sor in paginator.page(page).object_list]
    return JsonResponse(table_data)


def save_origin_task_info(request, save_request_id):
    request_info = get_save_origin_task_info(
        save_request_id, full_info=request.user.is_staff
    )
    for date_field in ("scheduled", "started", "ended"):
        if date_field in request_info and request_info[date_field] is not None:
            request_info[date_field] = request_info[date_field].isoformat()
    return JsonResponse(request_info)
