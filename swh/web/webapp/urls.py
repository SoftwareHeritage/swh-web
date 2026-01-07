# Copyright (C) 2022-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import logging

from django_js_reverse.views import urls_js
import requests

from django.shortcuts import render
from django.templatetags.static import static
from django.urls import re_path as url
from django.views.generic.base import RedirectView

from swh.web.config import get_config
from swh.web.utils import archive, django_cache, origin_visit_types
from swh.web.utils.exc import sentry_capture_exception

swh_web_config = get_config()

SWH_FAVICON = "img/icons/swh-logo-32x32.png"

favicon_view = RedirectView.as_view(url=static(SWH_FAVICON), permanent=True)

logger = logging.getLogger(__name__)


@django_cache()
def _stat_counters():
    stat_counters = archive.stat_counters()
    url = get_config()["history_counters_url"]
    stat_counters_history = {}

    if url:
        try:
            response = requests.get(url, timeout=5)
            stat_counters_history = json.loads(response.text)
        except Exception as exc:
            sentry_capture_exception(exc)

    return {
        "stat_counters": stat_counters,
        "stat_counters_history": stat_counters_history,
    }


def default_view(request):
    return render(
        request,
        "homepage.html",
        {"visit_types": origin_visit_types(use_cache=True), **_stat_counters()},
    )


urlpatterns = [
    url(r"^favicon\.ico/$", favicon_view, name="favicon"),
    # to prevent django.template.base.VariableDoesNotExist exception when
    # browsing django admin site
    url(r"^favicon\.ico$", favicon_view, name="favicon-no-trailing-slash"),
    url(r"^$", default_view, name="swh-web-homepage"),
    url(r"^jsreverse/$", urls_js, name="js-reverse"),
]
