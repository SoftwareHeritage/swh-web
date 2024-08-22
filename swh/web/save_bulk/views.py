# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import EmptyPage, Paginator
from django.http.request import HttpRequest
from django.http.response import JsonResponse

from swh.web.save_bulk.models import SaveBulkOrigin, SaveBulkRequest
from swh.web.utils.exc import NotFoundExc


def api_save_bulk_origins_list(request: HttpRequest, request_id: str) -> JsonResponse:
    """View that returns a list of origins and their visit types, submitted by a user
    through a POST request to the /api/1/origin/save/bulk/ endpoint, in a paginated
    way. Its purpose is to be consumed by the save-bulk lister that checks origins
    can be archived and schedules their loadings.
    """
    try:
        save_bulk_request = SaveBulkRequest.objects.get(id=request_id)
    except ObjectDoesNotExist:
        raise NotFoundExc(f"Bulk save request with id {request_id} not found!")

    page_num = int(request.GET.get("page", 1))
    per_page = int(request.GET.get("per_page", 1000))
    per_page = min(per_page, 1000)

    origins = SaveBulkOrigin.objects.filter(requests__in=[save_bulk_request])
    paginator = Paginator(origins.order_by("origin_url"), per_page)

    try:
        origins_list = paginator.page(page_num).object_list
    except EmptyPage:
        origins_list = []

    return JsonResponse(
        [
            {"origin_url": origin.origin_url, "visit_type": origin.visit_type}
            for origin in origins_list
        ],
        safe=False,
    )
