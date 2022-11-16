# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# Utility module for browsing the archive in a snapshot context.

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.html import escape

from swh.model.hashutil import hash_to_bytes
from swh.model.model import Snapshot
from swh.model.swhids import CoreSWHID, ObjectType
from swh.web.browse.utils import (
    format_log_entries,
    gen_release_link,
    gen_revision_link,
    gen_revision_log_link,
    gen_revision_url,
    gen_snapshot_link,
    get_directory_entries,
    get_readme_to_display,
)
from swh.web.config import get_config
from swh.web.utils import (
    archive,
    django_cache,
    format_utc_iso_date,
    gen_path_info,
    reverse,
    swh_object_icons,
)
from swh.web.utils.exc import BadInputExc, NotFoundExc, http_status_code_message
from swh.web.utils.identifiers import get_swhids_info
from swh.web.utils.origin_visits import get_origin_visit
from swh.web.utils.typing import (
    DirectoryMetadata,
    OriginInfo,
    SnapshotBranchInfo,
    SnapshotContext,
    SnapshotReleaseInfo,
    SWHObjectInfo,
)

_empty_snapshot_id = Snapshot(branches={}).id.hex()


def _get_branch(
    branches: List[SnapshotBranchInfo], branch_name: str, snapshot_id: str
) -> Optional[SnapshotBranchInfo]:
    """
    Utility function to get a specific branch from a snapshot.
    Returns None if the branch cannot be found.
    """
    filtered_branches = [b for b in branches if b["name"] == branch_name]
    if filtered_branches:
        return filtered_branches[0]
    else:
        # case where a large branches list has been truncated
        snp = archive.lookup_snapshot(
            snapshot_id,
            branches_from=branch_name,
            branches_count=1,
            target_types=["revision", "alias", "content", "directory"],
            # pull request branches must be browsable even if they are hidden
            # by default in branches list
            branch_name_exclude_prefix=None,
        )
        snp_branch, _, _ = process_snapshot_branches(snp)
        if snp_branch and snp_branch[0]["name"] == branch_name:
            branches.append(snp_branch[0])
            return snp_branch[0]
    return None


def _get_release(
    releases: List[SnapshotReleaseInfo], release_name: Optional[str], snapshot_id: str
) -> Optional[SnapshotReleaseInfo]:
    """
    Utility function to get a specific release from a snapshot.
    Returns None if the release cannot be found.
    """
    filtered_releases = [r for r in releases if r["name"] == release_name]
    if filtered_releases:
        return filtered_releases[0]
    elif release_name:
        # case where a large branches list has been truncated
        try:
            # git origins have specific branches for releases
            snp = archive.lookup_snapshot(
                snapshot_id,
                branches_from=f"refs/tags/{release_name}",
                branches_count=1,
                target_types=["release"],
            )
        except NotFoundExc:
            snp = archive.lookup_snapshot(
                snapshot_id,
                branches_from=release_name,
                branches_count=1,
                target_types=["release", "alias"],
            )
        _, snp_release, _ = process_snapshot_branches(snp)
        if snp_release and snp_release[0]["name"] == release_name:
            releases.append(snp_release[0])
            return snp_release[0]
    return None


def _branch_not_found(
    branch_type: str,
    branch: str,
    snapshot_id: str,
    snapshot_sizes: Dict[str, int],
    origin_info: Optional[OriginInfo],
    timestamp: Optional[str],
    visit_id: Optional[int],
) -> None:
    """
    Utility function to raise an exception when a specified branch/release
    can not be found.
    """
    if branch_type == "branch":
        branch_type = "Branch"
        branch_type_plural = "branches"
        target_type = "branch"
    else:
        branch_type = "Release"
        branch_type_plural = "releases"
        target_type = "release"

    if snapshot_id and snapshot_sizes[target_type] == 0:
        msg = "Snapshot with id %s has an empty list" " of %s!" % (
            snapshot_id,
            branch_type_plural,
        )
    elif snapshot_id:
        msg = "%s %s for snapshot with id %s" " not found!" % (
            branch_type,
            branch,
            snapshot_id,
        )
    elif visit_id and snapshot_sizes[target_type] == 0 and origin_info:
        msg = (
            "Origin with url %s"
            " for visit with id %s has an empty list"
            " of %s!" % (origin_info["url"], visit_id, branch_type_plural)
        )
    elif visit_id and origin_info:
        msg = (
            "%s %s associated to visit with"
            " id %s for origin with url %s"
            " not found!" % (branch_type, branch, visit_id, origin_info["url"])
        )
    elif snapshot_sizes[target_type] == 0 and origin_info and timestamp:
        msg = (
            "Origin with url %s"
            " for visit with timestamp %s has an empty list"
            " of %s!" % (origin_info["url"], timestamp, branch_type_plural)
        )
    elif origin_info and timestamp:
        msg = (
            "%s %s associated to visit with"
            " timestamp %s for origin with "
            "url %s not found!" % (branch_type, branch, timestamp, origin_info["url"])
        )
    raise NotFoundExc(escape(msg))


