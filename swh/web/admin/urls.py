# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.shortcuts import redirect
from django.urls import re_path as url

from swh.web.admin.adminurls import AdminUrls
import swh.web.admin.deposit  # noqa


def _admin_default_view(request):
    return redirect("admin-origin-save-requests")


urlpatterns = [
    url(r"^$", _admin_default_view, name="admin"),
]

urlpatterns += AdminUrls.get_url_patterns()
