# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from swh.web.save_code_now.models import (
    SaveAuthorizedOrigin,
    SaveOriginRequest,
    SaveUnauthorizedOrigin,
)
from swh.web.save_code_now.origin_save import (
    SAVE_REQUEST_PENDING,
    SAVE_REQUEST_REJECTED,
    create_save_origin_request,
)


@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def admin_origin_save_requests(request):
    return render(request, "admin/origin-save-requests.html")


@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def admin_origin_save_filters(request):
    return render(request, "admin/origin-save-filters.html")


def _datatables_origin_urls_response(request, urls_query_set):
    search_value = request.GET["search[value]"]
    if search_value:
        urls_query_set = urls_query_set.filter(url__icontains=search_value)

    column_order = request.GET["order[0][column]"]
    field_order = request.GET["columns[%s][name]" % column_order]
    order_dir = request.GET["order[0][dir]"]
    if order_dir == "desc":
        field_order = "-" + field_order

    urls_query_set = urls_query_set.order_by(field_order)

    table_data = {}
    table_data["draw"] = int(request.GET["draw"])
    table_data["recordsTotal"] = urls_query_set.count()
    table_data["recordsFiltered"] = urls_query_set.count()
    length = int(request.GET["length"])
    page = int(request.GET["start"]) / length + 1
    paginator = Paginator(urls_query_set, length)
    urls_query_set = paginator.page(page).object_list
    table_data["data"] = [{"url": u.url} for u in urls_query_set]
    return JsonResponse(table_data)


@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def admin_origin_save_authorized_urls_list(request):
    authorized_urls = SaveAuthorizedOrigin.objects.all()
    return _datatables_origin_urls_response(request, authorized_urls)


@require_POST
@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def admin_origin_save_add_authorized_url(request, origin_url):
    try:
        SaveAuthorizedOrigin.objects.get(url=origin_url)
    except ObjectDoesNotExist:
        # add the new authorized url
        SaveAuthorizedOrigin.objects.create(url=origin_url)
        # check if pending save requests with that url prefix exist
        pending_save_requests = SaveOriginRequest.objects.filter(
            origin_url__startswith=origin_url, status=SAVE_REQUEST_PENDING
        )
        # create origin save tasks for previously pending requests
        for psr in pending_save_requests:
            create_save_origin_request(psr.visit_type, psr.origin_url)
        status_code = 200
    else:
        status_code = 400
    return HttpResponse(status=status_code)


@require_POST
@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def admin_origin_save_remove_authorized_url(request, origin_url):
    try:
        entry = SaveAuthorizedOrigin.objects.get(url=origin_url)
    except ObjectDoesNotExist:
        status_code = 404
    else:
        entry.delete()
        status_code = 200
    return HttpResponse(status=status_code)


@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def admin_origin_save_unauthorized_urls_list(request):
    unauthorized_urls = SaveUnauthorizedOrigin.objects.all()
    return _datatables_origin_urls_response(request, unauthorized_urls)


@require_POST
@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def admin_origin_save_add_unauthorized_url(request, origin_url):
    try:
        SaveUnauthorizedOrigin.objects.get(url=origin_url)
    except ObjectDoesNotExist:
        SaveUnauthorizedOrigin.objects.create(url=origin_url)
        # check if pending save requests with that url prefix exist
        pending_save_requests = SaveOriginRequest.objects.filter(
            origin_url__startswith=origin_url, status=SAVE_REQUEST_PENDING
        )
        # mark pending requests as rejected
        for psr in pending_save_requests:
            psr.status = SAVE_REQUEST_REJECTED
            psr.save()
        status_code = 200
    else:
        status_code = 400
    return HttpResponse(status=status_code)


@require_POST
@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def admin_origin_save_remove_unauthorized_url(request, origin_url):
    try:
        entry = SaveUnauthorizedOrigin.objects.get(url=origin_url)
    except ObjectDoesNotExist:
        status_code = 404
    else:
        entry.delete()
        status_code = 200
    return HttpResponse(status=status_code)


@require_POST
@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def admin_origin_save_request_accept(request, visit_type, origin_url):
    try:
        SaveAuthorizedOrigin.objects.get(url=origin_url)
    except ObjectDoesNotExist:
        SaveAuthorizedOrigin.objects.create(url=origin_url)
    create_save_origin_request(visit_type, origin_url)
    return HttpResponse(status=200)


@require_POST
@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def admin_origin_save_request_reject(request, visit_type, origin_url):
    try:
        sor = SaveOriginRequest.objects.get(
            visit_type=visit_type, origin_url=origin_url, status=SAVE_REQUEST_PENDING
        )
    except ObjectDoesNotExist:
        status_code = 404
    else:
        status_code = 200
        sor.status = SAVE_REQUEST_REJECTED
        sor.note = json.loads(request.body).get("note")
        sor.save()
    return HttpResponse(status=status_code)


@require_POST
@staff_member_required(view_func=None, login_url=settings.LOGIN_URL)
def admin_origin_save_request_remove(request, sor_id):
    try:
        entry = SaveOriginRequest.objects.get(id=sor_id)
    except ObjectDoesNotExist:
        status_code = 404
    else:
        entry.delete()
        status_code = 200
    return HttpResponse(status=status_code)
