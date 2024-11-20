# Copyright (C) 2017-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import path as url

from swh.web.browse.browseurls import browse_urls
from swh.web.browse.identifiers import swhid_browse
import swh.web.browse.views.content  # noqa
import swh.web.browse.views.directory  # noqa
import swh.web.browse.views.iframe  # noqa
import swh.web.browse.views.origin  # noqa
import swh.web.browse.views.release  # noqa
import swh.web.browse.views.revision  # noqa
import swh.web.browse.views.snapshot  # noqa
from swh.web.utils import origin_visit_types, reverse


def _browse_help_view(request: HttpRequest) -> HttpResponse:
    return render(
        request, "browse-help.html", {"heading": "How to browse the archive ?"}
    )


def _browse_search_view(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "browse-search.html",
        {
            "heading": "Search software origins to browse",
            "visit_types": origin_visit_types(use_cache=True),
        },
    )


def _browse_origin_save_view(request: HttpRequest) -> HttpResponse:
    return redirect(reverse("origin-save"))


def _browse_swhid_iframe_legacy(request: HttpRequest, swhid: str) -> HttpResponse:
    return redirect(reverse("browse-swhid-iframe", url_args={"swhid": swhid}))


urlpatterns = [
    url("browse/", _browse_search_view),
    url("browse/help/", _browse_help_view, name="browse-help"),
    url("browse/search/", _browse_search_view, name="browse-search"),
    # for backward compatibility
    url("browse/origin/save/", _browse_origin_save_view, name="browse-origin-save"),
    url(
        "browse/<swhid:swhid>/",
        swhid_browse,
        name="browse-swhid-legacy",
    ),
    url(
        "embed/<swhid:swhid>/",
        _browse_swhid_iframe_legacy,
        name="browse-swhid-iframe-legacy",
    ),
    # keep legacy SWHID resolving URL with trailing slash for backward compatibility
    url(
        "<swhid:swhid>/",
        swhid_browse,
        name="browse-swhid-legacy",
    ),
    url(
        "<swhid:swhid>",
        swhid_browse,
        name="browse-swhid",
    ),
    *browse_urls.get_url_patterns(),
]
