# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from swh.web.api.apiurls import APIUrls
import swh.web.api.views.content  # noqa
import swh.web.api.views.directory  # noqa
import swh.web.api.views.identifiers  # noqa
import swh.web.api.views.origin  # noqa
import swh.web.api.views.origin_save  # noqa
import swh.web.api.views.ping  # noqa
import swh.web.api.views.release  # noqa
import swh.web.api.views.revision  # noqa
import swh.web.api.views.snapshot  # noqa
import swh.web.api.views.stat  # noqa
import swh.web.api.views.vault  # noqa


@login_required(login_url="/oidc/login/", redirect_field_name="next_path")
def _tokens_view(request):
    return render(request, "api/tokens.html")


urlpatterns = APIUrls.get_url_patterns()
urlpatterns.append(url(r"^tokens/$", _tokens_view, name="api-tokens"))
