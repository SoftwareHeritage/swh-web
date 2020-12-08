# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import hashlib
import json
import textwrap

from django.http import JsonResponse
from django.shortcuts import render
from django.template.defaultfilters import filesizeformat
from django.utils.safestring import mark_safe

from swh.model.identifiers import CONTENT, DIRECTORY, REVISION, SNAPSHOT, swhid
from swh.web.browse.browseurls import browse_route
from swh.web.browse.snapshot_context import get_snapshot_context
from swh.web.browse.utils import (
    content_display_max_size,
    format_log_entries,
    gen_link,
    gen_person_mail_link,
    gen_revision_url,
    get_directory_entries,
    get_readme_to_display,
    get_revision_log_url,
    prepare_content_for_display,
    request_content,
)
from swh.web.common import archive
from swh.web.common.exc import NotFoundExc, http_status_code_message
from swh.web.common.identifiers import get_swhids_info
from swh.web.common.typing import RevisionMetadata, SWHObjectInfo
from swh.web.common.utils import (
    format_utc_iso_date,
    gen_path_info,
    reverse,
    swh_object_icons,
)


def _gen_content_url(revision, query_string, path, snapshot_context):
    if snapshot_context:
        query_params = snapshot_context["query_params"]
        query_params["path"] = path
        query_params["revision"] = revision["id"]
        content_url = reverse("browse-origin-content", query_params=query_params)
    else:
        content_path = "%s/%s" % (revision["directory"], path)
        content_url = reverse(
            "browse-content",
            url_args={"query_string": query_string},
            query_params={"path": content_path},
        )
    return content_url


def _gen_diff_link(idx, diff_anchor, link_text):
    if idx < _max_displayed_file_diffs:
        return gen_link(diff_anchor, link_text)
    else:
        return link_text


# TODO: put in conf
_max_displayed_file_diffs = 1000


def _gen_revision_changes_list(revision, changes, snapshot_context):
    """
    Returns a HTML string describing the file changes
    introduced in a revision.
    As this string will be displayed in the browse revision view,
    links to adequate file diffs are also generated.

    Args:
        revision (str): hexadecimal representation of a revision identifier
        changes (list): list of file changes in the revision
        snapshot_context (dict): optional origin context used to reverse
            the content urls

    Returns:
        A string to insert in a revision HTML view.

    """
    changes_msg = []
    for i, change in enumerate(changes):
        hasher = hashlib.sha1()
        from_query_string = ""
        to_query_string = ""
        diff_id = "diff-"
        if change["from"]:
            from_query_string = "sha1_git:" + change["from"]["target"]
            diff_id += change["from"]["target"] + "-" + change["from_path"]
        diff_id += "-"
        if change["to"]:
            to_query_string = "sha1_git:" + change["to"]["target"]
            diff_id += change["to"]["target"] + change["to_path"]
        change["path"] = change["to_path"] or change["from_path"]
        url_args = {
            "from_query_string": from_query_string,
            "to_query_string": to_query_string,
        }
        query_params = {"path": change["path"]}
        change["diff_url"] = reverse(
            "diff-contents", url_args=url_args, query_params=query_params
        )

        hasher.update(diff_id.encode("utf-8"))
        diff_id = hasher.hexdigest()
        change["id"] = diff_id
        diff_link = "#diff_" + diff_id

        if change["type"] == "modify":
            change["content_url"] = _gen_content_url(
                revision, to_query_string, change["to_path"], snapshot_context
            )
            changes_msg.append(
                "modified:  %s" % _gen_diff_link(i, diff_link, change["to_path"])
            )
        elif change["type"] == "insert":
            change["content_url"] = _gen_content_url(
                revision, to_query_string, change["to_path"], snapshot_context
            )
            changes_msg.append(
                "new file:  %s" % _gen_diff_link(i, diff_link, change["to_path"])
            )
        elif change["type"] == "delete":
            parent = archive.lookup_revision(revision["parents"][0])
            change["content_url"] = _gen_content_url(
                parent, from_query_string, change["from_path"], snapshot_context
            )
            changes_msg.append(
                "deleted:   %s" % _gen_diff_link(i, diff_link, change["from_path"])
            )
        elif change["type"] == "rename":
            change["content_url"] = _gen_content_url(
                revision, to_query_string, change["to_path"], snapshot_context
            )
            link_text = change["from_path"] + " &rarr; " + change["to_path"]
            changes_msg.append(
                "renamed:   %s" % _gen_diff_link(i, diff_link, link_text)
            )
    if not changes:
        changes_msg.append("No changes")
    return mark_safe("\n".join(changes_msg))


