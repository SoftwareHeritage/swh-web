# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import difflib
import json

from distutils.util import strtobool

from django.http import HttpResponse
from django.shortcuts import render
from django.template.defaultfilters import filesizeformat
import sentry_sdk

from swh.model.hashutil import hash_to_hex
from swh.model.identifiers import CONTENT, DIRECTORY, RELEASE, REVISION, SNAPSHOT

from swh.web.browse.browseurls import browse_route
from swh.web.browse.snapshot_context import get_snapshot_context
from swh.web.browse.utils import (
    request_content,
    prepare_content_for_display,
    content_display_max_size,
    gen_link,
    gen_directory_link,
)
from swh.web.common import query, service, highlightjs
from swh.web.common.exc import NotFoundExc, handle_view_exception
from swh.web.common.identifiers import get_swhids_info
from swh.web.common.typing import ContentMetadata, SWHObjectInfo
from swh.web.common.utils import reverse, gen_path_info, swh_object_icons


@browse_route(
    r"content/(?P<query_string>[0-9a-z_:]*[0-9a-f]+.)/raw/",
    view_name="browse-content-raw",
    checksum_args=["query_string"],
)
def content_raw(request, query_string):
    """Django view that produces a raw display of a content identified
    by its hash value.

    The url that points to it is
    :http:get:`/browse/content/[(algo_hash):](hash)/raw/`
    """
    try:
        re_encode = bool(strtobool(request.GET.get("re_encode", "false")))
        algo, checksum = query.parse_hash(query_string)
        checksum = hash_to_hex(checksum)
        content_data = request_content(query_string, max_size=None, re_encode=re_encode)
    except Exception as exc:
        return handle_view_exception(request, exc)

    filename = request.GET.get("filename", None)
    if not filename:
        filename = "%s_%s" % (algo, checksum)

    if (
        content_data["mimetype"].startswith("text/")
        or content_data["mimetype"] == "inode/x-empty"
    ):
        response = HttpResponse(content_data["raw_data"], content_type="text/plain")
        response["Content-disposition"] = "filename=%s" % filename
    else:
        response = HttpResponse(
            content_data["raw_data"], content_type="application/octet-stream"
        )
        response["Content-disposition"] = "attachment; filename=%s" % filename
    return response


_auto_diff_size_limit = 20000


@browse_route(
    r"content/(?P<from_query_string>.*)/diff/(?P<to_query_string>.*)",
    view_name="diff-contents",
)
def _contents_diff(request, from_query_string, to_query_string):
    """
    Browse endpoint used to compute unified diffs between two contents.

    Diffs are generated only if the two contents are textual.
    By default, diffs whose size are greater than 20 kB will
    not be generated. To force the generation of large diffs,
    the 'force' boolean query parameter must be used.

    Args:
        request: input django http request
        from_query_string: a string of the form "[ALGO_HASH:]HASH" where
            optional ALGO_HASH can be either ``sha1``, ``sha1_git``,
            ``sha256``, or ``blake2s256`` (default to ``sha1``) and HASH
            the hexadecimal representation of the hash value identifying
            the first content
        to_query_string: same as above for identifying the second content

    Returns:
        A JSON object containing the unified diff.

    """
    diff_data = {}
    content_from = None
    content_to = None
    content_from_size = 0
    content_to_size = 0
    content_from_lines = []
    content_to_lines = []
    force = request.GET.get("force", "false")
    path = request.GET.get("path", None)
    language = "nohighlight"

    force = bool(strtobool(force))

    if from_query_string == to_query_string:
        diff_str = "File renamed without changes"
    else:
        try:
            text_diff = True
            if from_query_string:
                content_from = request_content(from_query_string, max_size=None)
                content_from_display_data = prepare_content_for_display(
                    content_from["raw_data"], content_from["mimetype"], path
                )
                language = content_from_display_data["language"]
                content_from_size = content_from["length"]
                if not (
                    content_from["mimetype"].startswith("text/")
                    or content_from["mimetype"] == "inode/x-empty"
                ):
                    text_diff = False

            if text_diff and to_query_string:
                content_to = request_content(to_query_string, max_size=None)
                content_to_display_data = prepare_content_for_display(
                    content_to["raw_data"], content_to["mimetype"], path
                )
                language = content_to_display_data["language"]
                content_to_size = content_to["length"]
                if not (
                    content_to["mimetype"].startswith("text/")
                    or content_to["mimetype"] == "inode/x-empty"
                ):
                    text_diff = False

            diff_size = abs(content_to_size - content_from_size)

            if not text_diff:
                diff_str = "Diffs are not generated for non textual content"
                language = "nohighlight"
            elif not force and diff_size > _auto_diff_size_limit:
                diff_str = "Large diffs are not automatically computed"
                language = "nohighlight"
            else:
                if content_from:
                    content_from_lines = (
                        content_from["raw_data"].decode("utf-8").splitlines(True)
                    )
                    if content_from_lines and content_from_lines[-1][-1] != "\n":
                        content_from_lines[-1] += "[swh-no-nl-marker]\n"

                if content_to:
                    content_to_lines = (
                        content_to["raw_data"].decode("utf-8").splitlines(True)
                    )
                    if content_to_lines and content_to_lines[-1][-1] != "\n":
                        content_to_lines[-1] += "[swh-no-nl-marker]\n"

                diff_lines = difflib.unified_diff(content_from_lines, content_to_lines)
                diff_str = "".join(list(diff_lines)[2:])
        except Exception as exc:
            sentry_sdk.capture_exception(exc)
            diff_str = str(exc)

    diff_data["diff_str"] = diff_str
    diff_data["language"] = language
    diff_data_json = json.dumps(diff_data, separators=(",", ": "))
    return HttpResponse(diff_data_json, content_type="application/json")


