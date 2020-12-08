# Copyright (C) 2018-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

# Utility module for browsing the archive in a snapshot context.

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from django.core.cache import cache
from django.shortcuts import render
from django.template.defaultfilters import filesizeformat
from django.utils.html import escape

from swh.model.identifiers import CONTENT, DIRECTORY, RELEASE, REVISION, SNAPSHOT, swhid
from swh.model.model import Snapshot
from swh.web.browse.utils import (
    content_display_max_size,
    format_log_entries,
    gen_content_link,
    gen_release_link,
    gen_revision_link,
    gen_revision_log_link,
    gen_revision_url,
    gen_snapshot_link,
    get_directory_entries,
    get_readme_to_display,
    prepare_content_for_display,
    request_content,
)
from swh.web.common import archive, highlightjs
from swh.web.common.exc import BadInputExc, NotFoundExc, http_status_code_message
from swh.web.common.identifiers import get_swhids_info
from swh.web.common.origin_visits import get_origin_visit
from swh.web.common.typing import (
    ContentMetadata,
    DirectoryMetadata,
    OriginInfo,
    SnapshotBranchInfo,
    SnapshotContext,
    SnapshotReleaseInfo,
    SWHObjectInfo,
)
from swh.web.common.utils import (
    format_utc_iso_date,
    gen_path_info,
    reverse,
    swh_object_icons,
)
from swh.web.config import get_config

_empty_snapshot_id = Snapshot(branches={}).id.hex()


def _get_branch(branches, branch_name, snapshot_id):
    """
    Utility function to get a specific branch from a branches list.
    Its purpose is to get the default HEAD branch as some software origin
    (e.g those with svn type) does not have it. In that latter case, check
    if there is a master branch instead and returns it.
    """
    filtered_branches = [b for b in branches if b["name"] == branch_name]
    if filtered_branches:
        return filtered_branches[0]
    elif branch_name == "HEAD":
        filtered_branches = [b for b in branches if b["name"].endswith("master")]
        if filtered_branches:
            return filtered_branches[0]
        elif branches:
            return branches[0]
    else:
        # case where a large branches list has been truncated
        snp = archive.lookup_snapshot(
            snapshot_id,
            branches_from=branch_name,
            branches_count=1,
            target_types=["revision", "alias"],
        )
        snp_branch, _, _ = process_snapshot_branches(snp)
        if snp_branch and snp_branch[0]["name"] == branch_name:
            branches.append(snp_branch[0])
            return snp_branch[0]


def _get_release(releases, release_name, snapshot_id):
    """
    Utility function to get a specific release from a releases list.
    Returns None if the release can not be found in the list.
    """
    filtered_releases = [r for r in releases if r["name"] == release_name]
    if filtered_releases:
        return filtered_releases[0]
    else:
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
                target_types=["release"],
            )
        _, snp_release, _ = process_snapshot_branches(snp)
        if snp_release and snp_release[0]["name"] == release_name:
            releases.append(snp_release[0])
            return snp_release[0]


