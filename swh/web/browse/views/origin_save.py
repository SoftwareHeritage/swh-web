# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST

from swh.web.browse.browseurls import browse_route
from swh.web.common.exc import ForbiddenExc
from swh.web.common.models import SaveOriginRequest
from swh.web.common.utils import is_recaptcha_valid
from swh.web.common.origin_save import (
    create_save_origin_request, get_savable_origin_types,
    get_save_origin_requests_from_queryset
)


@browse_route(r'origin/save/(?P<origin_type>.+)/url/(?P<origin_url>.+)/',
              view_name='browse-origin-save-request')
@require_POST
def _browse_origin_save_request(request, origin_type, origin_url):
    body_unicode = request.body.decode('utf-8')
    body = json.loads(body_unicode)
    if is_recaptcha_valid(request, body['g-recaptcha-response']):
        try:
            response = json.dumps(create_save_origin_request(origin_type,
                                                             origin_url),
                                  separators=(',', ': '))
            return HttpResponse(response, content_type='application/json')
        except ForbiddenExc as exc:
            return HttpResponseForbidden(str(exc))
    else:
        return HttpResponseForbidden('The reCAPTCHA could not be validated !')


@browse_route(r'origin/save/types/list/',
              view_name='browse-origin-save-types-list')
def _browse_origin_save_types_list(request):
    origin_types = json.dumps(get_savable_origin_types(),
                              separators=(',', ': '))
    return HttpResponse(origin_types, content_type='application/json')


@browse_route(r'origin/save/requests/list/(?P<status>.+)/',
              view_name='browse-origin-save-requests-list')
def _browse_origin_save_requests_list(request, status):

    if status != 'all':
        save_requests = SaveOriginRequest.objects.filter(status=status)
    else:
        save_requests = SaveOriginRequest.objects.all()

    table_data = {}
    table_data['recordsTotal'] = save_requests.count()
    table_data['draw'] = int(request.GET['draw'])

    search_value = request.GET['search[value]']

    column_order = request.GET['order[0][column]']
    field_order = request.GET['columns[%s][name]' % column_order]
    order_dir = request.GET['order[0][dir]']
    if order_dir == 'desc':
        field_order = '-' + field_order

    save_requests = save_requests.order_by(field_order)

    length = int(request.GET['length'])
    page = int(request.GET['start']) / length + 1
    save_requests = get_save_origin_requests_from_queryset(save_requests)
    if search_value:
        save_requests = \
            [sr for sr in save_requests
             if search_value.lower() in sr['save_request_status'].lower()
             or search_value.lower() in sr['save_task_status'].lower()
             or search_value.lower() in sr['origin_type'].lower()
             or search_value.lower() in sr['origin_url'].lower()]

    table_data['recordsFiltered'] = len(save_requests)
    paginator = Paginator(save_requests, length)
    table_data['data'] = paginator.page(page).object_list
    table_data_json = json.dumps(table_data, separators=(',', ': '))
    return HttpResponse(table_data_json, content_type='application/json')
