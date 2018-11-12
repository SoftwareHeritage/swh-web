# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from swh.web.admin.adminurls import admin_route

from swh.web.common.models import (
    SaveAuthorizedOrigin, SaveUnauthorizedOrigin, SaveOriginRequest
)

from swh.web.common.origin_save import (
    create_save_origin_request,
    SAVE_REQUEST_PENDING, SAVE_REQUEST_REJECTED
)


@admin_route(r'origin/save/', view_name='admin-origin-save')
@staff_member_required(login_url=settings.LOGIN_URL)
def _admin_origin_save(request):
    return render(request, 'admin/origin-save.html')


def _datatables_origin_urls_response(request, urls_query_set):
    search_value = request.GET['search[value]']
    if search_value:
        urls_query_set = urls_query_set.filter(url__icontains=search_value)

    column_order = request.GET['order[0][column]']
    field_order = request.GET['columns[%s][name]' % column_order]
    order_dir = request.GET['order[0][dir]']
    if order_dir == 'desc':
        field_order = '-' + field_order

    urls_query_set = urls_query_set.order_by(field_order)

    table_data = {}
    table_data['draw'] = int(request.GET['draw'])
    table_data['recordsTotal'] = urls_query_set.count()
    table_data['recordsFiltered'] = urls_query_set.count()
    length = int(request.GET['length'])
    page = int(request.GET['start']) / length + 1
    paginator = Paginator(urls_query_set, length)
    urls_query_set = paginator.page(page).object_list
    table_data['data'] = [{'url': u.url} for u in urls_query_set]
    table_data_json = json.dumps(table_data, separators=(',', ': '))
    return HttpResponse(table_data_json, content_type='application/json')


@admin_route(r'origin/save/authorized_urls/list/',
             view_name='admin-origin-save-authorized-urls-list')
@staff_member_required
def _admin_origin_save_authorized_urls_list(request):
    authorized_urls = SaveAuthorizedOrigin.objects.all()
    return _datatables_origin_urls_response(request, authorized_urls)


@admin_route(r'origin/save/authorized_urls/add/(?P<origin_url>.+)/',
             view_name='admin-origin-save-add-authorized-url')
@require_POST
@staff_member_required(login_url=settings.LOGIN_URL)
def _admin_origin_save_add_authorized_url(request, origin_url):
    try:
        SaveAuthorizedOrigin.objects.get(url=origin_url)
    except ObjectDoesNotExist:
        # add the new authorized url
        SaveAuthorizedOrigin.objects.create(url=origin_url)
        # check if pending save requests with that url prefix exist
        pending_save_requests = \
            SaveOriginRequest.objects.filter(origin_url__startswith=origin_url,
                                             status=SAVE_REQUEST_PENDING)
        # create origin save tasks for previously pending requests
        for psr in pending_save_requests:
            create_save_origin_request(psr.origin_type, psr.origin_url)
        status_code = 200
    else:
        status_code = 400
    return HttpResponse(status=status_code)


@admin_route(r'origin/save/authorized_urls/remove/(?P<origin_url>.+)/',
             view_name='admin-origin-save-remove-authorized-url')
@require_POST
@staff_member_required(login_url=settings.LOGIN_URL)
def _admin_origin_save_remove_authorized_url(request, origin_url):
    try:
        entry = SaveAuthorizedOrigin.objects.get(url=origin_url)
    except ObjectDoesNotExist:
        status_code = 404
    else:
        entry.delete()
        status_code = 200
    return HttpResponse(status=status_code)


@admin_route(r'origin/save/unauthorized_urls/list/',
             view_name='admin-origin-save-unauthorized-urls-list')
@staff_member_required(login_url=settings.LOGIN_URL)
def _admin_origin_save_unauthorized_urls_list(request):
    unauthorized_urls = SaveUnauthorizedOrigin.objects.all()
    return _datatables_origin_urls_response(request, unauthorized_urls)


@admin_route(r'origin/save/unauthorized_urls/add/(?P<origin_url>.+)/',
             view_name='admin-origin-save-add-unauthorized-url')
@require_POST
@staff_member_required(login_url=settings.LOGIN_URL)
def _admin_origin_save_add_unauthorized_url(request, origin_url):
    try:
        SaveUnauthorizedOrigin.objects.get(url=origin_url)
    except ObjectDoesNotExist:
        SaveUnauthorizedOrigin.objects.create(url=origin_url)
        # check if pending save requests with that url prefix exist
        pending_save_requests = \
            SaveOriginRequest.objects.filter(origin_url__startswith=origin_url,
                                             status=SAVE_REQUEST_PENDING)
        # mark pending requests as rejected
        for psr in pending_save_requests:
            psr.status = SAVE_REQUEST_REJECTED
            psr.save()
        status_code = 200
    else:
        status_code = 400
    return HttpResponse(status=status_code)


@admin_route(r'origin/save/unauthorized_urls/remove/(?P<origin_url>.+)/',
             view_name='admin-origin-save-remove-unauthorized-url')
@require_POST
@staff_member_required(login_url=settings.LOGIN_URL)
def _admin_origin_save_remove_unauthorized_url(request, origin_url):
    try:
        entry = SaveUnauthorizedOrigin.objects.get(url=origin_url)
    except ObjectDoesNotExist:
        status_code = 404
    else:
        entry.delete()
        status_code = 200
    return HttpResponse(status=status_code)


@admin_route(r'origin/save/request/accept/(?P<origin_type>.+)/url/(?P<origin_url>.+)/', # noqa
             view_name='admin-origin-save-request-accept')
@require_POST
@staff_member_required(login_url=settings.LOGIN_URL)
def _admin_origin_save_request_accept(request, origin_type, origin_url):
    SaveAuthorizedOrigin.objects.create(url=origin_url)
    create_save_origin_request(origin_type, origin_url)
    return HttpResponse(status=200)


@admin_route(r'origin/save/request/reject/(?P<origin_type>.+)/url/(?P<origin_url>.+)/', # noqa
             view_name='admin-origin-save-request-reject')
@require_POST
@staff_member_required(login_url=settings.LOGIN_URL)
def _admin_origin_save_request_reject(request, origin_type, origin_url):
    SaveUnauthorizedOrigin.objects.create(url=origin_url)
    sor = SaveOriginRequest.objects.get(origin_type=origin_type,
                                        origin_url=origin_url,
                                        status=SAVE_REQUEST_PENDING)
    sor.status = SAVE_REQUEST_REJECTED
    sor.save()
    return HttpResponse(status=200)
