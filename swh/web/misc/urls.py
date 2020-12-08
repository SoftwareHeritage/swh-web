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
from swh.web.common.utils import parse_iso8601_date_to_utc
from swh.web.config import get_config
from swh.web.misc.metrics import prometheus_metrics


def _jslicenses(request):
    jslicenses_file = finders.find("jssources/jslicenses.json")
    jslicenses_data = json.load(open(jslicenses_file))
    jslicenses_data = sorted(
        jslicenses_data.items(), key=lambda item: item[0].split("/")[-1]
    )
    return render(request, "misc/jslicenses.html", {"jslicenses_data": jslicenses_data})


# historical data for backfilling missing counter values
# https://forge.softwareheritage.org/T2619
_stat_counters_backfill = {
    "2015-09-01": {"revision": 0, "origin": 0, "content": 0},
    "2016-07-01": {"revision": 594305600, "origin": 22777052},
    "2016-09-14": {"revision": 644628800, "origin": 25258776},
    "2016-11-24": {"revision": 704845952, "origin": 53488904},
    "2017-05-10": {"revision": 780882048, "origin": 58257484},
    "2017-09-26": {"revision": 853277241, "origin": 65546644},
    "2018-01-24": {"revision": 943061517, "origin": 71814787},
    "2018-02-13": {"revision": 946216028, "origin": 81655813},
    "2018-03-25": {"revision": 980390191, "origin": 83797945},
    "2018-10-04": {"revision": 1126348335, "origin": 85202432},
    "2019-01-27": {"revision": 1248389319, "origin": 88288721},
    "2019-04-08": {"revision": 1293870115, "origin": 88297714},
    "2019-06-27": {"revision": 1326776432, "origin": 89301694},
    "2019-07-24": {"revision": 1358421267, "origin": 89601149},
    "2019-09-22": {"revision": 1379380527, "origin": 90231104},
    "2019-09-29": {"revision": 1385477933, "origin": 90487661},
    "2020-01-01": {"revision": 1414420369, "origin": 91400586},
    "2020-02-06": {"revision": 1428955761, "origin": 91512130},
    "2020-04-07": {"revision": 1590436149, "origin": 107875943},
    "2020-05-17": {"revision": 1717420203, "origin": 121172621},
    "2020-05-27": {"revision": 1744034936, "origin": 123781438},
}


def _stat_counters(request):
    stat_counters = archive.stat_counters()
    url = get_config()["history_counters_url"]
    stat_counters_history = {}
    try:
        response = requests.get(url, timeout=5)
        stat_counters_history = json.loads(response.text)
        for d, object_counts in _stat_counters_backfill.items():
            # convert date to javascript timestamp (in ms)
            timestamp = int(parse_iso8601_date_to_utc(d).timestamp()) * 1000
            for object_type, object_count in object_counts.items():
                stat_counters_history[object_type].append([timestamp, object_count])
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
