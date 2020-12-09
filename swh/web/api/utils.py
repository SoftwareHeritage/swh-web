# Copyright (C) 2015-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict, List, Optional, Tuple

from django.http import HttpRequest

from swh.web.common.query import parse_hash
from swh.web.common.utils import resolve_branch_alias, reverse


def filter_field_keys(data, field_keys):
    """Given an object instance (directory or list), and a csv field keys
    to filter on.

    Return the object instance with filtered keys.

    Note: Returns obj as is if it's an instance of types not in (dictionary,
    list)

    Args:
        - data: one object (dictionary, list...) to filter.
        - field_keys: csv or set of keys to filter the object on

    Returns:
        obj filtered on field_keys

    """
    if isinstance(data, map):
        return map(lambda x: filter_field_keys(x, field_keys), data)
    if isinstance(data, list):
        return [filter_field_keys(x, field_keys) for x in data]
    if isinstance(data, dict):
        return {k: v for (k, v) in data.items() if k in field_keys}
    return data


def person_to_string(person):
    """Map a person (person, committer, tagger, etc...) to a string.

    """
    return "".join([person["name"], " <", person["email"], ">"])


def enrich_object(
    object: Dict[str, str], request: Optional[HttpRequest] = None
) -> Dict[str, str]:
    """Enrich an object (revision, release) with link to the 'target' of
    type 'target_type'.

    Args:
        object: An object with target and target_type keys
        (e.g. release, revision)
        request: Absolute URIs will be generated if provided

    Returns:
        Object enriched with target object url (revision, release, content,
        directory)

    """
    if "target" in object and "target_type" in object:
        if object["target_type"] in ("revision", "release", "directory"):
            object["target_url"] = reverse(
                "api-1-%s" % object["target_type"],
                url_args={"sha1_git": object["target"]},
                request=request,
            )
        elif object["target_type"] == "content":
            object["target_url"] = reverse(
                "api-1-content",
                url_args={"q": "sha1_git:" + object["target"]},
                request=request,
            )
        elif object["target_type"] == "snapshot":
            object["target_url"] = reverse(
                "api-1-snapshot",
                url_args={"snapshot_id": object["target"]},
                request=request,
            )

    return object


enrich_release = enrich_object


def enrich_directory_entry(
    directory: Dict[str, str], request: Optional[HttpRequest] = None
) -> Dict[str, str]:
    """Enrich directory entry with url to target.

    Args:
        directory: dict of data associated to a swh directory entry
        request: Absolute URIs will be generated if provided

    Returns:
        An enriched directory dict filled with additional url
    """
    if "type" in directory:
        target_type = directory["type"]
        target = directory["target"]
        if target_type == "file":
            directory["target_url"] = reverse(
                "api-1-content", url_args={"q": "sha1_git:%s" % target}, request=request
            )
        elif target_type == "dir":
            directory["target_url"] = reverse(
                "api-1-directory", url_args={"sha1_git": target}, request=request
            )
        else:
            directory["target_url"] = reverse(
                "api-1-revision", url_args={"sha1_git": target}, request=request
            )

    return directory


def enrich_metadata_endpoint(
    content_metadata: Dict[str, str], request: Optional[HttpRequest] = None
) -> Dict[str, str]:
    """Enrich content metadata dict with link to the upper metadata endpoint.

    Args:
        content_metadata: dict of data associated to a swh content metadata
        request: Absolute URIs will be generated if provided

    Returns:
        An enriched content metadata dict filled with an additional url
    """
    c = content_metadata
    c["content_url"] = reverse(
        "api-1-content", url_args={"q": "sha1:%s" % c["id"]}, request=request
    )
    return c


def enrich_content(
    content: Dict[str, Any],
    top_url: Optional[bool] = False,
    query_string: Optional[str] = None,
    request: Optional[HttpRequest] = None,
) -> Dict[str, str]:
    """Enrich content with links to:
        - data_url: its raw data
        - filetype_url: its filetype information
        - language_url: its programming language information
        - license_url: its licensing information

    Args:
        content: dict of data associated to a swh content object
        top_url: whether or not to include the content url in
            the enriched data
        query_string: optional query string of type '<algo>:<hash>'
            used when requesting the content, it acts as a hint
            for picking the same hash method when computing
            the url listed above
        request: Absolute URIs will be generated if provided

    Returns:
        An enriched content dict filled with additional urls

    """
    checksums = content
    if "checksums" in content:
        checksums = content["checksums"]
    hash_algo = "sha1"
    if query_string:
        hash_algo = parse_hash(query_string)[0]
    if hash_algo in checksums:
        q = "%s:%s" % (hash_algo, checksums[hash_algo])
        if top_url:
            content["content_url"] = reverse("api-1-content", url_args={"q": q})
        content["data_url"] = reverse(
            "api-1-content-raw", url_args={"q": q}, request=request
        )
        content["filetype_url"] = reverse(
            "api-1-content-filetype", url_args={"q": q}, request=request
        )
        content["language_url"] = reverse(
            "api-1-content-language", url_args={"q": q}, request=request
        )
        content["license_url"] = reverse(
            "api-1-content-license", url_args={"q": q}, request=request
        )

    return content


