# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from swh.model.swhids import ObjectType
from swh.web.browse.browseurls import browse_route
from swh.web.browse.snapshot_context import get_snapshot_context
from swh.web.browse.utils import (
    gen_content_link,
    gen_directory_link,
    gen_link,
    gen_person_mail_link,
    gen_release_link,
    gen_revision_link,
)
from swh.web.utils import archive, format_utc_iso_date, reverse
from swh.web.utils.exc import NotFoundExc, sentry_capture_exception
from swh.web.utils.identifiers import get_swhids_info
from swh.web.utils.typing import ReleaseMetadata, SnapshotContext, SWHObjectInfo


@browse_route(
    r"release/(?P<sha1_git>[0-9a-f]+)/",
    view_name="browse-release",
    checksum_args=["sha1_git"],
)
def release_browse(request: HttpRequest, sha1_git: str) -> HttpResponse:
    """
    Django view that produces an HTML display of a release
    identified by its id.

    The url that points to it is :http:get:`/browse/release/(sha1_git)/`.
    """
    release = archive.lookup_release(sha1_git)
    snapshot_context: Optional[SnapshotContext] = None
    origin_info = None
    snapshot_id = request.GET.get("snapshot_id")
    if not snapshot_id:
        snapshot_id = request.GET.get("snapshot")
    origin_url = request.GET.get("origin_url")
    if not origin_url:
        origin_url = request.GET.get("origin")
    timestamp = request.GET.get("timestamp")
    visit_id = int(request.GET.get("visit_id", 0))
    if origin_url:
        try:
            snapshot_context = get_snapshot_context(
                snapshot_id,
                origin_url,
                timestamp,
                visit_id or None,
                release_name=release["name"],
            )
        except NotFoundExc as e:
            raw_rel_url = reverse("browse-release", url_args={"sha1_git": sha1_git})
            error_message = (
                "The Software Heritage archive has a release "
                "with the hash you provided but the origin "
                "mentioned in your request appears broken: %s. "
                "Please check the URL and try again.\n\n"
                "Nevertheless, you can still browse the release "
                "without origin information: %s"
                % (gen_link(origin_url), gen_link(raw_rel_url))
            )
            if str(e).startswith("Origin"):
                raise NotFoundExc(error_message)
            else:
                raise e
        origin_info = snapshot_context["origin_info"]
    elif snapshot_id:
        snapshot_context = get_snapshot_context(
            snapshot_id, release_name=release["name"]
        )

    if snapshot_context is not None:
        snapshot_id = snapshot_context.get("snapshot_id", None)

    release_metadata = ReleaseMetadata(
        object_type=ObjectType.RELEASE,
        object_id=sha1_git,
        release=sha1_git,
        author=release["author"]["fullname"] if release["author"] else "None",
        author_url=gen_person_mail_link(release["author"])
        if release["author"]
        else "None",
        date=format_utc_iso_date(release["date"]),
        name=release["name"],
        synthetic=release["synthetic"],
        target=release["target"],
        target_type=release["target_type"],
        snapshot=snapshot_id,
        origin_url=origin_url,
    )

    release_note_lines = []
    if release["message"]:
        release_note_lines = release["message"].split("\n")

    swh_objects = [SWHObjectInfo(object_type=ObjectType.RELEASE, object_id=sha1_git)]

    vault_cooking = None

    rev_directory = None
    target_link = None
    if release["target_type"] == ObjectType.REVISION.name.lower():
        target_link = gen_revision_link(
            release["target"],
            snapshot_context=snapshot_context,
            link_text=None,
            link_attrs=None,
        )
        try:
            revision = archive.lookup_revision(release["target"])
            rev_directory = revision["directory"]
            vault_cooking = {
                "directory_context": True,
                "directory_swhid": f"swh:1:dir:{rev_directory}",
                "revision_context": True,
                "revision_swhid": f"swh:1:rev:{release['target']}",
            }
            swh_objects.append(
                SWHObjectInfo(
                    object_type=ObjectType.REVISION, object_id=release["target"]
                )
            )
            swh_objects.append(
                SWHObjectInfo(object_type=ObjectType.DIRECTORY, object_id=rev_directory)
            )
        except Exception as exc:
            sentry_capture_exception(exc)
    elif release["target_type"] == ObjectType.DIRECTORY.name.lower():
        target_link = gen_directory_link(
            release["target"],
            snapshot_context=snapshot_context,
            link_text=None,
            link_attrs=None,
        )
        try:
            # check directory exists
            archive.lookup_directory(release["target"])
            vault_cooking = {
                "directory_context": True,
                "directory_swhid": f"swh:1:dir:{release['target']}",
                "revision_context": False,
                "revision_swhid": None,
            }
            swh_objects.append(
                SWHObjectInfo(
                    object_type=ObjectType.DIRECTORY, object_id=release["target"]
                )
            )
        except Exception as exc:
            sentry_capture_exception(exc)
    elif release["target_type"] == ObjectType.CONTENT.name.lower():
        target_link = gen_content_link(
            release["target"],
            snapshot_context=snapshot_context,
            link_text=None,
            link_attrs=None,
        )
        swh_objects.append(
            SWHObjectInfo(object_type=ObjectType.CONTENT, object_id=release["target"])
        )
    elif release["target_type"] == ObjectType.RELEASE.name.lower():
        target_link = gen_release_link(
            release["target"],
            snapshot_context=snapshot_context,
            link_text=None,
            link_attrs=None,
        )

    rev_directory_url = None
    if rev_directory is not None:
        if origin_info:
            rev_directory_url = reverse(
                "browse-origin-directory",
                query_params={
                    "origin_url": origin_info["url"],
                    "release": release["name"],
                    "snapshot": snapshot_id,
                },
            )
        elif snapshot_id:
            rev_directory_url = reverse(
                "browse-snapshot-directory",
                url_args={"snapshot_id": snapshot_id},
                query_params={"release": release["name"]},
            )
        else:
            rev_directory_url = reverse(
                "browse-directory", url_args={"sha1_git": rev_directory}
            )

    directory_link = None
    if rev_directory_url is not None:
        directory_link = gen_link(rev_directory_url, rev_directory)
    release["directory_link"] = directory_link
    release["target_link"] = target_link

    if snapshot_context:
        snapshot_id = snapshot_context["snapshot_id"]

    if snapshot_id:
        swh_objects.append(
            SWHObjectInfo(object_type=ObjectType.SNAPSHOT, object_id=snapshot_id)
        )

    swhids_info = get_swhids_info(swh_objects, snapshot_context)

    note_header = "None"
    if len(release_note_lines) > 0:
        note_header = release_note_lines[0]

    release["note_header"] = note_header
    release["note_body"] = "\n".join(release_note_lines[1:])

    heading = "Release - %s" % release["name"]
    if snapshot_context:
        context_found = "snapshot: %s" % snapshot_context["snapshot_id"]
        if origin_info:
            context_found = "origin: %s" % origin_info["url"]
        heading += " - %s" % context_found

    return render(
        request,
        "browse-release.html",
        {
            "heading": heading,
            "swh_object_id": swhids_info[0]["swhid"],
            "swh_object_name": "Release",
            "swh_object_metadata": release_metadata,
            "release": release,
            "snapshot_context": snapshot_context,
            "show_actions": True,
            "breadcrumbs": None,
            "vault_cooking": vault_cooking,
            "top_right_link": None,
            "swhids_info": swhids_info,
        },
    )
