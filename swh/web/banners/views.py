# Copyright (C) 2021-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import requests

from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt

from swh.web.config import get_config


@xframe_options_exempt
def fundraising_banner(request):
    config = get_config()
    public_key = config["give"]["public_key"]
    token = config["give"]["token"]
    give_api_forms_url = (
        "https://www.softwareheritage.org/give-api/v1/forms/"
        f"?key={public_key}&token={token}&form=27047"
    )

    donations_goal = 100
    nb_donations = -1

    try:
        fundraising_form = requests.get(give_api_forms_url).json().get("forms", [])
        if fundraising_form:
            nb_donations = int(
                fundraising_form[0]
                .get("stats", {})
                .get("total", {})
                .get("donations", -1)
            )
    except Exception:
        pass

    goal_percent = int(nb_donations / donations_goal * 100)

    lang = request.GET.get("lang")

    return render(
        request,
        "fundraising-banner.html",
        {
            "nb_donations": nb_donations,
            "donations_goal": donations_goal,
            "goal_percent": goal_percent,
            "lang": lang if lang else "en",
            "donation_form_url": (
                "https://www.softwareheritage.org/donations/"
                "help-preserve-sourcecode-2021/"
            ),
        },
    )


@xframe_options_exempt
def hiring_banner(request):

    lang = request.GET.get("lang")

    return render(
        request,
        "hiring-banner-iframe.html",
        {
            "lang": lang if lang else "en",
        },
    )