def process_snapshot_branches(
    snapshot: Dict[str, Any]
) -> Tuple[List[SnapshotBranchInfo], List[SnapshotReleaseInfo], Dict[str, Any]]:
    """
    Process a dictionary describing snapshot branches: extract those
    targeting revisions and releases, put them in two different lists,
    then sort those lists in lexicographical order of the branches' names.

    Args:
        snapshot: A dict describing a snapshot as returned for instance by
            :func:`swh.web.utils.archive.lookup_snapshot`

    Returns:
        A tuple whose first member is the sorted list of branches
        targeting revisions, second member the sorted list of branches
        targeting releases and third member a dict mapping resolved branch
        aliases to their real target.
    """
    snapshot_branches = snapshot["branches"]
    branches: Dict[str, SnapshotBranchInfo] = {}
    branch_aliases: Dict[str, str] = {}
    releases: Dict[str, SnapshotReleaseInfo] = {}
    revision_to_branch = defaultdict(set)
    revision_to_release = defaultdict(set)
    release_to_branch = defaultdict(set)
    for branch_name, target in snapshot_branches.items():
        if not target:
            # FIXME: display branches with an unknown target anyway
            continue
        target_id = target["target"]
        target_type = target["target_type"]
        if target_type in ("content", "directory", "revision"):
            branches[branch_name] = SnapshotBranchInfo(
                name=branch_name,
                alias=False,
                target_type=target_type,
                target=target_id,
                date=None,
                directory=None,
                message=None,
                url=None,
            )
            if target_type == "revision":
                revision_to_branch[target_id].add(branch_name)
        elif target_type == "release":
            release_to_branch[target_id].add(branch_name)
        elif target_type == "alias":
            branch_aliases[branch_name] = target_id
        # FIXME: handle pointers to other object types

    def _add_release_info(branch, release, alias=False):
        releases[branch] = SnapshotReleaseInfo(
            name=release["name"],
            alias=alias,
            branch_name=branch,
            date=format_utc_iso_date(release["date"]),
            directory=None,
            id=release["id"],
            message=release["message"],
            target_type=release["target_type"],
            target=release["target"],
            url=None,
        )

    def _add_branch_info(branch, revision, alias=False):
        branches[branch] = SnapshotBranchInfo(
            name=branch,
            alias=alias,
            target_type="revision",
            target=revision["id"],
            directory=revision["directory"],
            date=format_utc_iso_date(revision["date"]),
            message=revision["message"],
            url=None,
        )

    releases_info = archive.lookup_release_multiple(release_to_branch.keys())
    for release in releases_info:
        if release is None:
            continue
        branches_to_update = release_to_branch[release["id"]]
        for branch in branches_to_update:
            _add_release_info(branch, release)
        if release["target_type"] == "revision":
            revision_to_release[release["target"]].update(branches_to_update)

    revisions = archive.lookup_revision_multiple(
        set(revision_to_branch.keys()) | set(revision_to_release.keys())
    )

    for revision in revisions:
        if not revision:
            continue
        for branch in revision_to_branch[revision["id"]]:
            _add_branch_info(branch, revision)
        for release_id in revision_to_release[revision["id"]]:
            releases[release_id]["directory"] = revision["directory"]

    resolved_aliases = {}

    for branch_alias, _ in branch_aliases.items():
        resolved_alias = archive.lookup_snapshot_alias(snapshot["id"], branch_alias)
        resolved_aliases[branch_alias] = resolved_alias
        if resolved_alias is None:
            continue

        target_type = resolved_alias["target_type"]
        target = resolved_alias["target"]

        if target_type == "revision":
            revision = archive.lookup_revision(target)
            _add_branch_info(branch_alias, revision, alias=True)
        elif target_type == "release":
            release = archive.lookup_release(target)
            _add_release_info(branch_alias, release, alias=True)
        elif target_type in ("content", "directory"):
            branches[branch_name] = SnapshotBranchInfo(
                name=branch_alias,
                alias=True,
                target_type=target_type,
                target=target,
                date=None,
                directory=None,
                message=None,
                url=None,
            )

        if branch_alias in branches:
            branches[branch_alias]["name"] = branch_alias

    ret_branches = list(sorted(branches.values(), key=lambda b: b["name"]))
    ret_releases = list(sorted(releases.values(), key=lambda b: b["branch_name"]))

    return ret_branches, ret_releases, resolved_aliases


@django_cache()
def get_snapshot_content(
    snapshot_id: str,
) -> Tuple[List[SnapshotBranchInfo], List[SnapshotReleaseInfo], Dict[str, Any]]:
    """Returns the lists of branches and releases
    associated to a swh snapshot.
    That list is put in  cache in order to speedup the navigation
    in the swh-web/browse ui.

    .. warning:: At most 1000 branches contained in the snapshot
        will be returned for performance reasons.

    Args:
        snapshot_id: hexadecimal representation of the snapshot identifier

    Returns:
        A tuple with three members. The first one is a list of dict describing
        the snapshot branches. The second one is a list of dict describing the
        snapshot releases. The third one is a dict mapping resolved branch
        aliases to their real target.

    Raises:
        NotFoundExc if the snapshot does not exist
    """

    branches: List[SnapshotBranchInfo] = []
    releases: List[SnapshotReleaseInfo] = []
    aliases: Dict[str, Any] = {}

    snapshot_content_max_size = get_config()["snapshot_content_max_size"]

    if snapshot_id:
        snapshot = archive.lookup_snapshot(
            snapshot_id, branches_count=snapshot_content_max_size
        )
        branches, releases, aliases = process_snapshot_branches(snapshot)

    return branches, releases, aliases


