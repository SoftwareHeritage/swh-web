# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

from swh.web.admin.adminurls import admin_route
from swh.web.auth.utils import is_add_forge_now_moderator


@admin_route(
    r"add-forge/requests/",
    view_name="add-forge-now-requests-moderation",
)
@user_passes_test(is_add_forge_now_moderator, login_url=settings.LOGIN_URL)
def add_forge_now_requests_moderation_dashboard(request):
    """Moderation dashboard to allow listing current requests."""
    return render(
        request,
        "add_forge_now/requests-moderation.html",
        {"heading": "Add forge now requests moderation"},
    )


@admin_route(
    r"add-forge/request/(?P<request_id>(\d)+)/",
    view_name="add-forge-now-request-dashboard",
)
@user_passes_test(is_add_forge_now_moderator, login_url=settings.LOGIN_URL)
def add_forge_now_request_dashboard(request, request_id):
    """Moderation dashboard to allow listing current requests."""
    return render(
        request,
        "add_forge_now/request-dashboard.html",
        {"request_id": request_id, "heading": "Add forge now request dashboard"},
    )
