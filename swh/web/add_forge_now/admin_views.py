# Copyright (C) 2022-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

from swh.web.add_forge_now.models import RequestStatus
from swh.web.auth.utils import (
    ADD_FORGE_NOW_CHANGE_REQUEST_PERMISSION,
    ADD_FORGE_NOW_VIEW_REQUEST_PERMISSION,
    is_add_forge_now_moderator,
)
from swh.web.utils import reverse

if TYPE_CHECKING:
    from django.http.request import HttpRequest
    from django.http.response import HttpResponse


@user_passes_test(is_add_forge_now_moderator)
def add_forge_now_requests_moderation_dashboard(request: HttpRequest) -> HttpResponse:
    """Moderation dashboard to allow listing current requests."""
    return render(
        request,
        "add-forge-requests-moderation.html",
        {"heading": "Add forge now requests moderation"},
    )


@user_passes_test(is_add_forge_now_moderator)
def add_forge_now_request_dashboard(
    request: HttpRequest, request_id: int
) -> HttpResponse:
    """Moderation dashboard to allow listing current requests."""
    request_edit_url = ""
    if "swh.web.admin" in settings.SWH_DJANGO_APPS and request.user.has_perms(
        (
            ADD_FORGE_NOW_VIEW_REQUEST_PERMISSION,
            ADD_FORGE_NOW_CHANGE_REQUEST_PERMISSION,
        )
    ):
        request_edit_url = reverse(
            "admin:swh_web_add_forge_now_request_change",
            url_args={"object_id": request_id},
        )

    return render(
        request,
        "add-forge-request-dashboard.html",
        {
            "request_id": request_id,
            "heading": "Add forge now request dashboard",
            "next_statuses_for": RequestStatus.next_statuses_str(),
            "request_edit_url": request_edit_url,
        },
    )