@browse_route(
    r"content/(?P<query_string>[0-9a-z_:]*[0-9a-f]+.)/",
    view_name="browse-content",
    checksum_args=["query_string"],
)
def content_display(request, query_string):
    """Django view that produces an HTML display of a content identified
    by its hash value.

    The url that points to it is
    :http:get:`/browse/content/[(algo_hash):](hash)/`
    """
    try:
        algo, checksum = query.parse_hash(query_string)
        checksum = hash_to_hex(checksum)
        content_data = request_content(query_string, raise_if_unavailable=False)
        origin_url = request.GET.get("origin_url")
        selected_language = request.GET.get("language")
        if not origin_url:
            origin_url = request.GET.get("origin")
        snapshot_id = request.GET.get("snapshot")
        path = request.GET.get("path")
        snapshot_context = None
        if origin_url is not None or snapshot_id is not None:
            try:
                snapshot_context = get_snapshot_context(
                    origin_url=origin_url,
                    snapshot_id=snapshot_id,
                    branch_name=request.GET.get("branch"),
                    release_name=request.GET.get("release"),
                    revision_id=request.GET.get("revision"),
                    path=path,
                    browse_context=CONTENT,
                )
            except NotFoundExc as e:
                if str(e).startswith("Origin"):
                    raw_cnt_url = reverse(
                        "browse-content", url_args={"query_string": query_string}
                    )
                    error_message = (
                        "The Software Heritage archive has a content "
                        "with the hash you provided but the origin "
                        "mentioned in your request appears broken: %s. "
                        "Please check the URL and try again.\n\n"
                        "Nevertheless, you can still browse the content "
                        "without origin information: %s"
                        % (gen_link(origin_url), gen_link(raw_cnt_url))
                    )
                    raise NotFoundExc(error_message)
                else:
                    raise e
    except Exception as exc:
        return handle_view_exception(request, exc)

    content = None
    language = None
    mimetype = None
    if content_data["raw_data"] is not None:
        content_display_data = prepare_content_for_display(
            content_data["raw_data"], content_data["mimetype"], path
        )
        content = content_display_data["content_data"]
        language = content_display_data["language"]
        mimetype = content_display_data["mimetype"]

    # Override language with user-selected language
    if selected_language is not None:
        language = selected_language

    available_languages = None

    if mimetype and "text/" in mimetype:
        available_languages = highlightjs.get_supported_languages()

    filename = None
    path_info = None
    directory_id = None
    directory_url = None

    root_dir = None
    if snapshot_context:
        root_dir = snapshot_context.get("root_directory")

    query_params = snapshot_context["query_params"] if snapshot_context else {}

    breadcrumbs = []

    if path:
        split_path = path.split("/")
        root_dir = root_dir or split_path[0]
        filename = split_path[-1]
        if root_dir != path:
            path = path.replace(root_dir + "/", "")
            path = path[: -len(filename)]
            path_info = gen_path_info(path)
            query_params.pop("path", None)
            dir_url = reverse(
                "browse-directory",
                url_args={"sha1_git": root_dir},
                query_params=query_params,
            )
            breadcrumbs.append({"name": root_dir[:7], "url": dir_url})
            for pi in path_info:
                query_params["path"] = pi["path"]
                dir_url = reverse(
                    "browse-directory",
                    url_args={"sha1_git": root_dir},
                    query_params=query_params,
                )
                breadcrumbs.append({"name": pi["name"], "url": dir_url})
        breadcrumbs.append({"name": filename, "url": None})

    if path and root_dir != path:
        try:
            dir_info = service.lookup_directory_with_path(root_dir, path)
            directory_id = dir_info["target"]
        except Exception as exc:
            return handle_view_exception(request, exc)
    elif root_dir != path:
        directory_id = root_dir
    else:
        root_dir = None

    if directory_id:
        directory_url = gen_directory_link(directory_id)

    query_params = {"filename": filename}

    content_checksums = content_data["checksums"]

    content_url = reverse(
        "browse-content",
        url_args={"query_string": f'sha1_git:{content_checksums["sha1_git"]}'},
    )

    content_raw_url = reverse(
        "browse-content-raw",
        url_args={"query_string": query_string},
        query_params=query_params,
    )

    content_metadata = ContentMetadata(
        object_type=CONTENT,
        object_id=content_checksums["sha1_git"],
        sha1=content_checksums["sha1"],
        sha1_git=content_checksums["sha1_git"],
        sha256=content_checksums["sha256"],
        blake2s256=content_checksums["blake2s256"],
        content_url=content_url,
        mimetype=content_data["mimetype"],
        encoding=content_data["encoding"],
        size=filesizeformat(content_data["length"]),
        language=content_data["language"],
        licenses=content_data["licenses"],
        root_directory=root_dir,
        path=f"/{path}" if path else "",
        filename=filename or "",
        directory=directory_id,
        directory_url=directory_url,
        revision=None,
        release=None,
        snapshot=None,
        origin_url=origin_url,
    )

    swh_objects = [
        SWHObjectInfo(object_type=CONTENT, object_id=content_checksums["sha1_git"])
    ]

    if directory_id:
        swh_objects.append(SWHObjectInfo(object_type=DIRECTORY, object_id=directory_id))

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

    swhids_info = get_swhids_info(
        swh_objects, snapshot_context, extra_context=content_metadata,
    )

    heading = "Content - %s" % content_checksums["sha1_git"]
    if breadcrumbs:
        content_path = "/".join([bc["name"] for bc in breadcrumbs])
        heading += " - %s" % content_path

    return render(
        request,
        "browse/content.html",
        {
            "heading": heading,
            "swh_object_id": swhids_info[0]["swhid"],
            "swh_object_name": "Content",
            "swh_object_metadata": content_metadata,
            "content": content,
            "content_size": content_data["length"],
            "max_content_size": content_display_max_size,
            "filename": filename,
            "encoding": content_data["encoding"],
            "mimetype": mimetype,
            "language": language,
            "available_languages": available_languages,
            "breadcrumbs": breadcrumbs,
            "top_right_link": {
                "url": content_raw_url,
                "icon": swh_object_icons["content"],
                "text": "Raw File",
            },
            "snapshot_context": snapshot_context,
            "vault_cooking": None,
            "show_actions": True,
            "swhids_info": swhids_info,
            "error_code": content_data["error_code"],
            "error_message": content_data["error_message"],
            "error_description": content_data["error_description"],
        },
        status=content_data["error_code"],
    )
