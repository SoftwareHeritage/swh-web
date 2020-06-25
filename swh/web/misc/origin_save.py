# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from django.conf.urls import url
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseServerError
from django.shortcuts import render

from rest_framework.decorators import api_view, authentication_classes

from swh.web.api.throttling import throttle_scope
from swh.web.common.exc import ForbiddenExc
from swh.web.common.models import SaveOriginRequest
from swh.web.common.origin_save import (
    create_save_origin_request,
    get_savable_visit_types,
    get_save_origin_requests_from_queryset,
    get_save_origin_task_info,
)
from swh.web.common.utils import EnforceCSRFAuthentication


def _origin_save_view(request):
    return render(
        request,
        "misc/origin-save.html",
        {"heading": ("Request the saving of a software origin into " "the archive")},
    )


@api_view(["POST"])
@authentication_classes((EnforceCSRFAuthentication,))
@throttle_scope("swh_save_origin")
def _origin_save_request(request, visit_type, origin_url):
    """
    This view is called through AJAX from the save code now form of swh-web.
    We use DRF here as we want to rate limit the number of submitted requests
    per user to avoid being possibly flooded by bots.
    """
    try:
        response = json.dumps(
            create_save_origin_request(visit_type, origin_url), separators=(",", ": ")
        )
        return HttpResponse(response, content_type="application/json")
    except ForbiddenExc as exc:
        return HttpResponseForbidden(
            json.dumps({"detail": str(exc)}), content_type="application/json"
        )
    except Exception as exc:
        return HttpResponseServerError(
            json.dumps({"detail": str(exc)}), content_type="application/json"
        )


def _visit_save_types_list(request):
    visit_types = json.dumps(get_savable_visit_types(), separators=(",", ": "))
    return HttpResponse(visit_types, content_type="application/json")


def _origin_save_requests_list(request, status):

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
    save_requests = get_save_origin_requests_from_queryset(save_requests)
    if search_value:
        save_requests = [
            sr
            for sr in save_requests
            if search_value.lower() in sr["save_request_status"].lower()
            or search_value.lower() in sr["save_task_status"].lower()
            or search_value.lower() in sr["visit_type"].lower()
            or search_value.lower() in sr["origin_url"].lower()
        ]

    table_data["recordsFiltered"] = len(save_requests)
    paginator = Paginator(save_requests, length)
    table_data["data"] = paginator.page(page).object_list
    table_data_json = json.dumps(table_data, separators=(",", ": "))
    return HttpResponse(table_data_json, content_type="application/json")


def _save_origin_task_info(request, save_request_id):
    request_info = get_save_origin_task_info(
        save_request_id, full_info=request.user.is_staff
    )
    for date_field in ("scheduled", "started", "ended"):
        if date_field in request_info and request_info[date_field] is not None:
            request_info[date_field] = request_info[date_field].isoformat()
    return HttpResponse(json.dumps(request_info), content_type="application/json")


urlpatterns = [
    url(r"^save/$", _origin_save_view, name="origin-save"),
    url(
        r"^save/(?P<visit_type>.+)/url/(?P<origin_url>.+)/$",
        _origin_save_request,
        name="origin-save-request",
    ),
    url(r"^save/types/list/$", _visit_save_types_list, name="origin-save-types-list"),
    url(
        r"^save/requests/list/(?P<status>.+)/$",
        _origin_save_requests_list,
        name="origin-save-requests-list",
    ),
    url(
        r"^save/task/info/(?P<save_request_id>.+)/",
        _save_origin_task_info,
        name="origin-save-task-info",
    ),
]