def get_origin_visit_snapshot(
    origin_info: OriginInfo,
    visit_ts: Optional[str] = None,
    visit_id: Optional[int] = None,
    snapshot_id: Optional[str] = None,
) -> Tuple[List[SnapshotBranchInfo], List[SnapshotReleaseInfo], Dict[str, Any]]:
    """Returns the lists of branches and releases associated to an origin for
    a given visit.

    The visit is expressed by either:

        * a snapshot identifier
        * a timestamp, if no visit with that exact timestamp is found,
          the closest one from the provided timestamp will be used.

    If no visit parameter is provided, it returns the list of branches
    found for the latest visit.

    That list is put in  cache in order to speedup the navigation
    in the swh-web/browse ui.

    .. warning:: At most 1000 branches contained in the snapshot
        will be returned for performance reasons.

    Args:
        origin_info: a dict filled with origin information
        visit_ts: an ISO 8601 datetime string to parse
        visit_id: visit id for disambiguation in case several visits have
            the same timestamp
        snapshot_id: if provided, visit associated to the snapshot will be processed

    Returns:
        A tuple with three members. The first one is a list of dict describing
        the origin branches for the given visit.
        The second one is a list of dict describing the origin releases
        for the given visit. The third one is a dict mapping resolved branch
        aliases to their real target.

    Raises:
        NotFoundExc if the origin or its visit are not found
    """

    visit_info = get_origin_visit(origin_info, visit_ts, visit_id, snapshot_id)

    return get_snapshot_content(visit_info["snapshot"])


