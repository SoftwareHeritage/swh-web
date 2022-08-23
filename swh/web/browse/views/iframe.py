# Copyright (C) 2021-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict, List, Optional, Tuple

from django.shortcuts import render
from django.urls import re_path as url
from django.views.decorators.clickjacking import xframe_options_exempt

from swh.model.hashutil import hash_to_bytes
from swh.model.swhids import CoreSWHID, ObjectType, QualifiedSWHID
from swh.web.browse.browseurls import browse_route
from swh.web.browse.snapshot_context import get_snapshot_context
from swh.web.browse.utils import (
    content_display_max_size,
    get_directory_entries,
    prepare_content_for_display,
    request_content,
)
from swh.web.utils import archive, gen_path_info, reverse
from swh.web.utils.exc import BadInputExc, NotFoundExc, http_status_code_message
from swh.web.utils.identifiers import get_swhid, get_swhids_info
from swh.web.utils.typing import SnapshotContext, SWHObjectInfo


def _get_content_rendering_data(cnt_swhid: QualifiedSWHID, path: str) -> Dict[str, Any]:
    content_data = request_content(f"sha1_git:{cnt_swhid.object_id.hex()}")
    content = None
    language = None
    mimetype = None
    if content_data.get("raw_data") is not None:
        content_display_data = prepare_content_for_display(
            content_data["raw_data"], content_data["mimetype"], path
        )
        content = content_display_data["content_data"]
        language = content_display_data["language"]
        mimetype = content_display_data["mimetype"]

    return {
        "content": content,
        "content_size": content_data.get("length"),
        "max_content_size": content_display_max_size,
        "filename": path.split("/")[-1],
        "encoding": content_data.get("encoding"),
        "mimetype": mimetype,
        "language": language,
    }


def _get_directory_rendering_data(
    dir_swhid: QualifiedSWHID,
    focus_swhid: QualifiedSWHID,
    path: str,
) -> Dict[str, Any]:
    dirs, files = get_directory_entries(dir_swhid.object_id.hex())
    for d in dirs:
        if d["type"] == "rev":
            d["url"] = None
        else:
            dir_swhid = QualifiedSWHID(
                object_type=ObjectType.DIRECTORY,
                object_id=hash_to_bytes(d["target"]),
                origin=dir_swhid.origin,
                visit=dir_swhid.visit,
                anchor=dir_swhid.anchor,
                path=(path or "/") + d["name"] + "/",
            )
            d["url"] = reverse(
                "browse-swhid-iframe",
                url_args={"swhid": str(dir_swhid)},
                query_params={"focus_swhid": str(focus_swhid)},
            )

    for f in files:
        object_id = hash_to_bytes(f["target"])
        cnt_swhid = QualifiedSWHID(
            object_type=ObjectType.CONTENT,
            object_id=object_id,
            origin=dir_swhid.origin,
            visit=dir_swhid.visit,
            anchor=dir_swhid.anchor,
            path=(path or "/") + f["name"],
            lines=(focus_swhid.lines if object_id == focus_swhid.object_id else None),
        )
        f["url"] = reverse(
            "browse-swhid-iframe",
            url_args={"swhid": str(cnt_swhid)},
            query_params={"focus_swhid": str(focus_swhid)},
        )

    return {"dirs": dirs, "files": files}


