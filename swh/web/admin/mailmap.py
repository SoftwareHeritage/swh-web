# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.contrib.auth.decorators import permission_required
from django.shortcuts import render

from swh.web.admin.adminurls import admin_route
from swh.web.auth.utils import MAILMAP_ADMIN_PERMISSION


@admin_route(r"mailmap/", view_name="admin-mailmap")
@permission_required(MAILMAP_ADMIN_PERMISSION)
def _admin_mailmap(request):
    return render(request, "admin/mailmap.html")
