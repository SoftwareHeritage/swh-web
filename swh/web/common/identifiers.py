# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict, Iterable, List, Optional, cast
from urllib.parse import quote, unquote

from typing_extensions import TypedDict

from django.http import QueryDict

from swh.model.exceptions import ValidationError
from swh.model.hashutil import hash_to_bytes
from swh.model.identifiers import (
    CONTENT,
    DIRECTORY,
    ORIGIN,
    RELEASE,
    REVISION,
    SNAPSHOT,
    SWHID,
    parse_swhid,
    swhid,
)
from swh.web.common import archive
from swh.web.common.exc import BadInputExc
from swh.web.common.typing import (
    QueryParameters,
    SnapshotContext,
    SWHIDContext,
    SWHIDInfo,
    SWHObjectInfo,
)
from swh.web.common.utils import reverse


def gen_swhid(
    object_type: str,
    object_id: str,
    scheme_version: int = 1,
    metadata: SWHIDContext = {},
) -> str:
    """
    Returns the SoftWare Heritage persistent IDentifier for a swh object based on:

        * the object type
        * the object id
        * the SWHID scheme version

    Args:
        object_type: the swh object type
            (content/directory/release/revision/snapshot)
        object_id: the swh object id (hexadecimal representation
            of its hash value)
        scheme_version: the scheme version of the SWHIDs

    Returns:
        the SWHID of the object

    Raises:
        BadInputExc: if the provided parameters do not enable to
            generate a valid identifier
    """
    try:
        obj_swhid = swhid(
            object_type,
            object_id,
            scheme_version,
            cast(Dict[str, Any], {k: v for k, v in metadata.items() if v is not None}),
        )
    except ValidationError as e:
        raise BadInputExc("Invalid object (%s) for SWHID. %s" % (object_id, e))
    else:
        return obj_swhid


class ResolvedSWHID(TypedDict):
    """parsed SWHID with context"""

    swhid_parsed: SWHID
    """URL to browse object according to SWHID context"""
    browse_url: Optional[str]


