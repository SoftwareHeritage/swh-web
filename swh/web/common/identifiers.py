# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Dict, Iterable, List, Optional
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
from swh.web.common.typing import QueryParameters
from swh.web.common.utils import swh_object_icons, reverse


def get_swh_persistent_id(
    object_type: str, object_id: str, scheme_version: int = 1
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
        swh_id = persistent_identifier(object_type, object_id, scheme_version)
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


def get_swh_persistent_ids(swh_objects, snapshot_context=None):
    """
    Returns a list of dict containing info related to persistent
    identifiers of swh objects.

    Args:
        swh_objects (list): a list of dict with the following keys:

            * type: swh object type
              (content/directory/release/revision/snapshot)
            * id: swh object id

        snapshot_context (dict): optional parameter describing the snapshot in
            which the object has been found

    Returns:
        list: a list of dict with the following keys:
            * object_type: the swh object type
              (content/directory/release/revision/snapshot)
            * object_icon: the swh object icon to use in HTML views
            * swh_id: the computed swh object persistent identifier
            * swh_id_url: the url resolving the persistent identifier
            * show_options: boolean indicating if the persistent id options
                must be displayed in persistent ids HTML view
    """
    swh_ids = []
    for swh_object in swh_objects:
        if not swh_object["id"]:
            continue
        swh_id = get_swh_persistent_id(swh_object["type"], swh_object["id"])
        show_options = swh_object["type"] == "content" or (
            snapshot_context and snapshot_context["origin_info"] is not None
        )

        object_icon = swh_object_icons[swh_object["type"]]

        swh_ids.append(
            {
                "object_type": swh_object["type"],
                "object_id": swh_object["id"],
                "object_icon": object_icon,
                "swh_id": swh_id,
                "swh_id_url": reverse("browse-swh-id", url_args={"swh_id": swh_id}),
                "show_options": show_options,
            }
        )
    return swh_ids