def get_snapshot_context(
    snapshot_id: Optional[str] = None,
    origin_url: Optional[str] = None,
    timestamp: Optional[str] = None,
    visit_id: Optional[int] = None,
    branch_name: Optional[str] = None,
    release_name: Optional[str] = None,
    revision_id: Optional[str] = None,
    path: Optional[str] = None,
    browse_context: str = "directory",
) -> SnapshotContext:
    """
    Utility function to compute relevant information when navigating
    the archive in a snapshot context. The snapshot is either
    referenced by its id or it will be retrieved from an origin visit.

    Args:
        snapshot_id: hexadecimal representation of a snapshot identifier
        origin_url: an origin_url
        timestamp: a datetime string for retrieving the closest
            visit of the origin
        visit_id: optional visit id for disambiguation in case
            of several visits with the same timestamp
        branch_name: optional branch name set when browsing the snapshot in
            that scope (will default to "HEAD" if not provided)
        release_name: optional release name set when browsing the snapshot in
            that scope
        revision_id: optional revision identifier set when browsing the snapshot in
            that scope
        path: optional path of the object currently browsed in the snapshot
        browse_context: indicates which type of object is currently browsed

    Returns:
        A dict filled with snapshot context information.

    Raises:
        swh.web.utils.exc.NotFoundExc: if no snapshot is found for the visit
            of an origin.
    """
    assert origin_url is not None or snapshot_id is not None
    origin_info = None
    visit_info = None
    url_args = {}
    query_params: Dict[str, Any] = {}
    origin_visits_url = None

    if origin_url:

        if visit_id is not None:
            query_params["visit_id"] = visit_id
        elif snapshot_id is not None:
            query_params["snapshot"] = snapshot_id

        origin_info = archive.lookup_origin({"url": origin_url})

        visit_info = get_origin_visit(origin_info, timestamp, visit_id, snapshot_id)
        formatted_date = format_utc_iso_date(visit_info["date"])
        visit_info["formatted_date"] = formatted_date
        snapshot_id = visit_info["snapshot"]

        if not snapshot_id:
            raise NotFoundExc(
                "No snapshot associated to the visit of origin "
                "%s on %s" % (escape(origin_url), formatted_date)
            )

        # provided timestamp is not necessarily equals to the one
        # of the retrieved visit, so get the exact one in order
        # to use it in the urls generated below
        if timestamp:
            timestamp = visit_info["date"]

        branches, releases, aliases = get_origin_visit_snapshot(
            origin_info, timestamp, visit_id, snapshot_id
        )

        query_params["origin_url"] = origin_info["url"]

        origin_visits_url = reverse(
            "browse-origin-visits", query_params={"origin_url": origin_info["url"]}
        )

        if timestamp is not None:
            query_params["timestamp"] = format_utc_iso_date(
                timestamp, "%Y-%m-%dT%H:%M:%SZ"
            )

        visit_url = reverse("browse-origin-directory", query_params=query_params)
        visit_info["url"] = browse_url = visit_url

        branches_url = reverse("browse-origin-branches", query_params=query_params)

        releases_url = reverse("browse-origin-releases", query_params=query_params)
    else:
        assert snapshot_id is not None
        branches, releases, aliases = get_snapshot_content(snapshot_id)
        url_args = {"snapshot_id": snapshot_id}
        browse_url = reverse("browse-snapshot-directory", url_args=url_args)
        branches_url = reverse("browse-snapshot-branches", url_args=url_args)

        releases_url = reverse("browse-snapshot-releases", url_args=url_args)

    releases = list(reversed(releases))

    @django_cache()
    def _get_snapshot_sizes(snapshot_id):
        return archive.lookup_snapshot_sizes(snapshot_id)

    snapshot_sizes = _get_snapshot_sizes(snapshot_id)

    snapshot_total_size = sum(
        v for k, v in snapshot_sizes.items() if k not in ("alias", "branch")
    )

    is_empty = snapshot_total_size == 0

    swh_snp_id = str(
        CoreSWHID(object_type=ObjectType.SNAPSHOT, object_id=hash_to_bytes(snapshot_id))
    )

    if visit_info:
        timestamp = format_utc_iso_date(visit_info["date"])

    if origin_info:
        browse_view_name = f"browse-origin-{browse_context}"
    else:
        browse_view_name = f"browse-snapshot-{browse_context}"

    release_id = None
    root_directory = None

    if path is not None:
        query_params["path"] = path

    if snapshot_total_size and revision_id is not None:
        # browse specific revision for a snapshot requested
        revision = archive.lookup_revision(revision_id)
        root_directory = revision["directory"]
        branches.append(
            SnapshotBranchInfo(
                name=revision_id,
                alias=False,
                target_type="revision",
                target=revision_id,
                directory=root_directory,
                date=revision["date"],
                message=revision["message"],
                url=None,
            )
        )
        query_params["revision"] = revision_id
    elif snapshot_total_size and release_name:
        # browse specific release for a snapshot requested
        release = _get_release(releases, release_name, snapshot_id)
        if release is None:
            _branch_not_found(
                "release",
                release_name,
                snapshot_id,
                snapshot_sizes,
                origin_info,
                timestamp,
                visit_id,
            )
        else:
            if release["target_type"] == "revision":
                revision = archive.lookup_revision(release["target"])
                root_directory = revision["directory"]
                revision_id = release["target"]
            elif release["target_type"] == "directory":
                root_directory = release["target"]
            release_id = release["id"]
            query_params["release"] = release_name
    elif snapshot_total_size:
        head = aliases.get("HEAD")
        if branch_name:
            # browse specific branch for a snapshot requested
            query_params["branch"] = branch_name
            branch = _get_branch(branches, branch_name, snapshot_id)
            if branch is None:
                _branch_not_found(
                    "branch",
                    branch_name,
                    snapshot_id,
                    snapshot_sizes,
                    origin_info,
                    timestamp,
                    visit_id,
                )
            else:
                branch_name = branch["name"]
                if branch["target_type"] == "revision":
                    revision_id = branch["target"]
                    root_directory = branch["directory"]
                elif branch["target_type"] == "directory":
                    root_directory = branch["target"]
        elif head is not None:
            # otherwise, browse branch targeted by the HEAD alias if it exists
            if head["target_type"] in ("content", "directory", "revision"):
                branch_name = "HEAD"
                if head["target_type"] == "revision":
                    # HEAD alias targets a revision
                    head_rev = archive.lookup_revision(head["target"])
                    revision_id = head_rev["id"]
                    root_directory = head_rev["directory"]
                elif head["target_type"] == "directory":
                    # HEAD alias targets a directory
                    root_directory = head["target"]
            elif head["target_type"] == "release":
                # HEAD alias targets a release
                release_name = archive.lookup_release(head["target"])["name"]
                head_rel = _get_release(releases, release_name, snapshot_id)
                if head_rel is None:
                    _branch_not_found(
                        "release",
                        str(release_name),
                        snapshot_id,
                        snapshot_sizes,
                        origin_info,
                        timestamp,
                        visit_id,
                    )
                elif head_rel["target_type"] == "revision":
                    revision = archive.lookup_revision(head_rel["target"])
                    root_directory = revision["directory"]
                    revision_id = head_rel["target"]
                elif head_rel["target_type"] == "directory":
                    root_directory = head_rel["target"]
                if head_rel is not None:
                    release_id = head_rel["id"]
        elif branches:
            # fallback to browse first branch otherwise
            branch = branches[0]
            branch_name = branch["name"]
            revision_id = (
                branch["target"] if branch["target_type"] == "revision" else None
            )
            if branch["target_type"] == "revision":
                root_directory = branch["directory"]
            elif branch["target_type"] == "directory":
                root_directory = branch["target"]
        elif releases:
            # fallback to browse last release otherwise
            release = releases[-1]
            if release["target_type"] == "revision":
                revision = archive.lookup_revision(release["target"])
                root_directory = revision["directory"]
                revision_id = release["target"]
            elif release["target_type"] == "directory":
                root_directory = release["target"]
            release_id = release["id"]
            release_name = release["name"]

    for b in branches:
        branch_query_params = dict(query_params)
        branch_query_params.pop("release", None)
        if b["name"] != b["target"]:
            branch_query_params.pop("revision", None)
            branch_query_params["branch"] = b["name"]
        b["url"] = reverse(
            browse_view_name, url_args=url_args, query_params=branch_query_params
        )

    for r in releases:
        release_query_params = dict(query_params)
        release_query_params.pop("branch", None)
        release_query_params.pop("revision", None)
        release_query_params["release"] = r["name"]
        r["url"] = reverse(
            browse_view_name,
            url_args=url_args,
            query_params=release_query_params,
        )

    revision_info = None
    if revision_id:
        try:
            revision_info = archive.lookup_revision(revision_id)
        except NotFoundExc:
            pass
        else:
            revision_info["date"] = format_utc_iso_date(revision_info["date"])
            revision_info["committer_date"] = format_utc_iso_date(
                revision_info["committer_date"]
            )
            if revision_info["message"]:
                message_lines = revision_info["message"].split("\n")
                revision_info["message_header"] = message_lines[0]
            else:
                revision_info["message_header"] = ""

    snapshot_context = SnapshotContext(
        browse_url=browse_url,
        branch=branch_name,
        branch_alias=branch_name in aliases,
        branches=branches,
        branches_url=branches_url,
        is_empty=is_empty,
        origin_info=origin_info,
        origin_visits_url=origin_visits_url,
        release=release_name,
        release_alias=release_name in aliases,
        release_id=release_id,
        query_params=query_params,
        releases=releases,
        releases_url=releases_url,
        revision_id=revision_id,
        revision_info=revision_info,
        root_directory=root_directory,
        snapshot_id=snapshot_id,
        snapshot_sizes=snapshot_sizes,
        snapshot_swhid=swh_snp_id,
        url_args=url_args,
        visit_info=visit_info,
    )

    if revision_info:
        revision_info["revision_url"] = gen_revision_url(
            revision_info["id"], snapshot_context
        )

    return snapshot_context


