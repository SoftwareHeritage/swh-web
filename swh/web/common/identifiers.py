# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from urllib.parse import quote
from typing import Any, Dict, Iterable, List, Optional
from typing_extensions import TypedDict

from django.http import QueryDict

from swh.model.exceptions import ValidationError
from swh.model.hashutil import hash_to_bytes
from swh.model.identifiers import (
    persistent_identifier,
    parse_persistent_identifier,
    CONTENT,
    DIRECTORY,
    ORIGIN,
    RELEASE,
    REVISION,
    SNAPSHOT,
    PersistentId,
)

from swh.web.common.exc import BadInputExc
from swh.web.common.typing import (
    QueryParameters,
    SnapshotContext,
    SWHObjectInfo,
    SWHIDInfo,
    SWHIDContext,
)
from swh.web.common.utils import reverse


def get_swh_persistent_id(
    object_type: str,
    object_id: str,
    scheme_version: int = 1,
    metadata: SWHIDContext = {},
) -> str:
    """
    Returns the persistent identifier for a swh object based on:

        * the object type
        * the object id
        * the swh identifiers scheme version

    Args:
        object_type: the swh object type
            (content/directory/release/revision/snapshot)
        object_id: the swh object id (hexadecimal representation
            of its hash value)
        scheme_version: the scheme version of the swh
            persistent identifiers

    Returns:
        the swh object persistent identifier

    Raises:
        BadInputExc: if the provided parameters do not enable to
            generate a valid identifier
    """
    try:
        swh_id = persistent_identifier(object_type, object_id, scheme_version, metadata)
    except ValidationError as e:
        raise BadInputExc(
            "Invalid object (%s) for swh persistent id. %s" % (object_id, e)
        )
    else:
        return swh_id


ResolvedPersistentId = TypedDict(
    "ResolvedPersistentId", {"swh_id_parsed": PersistentId, "browse_url": Optional[str]}
)


def resolve_swh_persistent_id(
    swh_id: str, query_params: Optional[QueryParameters] = None
) -> ResolvedPersistentId:
    """
    Try to resolve a Software Heritage persistent id into an url for
    browsing the targeted object.

    Args:
        swh_id: a Software Heritage persistent identifier
        query_params: optional dict filled with
            query parameters to append to the browse url

    Returns:
        a dict with the following keys:

            * **swh_id_parsed**: the parsed identifier
            * **browse_url**: the url for browsing the targeted object
    """
    swh_id_parsed = get_persistent_identifier(swh_id)
    object_type = swh_id_parsed.object_type
    object_id = swh_id_parsed.object_id
    browse_url = None
    query_dict = QueryDict("", mutable=True)
    if query_params and len(query_params) > 0:
        for k in sorted(query_params.keys()):
            query_dict[k] = query_params[k]
    if "origin" in swh_id_parsed.metadata:
        query_dict["origin_url"] = swh_id_parsed.metadata["origin"]
    if object_type == CONTENT:
        query_string = "sha1_git:" + object_id
        fragment = ""
        if "lines" in swh_id_parsed.metadata:
            lines = swh_id_parsed.metadata["lines"].split("-")
            fragment += "#L" + lines[0]
            if len(lines) > 1:
                fragment += "-L" + lines[1]
        browse_url = (
            reverse(
                "browse-content",
                url_args={"query_string": query_string},
                query_params=query_dict,
            )
            + fragment
        )
    elif object_type == DIRECTORY:
        browse_url = reverse(
            "browse-directory",
            url_args={"sha1_git": object_id},
            query_params=query_dict,
        )
    elif object_type == RELEASE:
        browse_url = reverse(
            "browse-release", url_args={"sha1_git": object_id}, query_params=query_dict
        )
    elif object_type == REVISION:
        browse_url = reverse(
            "browse-revision", url_args={"sha1_git": object_id}, query_params=query_dict
        )
    elif object_type == SNAPSHOT:
        browse_url = reverse(
            "browse-snapshot",
            url_args={"snapshot_id": object_id},
            query_params=query_dict,
        )
    elif object_type == ORIGIN:
        raise BadInputExc(
            (
                "Origin PIDs (Persistent Identifiers) are not "
                "publicly resolvable because they are for "
                "internal usage only"
            )
        )

    return {"swh_id_parsed": swh_id_parsed, "browse_url": browse_url}