def _branch_not_found(
    branch_type, branch, snapshot_id, snapshot_sizes, origin_info, timestamp, visit_id
):
    """
    Utility function to raise an exception when a specified branch/release
    can not be found.
    """
    if branch_type == "branch":
        branch_type = "Branch"
        branch_type_plural = "branches"
        target_type = "revision"
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
    elif visit_id and snapshot_sizes[target_type] == 0:
        msg = (
            "Origin with url %s"
            " for visit with id %s has an empty list"
            " of %s!" % (origin_info["url"], visit_id, branch_type_plural)
        )
    elif visit_id:
        msg = (
            "%s %s associated to visit with"
            " id %s for origin with url %s"
            " not found!" % (branch_type, branch, visit_id, origin_info["url"])
        )
    elif snapshot_sizes[target_type] == 0:
        msg = (
            "Origin with url %s"
            " for visit with timestamp %s has an empty list"
            " of %s!" % (origin_info["url"], timestamp, branch_type_plural)
        )
    else:
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
            :func:`swh.web.common.archive.lookup_snapshot`

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
        if target_type == "revision":
            branches[branch_name] = SnapshotBranchInfo(
                name=branch_name,
                alias=False,
                revision=target_id,
                date=None,
                directory=None,
                message=None,
                url=None,
            )
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
            revision=revision["id"],
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

    for branch_alias, branch_target in branch_aliases.items():
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

        if branch_alias in branches:
            branches[branch_alias]["name"] = branch_alias

    ret_branches = list(sorted(branches.values(), key=lambda b: b["name"]))
    ret_releases = list(sorted(releases.values(), key=lambda b: b["name"]))

    return ret_branches, ret_releases, resolved_aliases


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
    cache_entry_id = "swh_snapshot_%s" % snapshot_id
    cache_entry = cache.get(cache_entry_id)

    if cache_entry:
        return (
            cache_entry["branches"],
            cache_entry["releases"],
            cache_entry.get("aliases", {}),
        )

    branches: List[SnapshotBranchInfo] = []
    releases: List[SnapshotReleaseInfo] = []
    aliases: Dict[str, Any] = {}

    snapshot_content_max_size = get_config()["snapshot_content_max_size"]

    if snapshot_id:
        snapshot = archive.lookup_snapshot(
            snapshot_id, branches_count=snapshot_content_max_size
        )
        branches, releases, aliases = process_snapshot_branches(snapshot)

    cache.set(
        cache_entry_id, {"branches": branches, "releases": releases, "aliases": aliases}
    )

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
        swh.web.common.exc.NotFoundExc: if no snapshot is found for the visit
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
        visit_info["url"] = visit_url

        branches_url = reverse("browse-origin-branches", query_params=query_params)

        releases_url = reverse("browse-origin-releases", query_params=query_params)
    else:
        assert snapshot_id is not None
        branches, releases, aliases = get_snapshot_content(snapshot_id)
        url_args = {"snapshot_id": snapshot_id}
        branches_url = reverse("browse-snapshot-branches", url_args=url_args)

        releases_url = reverse("browse-snapshot-releases", url_args=url_args)

    releases = list(reversed(releases))

    snapshot_sizes_cache_id = f"swh_snapshot_{snapshot_id}_sizes"
    snapshot_sizes = cache.get(snapshot_sizes_cache_id)
    if snapshot_sizes is None:
        snapshot_sizes = archive.lookup_snapshot_sizes(snapshot_id)
        cache.set(snapshot_sizes_cache_id, snapshot_sizes)

    is_empty = (snapshot_sizes["release"] + snapshot_sizes["revision"]) == 0

    swh_snp_id = swhid("snapshot", snapshot_id)

    if visit_info:
        timestamp = format_utc_iso_date(visit_info["date"])

    if origin_info:
        browse_view_name = f"browse-origin-{browse_context}"
    else:
        browse_view_name = f"browse-snapshot-{browse_context}"

    release_id = None
    root_directory = None

    snapshot_total_size = snapshot_sizes["release"] + snapshot_sizes["revision"]

    if path is not None:
        query_params["path"] = path

    if snapshot_total_size and revision_id is not None:
        revision = archive.lookup_revision(revision_id)
        root_directory = revision["directory"]
        branches.append(
            SnapshotBranchInfo(
                name=revision_id,
                alias=False,
                revision=revision_id,
                directory=root_directory,
                date=revision["date"],
                message=revision["message"],
                url=None,
            )
        )
        branch_name = revision_id
        query_params["revision"] = revision_id
    elif snapshot_total_size and release_name:
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
            root_directory = release["directory"]
            revision_id = release["target"]
            release_id = release["id"]
            query_params["release"] = release_name
    elif snapshot_total_size:
        if branch_name:
            query_params["branch"] = branch_name
        branch = _get_branch(branches, branch_name or "HEAD", snapshot_id)
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
            revision_id = branch["revision"]
            root_directory = branch["directory"]

    for b in branches:
        branch_query_params = dict(query_params)
        branch_query_params.pop("release", None)
        if b["name"] != b["revision"]:
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
            browse_view_name, url_args=url_args, query_params=release_query_params,
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
        revision_info["revision_url"] = gen_revision_url(revision_id, snapshot_context)

    return snapshot_context


def _build_breadcrumbs(snapshot_context: SnapshotContext, path: str):
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


def _check_origin_url(snapshot_id, origin_url):
    if snapshot_id is None and origin_url is None:
        raise BadInputExc("An origin URL must be provided as query parameter.")