def _build_breadcrumbs(
    snapshot_context: SnapshotContext, path: Optional[str]
) -> List[Dict[str, str]]:
    origin_info = snapshot_context["origin_info"]
    url_args = snapshot_context["url_args"]
    query_params = dict(snapshot_context["query_params"])
    root_directory = snapshot_context["root_directory"]

    path_info = gen_path_info(path)

    if origin_info:
        browse_view_name = "browse-origin-directory"
    else:
        browse_view_name = "browse-snapshot-directory"

    breadcrumbs = []
    if root_directory:
        query_params.pop("path", None)
        breadcrumbs.append(
            {
                "name": root_directory[:7],
                "url": reverse(
                    browse_view_name, url_args=url_args, query_params=query_params
                ),
            }
        )
    for pi in path_info:
        query_params["path"] = pi["path"]
        breadcrumbs.append(
            {
                "name": pi["name"],
                "url": reverse(
                    browse_view_name, url_args=url_args, query_params=query_params
                ),
            }
        )
    return breadcrumbs


def _check_origin_url(snapshot_id: Optional[str], origin_url: Optional[str]) -> None:
    if snapshot_id is None and origin_url is None:
        raise BadInputExc("An origin URL must be provided as query parameter.")


def browse_snapshot_directory(
    request: HttpRequest,
    snapshot_id: Optional[str] = None,
    origin_url: Optional[str] = None,
    timestamp: Optional[str] = None,
    path: Optional[str] = None,
) -> HttpResponse:
    """
    Django view implementation for browsing a directory in a snapshot context.
    """
    _check_origin_url(snapshot_id, origin_url)

    visit_id = int(request.GET.get("visit_id", 0))
    snapshot_context = get_snapshot_context(
        snapshot_id=snapshot_id,
        origin_url=origin_url,
        timestamp=timestamp,
        visit_id=visit_id or None,
        path=path,
        browse_context="directory",
        branch_name=request.GET.get("branch"),
        release_name=request.GET.get("release"),
        revision_id=request.GET.get("revision"),
    )

    root_directory = snapshot_context["root_directory"]

    if root_directory is None and snapshot_context["branch"] is not None:
        branch_info = [
            branch
            for branch in snapshot_context["branches"]
            if branch["name"] == snapshot_context["branch"]
        ]
        # special case where the branch to browse targets a content instead of a directory
        if branch_info and branch_info[0]["target_type"] == "content":
            # redirect to browse content view
            if "origin_url" not in snapshot_context["query_params"]:
                snapshot_id = snapshot_context["snapshot_id"]
                snapshot_context["query_params"]["snapshot"] = snapshot_id
            return redirect(
                reverse(
                    "browse-content",
                    url_args={"query_string": f"sha1_git:{branch_info[0]['target']}"},
                    query_params=snapshot_context["query_params"],
                )
            )

    sha1_git = root_directory
    error_info: Dict[str, Any] = {
        "status_code": 200,
        "description": None,
    }
    if root_directory and path:
        try:
            dir_info = archive.lookup_directory_with_path(root_directory, path)
            sha1_git = dir_info["target"]
        except NotFoundExc as e:
            sha1_git = None
            error_info["status_code"] = 404
            error_info["description"] = f"NotFoundExc: {str(e)}"

    dirs = []
    files = []
    if sha1_git:
        dirs, files = get_directory_entries(sha1_git)

    origin_info = snapshot_context["origin_info"]
    visit_info = snapshot_context["visit_info"]
    url_args = snapshot_context["url_args"]
    query_params = dict(snapshot_context["query_params"])
    revision_id = snapshot_context["revision_id"]
    snapshot_id = snapshot_context["snapshot_id"]

    if origin_info:
        browse_view_name = "browse-origin-directory"
    else:
        browse_view_name = "browse-snapshot-directory"

    breadcrumbs = _build_breadcrumbs(snapshot_context, path)

    path = "" if path is None else (path + "/")

    for d in dirs:
        if d["type"] == "rev":
            d["url"] = reverse("browse-revision", url_args={"sha1_git": d["target"]})
        else:
            query_params["path"] = path + d["name"]
            d["url"] = reverse(
                browse_view_name, url_args=url_args, query_params=query_params
            )

    sum_file_sizes = 0

    readmes = {}

    if origin_info:
        browse_view_name = "browse-origin-content"
    else:
        browse_view_name = "browse-snapshot-content"

    for f in files:
        query_params["path"] = path + f["name"]
        f["url"] = reverse(
            browse_view_name, url_args=url_args, query_params=query_params
        )
        if f["length"] is not None:
            sum_file_sizes += f["length"]
        if f["name"].lower().startswith("readme"):
            readmes[f["name"]] = f["checksums"]["sha1"]

    readme_name, readme_url, readme_html = get_readme_to_display(readmes)

    if origin_info:
        browse_view_name = "browse-origin-log"
    else:
        browse_view_name = "browse-snapshot-log"

    history_url = None
    if snapshot_id != _empty_snapshot_id:
        query_params.pop("path", None)
        history_url = reverse(
            browse_view_name, url_args=url_args, query_params=query_params
        )

    nb_files = None
    nb_dirs = None
    dir_path = None
    if root_directory:
        nb_files = len(files)
        nb_dirs = len(dirs)
        dir_path = "/" + path

    swh_objects = []
    vault_cooking: Dict[str, Any] = {
        "directory_context": False,
        "directory_swhid": None,
        "revision_context": False,
        "revision_swhid": None,
    }
    revision_found = False

    if revision_id is not None:
        try:
            archive.lookup_revision(revision_id)
        except NotFoundExc:
            pass
        else:
            revision_found = True

    if sha1_git is not None:
        swh_objects.append(
            SWHObjectInfo(object_type=ObjectType.DIRECTORY, object_id=sha1_git)
        )
        vault_cooking.update(
            {
                "directory_context": True,
                "directory_swhid": f"swh:1:dir:{sha1_git}",
            }
        )
    if revision_id is not None and revision_found:
        swh_objects.append(
            SWHObjectInfo(object_type=ObjectType.REVISION, object_id=revision_id)
        )
        vault_cooking.update(
            {
                "revision_context": True,
                "revision_swhid": f"swh:1:rev:{revision_id}",
            }
        )
    swh_objects.append(
        SWHObjectInfo(object_type=ObjectType.SNAPSHOT, object_id=snapshot_id)
    )

    visit_date = None
    visit_type = None
    if visit_info:
        visit_date = format_utc_iso_date(visit_info["date"])
        visit_type = visit_info["type"]

    release_id = snapshot_context["release_id"]
    if release_id:
        swh_objects.append(
            SWHObjectInfo(object_type=ObjectType.RELEASE, object_id=release_id)
        )

    dir_metadata = DirectoryMetadata(
        object_type=ObjectType.DIRECTORY,
        object_id=sha1_git,
        directory=sha1_git,
        nb_files=nb_files,
        nb_dirs=nb_dirs,
        sum_file_sizes=sum_file_sizes,
        root_directory=root_directory,
        path=dir_path,
        revision=revision_id,
        revision_found=revision_found,
        release=release_id,
        snapshot=snapshot_id,
        origin_url=origin_url,
        visit_date=visit_date,
        visit_type=visit_type,
    )

    swhids_info = get_swhids_info(swh_objects, snapshot_context, dir_metadata)

    dir_path = "/".join([bc["name"] for bc in breadcrumbs]) + "/"
    context_found = "snapshot: %s" % snapshot_context["snapshot_id"]
    if origin_info:
        context_found = "origin: %s" % origin_info["url"]
    heading = "Directory - %s - %s - %s" % (
        dir_path,
        snapshot_context["branch"],
        context_found,
    )

    top_right_link = None
    if not snapshot_context["is_empty"] and revision_found:
        top_right_link = {
            "url": history_url,
            "icon": swh_object_icons["revisions history"],
            "text": "History",
        }

    return render(
        request,
        "browse-directory.html",
        {
            "heading": heading,
            "swh_object_name": "Directory",
            "swh_object_metadata": dir_metadata,
            "dirs": dirs,
            "files": files,
            "breadcrumbs": breadcrumbs if root_directory else [],
            "top_right_link": top_right_link,
            "readme_name": readme_name,
            "readme_url": readme_url,
            "readme_html": readme_html,
            "snapshot_context": snapshot_context,
            "vault_cooking": vault_cooking,
            "show_actions": True,
            "swhids_info": swhids_info,
            "error_code": error_info["status_code"],
            "error_message": http_status_code_message.get(error_info["status_code"]),
            "error_description": error_info["description"],
        },
        status=error_info["status_code"],
    )


