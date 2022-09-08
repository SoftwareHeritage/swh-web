# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render

from swh.web.add_forge_now.models import RequestStatus
from swh.web.auth.utils import is_add_forge_now_moderator


@user_passes_test(is_add_forge_now_moderator)
def add_forge_now_requests_moderation_dashboard(request):
    """Moderation dashboard to allow listing current requests."""
    return render(
        request,
        "add-forge-requests-moderation.html",
        {"heading": "Add forge now requests moderation"},
    )


@user_passes_test(is_add_forge_now_moderator)
def add_forge_now_request_dashboard(request, request_id):
    """Moderation dashboard to allow listing current requests."""
    return render(
        request,
        "add-forge-request-dashboard.html",
        {
            "request_id": request_id,
            "heading": "Add forge now request dashboard",
            "next_statuses_for": RequestStatus.next_statuses_str(),
        },
    )
