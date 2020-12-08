# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

import sentry_sdk

from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.defaultfilters import filesizeformat

from swh.model.identifiers import DIRECTORY, RELEASE, REVISION, SNAPSHOT
from swh.web.browse.browseurls import browse_route
from swh.web.browse.snapshot_context import get_snapshot_context
from swh.web.browse.utils import gen_link, get_directory_entries, get_readme_to_display
from swh.web.common import archive
from swh.web.common.exc import NotFoundExc, http_status_code_message
from swh.web.common.identifiers import get_swhids_info
from swh.web.common.typing import DirectoryMetadata, SWHObjectInfo
from swh.web.common.utils import gen_path_info, reverse, swh_object_icons


def _directory_browse(request, sha1_git, path=None):
    root_sha1_git = sha1_git
    error_info = {"status_code": 200, "description": None}
    if path:
        try:
            dir_info = archive.lookup_directory_with_path(sha1_git, path)
            sha1_git = dir_info["target"]
        except NotFoundExc as e:
            error_info["status_code"] = 404
            error_info["description"] = f"NotFoundExc: {str(e)}"
            sha1_git = None

    dirs, files = [], []
    if sha1_git is not None:
        dirs, files = get_directory_entries(sha1_git)
    origin_url = request.GET.get("origin_url")
    if not origin_url:
        origin_url = request.GET.get("origin")
    snapshot_id = request.GET.get("snapshot")
    snapshot_context = None
    if origin_url is not None or snapshot_id is not None:
        try:
            snapshot_context = get_snapshot_context(
                snapshot_id=snapshot_id,
                origin_url=origin_url,
                branch_name=request.GET.get("branch"),
                release_name=request.GET.get("release"),
                revision_id=request.GET.get("revision"),
                path=path,
            )
        except NotFoundExc as e:
            if str(e).startswith("Origin"):
                raw_dir_url = reverse(
                    "browse-directory", url_args={"sha1_git": sha1_git}
                )
                error_message = (
                    "The Software Heritage archive has a directory "
                    "with the hash you provided but the origin "
                    "mentioned in your request appears broken: %s. "
                    "Please check the URL and try again.\n\n"
                    "Nevertheless, you can still browse the directory "
                    "without origin information: %s"
                    % (gen_link(origin_url), gen_link(raw_dir_url))
                )
                raise NotFoundExc(error_message)
            else:
                raise e

    path_info = gen_path_info(path)

    query_params = snapshot_context["query_params"] if snapshot_context else {}

    breadcrumbs = []
    breadcrumbs.append(
        {
            "name": root_sha1_git[:7],
            "url": reverse(
                "browse-directory",
                url_args={"sha1_git": root_sha1_git},
                query_params={**query_params, "path": None},
            ),
        }
    )

    for pi in path_info:
        breadcrumbs.append(
            {
                "name": pi["name"],
                "url": reverse(
                    "browse-directory",
                    url_args={"sha1_git": root_sha1_git},
                    query_params={**query_params, "path": pi["path"],},
                ),
            }
        )

    path = "" if path is None else (path + "/")

    for d in dirs:
        if d["type"] == "rev":
            d["url"] = reverse(
                "browse-revision",
                url_args={"sha1_git": d["target"]},
                query_params=query_params,
            )
        else:
            d["url"] = reverse(
                "browse-directory",
                url_args={"sha1_git": root_sha1_git},
                query_params={**query_params, "path": path + d["name"],},
            )

    sum_file_sizes = 0

    readmes = {}

    for f in files:
        query_string = "sha1_git:" + f["target"]
        f["url"] = reverse(
            "browse-content",
            url_args={"query_string": query_string},
            query_params={
                **query_params,
                "path": root_sha1_git + "/" + path + f["name"],
            },
        )
        if f["length"] is not None:
            sum_file_sizes += f["length"]
            f["length"] = filesizeformat(f["length"])
        if f["name"].lower().startswith("readme"):
            readmes[f["name"]] = f["checksums"]["sha1"]

    readme_name, readme_url, readme_html = get_readme_to_display(readmes)

    sum_file_sizes = filesizeformat(sum_file_sizes)

    dir_metadata = DirectoryMetadata(
        object_type=DIRECTORY,
        object_id=sha1_git,
        directory=root_sha1_git,
        nb_files=len(files),
        nb_dirs=len(dirs),
        sum_file_sizes=sum_file_sizes,
        root_directory=root_sha1_git,
        path=f"/{path}" if path else None,
        revision=None,
        revision_found=None,
        release=None,
        snapshot=None,
    )

    vault_cooking = {
        "directory_context": True,
        "directory_id": sha1_git,
        "revision_context": False,
        "revision_id": None,
    }

    swh_objects = [SWHObjectInfo(object_type=DIRECTORY, object_id=sha1_git)]

    if snapshot_context:
        swh_objects.append(
            SWHObjectInfo(
                object_type=REVISION, object_id=snapshot_context["revision_id"]
            )
        )
        swh_objects.append(
            SWHObjectInfo(
                object_type=SNAPSHOT, object_id=snapshot_context["snapshot_id"]
            )
        )
        if snapshot_context["release_id"]:
            swh_objects.append(
                SWHObjectInfo(
                    object_type=RELEASE, object_id=snapshot_context["release_id"]
                )
            )

    swhids_info = get_swhids_info(swh_objects, snapshot_context, dir_metadata)

    heading = "Directory - %s" % sha1_git
    if breadcrumbs:
        dir_path = "/".join([bc["name"] for bc in breadcrumbs]) + "/"
        heading += " - %s" % dir_path

    top_right_link = None
    if snapshot_context is not None and not snapshot_context["is_empty"]:
        history_url = reverse(
            "browse-revision-log",
            url_args={"sha1_git": snapshot_context["revision_id"]},
            query_params=query_params,
        )
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
            "swh_object_id": swhids_info[0]["swhid"],
            "swh_object_name": "Directory",
            "swh_object_metadata": dir_metadata,
            "dirs": dirs,
            "files": files,
            "breadcrumbs": breadcrumbs,
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


