# Copyright (C) 2020-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict, Iterable, List, Mapping, Optional
from urllib.parse import quote, unquote

from typing_extensions import TypedDict

from swh.model.exceptions import ValidationError
from swh.model.hashutil import hash_to_bytes, hash_to_hex
from swh.model.swhids import ObjectType, QualifiedSWHID
from swh.web.utils import archive, reverse
from swh.web.utils.exc import BadInputExc
from swh.web.utils.typing import SnapshotContext, SWHIDContext, SWHIDInfo, SWHObjectInfo


def parse_object_type(object_type: str) -> ObjectType:
    try:
        return ObjectType[object_type.upper()]
    except KeyError:
        valid_types = ", ".join(variant.name.lower() for variant in ObjectType)
        raise BadInputExc(
            f"Invalid swh object type! Valid types are {valid_types}; not {object_type}"
        )


def gen_swhid(
    object_type: ObjectType,
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
        decoded_object_id = hash_to_bytes(object_id)
        obj_swhid = str(
            QualifiedSWHID(
                object_type=object_type,
                object_id=decoded_object_id,
                scheme_version=scheme_version,
                **metadata,
            )
        )
    except (ValidationError, KeyError, ValueError) as e:
        raise BadInputExc("Invalid object (%s) for SWHID. %s" % (object_id, e))
    else:
        return obj_swhid


class ResolvedSWHID(TypedDict):
    """parsed SWHID with context"""

    swhid_parsed: QualifiedSWHID
    """URL to browse object according to SWHID context"""
    browse_url: Optional[str]


def resolve_swhid(
    swhid: str, query_params: Optional[Mapping[str, str]] = None
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
    fragment = ""
    process_lines = object_type == ObjectType.CONTENT

    query_dict: Dict[str, str] = dict(query_params or {})

    if swhid_parsed.origin:
        origin_url = unquote(swhid_parsed.origin)
        origin_url = archive.lookup_origin({"url": origin_url})["url"]
        query_dict["origin_url"] = origin_url

    if swhid_parsed.path and swhid_parsed.path != b"/":
        query_dict["path"] = swhid_parsed.path.decode("utf8", errors="replace")
        if swhid_parsed.anchor:
            directory = b""
            if swhid_parsed.anchor.object_type == ObjectType.DIRECTORY:
                directory = swhid_parsed.anchor.object_id
            elif swhid_parsed.anchor.object_type == ObjectType.REVISION:
                revision = archive.lookup_revision(
                    hash_to_hex(swhid_parsed.anchor.object_id)
                )
                directory = revision["directory"]
            elif swhid_parsed.anchor.object_type == ObjectType.RELEASE:
                release = archive.lookup_release(
                    hash_to_hex(swhid_parsed.anchor.object_id)
                )
                if release["target_type"] == ObjectType.REVISION.name.lower():
                    revision = archive.lookup_revision(release["target"])
                    directory = revision["directory"]
            if object_type == ObjectType.CONTENT:
                if (
                    not swhid_parsed.origin
                    and swhid_parsed.anchor.object_type != ObjectType.REVISION
                ):
                    # when no origin or revision context, content objects need to have
                    # their path prefixed by root directory id for breadcrumbs display
                    query_dict["path"] = hash_to_hex(directory) + query_dict["path"]
                elif query_dict["path"] is not None:
                    # remove leading slash from SWHID content path
                    query_dict["path"] = query_dict["path"].lstrip("/")
            elif object_type == ObjectType.DIRECTORY and query_dict["path"] is not None:
                object_id = directory
                # remove leading and trailing slashes from SWHID directory path
                query_dict["path"] = query_dict["path"].strip("/")

    # snapshot context
    if swhid_parsed.visit:
        if swhid_parsed.visit.object_type != ObjectType.SNAPSHOT:
            raise BadInputExc("Visit must be a snapshot SWHID.")
        query_dict["snapshot"] = hash_to_hex(swhid_parsed.visit.object_id)

        if swhid_parsed.anchor:
            if (
                swhid_parsed.anchor.object_type == ObjectType.REVISION
                and object_type != ObjectType.REVISION
            ):
                query_dict["revision"] = hash_to_hex(swhid_parsed.anchor.object_id)

            elif swhid_parsed.anchor.object_type == ObjectType.RELEASE:
                release = archive.lookup_release(
                    hash_to_hex(swhid_parsed.anchor.object_id)
                )
                if release:
                    query_dict["release"] = release["name"]

    # browsing content or directory without snapshot context
    elif (
        object_type in (ObjectType.CONTENT, ObjectType.DIRECTORY)
        and swhid_parsed.anchor
    ):
        if swhid_parsed.anchor.object_type == ObjectType.REVISION:
            # anchor revision, objects are browsed from its view
            object_type = ObjectType.REVISION
            object_id = swhid_parsed.anchor.object_id
        elif (
            object_type == ObjectType.DIRECTORY
            and swhid_parsed.anchor.object_type == ObjectType.DIRECTORY
        ):
            # a directory is browsed from its root
            object_id = swhid_parsed.anchor.object_id

    if object_type == ObjectType.CONTENT:
        url_args["query_string"] = f"sha1_git:{hash_to_hex(object_id)}"
    elif object_type in (ObjectType.DIRECTORY, ObjectType.RELEASE, ObjectType.REVISION):
        url_args["sha1_git"] = hash_to_hex(object_id)
    elif object_type == ObjectType.SNAPSHOT:
        url_args["snapshot_id"] = hash_to_hex(object_id)

    if swhid_parsed.lines and process_lines:
        lines = swhid_parsed.lines
        fragment += "#L" + str(lines[0])
        if lines[1]:
            fragment += "-L" + str(lines[1])

    if url_args:
        browse_url = (
            reverse(
                f"browse-{object_type.name.lower()}",
                url_args=url_args,
                query_params=query_dict,
            )
            + fragment
        )

    return ResolvedSWHID(swhid_parsed=swhid_parsed, browse_url=browse_url)


def get_swhid(swhid: str) -> QualifiedSWHID:
    """Check if a SWHID is valid and return it parsed.

    Args:
        swhid: a SoftWare Heritage persistent IDentifier.

    Raises:
        BadInputExc: if the provided SWHID can not be parsed.

    Return:
        A parsed SWHID.
    """
    try:
        # ensure core part of SWHID is in lower case to avoid parsing error
        (core, sep, qualifiers) = swhid.partition(";")
        core = core.lower()
        # quoted white spaces might have been automatically unquoted when a SWHID
        # is passed as URL argument so ensure to quote them back
        qualifiers = qualifiers.replace(" ", "%20")
        return QualifiedSWHID.from_string(core + sep + qualifiers)
    except ValidationError as ve:
        raise BadInputExc("Error when parsing identifier: %s" % " ".join(ve.messages))


def group_swhids(
    swhids: Iterable[QualifiedSWHID],
) -> Dict[ObjectType, List[bytes]]:
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
    swhids_by_type: Dict[ObjectType, List[bytes]] = {
        ObjectType.CONTENT: [],
        ObjectType.DIRECTORY: [],
        ObjectType.REVISION: [],
        ObjectType.RELEASE: [],
        ObjectType.SNAPSHOT: [],
    }

    for obj_swhid in swhids:
        obj_id = obj_swhid.object_id
        obj_type = obj_swhid.object_type
        swhids_by_type[obj_type].append(hash_to_bytes(obj_id))

    return swhids_by_type


def get_swhids_info(
    swh_objects: Iterable[SWHObjectInfo],
    snapshot_context: Optional[SnapshotContext] = None,
    extra_context: Optional[Mapping[str, Any]] = None,
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
            if object_type != ObjectType.SNAPSHOT:
                swhid_context["visit"] = gen_swhid(
                    ObjectType.SNAPSHOT, snapshot_context["snapshot_id"]
                )
            if object_type in (ObjectType.CONTENT, ObjectType.DIRECTORY):
                if snapshot_context["release_id"] is not None:
                    swhid_context["anchor"] = gen_swhid(
                        ObjectType.RELEASE, snapshot_context["release_id"]
                    )
                elif snapshot_context["revision_id"] is not None:
                    swhid_context["anchor"] = gen_swhid(
                        ObjectType.REVISION, snapshot_context["revision_id"]
                    )

        if object_type in (ObjectType.CONTENT, ObjectType.DIRECTORY):
            if (
                extra_context
                and "revision" in extra_context
                and extra_context["revision"]
                and "anchor" not in swhid_context
            ):
                swhid_context["anchor"] = gen_swhid(
                    ObjectType.REVISION, extra_context["revision"]
                )
            elif (
                extra_context
                and "root_directory" in extra_context
                and extra_context["root_directory"]
                and "anchor" not in swhid_context
                and (
                    object_type != ObjectType.DIRECTORY
                    or extra_context["root_directory"] != object_id
                )
            ):
                swhid_context["anchor"] = gen_swhid(
                    ObjectType.DIRECTORY, extra_context["root_directory"]
                )
            path = None
            if extra_context and "path" in extra_context:
                path = extra_context["path"] or "/"
                if "filename" in extra_context and object_type == ObjectType.CONTENT:
                    path += extra_context["filename"]
                if object_type == ObjectType.DIRECTORY and path == "/":
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
                "browse-swhid",
                url_args={"swhid": quote(swhid_with_context, safe=":;=/")},
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