def _get_breacrumbs_data(
    swhid: QualifiedSWHID,
    focus_swhid: QualifiedSWHID,
    path: str,
    snapshot_context: Optional[SnapshotContext] = None,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    breadcrumbs = []
    filename = None
    # strip any leading or trailing slash from path qualifier of SWHID
    if path and path[0] == "/":
        path = path[1:]
    if path and path[-1] == "/":
        path = path[:-1]
    if swhid.object_type == ObjectType.CONTENT:
        split_path = path.split("/")
        filename = split_path[-1]
        path = path[: -len(filename)]

    path_info = gen_path_info(path) if path != "/" else []

    root_dir = None
    if snapshot_context and snapshot_context["root_directory"]:
        root_dir = snapshot_context["root_directory"]
    elif swhid.anchor and swhid.anchor.object_type == ObjectType.DIRECTORY:
        root_dir = swhid.anchor.object_id.hex()
    elif focus_swhid.object_type == ObjectType.DIRECTORY:
        root_dir = focus_swhid.object_id.hex()

    if root_dir:
        root_dir_swhid = QualifiedSWHID(
            object_type=ObjectType.DIRECTORY,
            object_id=hash_to_bytes(root_dir),
            origin=swhid.origin,
            visit=swhid.visit,
            anchor=swhid.anchor,
        )

        breadcrumbs.append(
            {
                "name": root_dir[:7],
                "object_id": root_dir_swhid.object_id.hex(),
                "path": "/",
                "url": reverse(
                    "browse-swhid-iframe",
                    url_args={"swhid": str(root_dir_swhid)},
                    query_params={
                        "focus_swhid": str(focus_swhid)
                        if focus_swhid != root_dir_swhid
                        else None
                    },
                ),
            }
        )

        for pi in path_info:
            dir_info = archive.lookup_directory_with_path(root_dir, pi["path"])
            dir_swhid = QualifiedSWHID(
                object_type=ObjectType.DIRECTORY,
                object_id=hash_to_bytes(dir_info["target"]),
                origin=swhid.origin,
                visit=swhid.visit,
                anchor=swhid.anchor,
                path="/" + pi["path"] + "/",
            )
            breadcrumbs.append(
                {
                    "name": pi["name"],
                    "object_id": dir_swhid.object_id.hex(),
                    "path": dir_swhid.path.decode("utf-8") if dir_swhid.path else "",
                    "url": reverse(
                        "browse-swhid-iframe",
                        url_args={"swhid": str(dir_swhid)},
                        query_params={"focus_swhid": str(focus_swhid)},
                    ),
                }
            )
    if filename:
        breadcrumbs.append(
            {
                "name": filename,
                "object_id": swhid.object_id.hex(),
                "path": path,
                "url": "",
            }
        )

    return breadcrumbs, root_dir


@browse_route(
    r"embed/(?P<swhid>swh:[0-9]+:[a-z]+:[0-9a-f]+.*)/",
    view_name="browse-swhid-iframe",
)
@xframe_options_exempt
def swhid_iframe(request, swhid: str):
    """Django view that can be embedded in an iframe to display objects archived
    by Software Heritage (currently contents and directories) in a minimalist
    Web UI.
    """
    focus_swhid = request.GET.get("focus_swhid", swhid)
    parsed_swhid = None
    view_data = {}
    breadcrumbs: List[Dict[str, Any]] = []
    swh_objects = []
    snapshot_context = None
    swhids_info_extra_context = {}
    archive_link = None
    try:
        parsed_swhid = get_swhid(swhid)
        parsed_focus_swhid = get_swhid(focus_swhid)
        path = parsed_swhid.path.decode("utf-8") if parsed_swhid.path else ""

        snapshot_context = None
        revision_id = None
        if (
            parsed_swhid.anchor
            and parsed_swhid.anchor.object_type == ObjectType.REVISION
        ):
            revision_id = parsed_swhid.anchor.object_id.hex()
        if parsed_swhid.origin or parsed_swhid.visit:
            snapshot_context = get_snapshot_context(
                origin_url=parsed_swhid.origin,
                snapshot_id=parsed_swhid.visit.object_id.hex()
                if parsed_swhid.visit
                else None,
                revision_id=revision_id,
            )

        error_info: Dict[str, Any] = {"status_code": 200, "description": ""}

        if parsed_swhid and parsed_swhid.object_type == ObjectType.CONTENT:
            view_data = _get_content_rendering_data(parsed_swhid, path)
            swh_objects.append(
                SWHObjectInfo(
                    object_type=ObjectType.CONTENT,
                    object_id=parsed_swhid.object_id.hex(),
                )
            )

        elif parsed_swhid and parsed_swhid.object_type == ObjectType.DIRECTORY:
            view_data = _get_directory_rendering_data(
                parsed_swhid, parsed_focus_swhid, path
            )
            swh_objects.append(
                SWHObjectInfo(
                    object_type=ObjectType.DIRECTORY,
                    object_id=parsed_swhid.object_id.hex(),
                )
            )

        elif parsed_swhid:
            error_info = {
                "status_code": 400,
                "description": (
                    f"Objects of type {parsed_swhid.object_type} are not supported"
                ),
            }

        swhids_info_extra_context["path"] = path
        if parsed_swhid and view_data:
            breadcrumbs, root_dir = _get_breacrumbs_data(
                parsed_swhid, parsed_focus_swhid, path, snapshot_context
            )

            if parsed_swhid.object_type == ObjectType.CONTENT and len(breadcrumbs) > 1:
                swh_objects.append(
                    SWHObjectInfo(
                        object_type=ObjectType.DIRECTORY,
                        object_id=breadcrumbs[-2]["object_id"],
                    )
                )
                swhids_info_extra_context["path"] = breadcrumbs[-2]["path"]
                swhids_info_extra_context["filename"] = breadcrumbs[-1]["name"]

            if snapshot_context:
                swh_objects.append(
                    SWHObjectInfo(
                        object_type=ObjectType.REVISION,
                        object_id=snapshot_context["revision_id"] or "",
                    )
                )
                swh_objects.append(
                    SWHObjectInfo(
                        object_type=ObjectType.SNAPSHOT,
                        object_id=snapshot_context["snapshot_id"] or "",
                    )
                )

            archive_link = reverse("browse-swhid", url_args={"swhid": swhid})
            if (
                parsed_swhid.origin is None
                and parsed_swhid.visit is None
                and parsed_swhid.anchor is None
                and root_dir is not None
            ):
                # qualifier values cannot be used to get root directory from them,
                # we need to add it as anchor in the SWHID argument of the archive link
                root_dir_swhid = CoreSWHID(
                    object_type=ObjectType.DIRECTORY, object_id=hash_to_bytes(root_dir)
                )
                archive_swhid = QualifiedSWHID(
                    object_type=parsed_swhid.object_type,
                    object_id=parsed_swhid.object_id,
                    path=parsed_swhid.path,
                    anchor=root_dir_swhid,
                )
                archive_link = reverse(
                    "browse-swhid",
                    url_args={"swhid": f"{archive_swhid}"},
                )

    except BadInputExc as e:
        error_info = {"status_code": 400, "description": f"BadInputExc: {str(e)}"}
    except NotFoundExc as e:
        error_info = {"status_code": 404, "description": f"NotFoundExc: {str(e)}"}
    except Exception as e:
        error_info = {"status_code": 500, "description": str(e)}

    return render(
        request,
        "browse-iframe.html",
        {
            **view_data,
            "iframe_mode": True,
            "object_type": parsed_swhid.object_type.value if parsed_swhid else None,
            "lines": parsed_swhid.lines if parsed_swhid else None,
            "breadcrumbs": breadcrumbs,
            "swhid": swhid,
            "focus_swhid": focus_swhid,
            "archive_link": archive_link,
            "error_code": error_info["status_code"],
            "error_message": http_status_code_message.get(error_info["status_code"]),
            "error_description": error_info["description"],
            "snapshot_context": None,
            "swhids_info": get_swhids_info(
                swh_objects, snapshot_context, swhids_info_extra_context
            ),
        },
        status=error_info["status_code"],
    )


urlpatterns = [
    url(
        r"^embed/(?P<swhid>swh:[0-9]+:[a-z]+:[0-9a-f]+.*)/$",
        swhid_iframe,
        name="browse-swhid-iframe",
    ),
]
