# Copyright (C) 2021-2022 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict, List, Optional, cast

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from swh.web.browse.browseurls import browse_route
from swh.web.browse.snapshot_context import (
    browse_snapshot_directory,
    get_snapshot_context,
)
from swh.web.utils import (
    archive,
    format_utc_iso_date,
    parse_iso8601_date_to_utc,
    redirect_to_new_route,
    reverse,
)
from swh.web.utils.exc import BadInputExc
from swh.web.utils.origin_visits import get_origin_visits


@browse_route(
    r"origin/directory/",
    view_name="browse-origin-directory",
)
def origin_directory_browse(request: HttpRequest) -> HttpResponse:
    """Django view for browsing the content of a directory associated
    to an origin for a given visit.

    The URL that points to it is :http:get:`/browse/origin/directory/`
    """
    return browse_snapshot_directory(
        request,
        origin_url=request.GET.get("origin_url"),
        snapshot_id=request.GET.get("snapshot"),
        timestamp=request.GET.get("timestamp"),
        path=request.GET.get("path"),
    )


@browse_route(
    r"origin/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/directory/",
    r"origin/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/directory/(?P<path>.+)/",
    r"origin/(?P<origin_url>.+)/directory/(?P<path>.+)/",
    r"origin/(?P<origin_url>.+)/directory/",
    view_name="browse-origin-directory-legacy",
)
def origin_directory_browse_legacy(
    request: HttpRequest,
    origin_url: str,
    timestamp: Optional[str] = None,
    path: Optional[str] = None,
) -> HttpResponse:
    """Django view for browsing the content of a directory associated
    to an origin for a given visit.

    The URLs that point to it are
    :http:get:`/browse/origin/(origin_url)/directory/[(path)/]` and
    :http:get:`/browse/origin/(origin_url)/visit/(timestamp)/directory/[(path)/]`
    """
    return browse_snapshot_directory(
        request,
        origin_url=origin_url,
        snapshot_id=request.GET.get("snapshot"),
        timestamp=timestamp,
        path=path,
    )


@browse_route(
    r"origin/content/",
    view_name="browse-origin-content",
)
def origin_content_browse(request: HttpRequest) -> HttpResponse:
    """
    This route is deprecated; use http:get:`/browse/content` instead

    Django view that produces an HTML display of a content
    associated to an origin for a given visit.

    The URL that points to it is :http:get:`/browse/origin/content/`

    """
    return redirect_to_new_route(request, "browse-content")


