# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.shortcuts import redirect

from swh.web.browse.browseurls import browse_route
from swh.web.browse.snapshot_context import (
    browse_snapshot_branches,
    browse_snapshot_content,
    browse_snapshot_directory,
    browse_snapshot_log,
    browse_snapshot_releases,
)
from swh.web.common.utils import reverse


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/",
    view_name="browse-snapshot",
    checksum_args=["snapshot_id"],
)
def snapshot_browse(request, snapshot_id):
    """Django view for browsing the content of a snapshot.

    The url that points to it is :http:get:`/browse/snapshot/(snapshot_id)/`
    """
    browse_snapshot_url = reverse(
        "browse-snapshot-directory",
        url_args={"snapshot_id": snapshot_id},
        query_params=request.GET,
    )
    return redirect(browse_snapshot_url)


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/directory/",
    view_name="browse-snapshot-directory",
    checksum_args=["snapshot_id"],
)
def snapshot_directory_browse(request, snapshot_id):
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
def snapshot_directory_browse_legacy(request, snapshot_id, path=None):
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
def snapshot_content_browse(request, snapshot_id):
    """Django view that produces an HTML display of a content
    collected in a snapshot.

    The url that points to it is :http:get:`/browse/snapshot/(snapshot_id)/content/`
    """
    return browse_snapshot_content(
        request,
        snapshot_id=snapshot_id,
        path=request.GET.get("path"),
        selected_language=request.GET.get("language"),
    )


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/content/(?P<path>.+)/",
    view_name="browse-snapshot-content-legacy",
    checksum_args=["snapshot_id"],
)
def snapshot_content_browse_legacy(request, snapshot_id, path):
    """Django view that produces an HTML display of a content
    collected in a snapshot.

    The url that points to it is
    :http:get:`/browse/snapshot/(snapshot_id)/content/(path)/`
    """
    return browse_snapshot_content(
        request,
        snapshot_id=snapshot_id,
        path=path,
        selected_language=request.GET.get("language"),
    )


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/log/",
    view_name="browse-snapshot-log",
    checksum_args=["snapshot_id"],
)
def snapshot_log_browse(request, snapshot_id):
    """Django view that produces an HTML display of revisions history (aka
    the commit log) collected in a snapshot.

    The url that points to it is
    :http:get:`/browse/snapshot/(snapshot_id)/log/`
    """
    return browse_snapshot_log(request, snapshot_id=snapshot_id)


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/branches/",
    view_name="browse-snapshot-branches",
    checksum_args=["snapshot_id"],
)
def snapshot_branches_browse(request, snapshot_id):
    """Django view that produces an HTML display of the list of releases
    collected in a snapshot.

    The url that points to it is
    :http:get:`/browse/snapshot/(snapshot_id)/branches/`
    """
    return browse_snapshot_branches(request, snapshot_id=snapshot_id)


@browse_route(
    r"snapshot/(?P<snapshot_id>[0-9a-f]+)/releases/",
    view_name="browse-snapshot-releases",
    checksum_args=["snapshot_id"],
)
def snapshot_releases_browse(request, snapshot_id):
    """Django view that produces an HTML display of the list of releases
    collected in a snapshot.

    The url that points to it is
    :http:get:`/browse/snapshot/(snapshot_id)/releases/`
    """
    return browse_snapshot_releases(request, snapshot_id=snapshot_id)