def browse_snapshot_directory(
    request, snapshot_id=None, origin_url=None, timestamp=None, path=None
):
    """
    Django view implementation for browsing a directory in a snapshot context.
    """
    _check_origin_url(snapshot_id, origin_url)

    snapshot_context = get_snapshot_context(
        snapshot_id=snapshot_id,
        origin_url=origin_url,
        timestamp=timestamp,
        visit_id=request.GET.get("visit_id"),
        path=path,
        browse_context="directory",
        branch_name=request.GET.get("branch"),
        release_name=request.GET.get("release"),
        revision_id=request.GET.get("revision"),
    )

    root_directory = snapshot_context["root_directory"]
    sha1_git = root_directory
    error_info = {
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
            f["length"] = filesizeformat(f["length"])
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
        sum_file_sizes = filesizeformat(sum_file_sizes)
        dir_path = "/" + path

    revision_found = True
    if sha1_git is None and revision_id is not None:
        try:
            archive.lookup_revision(revision_id)
        except NotFoundExc:
            revision_found = False

    swh_objects = [
        SWHObjectInfo(object_type=DIRECTORY, object_id=sha1_git),
        SWHObjectInfo(object_type=REVISION, object_id=revision_id),
        SWHObjectInfo(object_type=SNAPSHOT, object_id=snapshot_id),
    ]

    visit_date = None
    visit_type = None
    if visit_info:
        visit_date = format_utc_iso_date(visit_info["date"])
        visit_type = visit_info["type"]

    release_id = snapshot_context["release_id"]
    if release_id:
        swh_objects.append(SWHObjectInfo(object_type=RELEASE, object_id=release_id))

    dir_metadata = DirectoryMetadata(
        object_type=DIRECTORY,
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

    vault_cooking = {
        "directory_context": True,
        "directory_id": sha1_git,
        "revision_context": True,
        "revision_id": revision_id,
    }

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
    if not snapshot_context["is_empty"]:
        top_right_link = {
            "url": history_url,
            "icon": swh_object_icons["revisions history"],
            "text": "History",
        }

    return render(
        request,
        "browse/directory.html",
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


def browse_snapshot_content(
    request,
    snapshot_id=None,
    origin_url=None,
    timestamp=None,
    path=None,
    selected_language=None,
):
    """
    Django view implementation for browsing a content in a snapshot context.
    """
    _check_origin_url(snapshot_id, origin_url)

    if path is None:
        raise BadInputExc("The path of a content must be given as query parameter.")

    snapshot_context = get_snapshot_context(
        snapshot_id=snapshot_id,
        origin_url=origin_url,
        timestamp=timestamp,
        visit_id=request.GET.get("visit_id"),
        path=path,
        browse_context="content",
        branch_name=request.GET.get("branch"),
        release_name=request.GET.get("release"),
        revision_id=request.GET.get("revision"),
    )

    root_directory = snapshot_context["root_directory"]
    sha1_git = None
    query_string = None
    content_data = {}
    directory_id = None
    split_path = path.split("/")
    filename = split_path[-1]
    filepath = path[: -len(filename)]
    error_info = {
        "status_code": 200,
        "description": None,
    }
    if root_directory:
        try:
            content_info = archive.lookup_directory_with_path(root_directory, path)
            sha1_git = content_info["target"]
            query_string = "sha1_git:" + sha1_git
            content_data = request_content(query_string)

            if filepath:
                dir_info = archive.lookup_directory_with_path(root_directory, filepath)
                directory_id = dir_info["target"]
            else:
                directory_id = root_directory
        except NotFoundExc as e:
            error_info["status_code"] = 404
            error_info["description"] = f"NotFoundExc: {str(e)}"

    revision_id = snapshot_context["revision_id"]
    origin_info = snapshot_context["origin_info"]
    visit_info = snapshot_context["visit_info"]
    snapshot_id = snapshot_context["snapshot_id"]

    if content_data.get("raw_data") is not None:
        content_display_data = prepare_content_for_display(
            content_data["raw_data"], content_data["mimetype"], path
        )
        content_data.update(content_display_data)

    # Override language with user-selected language
    if selected_language is not None:
        content_data["language"] = selected_language

    available_languages = None

    if content_data.get("mimetype") is not None and "text/" in content_data["mimetype"]:
        available_languages = highlightjs.get_supported_languages()

    breadcrumbs = _build_breadcrumbs(snapshot_context, filepath)

    breadcrumbs.append({"name": filename, "url": None})

    browse_content_link = gen_content_link(sha1_git)

    content_raw_url = None
    if query_string:
        content_raw_url = reverse(
            "browse-content-raw",
            url_args={"query_string": query_string},
            query_params={"filename": filename},
        )

    content_checksums = content_data.get("checksums", {})

    swh_objects = [
        SWHObjectInfo(object_type=CONTENT, object_id=content_checksums.get("sha1_git")),
        SWHObjectInfo(object_type=DIRECTORY, object_id=directory_id),
        SWHObjectInfo(object_type=REVISION, object_id=revision_id),
        SWHObjectInfo(object_type=SNAPSHOT, object_id=snapshot_id),
    ]

    visit_date = None
    visit_type = None
    if visit_info:
        visit_date = format_utc_iso_date(visit_info["date"])
        visit_type = visit_info["type"]

    release_id = snapshot_context["release_id"]
    if release_id:
        swh_objects.append(SWHObjectInfo(object_type=RELEASE, object_id=release_id))

    content_metadata = ContentMetadata(
        object_type=CONTENT,
        object_id=content_checksums.get("sha1_git"),
        sha1=content_checksums.get("sha1"),
        sha1_git=content_checksums.get("sha1_git"),
        sha256=content_checksums.get("sha256"),
        blake2s256=content_checksums.get("blake2s256"),
        content_url=browse_content_link,
        mimetype=content_data.get("mimetype"),
        encoding=content_data.get("encoding"),
        size=filesizeformat(content_data.get("length", 0)),
        language=content_data.get("language"),
        root_directory=root_directory,
        path=f"/{filepath}",
        filename=filename,
        directory=directory_id,
        revision=revision_id,
        release=release_id,
        snapshot=snapshot_id,
        origin_url=origin_url,
        visit_date=visit_date,
        visit_type=visit_type,
    )

    swhids_info = get_swhids_info(swh_objects, snapshot_context, content_metadata)

    content_path = "/".join([bc["name"] for bc in breadcrumbs])
    context_found = "snapshot: %s" % snapshot_context["snapshot_id"]
    if origin_info:
        context_found = "origin: %s" % origin_info["url"]
    heading = "Content - %s - %s - %s" % (
        content_path,
        snapshot_context["branch"],
        context_found,
    )

    top_right_link = None
    if not snapshot_context["is_empty"]:
        top_right_link = {
            "url": content_raw_url,
            "icon": swh_object_icons["content"],
            "text": "Raw File",
        }

    return render(
        request,
        "browse/content.html",
        {
            "heading": heading,
            "swh_object_name": "Content",
            "swh_object_metadata": content_metadata,
            "content": content_data.get("content_data"),
            "content_size": content_data.get("length"),
            "max_content_size": content_display_max_size,
            "filename": filename,
            "encoding": content_data.get("encoding"),
            "mimetype": content_data.get("mimetype"),
            "language": content_data.get("language"),
            "available_languages": available_languages,
            "breadcrumbs": breadcrumbs if root_directory else [],
            "top_right_link": top_right_link,
            "snapshot_context": snapshot_context,
            "vault_cooking": None,
            "show_actions": True,
            "swhids_info": swhids_info,
            "error_code": error_info["status_code"],
            "error_message": http_status_code_message.get(error_info["status_code"]),
            "error_description": error_info["description"],
        },
        status=error_info["status_code"],
    )


PER_PAGE = 100


def browse_snapshot_log(request, snapshot_id=None, origin_url=None, timestamp=None):
    """
    Django view implementation for browsing a revision history in a
    snapshot context.
    """
    _check_origin_url(snapshot_id, origin_url)

    snapshot_context = get_snapshot_context(
        snapshot_id=snapshot_id,
        origin_url=origin_url,
        timestamp=timestamp,
        visit_id=request.GET.get("visit_id"),
        browse_context="log",
        branch_name=request.GET.get("branch"),
        release_name=request.GET.get("release"),
        revision_id=request.GET.get("revision"),
    )

    revision_id = snapshot_context["revision_id"]

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

    query_params["per_page"] = per_page
    revs_ordering = request.GET.get("revs_ordering", "")
    query_params["revs_ordering"] = revs_ordering or None

    if origin_info:
        browse_view_name = "browse-origin-log"
    else:
        browse_view_name = "browse-snapshot-log"

    prev_log_url = None
    if len(rev_log) > offset + per_page:
        query_params["offset"] = offset + per_page
        prev_log_url = reverse(
            browse_view_name, url_args=url_args, query_params=query_params
        )

    next_log_url = None
    if offset != 0:
        query_params["offset"] = offset - per_page
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

    if origin_info:
        revision_metadata["origin url"] = origin_info["url"]
        revision_metadata["origin visit date"] = format_utc_iso_date(visit_info["date"])
        revision_metadata["origin visit type"] = visit_info["type"]

    swh_objects = [
        SWHObjectInfo(object_type=REVISION, object_id=revision_id),
        SWHObjectInfo(object_type=SNAPSHOT, object_id=snapshot_id),
    ]

    release_id = snapshot_context["release_id"]
    if release_id:
        swh_objects.append(SWHObjectInfo(object_type=RELEASE, object_id=release_id))
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
        "browse/revision-log.html",
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
    request, snapshot_id=None, origin_url=None, timestamp=None
):
    """
    Django view implementation for browsing a list of branches in a snapshot
    context.
    """
    _check_origin_url(snapshot_id, origin_url)

    snapshot_context = get_snapshot_context(
        snapshot_id=snapshot_id,
        origin_url=origin_url,
        timestamp=timestamp,
        visit_id=request.GET.get("visit_id"),
    )

    branches_bc = request.GET.get("branches_breadcrumbs", "")
    branches_bc = branches_bc.split(",") if branches_bc else []
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
        target_types=["revision", "alias"],
    )

    displayed_branches, _, _ = process_snapshot_branches(snapshot)

    for branch in displayed_branches:
        rev_query_params = {}
        if origin_info:
            rev_query_params["origin_url"] = origin_info["url"]

        revision_url = reverse(
            "browse-revision",
            url_args={"sha1_git": branch["revision"]},
            query_params=query_params,
        )

        query_params["branch"] = branch["name"]
        directory_url = reverse(
            browse_view_name, url_args=url_args, query_params=query_params
        )
        del query_params["branch"]
        branch["revision_url"] = revision_url
        branch["directory_url"] = directory_url

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

    if snapshot["next_branch"] is not None:
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
        "browse/branches.html",
        {
            "heading": heading,
            "swh_object_name": "Branches",
            "swh_object_metadata": {},
            "top_right_link": None,
            "displayed_branches": displayed_branches,
            "prev_branches_url": prev_branches_url,
            "next_branches_url": next_branches_url,
            "snapshot_context": snapshot_context,
        },
    )