def resolve_swhid(
    swhid: str, query_params: Optional[QueryParameters] = None
) -> ResolvedSWHID:
    """
    Try to resolve a SoftWare Heritage persistent IDentifier into an url for
    browsing the targeted object.

    Args:
        swhid: a SoftWare Heritage persistent IDentifier
        query_params: optional dict filled with
            query parameters to append to the browse url

    Returns:
        a dict with the following keys:

            * **swhid_parsed**: the parsed identifier
            * **browse_url**: the url for browsing the targeted object
    """
    swhid_parsed = get_swhid(swhid)
    object_type = swhid_parsed.object_type
    object_id = swhid_parsed.object_id
    browse_url = None
    url_args = {}
    query_dict = QueryDict("", mutable=True)
    fragment = ""
    anchor_swhid_parsed = None
    process_lines = object_type is CONTENT

    if query_params and len(query_params) > 0:
        for k in sorted(query_params.keys()):
            query_dict[k] = query_params[k]

    if "origin" in swhid_parsed.metadata:
        origin_url = unquote(swhid_parsed.metadata["origin"])
        origin_url = archive.lookup_origin({"url": origin_url})["url"]
        query_dict["origin_url"] = origin_url

    if "anchor" in swhid_parsed.metadata:
        anchor_swhid_parsed = get_swhid(swhid_parsed.metadata["anchor"])

    if "path" in swhid_parsed.metadata and swhid_parsed.metadata["path"] != "/":
        query_dict["path"] = unquote(swhid_parsed.metadata["path"])
        if anchor_swhid_parsed:
            directory = ""
            if anchor_swhid_parsed.object_type == DIRECTORY:
                directory = anchor_swhid_parsed.object_id
            elif anchor_swhid_parsed.object_type == REVISION:
                revision = archive.lookup_revision(anchor_swhid_parsed.object_id)
                directory = revision["directory"]
            elif anchor_swhid_parsed.object_type == RELEASE:
                release = archive.lookup_release(anchor_swhid_parsed.object_id)
                if release["target_type"] == REVISION:
                    revision = archive.lookup_revision(release["target"])
                    directory = revision["directory"]
            if object_type == CONTENT:
                if "origin" not in swhid_parsed.metadata:
                    # when no origin context, content objects need to have their
                    # path prefixed by root directory id for proper breadcrumbs display
                    query_dict["path"] = directory + query_dict["path"]
                else:
                    # remove leading slash from SWHID content path
                    query_dict["path"] = query_dict["path"][1:]
            elif object_type == DIRECTORY:
                object_id = directory
                # remove leading and trailing slashes from SWHID directory path
                if query_dict["path"].endswith("/"):
                    query_dict["path"] = query_dict["path"][1:-1]
                else:
                    query_dict["path"] = query_dict["path"][1:]

    # snapshot context
    if "visit" in swhid_parsed.metadata:

        snp_swhid_parsed = get_swhid(swhid_parsed.metadata["visit"])
        if snp_swhid_parsed.object_type != SNAPSHOT:
            raise BadInputExc("Visit must be a snapshot SWHID.")
        query_dict["snapshot"] = snp_swhid_parsed.object_id

        if anchor_swhid_parsed:
            if anchor_swhid_parsed.object_type == REVISION:
                # check if the anchor revision is the tip of a branch
                branch_name = archive.lookup_snapshot_branch_name_from_tip_revision(
                    snp_swhid_parsed.object_id, anchor_swhid_parsed.object_id
                )
                if branch_name:
                    query_dict["branch"] = branch_name
                elif object_type != REVISION:
                    query_dict["revision"] = anchor_swhid_parsed.object_id

            elif anchor_swhid_parsed.object_type == RELEASE:
                release = archive.lookup_release(anchor_swhid_parsed.object_id)
                if release:
                    query_dict["release"] = release["name"]

        if object_type == REVISION and "release" not in query_dict:
            branch_name = archive.lookup_snapshot_branch_name_from_tip_revision(
                snp_swhid_parsed.object_id, object_id
            )
            if branch_name:
                query_dict["branch"] = branch_name

    # browsing content or directory without snapshot context
    elif object_type in (CONTENT, DIRECTORY) and anchor_swhid_parsed:
        if anchor_swhid_parsed.object_type == REVISION:
            # anchor revision, objects are browsed from its view
            object_type = REVISION
            object_id = anchor_swhid_parsed.object_id
        elif object_type == DIRECTORY and anchor_swhid_parsed.object_type == DIRECTORY:
            # a directory is browsed from its root
            object_id = anchor_swhid_parsed.object_id

    if object_type == CONTENT:
        url_args["query_string"] = f"sha1_git:{object_id}"
    elif object_type == DIRECTORY:
        url_args["sha1_git"] = object_id
    elif object_type == RELEASE:
        url_args["sha1_git"] = object_id
    elif object_type == REVISION:
        url_args["sha1_git"] = object_id
    elif object_type == SNAPSHOT:
        url_args["snapshot_id"] = object_id
    elif object_type == ORIGIN:
        raise BadInputExc(
            (
                "Origin SWHIDs are not publicly resolvable because they are for "
                "internal usage only"
            )
        )

    if "lines" in swhid_parsed.metadata and process_lines:
        lines = swhid_parsed.metadata["lines"].split("-")
        fragment += "#L" + lines[0]
        if len(lines) > 1:
            fragment += "-L" + lines[1]

    if url_args:
        browse_url = (
            reverse(
                f"browse-{object_type}", url_args=url_args, query_params=query_dict,
            )
            + fragment
        )

    return ResolvedSWHID(swhid_parsed=swhid_parsed, browse_url=browse_url)


def get_swhid(swhid: str) -> SWHID:
    """Check if a SWHID is valid and return it parsed.

        Args:
            swhid: a SoftWare Heritage persistent IDentifier.

        Raises:
            BadInputExc: if the provided SWHID can not be parsed.

        Return:
            A parsed SWHID.
    """
    try:
        swhid_parsed = parse_swhid(swhid)
    except ValidationError as ve:
        raise BadInputExc("Error when parsing identifier: %s" % " ".join(ve.messages))
    else:
        return swhid_parsed