@browse_route(
    r"revision/(?P<sha1_git>[0-9a-f]+)/diff/",
    view_name="diff-revision",
    checksum_args=["sha1_git"],
)
def _revision_diff(request, sha1_git):
    """
    Browse internal endpoint to compute revision diff
    """
    revision = archive.lookup_revision(sha1_git)
    snapshot_context = None
    origin_url = request.GET.get("origin_url", None)
    if not origin_url:
        origin_url = request.GET.get("origin", None)
    timestamp = request.GET.get("timestamp", None)
    visit_id = request.GET.get("visit_id", None)
    if origin_url:
        snapshot_context = get_snapshot_context(
            origin_url=origin_url, timestamp=timestamp, visit_id=visit_id
        )

    changes = archive.diff_revision(sha1_git)
    changes_msg = _gen_revision_changes_list(revision, changes, snapshot_context)

    diff_data = {
        "total_nb_changes": len(changes),
        "changes": changes[:_max_displayed_file_diffs],
        "changes_msg": changes_msg,
    }
    return JsonResponse(diff_data)


NB_LOG_ENTRIES = 100


@browse_route(
    r"revision/(?P<sha1_git>[0-9a-f]+)/log/",
    view_name="browse-revision-log",
    checksum_args=["sha1_git"],
)
def revision_log_browse(request, sha1_git):
    """
    Django view that produces an HTML display of the history
    log for a revision identified by its id.

    The url that points to it is :http:get:`/browse/revision/(sha1_git)/log/`
    """
    origin_url = request.GET.get("origin_url")
    snapshot_id = request.GET.get("snapshot")
    snapshot_context = None
    if origin_url or snapshot_id:
        snapshot_context = get_snapshot_context(
            snapshot_id=snapshot_id,
            origin_url=origin_url,
            timestamp=request.GET.get("timestamp"),
            visit_id=request.GET.get("visit_id"),
            branch_name=request.GET.get("branch"),
            release_name=request.GET.get("release"),
            revision_id=sha1_git,
        )
    per_page = int(request.GET.get("per_page", NB_LOG_ENTRIES))
    offset = int(request.GET.get("offset", 0))
    revs_ordering = request.GET.get("revs_ordering", "committer_date")
    session_key = "rev_%s_log_ordering_%s" % (sha1_git, revs_ordering)
    rev_log_session = request.session.get(session_key, None)
    rev_log = []
    revs_walker_state = None
    if rev_log_session:
        rev_log = rev_log_session["rev_log"]
        revs_walker_state = rev_log_session["revs_walker_state"]

    if len(rev_log) < offset + per_page:
        revs_walker = archive.get_revisions_walker(
            revs_ordering,
            sha1_git,
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

    revs_ordering = request.GET.get("revs_ordering", "")

    prev_log_url = None
    if len(rev_log) > offset + per_page:
        prev_log_url = reverse(
            "browse-revision-log",
            url_args={"sha1_git": sha1_git},
            query_params={
                "per_page": per_page,
                "offset": offset + per_page,
                "revs_ordering": revs_ordering or None,
            },
        )

    next_log_url = None
    if offset != 0:
        next_log_url = reverse(
            "browse-revision-log",
            url_args={"sha1_git": sha1_git},
            query_params={
                "per_page": per_page,
                "offset": offset - per_page,
                "revs_ordering": revs_ordering or None,
            },
        )

    revision_log_data = format_log_entries(revision_log, per_page)

    swh_rev_id = swhid("revision", sha1_git)

    return render(
        request,
        "browse/revision-log.html",
        {
            "heading": "Revision history",
            "swh_object_id": swh_rev_id,
            "swh_object_name": "Revisions history",
            "swh_object_metadata": None,
            "revision_log": revision_log_data,
            "revs_ordering": revs_ordering,
            "next_log_url": next_log_url,
            "prev_log_url": prev_log_url,
            "breadcrumbs": None,
            "top_right_link": None,
            "snapshot_context": snapshot_context,
            "vault_cooking": None,
            "show_actions": True,
            "swhids_info": None,
        },
    )


@browse_route(
    r"revision/(?P<sha1_git>[0-9a-f]+)/",
    view_name="browse-revision",
    checksum_args=["sha1_git"],
)
def revision_browse(request, sha1_git):
    """
    Django view that produces an HTML display of a revision
    identified by its id.

    The url that points to it is :http:get:`/browse/revision/(sha1_git)/`.
    """
    revision = archive.lookup_revision(sha1_git)
    origin_info = None
    snapshot_context = None
    origin_url = request.GET.get("origin_url")
    if not origin_url:
        origin_url = request.GET.get("origin")
    timestamp = request.GET.get("timestamp")
    visit_id = request.GET.get("visit_id")
    snapshot_id = request.GET.get("snapshot_id")
    if not snapshot_id:
        snapshot_id = request.GET.get("snapshot")
    path = request.GET.get("path")
    dir_id = None
    dirs, files = [], []
    content_data = {}
    if origin_url:
        try:
            snapshot_context = get_snapshot_context(
                snapshot_id=snapshot_id,
                origin_url=origin_url,
                timestamp=timestamp,
                visit_id=visit_id,
                branch_name=request.GET.get("branch"),
                release_name=request.GET.get("release"),
                revision_id=sha1_git,
                path=path,
            )
        except NotFoundExc as e:
            raw_rev_url = reverse("browse-revision", url_args={"sha1_git": sha1_git})
            error_message = (
                "The Software Heritage archive has a revision "
                "with the hash you provided but the origin "
                "mentioned in your request appears broken: %s. "
                "Please check the URL and try again.\n\n"
                "Nevertheless, you can still browse the revision "
                "without origin information: %s"
                % (gen_link(origin_url), gen_link(raw_rev_url))
            )
            if str(e).startswith("Origin"):
                raise NotFoundExc(error_message)
            else:
                raise e
        origin_info = snapshot_context["origin_info"]
        snapshot_id = snapshot_context["snapshot_id"]
    elif snapshot_id:
        snapshot_context = get_snapshot_context(snapshot_id)

    error_info = {"status_code": 200, "description": None}

    if path:
        try:
            file_info = archive.lookup_directory_with_path(revision["directory"], path)
            if file_info["type"] == "dir":
                dir_id = file_info["target"]
            else:
                query_string = "sha1_git:" + file_info["target"]
                content_data = request_content(query_string)
        except NotFoundExc as e:
            error_info["status_code"] = 404
            error_info["description"] = f"NotFoundExc: {str(e)}"
    else:
        dir_id = revision["directory"]

    if dir_id:
        path = "" if path is None else (path + "/")
        dirs, files = get_directory_entries(dir_id)

    revision_metadata = RevisionMetadata(
        object_type=REVISION,
        object_id=sha1_git,
        revision=sha1_git,
        author=revision["author"]["fullname"] if revision["author"] else "None",
        author_url=gen_person_mail_link(revision["author"])
        if revision["author"]
        else "None",
        committer=revision["committer"]["fullname"]
        if revision["committer"]
        else "None",
        committer_url=gen_person_mail_link(revision["committer"])
        if revision["committer"]
        else "None",
        committer_date=format_utc_iso_date(revision["committer_date"]),
        date=format_utc_iso_date(revision["date"]),
        directory=revision["directory"],
        merge=revision["merge"],
        metadata=json.dumps(
            revision["metadata"], sort_keys=True, indent=4, separators=(",", ": ")
        ),
        parents=revision["parents"],
        synthetic=revision["synthetic"],
        type=revision["type"],
        snapshot=snapshot_id,
        origin_url=origin_url,
    )

    message_lines = ["None"]
    if revision["message"]:
        message_lines = revision["message"].split("\n")

    parents = []
    for p in revision["parents"]:
        parent_url = gen_revision_url(p, snapshot_context)
        parents.append({"id": p, "url": parent_url})

    path_info = gen_path_info(path)

    query_params = snapshot_context["query_params"] if snapshot_context else {}

    breadcrumbs = []
    breadcrumbs.append(
        {
            "name": revision["directory"][:7],
            "url": reverse(
                "browse-revision",
                url_args={"sha1_git": sha1_git},
                query_params=query_params,
            ),
        }
    )
    for pi in path_info:
        query_params["path"] = pi["path"]
        breadcrumbs.append(
            {
                "name": pi["name"],
                "url": reverse(
                    "browse-revision",
                    url_args={"sha1_git": sha1_git},
                    query_params=query_params,
                ),
            }
        )

    vault_cooking = {
        "directory_context": False,
        "directory_id": None,
        "revision_context": True,
        "revision_id": sha1_git,
    }

    swh_objects = [SWHObjectInfo(object_type=REVISION, object_id=sha1_git)]

    content = None
    content_size = None
    filename = None
    mimetype = None
    language = None
    readme_name = None
    readme_url = None
    readme_html = None
    readmes = {}

    extra_context = dict(revision_metadata)
    extra_context["path"] = f"/{path}" if path else None

    if content_data:
        breadcrumbs[-1]["url"] = None
        content_size = content_data["length"]
        mimetype = content_data["mimetype"]
        if content_data["raw_data"]:
            content_display_data = prepare_content_for_display(
                content_data["raw_data"], content_data["mimetype"], path
            )
            content = content_display_data["content_data"]
            language = content_display_data["language"]
            mimetype = content_display_data["mimetype"]
        if path:
            filename = path_info[-1]["name"]
            query_params["filename"] = filename
            filepath = "/".join(pi["name"] for pi in path_info[:-1])
            extra_context["path"] = f"/{filepath}/" if filepath else "/"
            extra_context["filename"] = filename

        top_right_link = {
            "url": reverse(
                "browse-content-raw",
                url_args={"query_string": query_string},
                query_params={"filename": filename},
            ),
            "icon": swh_object_icons["content"],
            "text": "Raw File",
        }

        swh_objects.append(
            SWHObjectInfo(object_type=CONTENT, object_id=file_info["target"])
        )
    else:
        for d in dirs:
            if d["type"] == "rev":
                d["url"] = reverse(
                    "browse-revision", url_args={"sha1_git": d["target"]}
                )
            else:
                query_params["path"] = path + d["name"]
                d["url"] = reverse(
                    "browse-revision",
                    url_args={"sha1_git": sha1_git},
                    query_params=query_params,
                )
        for f in files:
            query_params["path"] = path + f["name"]
            f["url"] = reverse(
                "browse-revision",
                url_args={"sha1_git": sha1_git},
                query_params=query_params,
            )
            if f["length"] is not None:
                f["length"] = filesizeformat(f["length"])
            if f["name"].lower().startswith("readme"):
                readmes[f["name"]] = f["checksums"]["sha1"]

        readme_name, readme_url, readme_html = get_readme_to_display(readmes)

        top_right_link = {
            "url": get_revision_log_url(sha1_git, snapshot_context),
            "icon": swh_object_icons["revisions history"],
            "text": "History",
        }

        vault_cooking["directory_context"] = True
        vault_cooking["directory_id"] = dir_id

        swh_objects.append(SWHObjectInfo(object_type=DIRECTORY, object_id=dir_id))

    query_params.pop("path", None)

    diff_revision_url = reverse(
        "diff-revision", url_args={"sha1_git": sha1_git}, query_params=query_params,
    )

    if snapshot_id:
        swh_objects.append(SWHObjectInfo(object_type=SNAPSHOT, object_id=snapshot_id))

    swhids_info = get_swhids_info(swh_objects, snapshot_context, extra_context)

    heading = "Revision - %s - %s" % (
        sha1_git[:7],
        textwrap.shorten(message_lines[0], width=70),
    )
    if snapshot_context:
        context_found = "snapshot: %s" % snapshot_context["snapshot_id"]
        if origin_info:
            context_found = "origin: %s" % origin_info["url"]
        heading += " - %s" % context_found

    return render(
        request,
        "browse/revision.html",
        {
            "heading": heading,
            "swh_object_id": swhids_info[0]["swhid"],
            "swh_object_name": "Revision",
            "swh_object_metadata": revision_metadata,
            "message_header": message_lines[0],
            "message_body": "\n".join(message_lines[1:]),
            "parents": parents,
            "snapshot_context": snapshot_context,
            "dirs": dirs,
            "files": files,
            "content": content,
            "content_size": content_size,
            "max_content_size": content_display_max_size,
            "filename": filename,
            "encoding": content_data.get("encoding"),
            "mimetype": mimetype,
            "language": language,
            "readme_name": readme_name,
            "readme_url": readme_url,
            "readme_html": readme_html,
            "breadcrumbs": breadcrumbs,
            "top_right_link": top_right_link,
            "vault_cooking": vault_cooking,
            "diff_revision_url": diff_revision_url,
            "show_actions": True,
            "swhids_info": swhids_info,
            "error_code": error_info["status_code"],
            "error_message": http_status_code_message.get(error_info["status_code"]),
            "error_description": error_info["description"],
        },
        status=error_info["status_code"],
    )
