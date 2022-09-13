# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from django.contrib.staticfiles import finders
from django.shortcuts import render
from django.urls import re_path as url


def jslicenses(request):
    jslicenses_file = finders.find("jssources/jslicenses.json")
    jslicenses_data = {}
    if jslicenses_file is not None:
        jslicenses_data = json.load(open(jslicenses_file))
    jslicenses_data = sorted(
        jslicenses_data.items(), key=lambda item: item[0].split("/")[-1]
    )
    return render(request, "jslicenses.html", {"jslicenses_data": jslicenses_data})


urlpatterns = [
    url(r"^jslicenses/$", jslicenses, name="jslicenses"),
]
