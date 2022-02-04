# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.http.response import HttpResponse, HttpResponseForbidden
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


@api_view(["POST"])
def profile_add_mailmap(request: Request) -> HttpResponse:
    if not request.user.has_perm(MAILMAP_PERMISSION):
        return HttpResponseForbidden()

    UserMailmap.objects.create(user_id=str(request.user.id), **request.data)
    mm = UserMailmap.objects.get(
        user_id=str(request.user.id), from_email=request.data.get("from_email")
    )
    return Response(UserMailmapSerializer(mm).data)


@api_view(["POST"])
def profile_update_mailmap(request: Request) -> HttpResponse:
    if not request.user.has_perm(MAILMAP_PERMISSION):
        return HttpResponseForbidden()

    UserMailmap.objects.update(user_id=str(request.user.id), **request.data)
    mm = UserMailmap.objects.get(
        user_id=str(request.user.id), from_email=request.data.get("from_email")
    )
    return Response(UserMailmapSerializer(mm).data)


urlpatterns = [
    url(r"^profile/mailmap/add$", profile_add_mailmap, name="profile-mailmap-add",),
    url(
        r"^profile/mailmap/update$",
        profile_update_mailmap,
        name="profile-mailmap-update",
    ),
]
