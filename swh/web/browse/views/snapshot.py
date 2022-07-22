# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from swh.web.browse.browseurls import browse_route
from swh.web.browse.snapshot_context import (
    browse_snapshot_branches,
    browse_snapshot_directory,
    browse_snapshot_log,
    browse_snapshot_releases,
    get_snapshot_context,
)
from swh.web.utils import redirect_to_new_route, reverse
from swh.web.utils.exc import BadInputExc


def get_snapshot_from_request(request: HttpRequest) -> str:
    snapshot = request.GET.get("snapshot")
    if snapshot:
        return snapshot
    if request.GET.get("origin_url") is None:
        raise BadInputExc("An origin URL must be provided as a query parameter.")
    return get_snapshot_context(
        origin_url=request.GET.get("origin_url"), timestamp=request.GET.get("timestamp")
    )["snapshot_id"]


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/",
    view_name="browse-snapshot",
    checksum_args=["snapshot_id"],
)
def snapshot_browse(request: HttpRequest, snapshot_id: str) -> HttpResponse:
    """Django view for browsing the content of a snapshot.

    The url that points to it is :http:get:`/browse/snapshot/(snapshot_id)/`
    """
    browse_snapshot_url = reverse(
        "browse-snapshot-directory",
        url_args={"snapshot_id": snapshot_id},
        query_params=request.GET.dict(),
    )
    return redirect(browse_snapshot_url)


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/directory/",
    view_name="browse-snapshot-directory",
    checksum_args=["snapshot_id"],
)
def snapshot_directory_browse(request: HttpRequest, snapshot_id: str) -> HttpResponse:
    """Django view for browsing the content of a directory collected
    in a snapshot.

    The URL that points to it is :http:get:`/browse/snapshot/(snapshot_id)/directory/`
    """
    return browse_snapshot_directory(
        request,
        snapshot_id=snapshot_id,
        path=request.GET.get("path"),
        origin_url=request.GET.get("origin_url"),
    )


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/directory/(?P<path>.+)/",
    view_name="browse-snapshot-directory-legacy",
    checksum_args=["snapshot_id"],
)
def snapshot_directory_browse_legacy(
    request: HttpRequest, snapshot_id: str, path: Optional[str] = None
) -> HttpResponse:
    """Django view for browsing the content of a directory collected
    in a snapshot.

    The URL that points to it is
    :http:get:`/browse/snapshot/(snapshot_id)/directory/(path)/`
    """
    origin_url = request.GET.get("origin_url", None)
    if not origin_url:
        origin_url = request.GET.get("origin", None)
    return browse_snapshot_directory(
        request, snapshot_id=snapshot_id, path=path, origin_url=origin_url
    )


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/content/",
    view_name="browse-snapshot-content",
    checksum_args=["snapshot_id"],
)
def snapshot_content_browse(request: HttpRequest, snapshot_id: str) -> HttpResponse:
    """
    This route is deprecated; use http:get:`/browse/content` instead

    Django view that produces an HTML display of a content
    collected in a snapshot.

    The url that points to it is :http:get:`/browse/snapshot/(snapshot_id)/content/`
    """

    return redirect_to_new_route(request, "browse-content")


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/content/(?P<path>.+)/",
    view_name="browse-snapshot-content-legacy",
    checksum_args=["snapshot_id"],
)
def snapshot_content_browse_legacy(
    request: HttpRequest, snapshot_id: str, path: str
) -> HttpResponse:
    """
    This route is deprecated; use http:get:`/browse/content` instead

    Django view that produces an HTML display of a content
    collected in a snapshot.

    The url that points to it is
    :http:get:`/browse/snapshot/(snapshot_id)/content/(path)/`
    """
    return redirect_to_new_route(request, "browse-content")


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/log/",
    r"snapshot/log/",
    view_name="browse-snapshot-log",
    checksum_args=["snapshot_id"],
)
def snapshot_log_browse(
    request: HttpRequest, snapshot_id: Optional[str] = None
) -> HttpResponse:
    """Django view that produces an HTML display of revisions history (aka
    the commit log) collected in a snapshot.

    The URLs that point to it are
    :http:get:`/browse/snapshot/(snapshot_id)/log/` and
    :http:get:`/browse/snapshot/log/`
    """
    if snapshot_id is None:
        # This case happens when redirected from /origin/log
        snapshot_id = get_snapshot_from_request(request)
        # Redirect to the same route with snapshot_id
        return redirect(
            reverse(
                "browse-snapshot-log",
                url_args={"snapshot_id": snapshot_id},
                query_params=request.GET,
            ),
        )
    return browse_snapshot_log(
        request,
        snapshot_id=snapshot_id,
        origin_url=request.GET.get("origin_url"),
        timestamp=request.GET.get("timestamp"),
    )


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/branches/",
    r"snapshot/branches/",
    view_name="browse-snapshot-branches",
    checksum_args=["snapshot_id"],
)
def snapshot_branches_browse(
    request: HttpRequest, snapshot_id: Optional[str] = None
) -> HttpResponse:
    """Django view that produces an HTML display of the list of branches
    collected in a snapshot.

    The URLs that point to it are
    :http:get:`/browse/snapshot/(snapshot_id)/branches/` and
    :http:get:`/browse/snapshot/branches/`
    """
    if snapshot_id is None:
        # This case happens when redirected from /origin/branches
        snapshot_id = get_snapshot_from_request(request)
        # Redirect to the same route with the newest snapshot_id
        # for the given origin
        return redirect(
            reverse(
                "browse-snapshot-branches",
                url_args={"snapshot_id": snapshot_id},
                query_params=request.GET,
            ),
        )
    return browse_snapshot_branches(
        request,
        snapshot_id=snapshot_id,
        origin_url=request.GET.get("origin_url"),
        timestamp=request.GET.get("timestamp"),
        branch_name_include=request.GET.get("name_include"),
    )


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/releases/",
    r"snapshot/releases/",
    view_name="browse-snapshot-releases",
    checksum_args=["snapshot_id"],
)
def snapshot_releases_browse(
    request: HttpRequest, snapshot_id: Optional[str] = None
) -> HttpResponse:
    """Django view that produces an HTML display of the list of releases
    collected in a snapshot.

    The URLs that point to it are
    :http:get:`/browse/snapshot/(snapshot_id)/releases/`
    :http:get:`/browse/snapshot/releases/`
    """
    if snapshot_id is None:
        # This case happens when redirected from /origin/releases
        snapshot_id = get_snapshot_from_request(request)
        # Redirect to the same route with the newest snapshot_id
        # for the given origin
        return redirect(
            reverse(
                "browse-snapshot-releases",
                url_args={"snapshot_id": snapshot_id},
                query_params=request.GET,
            ),
        )
    return browse_snapshot_releases(
        request,
        snapshot_id=snapshot_id,
        origin_url=request.GET.get("origin_url"),
        timestamp=request.GET.get("timestamp"),
        release_name_include=request.GET.get("name_include"),
    )
