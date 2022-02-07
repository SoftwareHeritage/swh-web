# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.db import IntegrityError
from django.db.models import Q
from django.http.response import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseNotFound,
)
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from swh.web.auth.models import UserMailmap
from swh.web.auth.utils import MAILMAP_PERMISSION


class UserMailmapSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMailmap
        fields = "__all__"


@api_view(["GET"])
def profile_list_mailmap(request: Request) -> HttpResponse:
    if not request.user.has_perm(MAILMAP_PERMISSION):
        return HttpResponseForbidden()

    mms = UserMailmap.objects.filter(user_id=str(request.user.id),).all()
    return Response(UserMailmapSerializer(mms, many=True).data)


@api_view(["POST"])
def profile_add_mailmap(request: Request) -> HttpResponse:
    if not request.user.has_perm(MAILMAP_PERMISSION):
        return HttpResponseForbidden()

    try:
        UserMailmap.objects.create(user_id=str(request.user.id), **request.data)
    except IntegrityError:
        return HttpResponseBadRequest("This 'from_email' already exists.")
    mm = UserMailmap.objects.get(
        user_id=str(request.user.id), from_email=request.data.get("from_email")
    )
    return Response(UserMailmapSerializer(mm).data)


@api_view(["POST"])
def profile_update_mailmap(request: Request) -> HttpResponse:
    if not request.user.has_perm(MAILMAP_PERMISSION):
        return HttpResponseForbidden()

    try:
        from_email = request.data.pop("from_email")
    except KeyError:
        return HttpResponseBadRequest("Missing from_email value")

    user_id = str(request.user.id)

    try:
        to_update = (
            UserMailmap.objects.filter(Q(user_id__isnull=True) | Q(user_id=user_id))
            .filter(from_email=from_email)
            .get()
        )
    except UserMailmap.DoesNotExist:
        return HttpResponseNotFound()

    for attr, value in request.data.items():
        setattr(to_update, attr, value)

    to_update.save()

    mm = UserMailmap.objects.get(user_id=user_id, from_email=from_email)
    return Response(UserMailmapSerializer(mm).data)


urlpatterns = [
    url(r"^profile/mailmap/list$", profile_list_mailmap, name="profile-mailmap-list",),
    url(r"^profile/mailmap/add$", profile_add_mailmap, name="profile-mailmap-add",),
    url(
        r"^profile/mailmap/update$",
        profile_update_mailmap,
        name="profile-mailmap-update",
    ),
]
