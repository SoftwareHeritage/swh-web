# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from importlib.util import find_spec
from typing import List, Union

from django.conf import settings
from django.conf.urls import handler400, handler403, handler404, handler500, include
from django.contrib.staticfiles.views import serve
from django.urls import URLPattern, URLResolver
from django.urls import re_path as url

from swh.web.config import get_config
from swh.web.utils.exc import swh_handle400, swh_handle403, swh_handle404, swh_handle500

swh_web_config = get_config()

urlpatterns: List[Union[URLPattern, URLResolver]] = []

# Register URLs for each SWH Django application
for app in settings.SWH_DJANGO_APPS:
    app_urls = app + ".urls"
    try:
        app_urls_spec = find_spec(app_urls)
        if app_urls_spec is not None:
            urlpatterns.append(url(r"^", include(app_urls)))
    except ModuleNotFoundError:
        assert False, f"Django application {app} not found !"


# allow to serve assets through django staticfiles
# even if settings.DEBUG is False
def insecure_serve(request, path, **kwargs):
    return serve(request, path, insecure=True, **kwargs)


# enable to serve compressed assets through django development server
if swh_web_config["serve_assets"]:
    static_pattern = r"^%s(?P<path>.*)/$" % settings.STATIC_URL[1:]
    urlpatterns.append(url(static_pattern, insecure_serve))


handler400 = swh_handle400  # noqa
handler403 = swh_handle403  # noqa
handler404 = swh_handle404  # noqa
handler500 = swh_handle500  # noqa
