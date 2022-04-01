# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect

from swh.web.admin.adminurls import AdminUrls
import swh.web.admin.deposit  # noqa
import swh.web.admin.mailmap  # noqa
import swh.web.admin.origin_save  # noqa
from swh.web.config import is_feature_enabled

if is_feature_enabled("add_forge_now"):
    import swh.web.admin.add_forge_now  # noqa


def _admin_default_view(request):
    return redirect("admin-origin-save-requests")


urlpatterns = [
    url(r"^$", _admin_default_view, name="admin"),
    url(r"^login/$", LoginView.as_view(template_name="login.html"), name="login"),
]

urlpatterns += AdminUrls.get_url_patterns()