PER_PAGE = 100


def browse_snapshot_log(
    request: HttpRequest,
    snapshot_id: Optional[str] = None,
    origin_url: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> HttpResponse:
    """
    Django view implementation for browsing a revision history in a
    snapshot context.
    """
    _check_origin_url(snapshot_id, origin_url)

    visit_id = int(request.GET.get("visit_id", 0))
    snapshot_context = get_snapshot_context(
        snapshot_id=snapshot_id,
        origin_url=origin_url,
        timestamp=timestamp,
        visit_id=visit_id or None,
        browse_context="log",
        branch_name=request.GET.get("branch"),
        release_name=request.GET.get("release"),
        revision_id=request.GET.get("revision"),
    )

    revision_id = snapshot_context["revision_id"]

    if revision_id is None:
        raise NotFoundExc("No revisions history found in the current snapshot context.")

    per_page = int(request.GET.get("per_page", PER_PAGE))
    offset = int(request.GET.get("offset", 0))
    revs_ordering = request.GET.get("revs_ordering", "committer_date")
    session_key = "rev_%s_log_ordering_%s" % (revision_id, revs_ordering)
    rev_log_session = request.session.get(session_key, None)
    rev_log = []
    revs_walker_state = None
    if rev_log_session:
        rev_log = rev_log_session["rev_log"]
        revs_walker_state = rev_log_session["revs_walker_state"]

    if len(rev_log) < offset + per_page:
        revs_walker = archive.get_revisions_walker(
            revs_ordering,
            revision_id,
            max_revs=offset + per_page + 1,
            state=revs_walker_state,
        )
        rev_log += [rev["id"] for rev in revs_walker]
        revs_walker_state = revs_walker.export_state()

    revs = rev_log[offset : offset + per_page]
    revision_log = archive.lookup_revision_multiple(revs)

    request.session[session_key] = {
        "rev_log": rev_log,
        "revs_walker_state": revs_walker_state,
    }

    origin_info = snapshot_context["origin_info"]
    visit_info = snapshot_context["visit_info"]
    url_args = snapshot_context["url_args"]
    query_params = snapshot_context["query_params"]
    snapshot_id = snapshot_context["snapshot_id"]

    query_params["per_page"] = str(per_page)
    revs_ordering = request.GET.get("revs_ordering", "")
    if revs_ordering:
        query_params["revs_ordering"] = revs_ordering

    if origin_info:
        browse_view_name = "browse-origin-log"
    else:
        browse_view_name = "browse-snapshot-log"

    prev_log_url = None
    if len(rev_log) > offset + per_page:
        query_params["offset"] = str(offset + per_page)
        prev_log_url = reverse(
            browse_view_name, url_args=url_args, query_params=query_params
        )

    next_log_url = None
    if offset != 0:
        query_params["offset"] = str(offset - per_page)
        next_log_url = reverse(
            browse_view_name, url_args=url_args, query_params=query_params
        )

    revision_log_data = format_log_entries(revision_log, per_page, snapshot_context)

    browse_rev_link = gen_revision_link(revision_id)

    browse_log_link = gen_revision_log_link(revision_id)

    browse_snp_link = gen_snapshot_link(snapshot_id)

    revision_metadata = {
        "context-independent revision": browse_rev_link,
        "context-independent revision history": browse_log_link,
        "context-independent snapshot": browse_snp_link,
        "snapshot": snapshot_id,
    }

    if origin_info and visit_info:
        revision_metadata["origin url"] = origin_info["url"]
        revision_metadata["origin visit date"] = format_utc_iso_date(visit_info["date"])
        revision_metadata["origin visit type"] = visit_info["type"]

    swh_objects = [
        SWHObjectInfo(object_type=ObjectType.REVISION, object_id=revision_id),
        SWHObjectInfo(object_type=ObjectType.SNAPSHOT, object_id=snapshot_id),
    ]

    release_id = snapshot_context["release_id"]
    if release_id:
        swh_objects.append(
            SWHObjectInfo(object_type=ObjectType.RELEASE, object_id=release_id)
        )
        browse_rel_link = gen_release_link(release_id)
        revision_metadata["release"] = release_id
        revision_metadata["context-independent release"] = browse_rel_link

    swhids_info = get_swhids_info(swh_objects, snapshot_context)

    context_found = "snapshot: %s" % snapshot_context["snapshot_id"]
    if origin_info:
        context_found = "origin: %s" % origin_info["url"]
    heading = "Revision history - %s - %s" % (snapshot_context["branch"], context_found)

    return render(
        request,
        "browse-revision-log.html",
        {
            "heading": heading,
            "swh_object_name": "Revisions history",
            "swh_object_metadata": revision_metadata,
            "revision_log": revision_log_data,
            "revs_ordering": revs_ordering,
            "next_log_url": next_log_url,
            "prev_log_url": prev_log_url,
            "breadcrumbs": None,
            "top_right_link": None,
            "snapshot_context": snapshot_context,
            "vault_cooking": None,
            "show_actions": True,
            "swhids_info": swhids_info,
        },
    )


def browse_snapshot_branches(
    request: HttpRequest,
    snapshot_id: Optional[str] = None,
    origin_url: Optional[str] = None,
    timestamp: Optional[str] = None,
    branch_name_include: Optional[str] = None,
) -> HttpResponse:
    """
    Django view implementation for browsing a list of branches in a snapshot
    context.
    """
    _check_origin_url(snapshot_id, origin_url)

    visit_id = int(request.GET.get("visit_id", 0))
    snapshot_context = get_snapshot_context(
        snapshot_id=snapshot_id,
        origin_url=origin_url,
        timestamp=timestamp,
        visit_id=visit_id or None,
    )

    branches_bc_str = request.GET.get("branches_breadcrumbs", "")
    branches_bc = branches_bc_str.split(",") if branches_bc_str else []
    branches_from = branches_bc[-1] if branches_bc else ""

    origin_info = snapshot_context["origin_info"]
    url_args = snapshot_context["url_args"]
    query_params = snapshot_context["query_params"]

    if origin_info:
        browse_view_name = "browse-origin-directory"
    else:
        browse_view_name = "browse-snapshot-directory"

    snapshot = archive.lookup_snapshot(
        snapshot_context["snapshot_id"],
        branches_from,
        PER_PAGE + 1,
        target_types=["content", "directory", "revision", "alias"],
        branch_name_include_substring=branch_name_include,
    )
    displayed_branches: List[Dict[str, Any]] = []
    if snapshot:
        branches, _, _ = process_snapshot_branches(snapshot)
        displayed_branches = [dict(branch) for branch in branches]

    for branch in displayed_branches:
        query_params = {"snapshot": snapshot_id, "branch": branch["name"]}
        if origin_info:
            query_params["origin_url"] = origin_info["url"]

        directory_url = reverse(
            browse_view_name, url_args=url_args, query_params=query_params
        )
        branch["directory_url"] = directory_url
        del query_params["branch"]

        if branch["target_type"] in ("directory", "revision"):
            target_url = reverse(
                f"browse-{branch['target_type']}",
                url_args={"sha1_git": branch["target"]},
                query_params=query_params,
            )
        elif branch["target_type"] == "content":
            target_url = reverse(
                "browse-content",
                url_args={"query_string": f"sha1_git:{branch['target']}"},
                query_params=query_params,
            )
        branch["target_url"] = target_url
        branch["tooltip"] = (
            f"The branch {branch['name']} targets "
            f"{branch['target_type']} {branch['target']}"
        )

    if origin_info:
        browse_view_name = "browse-origin-branches"
    else:
        browse_view_name = "browse-snapshot-branches"

    prev_branches_url = None
    next_branches_url = None

    if branches_bc:
        query_params_prev = dict(query_params)

        query_params_prev["branches_breadcrumbs"] = ",".join(branches_bc[:-1])
        prev_branches_url = reverse(
            browse_view_name, url_args=url_args, query_params=query_params_prev
        )
    elif branches_from:
        prev_branches_url = reverse(
            browse_view_name, url_args=url_args, query_params=query_params
        )

    if snapshot and snapshot["next_branch"] is not None:
        query_params_next = dict(query_params)
        next_branch = displayed_branches[-1]["name"]
        del displayed_branches[-1]
        branches_bc.append(next_branch)
        query_params_next["branches_breadcrumbs"] = ",".join(branches_bc)
        next_branches_url = reverse(
            browse_view_name, url_args=url_args, query_params=query_params_next
        )

    heading = "Branches - "
    if origin_info:
        heading += "origin: %s" % origin_info["url"]
    else:
        heading += "snapshot: %s" % snapshot_id

    return render(
        request,
        "browse-branches.html",
        {
            "heading": heading,
            "swh_object_name": "Branches",
            "swh_object_metadata": {},
            "top_right_link": None,
            "displayed_branches": displayed_branches,
            "prev_branches_url": prev_branches_url,
            "next_branches_url": next_branches_url,
            "snapshot_context": snapshot_context,
            "search_string": branch_name_include or "",
        },
    )


def browse_snapshot_releases(
    request: HttpRequest,
    snapshot_id: Optional[str] = None,
    origin_url: Optional[str] = None,
    timestamp: Optional[str] = None,
    release_name_include: Optional[str] = None,
):
    """
    Django view implementation for browsing a list of releases in a snapshot
    context.
    """
    _check_origin_url(snapshot_id, origin_url)

    visit_id = int(request.GET.get("visit_id", 0))
    snapshot_context = get_snapshot_context(
        snapshot_id=snapshot_id,
        origin_url=origin_url,
        timestamp=timestamp,
        visit_id=visit_id or None,
    )

    rel_bc_str = request.GET.get("releases_breadcrumbs", "")
    rel_bc = rel_bc_str.split(",") if rel_bc_str else []
    rel_from = rel_bc[-1] if rel_bc else ""

    origin_info = snapshot_context["origin_info"]
    url_args = snapshot_context["url_args"]
    query_params = snapshot_context["query_params"]

    snapshot = archive.lookup_snapshot(
        snapshot_context["snapshot_id"],
        rel_from,
        PER_PAGE + 1,
        target_types=["release", "alias"],
        branch_name_include_substring=release_name_include,
    )
    displayed_releases: List[Dict[str, Any]] = []
    if snapshot:
        _, releases, _ = process_snapshot_branches(snapshot)
        displayed_releases = [dict(release) for release in releases]

    for release in displayed_releases:
        query_params_tgt = {"snapshot": snapshot_id, "release": release["name"]}
        if origin_info:
            query_params_tgt["origin_url"] = origin_info["url"]

        release_url = reverse(
            "browse-release",
            url_args={"sha1_git": release["id"]},
            query_params=query_params_tgt,
        )

        target_url = ""
        tooltip = (
            f"The release {release['name']} targets "
            f"{release['target_type']} {release['target']}"
        )
        if release["target_type"] == "revision":
            target_url = reverse(
                "browse-revision",
                url_args={"sha1_git": release["target"]},
                query_params=query_params_tgt,
            )
        elif release["target_type"] == "directory":
            target_url = reverse(
                "browse-directory",
                url_args={"sha1_git": release["target"]},
                query_params=query_params_tgt,
            )
        elif release["target_type"] == "content":
            target_url = reverse(
                "browse-content",
                url_args={"query_string": release["target"]},
                query_params=query_params_tgt,
            )
        elif release["target_type"] == "release":
            target_url = reverse(
                "browse-release",
                url_args={"sha1_git": release["target"]},
                query_params=query_params_tgt,
            )
            tooltip = (
                f"The release {release['name']} "
                f"is an alias for release {release['target']}"
            )

        release["release_url"] = release_url
        release["target_url"] = target_url
        release["tooltip"] = tooltip

    if origin_info:
        browse_view_name = "browse-origin-releases"
    else:
        browse_view_name = "browse-snapshot-releases"

    prev_releases_url = None
    next_releases_url = None

    if rel_bc:
        query_params_prev = dict(query_params)

        query_params_prev["releases_breadcrumbs"] = ",".join(rel_bc[:-1])
        prev_releases_url = reverse(
            browse_view_name, url_args=url_args, query_params=query_params_prev
        )
    elif rel_from:
        prev_releases_url = reverse(
            browse_view_name, url_args=url_args, query_params=query_params
        )

    if snapshot and snapshot["next_branch"] is not None:
        query_params_next = dict(query_params)
        next_rel = displayed_releases[-1]["branch_name"]
        del displayed_releases[-1]
        rel_bc.append(next_rel)
        query_params_next["releases_breadcrumbs"] = ",".join(rel_bc)
        next_releases_url = reverse(
            browse_view_name, url_args=url_args, query_params=query_params_next
        )

    heading = "Releases - "
    if origin_info:
        heading += "origin: %s" % origin_info["url"]
    else:
        heading += "snapshot: %s" % snapshot_id

    return render(
        request,
        "browse-releases.html",
        {
            "heading": heading,
            "top_panel_visible": False,
            "top_panel_collapsible": False,
            "swh_object_name": "Releases",
            "swh_object_metadata": {},
            "top_right_link": None,
            "displayed_releases": displayed_releases,
            "prev_releases_url": prev_releases_url,
            "next_releases_url": next_releases_url,
            "snapshot_context": snapshot_context,
            "vault_cooking": None,
            "show_actions": False,
            "search_string": release_name_include or "",
        },
    )
