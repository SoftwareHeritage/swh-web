# Copyright (C) 2024-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.conf import settings
from django.contrib import admin
from django.contrib.admin.forms import AdminAuthenticationForm
from django.urls import path as url

from swh.web.auth.utils import (
    ADD_FORGE_NOW_CHANGE_REQUEST_PERMISSION,
    ADD_FORGE_NOW_VIEW_REQUEST_PERMISSION,
)
from swh.web.config import get_config, oidc_enabled

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


def _user_can_access_admin_views(user):
    # give access to admin UI to staff users but also to non staff users
    # having adequate permissions to edit AFN requests
    return (user.is_active and user.is_staff) or (
        user.is_active
        and user.has_perms(
            [
                ADD_FORGE_NOW_VIEW_REQUEST_PERMISSION,
                ADD_FORGE_NOW_CHANGE_REQUEST_PERMISSION,
            ]
        )
    )


class SwhAdminAuthenticationForm(AdminAuthenticationForm):
    def confirm_login_allowed(self, user):
        return _user_can_access_admin_views(user)


admin.site.login_form = SwhAdminAuthenticationForm
admin.site.has_permission = lambda request: _user_can_access_admin_views(request.user)  # type: ignore [method-assign]
admin.site.site_header = "swh-web management"
admin.site.site_title = "Software Heritage Web Application management"

admin_urls = url("manage/", admin.site.urls)
# to prevent noisy tracebacks in debug mode when a redirection is performed
setattr(admin_urls, "name", "manage")

urlpatterns = [admin_urls]
