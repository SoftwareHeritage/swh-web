# Copyright (C) 2018-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

from django.core.management import call_command
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt

from swh.web.archive_coverage import get_coverage_data


@xframe_options_exempt
def swh_coverage(request: HttpRequest) -> HttpResponse:

    coverage_data = get_coverage_data()

    if (
        "production" not in os.environ.get("DJANGO_SETTINGS_MODULE", "")
        and coverage_data is None
    ):
        # with production settings the command below is called from a cron,
        # with development settings, coverage data is generated here
        # and put in cache for five minutes
        call_command("generate_coverage_data", "--cache-timeout=300")
        coverage_data = get_coverage_data()

    focus = []
    focus_param = request.GET.get("focus")
    if focus_param:
        focus = focus_param.split(",")

    return render(
        request,
        "archive-coverage.html",
        {
            "origins": coverage_data,
            "focus": focus,
        },
    )