@browse_route(
    r"origin/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/content/(?P<path>.+)/",
    r"origin/(?P<origin_url>.+)/content/(?P<path>.+)/",
    r"origin/(?P<origin_url>.+)/content/",
    view_name="browse-origin-content-legacy",
)
def origin_content_browse_legacy(
    request: HttpRequest,
    origin_url: str,
    path: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> HttpResponse:
    """
    This route is deprecated; use http:get:`/browse/content` instead

    Django view that produces an HTML display of a content
    associated to an origin for a given visit.

    The URLs that point to it are
    :http:get:`/browse/origin/(origin_url)/content/(path)/` and
    :http:get:`/browse/origin/(origin_url)/visit/(timestamp)/content/(path)/`

    """
    return redirect_to_new_route(request, "browse-content")


@browse_route(
    r"origin/log/",
    view_name="browse-origin-log",
)
def origin_log_browse(request: HttpRequest) -> HttpResponse:
    """
    This route is deprecated; use http:get:`/browse/snapshot/log` instead

    Django view that produces an HTML display of revisions history (aka
    the commit log) associated to a software origin.

    The URL that points to it is :http:get:`/browse/origin/log/`
    """
    return redirect_to_new_route(request, "browse-snapshot-log")


@browse_route(
    r"origin/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/log/",
    r"origin/(?P<origin_url>.+)/log/",
    view_name="browse-origin-log-legacy",
)
def origin_log_browse_legacy(
    request: HttpRequest, origin_url: str, timestamp: Optional[str] = None
) -> HttpResponse:
    """
    This route is deprecated; use http:get:`/browse/snapshot/log` instead

    Django view that produces an HTML display of revisions history (aka
    the commit log) associated to a software origin.

    The URLs that point to it are
    :http:get:`/browse/origin/(origin_url)/log/` and
    :http:get:`/browse/origin/(origin_url)/visit/(timestamp)/log/`

    """
    return redirect_to_new_route(
        request,
        "browse-snapshot-log",
    )


@browse_route(
    r"origin/branches/",
    view_name="browse-origin-branches",
)
def origin_branches_browse(request: HttpRequest) -> HttpResponse:
    """
    This route is deprecated; use http:get:`/browse/snapshot/branches` instead

    Django view that produces an HTML display of the list of branches
    associated to an origin for a given visit.

    The URL that points to it is :http:get:`/browse/origin/branches/`

    """
    return redirect_to_new_route(request, "browse-snapshot-branches")


@browse_route(
    r"origin/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/branches/",
    r"origin/(?P<origin_url>.+)/branches/",
    view_name="browse-origin-branches-legacy",
)
def origin_branches_browse_legacy(
    request: HttpRequest, origin_url: str, timestamp: Optional[str] = None
) -> HttpResponse:
    """
    This route is deprecated; use http:get:`/browse/snapshot/branches` instead

    Django view that produces an HTML display of the list of branches
    associated to an origin for a given visit.

    The URLs that point to it are
    :http:get:`/browse/origin/(origin_url)/branches/` and
    :http:get:`/browse/origin/(origin_url)/visit/(timestamp)/branches/`

    """
    return redirect_to_new_route(request, "browse-snapshot-branches")


@browse_route(
    r"origin/releases/",
    view_name="browse-origin-releases",
)
def origin_releases_browse(request: HttpRequest) -> HttpResponse:
    """
    This route is deprecated; use http:get:`/browse/snapshot/releases` instead

    Django view that produces an HTML display of the list of releases
    associated to an origin for a given visit.

    The URL that points to it is :http:get:`/browse/origin/releases/`

    """
    return redirect_to_new_route(request, "browse-snapshot-releases")


@browse_route(
    r"origin/(?P<origin_url>.+)/visit/(?P<timestamp>.+)/releases/",
    r"origin/(?P<origin_url>.+)/releases/",
    view_name="browse-origin-releases-legacy",
)
def origin_releases_browse_legacy(
    request: HttpRequest, origin_url: str, timestamp: Optional[str] = None
) -> HttpResponse:
    """
    This route is deprecated; use http:get:`/browse/snapshot/releases` instead

    Django view that produces an HTML display of the list of releases
    associated to an origin for a given visit.

    The URLs that point to it are
    :http:get:`/browse/origin/(origin_url)/releases/` and
    :http:get:`/browse/origin/(origin_url)/visit/(timestamp)/releases/`

    """
    return redirect_to_new_route(request, "browse-snapshot-releases")


def _origin_visits_browse(
    request: HttpRequest, origin_url: Optional[str]
) -> HttpResponse:
    if origin_url is None:
        raise BadInputExc("An origin URL must be provided as query parameter.")

    origin_info = archive.lookup_origin({"url": origin_url})
    origin_visits = cast(List[Dict[str, Any]], get_origin_visits(origin_info))

    snapshot_context = get_snapshot_context(origin_url=origin_url)

    for i, visit in enumerate(origin_visits):
        url_date = format_utc_iso_date(visit["date"], "%Y-%m-%dT%H:%M:%SZ")
        visit["formatted_date"] = format_utc_iso_date(visit["date"])
        query_params = {"origin_url": origin_url, "timestamp": url_date}
        if i < len(origin_visits) - 1:
            if visit["date"] == origin_visits[i + 1]["date"]:
                query_params = {"visit_id": visit["visit"]}
        if i > 0:
            if visit["date"] == origin_visits[i - 1]["date"]:
                query_params = {"visit_id": visit["visit"]}

        snapshot = visit["snapshot"] if visit["snapshot"] else ""

        visit["url"] = reverse(
            "browse-origin-directory",
            query_params=query_params,
        )
        if not snapshot:
            visit["snapshot"] = ""
        visit["date"] = parse_iso8601_date_to_utc(visit["date"]).timestamp()

    heading = "Origin visits - %s" % origin_url

    return render(
        request,
        "browse-origin-visits.html",
        {
            "heading": heading,
            "swh_object_name": "Visits",
            "swh_object_metadata": origin_info,
            "origin_visits": origin_visits,
            "origin_info": origin_info,
            "snapshot_context": snapshot_context,
            "vault_cooking": None,
            "show_actions": False,
        },
    )


@browse_route(r"origin/visits/", view_name="browse-origin-visits")
def origin_visits_browse(request: HttpRequest) -> HttpResponse:
    """Django view that produces an HTML display of visits reporting
    for a given origin.

    The URL that points to it is
    :http:get:`/browse/origin/visits/`.
    """
    return _origin_visits_browse(request, request.GET.get("origin_url"))


@browse_route(
    r"origin/(?P<origin_url>.+)/visits/", view_name="browse-origin-visits-legacy"
)
def origin_visits_browse_legacy(request: HttpRequest, origin_url: str) -> HttpResponse:
    """Django view that produces an HTML display of visits reporting
    for a given origin.

    The URL that points to it is
    :http:get:`/browse/origin/(origin_url)/visits/`.
    """
    return _origin_visits_browse(request, origin_url)


@browse_route(r"origin/", view_name="browse-origin")
def origin_browse(request: HttpRequest) -> HttpResponse:
    """Django view that redirects to the display of the latest archived
    snapshot for a given software origin.
    """
    last_snapshot_url = reverse(
        "browse-origin-directory",
        query_params=request.GET,
    )
    return redirect(last_snapshot_url)


@browse_route(r"origin/(?P<origin_url>.+)/", view_name="browse-origin-legacy")
def origin_browse_legacy(request: HttpRequest, origin_url: str) -> HttpResponse:
    """Django view that redirects to the display of the latest archived
    snapshot for a given software origin.
    """
    last_snapshot_url = reverse(
        "browse-origin-directory",
        query_params={"origin_url": origin_url, **request.GET},
    )
    return redirect(last_snapshot_url)
