# Copyright (C) 2017-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django_js_reverse.views import urls_js

from django.conf import settings
from django.conf.urls import (
    handler400,
    handler403,
    handler404,
    handler500,
    include,
    url,
)
from django.contrib.auth.views import LogoutView
from django.contrib.staticfiles.views import serve
from django.shortcuts import render
from django.views.generic.base import RedirectView

from swh.web.browse.identifiers import swhid_browse
from swh.web.common.exc import (
    swh_handle400,
    swh_handle403,
    swh_handle404,
    swh_handle500,
)
from swh.web.config import get_config

swh_web_config = get_config()

favicon_view = RedirectView.as_view(
    url="/static/img/icons/swh-logo-32x32.png", permanent=True
)


def _default_view(request):
    return render(request, "homepage.html")


urlpatterns = [
    url(r"^admin/", include("swh.web.admin.urls")),
    url(r"^favicon\.ico$", favicon_view),
    url(r"^api/", include("swh.web.api.urls")),
    url(r"^browse/", include("swh.web.browse.urls")),
    url(r"^$", _default_view, name="swh-web-homepage"),
    url(r"^jsreverse/$", urls_js, name="js_reverse"),
    # keep legacy SWHID resolving URL with trailing slash for backward compatibility
    url(
        r"^(?P<swhid>swh:[0-9]+:[a-z]+:[0-9a-f]+.*)/$",
        swhid_browse,
        name="browse-swhid-legacy",
    ),
    url(
        r"^(?P<swhid>swh:[0-9]+:[a-z]+:[0-9a-f]+.*)$",
        swhid_browse,
        name="browse-swhid",
    ),
    url(r"^", include("swh.web.misc.urls")),
    url(r"^", include("swh.web.auth.views")),
    url(r"^logout/$", LogoutView.as_view(template_name="logout.html"), name="logout"),
]


# allow to serve assets through django staticfiles
# even if settings.DEBUG is False
def insecure_serve(request, path, **kwargs):
    return serve(request, path, insecure=True, **kwargs)


# enable to serve compressed assets through django development server
if swh_web_config["serve_assets"]:
    static_pattern = r"^%s(?P<path>.*)$" % settings.STATIC_URL[1:]
    urlpatterns.append(url(static_pattern, insecure_serve))


handler400 = swh_handle400  # noqa
handler403 = swh_handle403  # noqa
handler404 = swh_handle404  # noqa
handler500 = swh_handle500  # noqa