def group_swhids(swhids: Iterable[SWHID],) -> Dict[str, List[bytes]]:
    """
    Groups many SoftWare Heritage persistent IDentifiers into a
    dictionary depending on their type.

    Args:
        swhids: an iterable of SoftWare Heritage persistent
            IDentifier objects

    Returns:
        A dictionary with:
            keys: object types
            values: object hashes
    """
    swhids_by_type: Dict[str, List[bytes]] = {
        CONTENT: [],
        DIRECTORY: [],
        REVISION: [],
        RELEASE: [],
        SNAPSHOT: [],
    }

    for obj_swhid in swhids:
        obj_id = obj_swhid.object_id
        obj_type = obj_swhid.object_type
        swhids_by_type[obj_type].append(hash_to_bytes(obj_id))

    return swhids_by_type


def get_swhids_info(
    swh_objects: Iterable[SWHObjectInfo],
    snapshot_context: Optional[SnapshotContext] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> List[SWHIDInfo]:
    """
    Returns a list of dict containing info related to SWHIDs of objects.

    Args:
        swh_objects: an iterable of dict describing archived objects
        snapshot_context: optional dict parameter describing the snapshot in
            which the objects have been found
        extra_context: optional dict filled with extra contextual info about
            the objects

    Returns:
        a list of dict containing SWHIDs info

    """
    swhids_info = []
    for swh_object in swh_objects:
        if not swh_object["object_id"]:
            swhids_info.append(
                SWHIDInfo(
                    object_type=swh_object["object_type"],
                    object_id="",
                    swhid="",
                    swhid_url="",
                    context={},
                    swhid_with_context=None,
                    swhid_with_context_url=None,
                )
            )
            continue
        object_type = swh_object["object_type"]
        object_id = swh_object["object_id"]
        swhid_context: SWHIDContext = {}
        if snapshot_context:
            if snapshot_context["origin_info"] is not None:
                swhid_context["origin"] = quote(
                    snapshot_context["origin_info"]["url"], safe="/?:@&"
                )
            if object_type != SNAPSHOT:
                swhid_context["visit"] = gen_swhid(
                    SNAPSHOT, snapshot_context["snapshot_id"]
                )
            if object_type in (CONTENT, DIRECTORY):
                if snapshot_context["release_id"] is not None:
                    swhid_context["anchor"] = gen_swhid(
                        RELEASE, snapshot_context["release_id"]
                    )
                elif snapshot_context["revision_id"] is not None:
                    swhid_context["anchor"] = gen_swhid(
                        REVISION, snapshot_context["revision_id"]
                    )

        if object_type in (CONTENT, DIRECTORY):
            if (
                extra_context
                and "revision" in extra_context
                and extra_context["revision"]
                and "anchor" not in swhid_context
            ):
                swhid_context["anchor"] = gen_swhid(REVISION, extra_context["revision"])
            elif (
                extra_context
                and "root_directory" in extra_context
                and extra_context["root_directory"]
                and "anchor" not in swhid_context
                and (
                    object_type != DIRECTORY
                    or extra_context["root_directory"] != object_id
                )
            ):
                swhid_context["anchor"] = gen_swhid(
                    DIRECTORY, extra_context["root_directory"]
                )
            path = None
            if extra_context and "path" in extra_context:
                path = extra_context["path"] or "/"
                if "filename" in extra_context and object_type == CONTENT:
                    path += extra_context["filename"]
                if object_type == DIRECTORY and path == "/":
                    path = None
            if path:
                swhid_context["path"] = quote(path, safe="/?:@&")

        swhid = gen_swhid(object_type, object_id)
        swhid_url = reverse("browse-swhid", url_args={"swhid": swhid})

        swhid_with_context = None
        swhid_with_context_url = None
        if swhid_context:
            swhid_with_context = gen_swhid(
                object_type, object_id, metadata=swhid_context
            )
            swhid_with_context_url = reverse(
                "browse-swhid", url_args={"swhid": swhid_with_context}
            )

        swhids_info.append(
            SWHIDInfo(
                object_type=object_type,
                object_id=object_id,
                swhid=swhid,
                swhid_url=swhid_url,
                context=swhid_context,
                swhid_with_context=swhid_with_context,
                swhid_with_context_url=swhid_with_context_url,
            )
        )
    return swhids_info
