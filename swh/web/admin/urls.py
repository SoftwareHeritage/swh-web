# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

from django.conf import settings
from django.contrib import admin
from django.urls import path as url

from swh.web.config import get_config, oidc_enabled

# prevent code execution when building documentation to avoid errors
# with autodoc processing
if "SWH_DOC_BUILD" not in os.environ:
    config = get_config()

    if oidc_enabled():
        # use swh-auth views in admin site for login/logout when webapp
        # uses Keycloak for authentication
        from swh.auth.django.views import oidc_login, oidc_logout

        admin.site.login = oidc_login  # type: ignore[assignment]
        admin.site.logout = oidc_logout  # type: ignore[assignment]

    if "swh.web.add_forge_now" in settings.SWH_DJANGO_APPS:
        # register add forge now request model as manageable by admin site
        from swh.web.add_forge_now.models import Request

        if not admin.site.is_registered(Request):
            admin.site.register(Request)

    if "swh.web.save_code_now" in settings.SWH_DJANGO_APPS:
        # register save code now request model as manageable by admin site
        from swh.web.save_code_now.models import SaveOriginRequest

        if not admin.site.is_registered(SaveOriginRequest):
            admin.site.register(SaveOriginRequest)

    admin.site.site_header = "swh-web management"
    admin.site.site_title = "Software Heritage Web Application management"

    urlpatterns = [
        url("manage/", admin.site.urls),
    ]
