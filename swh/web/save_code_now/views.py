# Copyright (C) 2018-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Optional, cast

from django_ratelimit.decorators import ratelimit

from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.safestring import mark_safe

from swh.web.auth.utils import SWH_AMBASSADOR_PERMISSION, privileged_user
from swh.web.save_code_now.models import SaveOriginRequest
from swh.web.save_code_now.origin_save import (
    create_save_origin_request,
    get_savable_visit_types,
    get_save_origin_task_info,
)
from swh.web.utils import datatables_order_params, datatables_pagination_params, reverse


@ratelimit(key="user_or_ip", rate="60/m", method="POST", block=False)
def origin_save_help_view(request):
    visit_type = request.POST.get("visit_type")
    origin_url = request.POST.get("origin_url")
    submit_status = ""
    alert_level = ""
    if request.method == "POST":
        if request.limited:
            alert_level = "danger"
            submit_status = (
                'The rate limit for "save code now" requests has been reached. '
                "Please try again later."
            )

        else:
            try:
                sor = create_save_origin_request(
                    visit_type,
                    origin_url,
                    privileged_user=request.user.is_staff,
                    user_id=cast(Optional[int], request.user.id),
                )
            except Exception as exc:
                alert_level = "danger"
                submit_status = (
                    f'An error happened when submitting the "save code now request": '
                    f"{exc}"
                )
            else:
                request_url = reverse(
                    "api-1-save-origin", url_args={"request_id": sor["id"]}
                )
                if sor["save_request_status"] == "accepted":
                    alert_level = "success"
                    submit_status = (
                        'The "save code now" request has been accepted and will be '
                        "processed as soon as possible. You can follow its processing "
                        f'by querying <a href="{request_url}">{request_url}</a>.'
                    )

                else:
                    alert_level = "warning"
                    submit_status = (
                        'The "save code now" request has been put in pending state and '
                        "may be accepted for processing after manual review. You can "
                        "follow its processing by querying "
                        f'<a href="{request_url}">{request_url}</a>.'
                    )
    else:
        origin_url = request.GET.get("origin_url", "")
    return render(
        request,
        "origin-save-help.html",
        {
            "heading": ("Request the saving of a software origin into the archive"),
            "visit_types": get_savable_visit_types(
                privileged_user(request, permissions=[SWH_AMBASSADOR_PERMISSION])
            ),
            "origin_url": origin_url,
            "visit_type": visit_type,
            "submit_status": mark_safe(submit_status),
            "alert_level": alert_level,
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
            "origin_url": request.GET.get("origin_url", ""),
        },
    )


def origin_save_requests_list(request, status):
    if status != "all":
        save_requests = SaveOriginRequest.objects.filter(status=status)
    else:
        save_requests = SaveOriginRequest.objects.all()

    table_data = {}
    table_data["recordsTotal"] = save_requests.count()
    table_data["draw"] = int(request.GET.get("draw", 1))

    search_value = request.GET.get("search[value]")

    field_order = datatables_order_params(request, "id", "desc")

    save_requests = save_requests.order_by(*field_order)

    length, page = datatables_pagination_params(request)

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
    request_info = get_save_origin_task_info(save_request_id)
    for date_field in ("scheduled", "started", "ended"):
        if date_field in request_info and request_info[date_field] is not None:
            request_info[date_field] = request_info[date_field].isoformat()
    return JsonResponse(request_info)
