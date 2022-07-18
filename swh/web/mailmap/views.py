# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
from typing import Any, Dict

from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db import IntegrityError
from django.db.models import Q
from django.http.request import HttpRequest
from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseNotFound,
    JsonResponse,
)
from django.shortcuts import render
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from swh.web.auth.utils import (
    MAILMAP_ADMIN_PERMISSION,
    MAILMAP_PERMISSION,
    any_permission_required,
)
from swh.web.mailmap.models import UserMailmap, UserMailmapEvent


class UserMailmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMailmap
        fields = "__all__"


@api_view(["GET"])
@any_permission_required(MAILMAP_PERMISSION, MAILMAP_ADMIN_PERMISSION)
def profile_list_mailmap(request: Request) -> HttpResponse:
    mailmap_admin = request.user.has_perm(MAILMAP_ADMIN_PERMISSION)

    mms = UserMailmap.objects.filter(
        user_id=None if mailmap_admin else str(request.user.id)
    ).all()
    return Response(UserMailmapSerializer(mms, many=True).data)


@api_view(["POST"])
@any_permission_required(MAILMAP_PERMISSION, MAILMAP_ADMIN_PERMISSION)
def profile_add_mailmap(request: Request) -> HttpResponse:
    mailmap_admin = request.user.has_perm(MAILMAP_ADMIN_PERMISSION)

    event = UserMailmapEvent.objects.create(
        user_id=str(request.user.id),
        request_type="add",
        request=json.dumps(request.data),
    )

    from_email = request.data.pop("from_email", None)
    if not from_email:
        return HttpResponseBadRequest(
            "'from_email' must be provided and non-empty.", content_type="text/plain"
        )

    user_id = None if mailmap_admin else str(request.user.id)

    from_email_verified = request.data.pop("from_email_verified", False)
    if mailmap_admin:
        # consider email verified when mailmap is added by admin
        from_email_verified = True

    try:
        UserMailmap.objects.create(
            user_id=user_id,
            from_email=from_email,
            from_email_verified=from_email_verified,
            **request.data,
        )
    except IntegrityError as e:
        if (
            "user_mailmap_from_email_key" in e.args[0]
            or "user_mailmap.from_email" in e.args[0]
        ):
            return HttpResponseBadRequest(
                "This 'from_email' already exists.", content_type="text/plain"
            )
        else:
            raise

    event.successful = True
    event.save()

    mm = UserMailmap.objects.get(user_id=user_id, from_email=from_email)
    return Response(UserMailmapSerializer(mm).data)


@api_view(["POST"])
@any_permission_required(MAILMAP_PERMISSION, MAILMAP_ADMIN_PERMISSION)
def profile_update_mailmap(request: Request) -> HttpResponse:
    mailmap_admin = request.user.has_perm(MAILMAP_ADMIN_PERMISSION)

    event = UserMailmapEvent.objects.create(
        user_id=str(request.user.id),
        request_type="update",
        request=json.dumps(request.data),
    )

    from_email = request.data.pop("from_email", None)
    if not from_email:
        return HttpResponseBadRequest(
            "'from_email' must be provided and non-empty.", content_type="text/plain"
        )

    user_id = None if mailmap_admin else str(request.user.id)

    try:
        to_update = (
            UserMailmap.objects.filter(user_id=user_id)
            .filter(from_email=from_email)
            .get()
        )
    except UserMailmap.DoesNotExist:
        return HttpResponseNotFound("'from_email' cannot be found in mailmaps.")

    for attr, value in request.data.items():
        setattr(to_update, attr, value)

    to_update.save()

    event.successful = True
    event.save()

    mm = UserMailmap.objects.get(user_id=user_id, from_email=from_email)
    return Response(UserMailmapSerializer(mm).data)


@any_permission_required(MAILMAP_PERMISSION, MAILMAP_ADMIN_PERMISSION)
def profile_list_mailmap_datatables(request: HttpRequest) -> HttpResponse:
    mailmap_admin = request.user.has_perm(MAILMAP_ADMIN_PERMISSION)

    mailmaps = UserMailmap.objects.filter(
        user_id=None if mailmap_admin else str(request.user.id)
    )

    search_value = request.GET.get("search[value]", "")

    column_order = request.GET.get("order[0][column]")
    field_order = request.GET.get(f"columns[{column_order}][name]", "from_email")
    order_dir = request.GET.get("order[0][dir]", "asc")
    if order_dir == "desc":
        field_order = "-" + field_order

    mailmaps = mailmaps.order_by(field_order)

    table_data: Dict[str, Any] = {}
    table_data["draw"] = int(request.GET.get("draw", 1))
    table_data["recordsTotal"] = mailmaps.count()

    length = int(request.GET.get("length", 10))
    page = int(request.GET.get("start", 0)) / length + 1

    if search_value:
        mailmaps = mailmaps.filter(
            Q(from_email__icontains=search_value)
            | Q(display_name__icontains=search_value)
        )

    table_data["recordsFiltered"] = mailmaps.count()

    paginator = Paginator(mailmaps, length)

    mailmaps_data = [
        UserMailmapSerializer(mm).data for mm in paginator.page(int(page)).object_list
    ]

    table_data["data"] = mailmaps_data

    return JsonResponse(table_data)


@permission_required(MAILMAP_ADMIN_PERMISSION)
def admin_mailmap(request):
    return render(request, "admin/mailmap.html")
