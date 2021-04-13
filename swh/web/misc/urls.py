# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

import requests
import sentry_sdk

from django.conf.urls import include, url
from django.contrib.staticfiles import finders
from django.http import JsonResponse
from django.shortcuts import render

from swh.web.common import archive
from swh.web.config import get_config
from swh.web.misc.metrics import prometheus_metrics


def _jslicenses(request):
    jslicenses_file = finders.find("jssources/jslicenses.json")
    jslicenses_data = json.load(open(jslicenses_file))
    jslicenses_data = sorted(
        jslicenses_data.items(), key=lambda item: item[0].split("/")[-1]
    )
    return render(request, "misc/jslicenses.html", {"jslicenses_data": jslicenses_data})


def _stat_counters(request):
    stat_counters = archive.stat_counters()
    url = get_config()["history_counters_url"]
    stat_counters_history = {}
    try:
        response = requests.get(url, timeout=5)
        stat_counters_history = json.loads(response.text)
    except Exception as exc:
        sentry_sdk.capture_exception(exc)

    counters = {
        "stat_counters": stat_counters,
        "stat_counters_history": stat_counters_history,
    }
    return JsonResponse(counters)


urlpatterns = [
    url(r"^", include("swh.web.misc.coverage")),
    url(r"^jslicenses/$", _jslicenses, name="jslicenses"),
    url(r"^", include("swh.web.misc.origin_save")),
    url(r"^stat_counters/", _stat_counters, name="stat-counters"),
    url(r"^", include("swh.web.misc.badges")),
    url(r"^metrics/prometheus/$", prometheus_metrics, name="metrics-prometheus"),
]


# when running end to end tests trough cypress, declare some extra
# endpoints to provide input data for some of those tests
if get_config()["e2e_tests_mode"]:
    from swh.web.tests.views import (
        get_content_code_data_all_exts,
        get_content_code_data_all_filenames,
        get_content_code_data_by_ext,
        get_content_code_data_by_filename,
        get_content_other_data_by_ext,
    )

    urlpatterns.append(
        url(
            r"^tests/data/content/code/extension/(?P<ext>.+)/$",
            get_content_code_data_by_ext,
            name="tests-content-code-extension",
        )
    )
    urlpatterns.append(
        url(
            r"^tests/data/content/other/extension/(?P<ext>.+)/$",
            get_content_other_data_by_ext,
            name="tests-content-other-extension",
        )
    )
    urlpatterns.append(
        url(
            r"^tests/data/content/code/extensions/$",
            get_content_code_data_all_exts,
            name="tests-content-code-extensions",
        )
    )
    urlpatterns.append(
        url(
            r"^tests/data/content/code/filename/(?P<filename>.+)/$",
            get_content_code_data_by_filename,
            name="tests-content-code-filename",
        )
    )
    urlpatterns.append(
        url(
            r"^tests/data/content/code/filenames/$",
            get_content_code_data_all_filenames,
            name="tests-content-code-filenames",
        )
    )