def get_persistent_identifier(persistent_id: str) -> PersistentId:
    """Check if a persistent identifier is valid.

        Args:
            persistent_id: A string representing a Software Heritage
                persistent identifier.

        Raises:
            BadInputExc: if the provided persistent identifier can
            not be parsed.

        Return:
            A persistent identifier object.
    """
    try:
        pid_object = parse_persistent_identifier(persistent_id)
    except ValidationError as ve:
        raise BadInputExc("Error when parsing identifier: %s" % " ".join(ve.messages))
    else:
        return pid_object


def group_swh_persistent_identifiers(
    persistent_ids: Iterable[PersistentId],
) -> Dict[str, List[bytes]]:
    """
    Groups many Software Heritage persistent identifiers into a
    dictionary depending on their type.

    Args:
        persistent_ids: an iterable of Software Heritage persistent
            identifier objects

    Returns:
        A dictionary with:
            keys: persistent identifier types
            values: persistent identifiers id
    """
    pids_by_type: Dict[str, List[bytes]] = {
        CONTENT: [],
        DIRECTORY: [],
        REVISION: [],
        RELEASE: [],
        SNAPSHOT: [],
    }

    for pid in persistent_ids:
        obj_id = pid.object_id
        obj_type = pid.object_type
        pids_by_type[obj_type].append(hash_to_bytes(obj_id))

    return pids_by_type


def get_swhids_info(
    swh_objects: Iterable[SWHObjectInfo],
    snapshot_context: Optional[SnapshotContext] = None,
    extra_context: Optional[Dict[str, Any]] = None,
) -> List[SWHIDInfo]:
    """
    Returns a list of dict containing info related to persistent
    identifiers of swh objects.

    Args:
        swh_objects: an iterable of dict describing archived objects
        snapshot_context: optional dict parameter describing the snapshot in
            which the objects have been found
        extra_context: optional dict filled with extra contextual info about
            the objects

    Returns:
        a list of dict containing persistent identifiers info

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
                swhid_context["visit"] = get_swh_persistent_id(
                    SNAPSHOT, snapshot_context["snapshot_id"]
                )
            if object_type in (CONTENT, DIRECTORY):
                if snapshot_context["release_id"] is not None:
                    swhid_context["anchor"] = get_swh_persistent_id(
                        RELEASE, snapshot_context["release_id"]
                    )
                elif snapshot_context["revision_id"] is not None:
                    swhid_context["anchor"] = get_swh_persistent_id(
                        REVISION, snapshot_context["revision_id"]
                    )

        if object_type in (CONTENT, DIRECTORY):
            if (
                extra_context
                and "revision" in extra_context
                and extra_context["revision"]
                and "anchor" not in swhid_context
            ):
                swhid_context["anchor"] = get_swh_persistent_id(
                    REVISION, extra_context["revision"]
                )
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
                swhid_context["anchor"] = get_swh_persistent_id(
                    DIRECTORY, extra_context["root_directory"]
                )
            path = None
            if extra_context and "path" in extra_context:
                path = extra_context["path"]
                if "filename" in extra_context and object_type == CONTENT:
                    path += extra_context["filename"]
            if path:
                swhid_context["path"] = quote(path, safe="/?:@&")

        swhid = get_swh_persistent_id(object_type, object_id)
        swhid_url = reverse("browse-swh-id", url_args={"swh_id": swhid})

        swhid_with_context = None
        swhid_with_context_url = None
        if swhid_context:
            swhid_with_context = get_swh_persistent_id(
                object_type, object_id, metadata=swhid_context
            )
            swhid_with_context_url = reverse(
                "browse-swh-id", url_args={"swh_id": swhid_with_context}
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