@browse_route(
    r"directory/(?P<sha1_git>[0-9a-f]+)/",
    view_name="browse-directory",
    checksum_args=["sha1_git"],
)
def directory_browse(request, sha1_git):
    """Django view for browsing the content of a directory identified
    by its sha1_git value.

    The url that points to it is
    :http:get:`/browse/directory/(sha1_git)/`
    """
    return _directory_browse(request, sha1_git, request.GET.get("path"))


@browse_route(
    r"directory/(?P<sha1_git>[0-9a-f]+)/(?P<path>.+)/",
    view_name="browse-directory-legacy",
    checksum_args=["sha1_git"],
)
def directory_browse_legacy(request, sha1_git, path):
    """Django view for browsing the content of a directory identified
    by its sha1_git value.

    The url that points to it is
    :http:get:`/browse/directory/(sha1_git)/(path)/`
    """
    return _directory_browse(request, sha1_git, path)


@browse_route(
    r"directory/resolve/content-path/(?P<sha1_git>[0-9a-f]+)/",
    view_name="browse-directory-resolve-content-path",
    checksum_args=["sha1_git"],
)
def _directory_resolve_content_path(request, sha1_git):
    """
    Internal endpoint redirecting to data url for a specific file path
    relative to a root directory.
    """
    try:
        path = os.path.normpath(request.GET.get("path"))
        if not path.startswith("../"):
            dir_info = archive.lookup_directory_with_path(sha1_git, path)
            if dir_info["type"] == "file":
                sha1 = dir_info["checksums"]["sha1"]
                data_url = reverse(
                    "browse-content-raw", url_args={"query_string": sha1}
                )
                return redirect(data_url)
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
    return HttpResponse(status=404)