def enrich_revision(
    revision: Dict[str, Any], request: Optional[HttpRequest] = None
) -> Dict[str, Any]:
    """Enrich revision with links where it makes sense (directory, parents).
    Keep track of the navigation breadcrumbs if they are specified.

    Args:
        revision: the revision as a dict
        request: Absolute URIs will be generated if provided

    Returns:
        An enriched revision dict filled with additional urls
    """

    revision["url"] = reverse(
        "api-1-revision", url_args={"sha1_git": revision["id"]}, request=request
    )
    revision["history_url"] = reverse(
        "api-1-revision-log", url_args={"sha1_git": revision["id"]}, request=request
    )

    if "directory" in revision:
        revision["directory_url"] = reverse(
            "api-1-directory",
            url_args={"sha1_git": revision["directory"]},
            request=request,
        )

    if "parents" in revision:
        parents = []
        for parent in revision["parents"]:
            parents.append(
                {
                    "id": parent,
                    "url": reverse(
                        "api-1-revision", url_args={"sha1_git": parent}, request=request
                    ),
                }
            )

        revision["parents"] = tuple(parents)

    if "children" in revision:
        children = []
        for child in revision["children"]:
            children.append(
                reverse("api-1-revision", url_args={"sha1_git": child}, request=request)
            )
        revision["children_urls"] = children

    if "decoding_failures" in revision and "message" in revision["decoding_failures"]:
        revision["message_url"] = reverse(
            "api-1-revision-raw-message",
            url_args={"sha1_git": revision["id"]},
            request=request,
        )

    return revision


def enrich_snapshot(
    snapshot: Dict[str, Any], request: Optional[HttpRequest] = None
) -> Dict[str, Any]:
    """Enrich snapshot with links to the branch targets

    Args:
        snapshot: the snapshot as a dict
        request: Absolute URIs will be generated if provided

    Returns:
        An enriched snapshot dict filled with additional urls
    """
    if "branches" in snapshot:
        snapshot["branches"] = {
            k: enrich_object(v, request) if v else None
            for k, v in snapshot["branches"].items()
        }
        for k, v in snapshot["branches"].items():
            if v and v["target_type"] == "alias":
                branch = resolve_branch_alias(snapshot, v)
                if branch:
                    branch = enrich_object(branch, request)
                    v["target_url"] = branch["target_url"]
    return snapshot


def enrich_origin(
    origin: Dict[str, Any], request: Optional[HttpRequest] = None
) -> Dict[str, Any]:
    """Enrich origin dict with link to its visits

    Args:
        origin: the origin as a dict
        request: Absolute URIs will be generated if provided

    Returns:
        An enriched origin dict filled with an additional url
    """
    if "url" in origin:
        origin["origin_visits_url"] = reverse(
            "api-1-origin-visits",
            url_args={"origin_url": origin["url"]},
            request=request,
        )

    return origin


def enrich_origin_search_result(
    origin_search_result: Tuple[List[Dict[str, Any]], Optional[str]],
    request: Optional[HttpRequest] = None,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Enrich origin search result with additional links

    Args:
        origin_search_result: tuple returned when searching origins
        request: Absolute URIs will be generated if provided

    Returns:
        An enriched origin search result filled with additional urls
    """
    origins, page_token = origin_search_result
    return [enrich_origin(origin, request=request) for origin in origins], page_token


def enrich_origin_visit(
    origin_visit: Dict[str, Any],
    *,
    with_origin_link: bool,
    with_origin_visit_link: bool,
    request: Optional[HttpRequest] = None,
) -> Dict[str, Any]:
    """Enrich origin visit dict with additional links

    Args:
        origin_visit: the origin visit as a dict
        with_origin_link: whether to add link to origin
        with_origin_visit_link: whether to add link to origin visit
        request: Absolute URIs will be generated if provided

    Returns:
        An enriched origin visit dict filled with additional urls
    """
    ov = origin_visit
    if with_origin_link:
        ov["origin_url"] = reverse(
            "api-1-origin", url_args={"origin_url": ov["origin"]}, request=request
        )
    if with_origin_visit_link:
        ov["origin_visit_url"] = reverse(
            "api-1-origin-visit",
            url_args={"origin_url": ov["origin"], "visit_id": ov["visit"]},
            request=request,
        )
    snapshot = ov["snapshot"]
    if snapshot:
        ov["snapshot_url"] = reverse(
            "api-1-snapshot", url_args={"snapshot_id": snapshot}, request=request
        )
    else:
        ov["snapshot_url"] = None
    return ov