def browse_snapshot_releases(
    request, snapshot_id=None, origin_url=None, timestamp=None
):
    """
    Django view implementation for browsing a list of releases in a snapshot
    context.
    """
    _check_origin_url(snapshot_id, origin_url)

    snapshot_context = get_snapshot_context(
        snapshot_id=snapshot_id,
        origin_url=origin_url,
        timestamp=timestamp,
        visit_id=request.GET.get("visit_id"),
    )

    rel_bc = request.GET.get("releases_breadcrumbs", "")
    rel_bc = rel_bc.split(",") if rel_bc else []
    rel_from = rel_bc[-1] if rel_bc else ""

    origin_info = snapshot_context["origin_info"]
    url_args = snapshot_context["url_args"]
    query_params = snapshot_context["query_params"]

    snapshot = archive.lookup_snapshot(
        snapshot_context["snapshot_id"],
        rel_from,
        PER_PAGE + 1,
        target_types=["release", "alias"],
    )

    _, displayed_releases, _ = process_snapshot_branches(snapshot)

    for release in displayed_releases:
        query_params_tgt = {"snapshot": snapshot_id}
        if origin_info:
            query_params_tgt["origin_url"] = origin_info["url"]

        release_url = reverse(
            "browse-release",
            url_args={"sha1_git": release["id"]},
            query_params=query_params_tgt,
        )

        target_url = ""
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

        release["release_url"] = release_url
        release["target_url"] = target_url

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

    if snapshot["next_branch"] is not None:
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
        "browse/releases.html",
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
        },
    )
