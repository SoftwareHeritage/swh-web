# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.shortcuts import render
from django.views.decorators.clickjacking import xframe_options_exempt

from swh.model.hashutil import hash_to_bytes
from swh.model.identifiers import ObjectType, QualifiedSWHID
from swh.web.browse.snapshot_context import get_snapshot_context
from swh.web.browse.utils import (
    content_display_max_size,
    get_directory_entries,
    prepare_content_for_display,
    request_content,
)
from swh.web.common import archive
from swh.web.common.exc import BadInputExc, NotFoundExc, http_status_code_message
from swh.web.common.identifiers import get_swhid
from swh.web.common.utils import gen_path_info, reverse


@xframe_options_exempt
def swhid_iframe(request, swhid):
    focus_swhid = request.GET.get("focus_swhid", swhid)
    swhid_parsed = None
    snapshot_context = None
    view_data = {}
    breadcrumbs = []
    try:
        swhid_parsed = get_swhid(swhid)
        focus_swhid_parsed = get_swhid(focus_swhid)
        if swhid_parsed.origin or swhid_parsed.visit:
            snapshot_context = get_snapshot_context(
                origin_url=swhid_parsed.origin,
                snapshot_id=swhid_parsed.visit.object_id.hex()
                if swhid_parsed.visit
                else None,
            )
        path = swhid_parsed.path.decode("utf-8") if swhid_parsed.path else ""

        error_info = {"status_code": 200, "description": None}

        if swhid_parsed and swhid_parsed.object_type == ObjectType.CONTENT:

            content_data = request_content(f"sha1_git:{swhid_parsed.object_id.hex()}")
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

            view_data = {
                "content": content,
                "content_size": content_data.get("length"),
                "max_content_size": content_display_max_size,
                "filename": path.split("/")[-1],
                "encoding": content_data.get("encoding"),
                "mimetype": mimetype,
                "language": language,
            }

        elif swhid_parsed and swhid_parsed.object_type == ObjectType.DIRECTORY:
            dirs, files = get_directory_entries(swhid_parsed.object_id.hex())
            for d in dirs:
                if d["type"] == "rev":
                    d["url"] = None
                else:
                    dir_swhid = QualifiedSWHID(
                        object_type=ObjectType.DIRECTORY,
                        object_id=hash_to_bytes(d["target"]),
                        origin=swhid_parsed.origin,
                        visit=swhid_parsed.visit,
                        anchor=swhid_parsed.anchor,
                        path=(path or "/") + d["name"] + "/",
                    )
                    d["url"] = reverse(
                        "swhid-iframe",
                        url_args={"swhid": str(dir_swhid)},
                        query_params={"focus_swhid": focus_swhid},
                    )

            for f in files:
                object_id = hash_to_bytes(f["target"])
                cnt_swhid = QualifiedSWHID(
                    object_type=ObjectType.CONTENT,
                    object_id=object_id,
                    origin=swhid_parsed.origin,
                    visit=swhid_parsed.visit,
                    anchor=swhid_parsed.anchor,
                    path=(path or "/") + f["name"],
                    lines=(
                        focus_swhid_parsed.lines
                        if object_id == focus_swhid_parsed.object_id
                        else None
                    ),
                )
                f["url"] = reverse(
                    "swhid-iframe",
                    url_args={"swhid": str(cnt_swhid)},
                    query_params={"focus_swhid": focus_swhid},
                )

            view_data = {"dirs": dirs, "files": files}

        elif swhid_parsed:
            error_info = {
                "status_code": 400,
                "description": (
                    f"Objects of type {swhid_parsed.object_type} are not supported"
                ),
            }

        if swhid_parsed and view_data:

            filename = None
            if swhid_parsed.object_type == ObjectType.CONTENT:
                split_path = path.split("/")
                filename = split_path[-1]
                path = path[: -len(filename)]

            path_info = gen_path_info(path) if path != "/" else []

            root_dir = None
            if snapshot_context and snapshot_context["root_directory"]:
                root_dir = snapshot_context["root_directory"]
            elif focus_swhid_parsed.object_type == ObjectType.DIRECTORY:
                root_dir = focus_swhid_parsed.object_id.hex()

            if root_dir:
                root_dir_swhid = QualifiedSWHID(
                    object_type=ObjectType.DIRECTORY,
                    object_id=hash_to_bytes(root_dir),
                    origin=swhid_parsed.origin,
                    visit=swhid_parsed.visit,
                    anchor=swhid_parsed.anchor,
                )
                breadcrumbs.append(
                    {
                        "name": root_dir[:7],
                        "url": reverse(
                            "swhid-iframe",
                            url_args={"swhid": str(root_dir_swhid)},
                            query_params={"focus_swhid": focus_swhid},
                        ),
                    }
                )

                for pi in path_info:
                    dir_info = archive.lookup_directory_with_path(root_dir, pi["path"])
                    dir_swhid = QualifiedSWHID(
                        object_type=ObjectType.DIRECTORY,
                        object_id=hash_to_bytes(dir_info["target"]),
                        origin=swhid_parsed.origin,
                        visit=swhid_parsed.visit,
                        anchor=swhid_parsed.anchor,
                        path="/" + pi["path"] + "/",
                    )
                    breadcrumbs.append(
                        {
                            "name": pi["name"],
                            "url": reverse(
                                "swhid-iframe",
                                url_args={"swhid": str(dir_swhid)},
                                query_params={"focus_swhid": focus_swhid},
                            ),
                        }
                    )
            if filename:
                breadcrumbs.append({"name": filename, "url": None})

    except BadInputExc as e:
        error_info = {"status_code": 400, "description": f"BadInputExc: {str(e)}"}
    except NotFoundExc as e:
        error_info = {"status_code": 404, "description": f"NotFoundExc: {str(e)}"}
    except Exception as e:
        error_info = {"status_code": 500, "description": str(e)}

    return render(
        request,
        "misc/iframe.html",
        {
            **view_data,
            "iframe_mode": True,
            "object_type": swhid_parsed.object_type.value if swhid_parsed else None,
            "lines": swhid_parsed.lines if swhid_parsed else None,
            "breadcrumbs": breadcrumbs,
            "swhid": swhid,
            "focus_swhid": focus_swhid,
            "error_code": error_info["status_code"],
            "error_message": http_status_code_message.get(error_info["status_code"]),
            "error_description": error_info["description"],
        },
        status=error_info["status_code"],
    )


urlpatterns = [
    url(
        r"^iframe/(?P<swhid>swh:[0-9]+:[a-z]+:[0-9a-f]+.*)$",
        swhid_iframe,
        name="swhid-iframe",
    ),
]
