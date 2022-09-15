# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import logging

from django_js_reverse.views import urls_js
import requests

from django.http import JsonResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.urls import re_path as url
from django.views.generic.base import RedirectView

from swh.web.config import get_config
from swh.web.utils import archive, is_swh_web_production, origin_visit_types
from swh.web.utils.exc import sentry_capture_exception

swh_web_config = get_config()

SWH_FAVICON = "img/icons/swh-logo-32x32.png"

favicon_view = RedirectView.as_view(url=static(SWH_FAVICON), permanent=True)

logger = logging.getLogger(__name__)


def default_view(request):
    return render(
        request,
        "homepage.html",
        {"visit_types": origin_visit_types(use_cache=is_swh_web_production(request))},
    )


def stat_counters(request):
    stat_counters = archive.stat_counters()
    url = get_config()["history_counters_url"]
    stat_counters_history = {}

    try:
        response = requests.get(url, timeout=5)
        stat_counters_history = json.loads(response.text)
    except Exception as exc:
        logger.exception(exc)
        sentry_capture_exception(exc)

    counters = {
        "stat_counters": stat_counters,
        "stat_counters_history": stat_counters_history,
    }
    return JsonResponse(counters)


urlpatterns = [
    url(r"^favicon\.ico/$", favicon_view, name="favicon"),
    url(r"^$", default_view, name="swh-web-homepage"),
    url(r"^jsreverse/$", urls_js, name="js-reverse"),
    url(r"^stat_counters/$", stat_counters, name="stat-counters"),
]
