# Copyright (C) 2015-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from collections import defaultdict
import datetime
import itertools
import os
import re
from typing import Any, Dict, Iterable, Iterator, List, Optional, Set, Tuple, Union
from urllib.parse import urlparse

from swh.model import hashutil
from swh.model.model import Revision
from swh.model.swhids import CoreSWHID, ObjectType
from swh.storage.algos import diff, revisions_walker
from swh.storage.algos.origin import origin_get_latest_visit_status
from swh.storage.algos.snapshot import snapshot_get_latest, snapshot_resolve_alias
from swh.storage.interface import OriginVisitWithStatuses
from swh.vault.exc import NotFoundExc as VaultNotFoundExc
from swh.web import config
from swh.web.utils import converters, query
from swh.web.utils.exc import NotFoundExc
from swh.web.utils.typing import (
    OriginInfo,
    OriginMetadataInfo,
    OriginVisitInfo,
    PagedResult,
)

search = config.search()
storage = config.storage()
vault = config.vault()
idx_storage = config.indexer_storage()
counters = config.counters()


MAX_LIMIT = 1000  # Top limit the users can ask for


def _first_element(lst):
    """Returns the first element in the provided list or None
    if it is empty or None"""
    return next(iter(lst or []), None)


def lookup_multiple_hashes(hashes):
    """Lookup the passed hashes in a single DB connection, using batch
    processing.

    Args:
        An array of {filename: X, sha1: Y}, string X, hex sha1 string Y.
    Returns:
        The same array with elements updated with elem['found'] = true if
        the hash is present in storage, elem['found'] = false if not.

    """
    hashlist = [hashutil.hash_to_bytes(elem["sha1"]) for elem in hashes]
    content_missing = storage.content_missing_per_sha1(hashlist)
    missing = [hashutil.hash_to_hex(x) for x in content_missing]
    for x in hashes:
        x.update({"found": True})
    for h in hashes:
        if h["sha1"] in missing:
            h["found"] = False
    return hashes


def lookup_hash(q: str) -> Dict[str, Any]:
    """Check if the storage contains a given content checksum and return it if found.

    Args:
        q: query string of the form <hash_algo:hash>

    Returns:
        Dict with key found containing the hash info if the
    hash is present, None if not.

    """
    algo, hash_ = query.parse_hash(q)
    found = _first_element(storage.content_find({algo: hash_}))
    if found:
        content = converters.from_content(found.to_dict())
    else:
        content = None
    return {"found": content, "algo": algo}


def search_hash(q: str) -> Dict[str, bool]:
    """Search storage for a given content checksum.

    Args:
        q: query string of the form <hash_algo:hash>

    Returns:
        Dict with key found to True or False, according to
        whether the checksum is present or not

    """
    algo, hash_ = query.parse_hash(q)
    found = _first_element(storage.content_find({algo: hash_}))
    return {"found": found is not None}


def _lookup_content_sha1(q: str) -> Optional[bytes]:
    """Given a possible input, query for the content's sha1.

    Args:
        q: query string of the form <hash_algo:hash>

    Returns:
        binary sha1 if found or None

    """
    algo, hash_ = query.parse_hash(q)
    if algo != "sha1":
        hashes = _first_element(storage.content_find({algo: hash_}))
        if not hashes:
            return None
        return hashes.sha1
    return hash_


def lookup_content_filetype(q):
    """Return filetype information from a specified content.

    Args:
        q: query string of the form <hash_algo:hash>

    Yields:
        filetype information (dict) list if the content is found.

    """
    sha1 = _lookup_content_sha1(q)
    if not sha1:
        return None
    filetype = _first_element(list(idx_storage.content_mimetype_get([sha1])))
    if not filetype:
        return None
    return converters.from_filetype(filetype.to_dict())


def lookup_content_language(q):
    """Always returns None.

    This used to return language information from a specified content,
    but this is currently disabled.

    Args:
        q: query string of the form <hash_algo:hash>

    Yields:
        language information (dict) list if the content is found.

    """
    return None


def lookup_content_license(q):
    """Return license information from a specified content.

    Args:
        q: query string of the form <hash_algo:hash>

    Yields:
        license information (dict) list if the content is found.

    """
    sha1 = _lookup_content_sha1(q)
    if not sha1:
        return None
    licenses = list(idx_storage.content_fossology_license_get([sha1]))

    if not licenses:
        return None
    license_dicts = [license.to_dict() for license in licenses]
    for license_dict in license_dicts:
        del license_dict["id"]
    lic = {
        "id": sha1,
        "facts": license_dicts,
    }
    return converters.from_swh(lic, hashess={"id"})


def lookup_origin(origin: OriginInfo, lookup_similar_urls: bool = True) -> OriginInfo:
    """Return information about the origin matching dict origin.

    Args:
        origin: origin's dict with 'url' key
        lookup_similar_urls: if :const:`True`, lookup origin with and
            without trailing slash in its URL

    Returns:
        origin information as dict.

    """
    origin_urls = [origin["url"]]
    if origin["url"] and lookup_similar_urls:
        # handle case when user provided an origin url with a trailing
        # slash while the url in storage does not have it (e.g. GitHub)
        if origin["url"].endswith("/"):
            origin_urls.append(origin["url"][:-1])
        # handle case when user provided an origin url without a trailing
        # slash while the url in storage have it (e.g. Debian source package)
        else:
            origin_urls.append(f"{origin['url']}/")
        try:
            # handle case where the "://" character sequence was mangled into ":/"
            parsed_url = urlparse(origin["url"])
            if (
                parsed_url.scheme
                and not parsed_url.netloc
                and origin["url"].startswith(f"{parsed_url.scheme}:/")
                and not origin["url"].startswith(f"{parsed_url.scheme}://")
            ):
                origin_urls.append(
                    origin["url"].replace(
                        f"{parsed_url.scheme}:/", f"{parsed_url.scheme}://"
                    )
                )
        except Exception:
            pass
    origins = [o for o in storage.origin_get(origin_urls) if o is not None]
    if not origins:
        msg = "Origin with url %s not found!" % origin["url"]
        raise NotFoundExc(msg)
    return converters.from_origin(origins[0].to_dict())


def lookup_origins(
    page_token: Optional[str], limit: int = 100
) -> PagedResult[OriginInfo]:
    """Get list of archived software origins in a paginated way.

    Origins are sorted by id before returning them

    Args:
        origin_from (int): The minimum id of the origins to return
        origin_count (int): The maximum number of origins to return

    Returns:
        Page of OriginInfo

    """
    page = storage.origin_list(page_token=page_token, limit=limit)
    return PagedResult(
        [converters.from_origin(o.to_dict()) for o in page.results],
        next_page_token=page.next_page_token,
    )


def lookup_origin_snapshots(origin: OriginInfo) -> List[str]:
    """Return ids of the snapshots of an origin.

    Args:
        origin: origin's dict with 'url' key

    Returns:
        List of unique snapshot identifiers in hexadecimal format resulting
        from the visits of the origin.
    """
    return [
        snapshot.hex() for snapshot in storage.origin_snapshot_get_all(origin["url"])
    ]


def search_origin(
    url_pattern: str,
    use_ql: bool = False,
    limit: int = 50,
    with_visit: bool = False,
    visit_types: Optional[List[str]] = None,
    page_token: Optional[str] = None,
) -> Tuple[List[OriginInfo], Optional[str]]:
    """Search for origins whose urls contain a provided string pattern
    or match a provided regular expression.

    Args:
        url_pattern: the string pattern to search for in origin urls
        use_ql: whether to use swh search query language or not
        limit: the maximum number of found origins to return
        with_visit: Whether origins with no visit are to be filtered out
        visit_types: Only origins having any of the provided visit types
            (e.g. git, svn, pypi) will be returned
        page_token: opaque string used to get the next results of a search

    Returns:
        list of origin information as dict.

    """
    if page_token:
        assert isinstance(page_token, str)

    if search:
        if use_ql:
            page_result = search.origin_search(
                query=url_pattern,
                page_token=page_token,
                with_visit=with_visit,
                visit_types=visit_types,
                limit=limit,
            )
        else:
            page_result = search.origin_search(
                url_pattern=url_pattern,
                page_token=page_token,
                with_visit=with_visit,
                visit_types=visit_types,
                limit=limit,
            )
        origins = [converters.from_origin(ori_dict) for ori_dict in page_result.results]
    else:
        # Fallback to swh-storage if swh-search is not configured
        search_words = [re.escape(word) for word in url_pattern.split()]
        if len(search_words) >= 7:
            url_pattern = ".*".join(search_words)
        else:
            pattern_parts = []
            for permut in itertools.permutations(search_words):
                pattern_parts.append(".*".join(permut))
            url_pattern = "|".join(pattern_parts)

        page_result = storage.origin_search(
            url_pattern,
            page_token=page_token,
            with_visit=with_visit,
            limit=limit,
            visit_types=visit_types,
            regexp=True,
        )
        origins = [converters.from_origin(ori.to_dict()) for ori in page_result.results]

    return (origins, page_result.next_page_token)


def search_origin_metadata(
    fulltext: str, limit: int = 50
) -> Iterable[OriginMetadataInfo]:
    """Search for origins whose metadata match a provided string pattern.

    Args:
        fulltext: the string pattern to search for in origin metadata
        limit: the maximum number of found origins to return

    Returns:
        Iterable of origin metadata information for existing origins

    """
    results = []
    if (
        search
        and config.get_config()["search_config"]["metadata_backend"] == "swh-search"
    ):
        page_result = search.origin_search(
            metadata_pattern=fulltext,
            limit=limit,
        )
        matches = idx_storage.origin_intrinsic_metadata_get(
            [r["url"] for r in page_result.results]
        )
    else:
        matches = idx_storage.origin_intrinsic_metadata_search_fulltext(
            conjunction=[fulltext], limit=limit
        )

    matches = [match.to_dict() for match in matches]
    origins = storage.origin_get([match["id"] for match in matches])
    for origin, match in zip(origins, matches):
        if not origin:
            continue
        for field in ("from_directory", "from_revision"):
            # from_directory when using swh.indexer >= 2.0.0, from_revision otherwise
            if field in match:
                match[field] = hashutil.hash_to_hex(match[field])
        del match["id"]
        results.append(OriginMetadataInfo(url=origin.url, metadata=match))

    return results


def lookup_origin_intrinsic_metadata(origin_url: str) -> Dict[str, Any]:
    """Return intrinsic metadata for origin whose origin matches given
    origin.

    Args:
        origin_url: origin url

    Raises:
        NotFoundExc when the origin is not found

    Returns:
        origin metadata.

    """
    origins = [origin_url]
    origin_info = storage.origin_get(origins)[0]
    if not origin_info:
        raise NotFoundExc(f"Origin with url {origin_url} not found!")

    match = _first_element(idx_storage.origin_intrinsic_metadata_get(origins))
    result = {}
    if match:
        result = match.metadata
    return result


def _to_sha1_bin(sha1_hex):
    _, sha1_git_bin = query.parse_hash_with_algorithms_or_throws(
        sha1_hex, ["sha1"], "Only sha1_git is supported."  # HACK: sha1_git really
    )
    return sha1_git_bin


def _check_directory_exists(sha1_git, sha1_git_bin):
    if len(list(storage.directory_missing([sha1_git_bin]))):
        raise NotFoundExc("Directory with sha1_git %s not found" % sha1_git)


def lookup_directory(sha1_git):
    """Return information about the directory with id sha1_git.

    Args:
        sha1_git as string

    Returns:
        directory information as dict.

    """
    empty_dir_sha1 = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

    if sha1_git == empty_dir_sha1:
        return []

    sha1_git_bin = _to_sha1_bin(sha1_git)

    _check_directory_exists(sha1_git, sha1_git_bin)

    directory_entries = storage.directory_ls(sha1_git_bin)
    return map(converters.from_directory_entry, directory_entries)


def lookup_directory_with_path(sha1_git: str, path: str) -> Dict[str, Any]:
    """Return directory information for entry with specified path w.r.t.
    root directory pointed by sha1_git

    Args:
        sha1_git: sha1_git corresponding to the directory to which we
            append paths to (hopefully) find the entry
        path: the relative path to the entry starting from the root
            directory pointed by sha1_git

    Returns:
        Directory entry information as dict.

    Raises:
        NotFoundExc if the directory entry is not found
    """
    sha1_git_bin = _to_sha1_bin(sha1_git)

    _check_directory_exists(sha1_git, sha1_git_bin)

    paths = path.strip(os.path.sep).split(os.path.sep)
    queried_dir = storage.directory_entry_get_by_path(
        sha1_git_bin, [p.encode("utf-8") for p in paths]
    )

    if not queried_dir:
        raise NotFoundExc(
            f"Directory entry with path {path} from root directory {sha1_git} not found"
        )

    return converters.from_directory_entry(queried_dir)


def lookup_release(release_sha1_git: str) -> Dict[str, Any]:
    """Return information about the release with sha1 release_sha1_git.

    Args:
        release_sha1_git: The release's sha1 as hexadecimal

    Returns:
        Release information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    sha1_git_bin = _to_sha1_bin(release_sha1_git)
    release = _first_element(storage.release_get([sha1_git_bin]))
    if not release:
        raise NotFoundExc(f"Release with sha1_git {release_sha1_git} not found.")
    return converters.from_release(release)


def lookup_release_multiple(sha1_git_list) -> Iterator[Optional[Dict[str, Any]]]:
    """Return information about the releases identified with
    their sha1_git identifiers.

    Args:
        sha1_git_list: A list of release sha1_git identifiers

    Returns:
        Iterator of Release metadata information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    sha1_bin_list = [_to_sha1_bin(sha1_git) for sha1_git in sha1_git_list]
    releases = storage.release_get(sha1_bin_list)
    for r in releases:
        if r is not None:
            yield converters.from_release(r)
        else:
            yield None


def lookup_revision(rev_sha1_git) -> Dict[str, Any]:
    """Return information about the revision with sha1 revision_sha1_git.

    Args:
        revision_sha1_git: The revision's sha1 as hexadecimal

    Returns:
        Revision information as dict.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.
        NotFoundExc if there is no revision with the provided sha1_git.

    """
    sha1_git_bin = _to_sha1_bin(rev_sha1_git)
    revision = storage.revision_get([sha1_git_bin])[0]
    if not revision:
        raise NotFoundExc(f"Revision with sha1_git {rev_sha1_git} not found.")
    return converters.from_revision(revision)


def lookup_revision_multiple(sha1_git_list) -> Iterator[Optional[Dict[str, Any]]]:
    """Return information about the revisions identified with
    their sha1_git identifiers.

    Args:
        sha1_git_list: A list of revision sha1_git identifiers

    Yields:
        revision information as dict if the revision exists, None otherwise.

    Raises:
        ValueError if the identifier provided is not of sha1 nature.

    """
    sha1_bin_list = [_to_sha1_bin(sha1_git) for sha1_git in sha1_git_list]
    revisions = storage.revision_get(sha1_bin_list)
    for revision in revisions:
        if revision is not None:
            yield converters.from_revision(revision)
        else:
            yield None


def lookup_revision_message(rev_sha1_git) -> Dict[str, bytes]:
    """Return the raw message of the revision with sha1 revision_sha1_git.

    Args:
        revision_sha1_git: The revision's sha1 as hexadecimal

    Returns:
        Decoded revision message as dict {'message': <the_message>}

    Raises:
        ValueError if the identifier provided is not of sha1 nature.
        NotFoundExc if the revision is not found, or if it has no message

    """
    sha1_git_bin = _to_sha1_bin(rev_sha1_git)
    revision = storage.revision_get([sha1_git_bin])[0]
    if not revision:
        raise NotFoundExc(f"Revision with sha1_git {rev_sha1_git} not found.")
    if not revision.message:
        raise NotFoundExc(f"No message for revision with sha1_git {rev_sha1_git}.")
    return {"message": revision.message}


def _lookup_revision_id_by(origin, branch_name, timestamp):
    def _get_snapshot_branch(snapshot, branch_name):
        snapshot = lookup_snapshot(
            visit["snapshot"],
            branches_from=branch_name,
            branches_count=10,
            branch_name_exclude_prefix=None,
        )
        branch = None
        if branch_name in snapshot["branches"]:
            branch = snapshot["branches"][branch_name]
        return branch

    if isinstance(origin, int):
        origin = {"id": origin}
    elif isinstance(origin, str):
        origin = {"url": origin}
    else:
        raise TypeError('"origin" must be an int or a string.')

    from swh.web.utils.origin_visits import get_origin_visit

    visit = get_origin_visit(origin, visit_ts=timestamp)
    branch = _get_snapshot_branch(visit["snapshot"], branch_name)
    rev_id = None
    if branch and branch["target_type"] == "revision":
        rev_id = branch["target"]
    elif branch and branch["target_type"] == "alias":
        branch = _get_snapshot_branch(visit["snapshot"], branch["target"])
        if branch and branch["target_type"] == "revision":
            rev_id = branch["target"]

    if not rev_id:
        raise NotFoundExc(
            "Revision for origin %s and branch %s not found."
            % (origin.get("url"), branch_name)
        )

    return rev_id


def lookup_revision_by(origin, branch_name="HEAD", timestamp=None):
    """Lookup revision by origin, snapshot branch name and visit timestamp.

    If branch_name is not provided, lookup using 'HEAD' as default.
    If timestamp is not provided, use the most recent.

    Args:
        origin (Union[int,str]): origin of the revision
        branch_name (str): snapshot branch name
        timestamp (str/int): origin visit time frame

    Returns:
        dict: The revision matching the criterions

    Raises:
        NotFoundExc if no revision corresponds to the criterion

    """
    rev_id = _lookup_revision_id_by(origin, branch_name, timestamp)
    return lookup_revision(rev_id)


def lookup_revision_log(rev_sha1_git, limit):
    """Lookup revision log by revision id.

    Args:
        rev_sha1_git (str): The revision's sha1 as hexadecimal
        limit (int): the maximum number of revisions returned

    Returns:
        list: Revision log as list of revision dicts

    Raises:
        ValueError: if the identifier provided is not of sha1 nature.
        swh.web.utils.exc.NotFoundExc: if there is no revision with the
            provided sha1_git.

    """
    lookup_revision(rev_sha1_git)
    sha1_git_bin = _to_sha1_bin(rev_sha1_git)
    revision_entries = storage.revision_log([sha1_git_bin], limit=limit)
    return map(converters.from_revision, revision_entries)


def lookup_revision_log_by(origin, branch_name, timestamp, limit):
    """Lookup revision by origin, snapshot branch name and visit timestamp.

    Args:
        origin (Union[int,str]): origin of the revision
        branch_name (str): snapshot branch
        timestamp (str/int): origin visit time frame
        limit (int): the maximum number of revisions returned

    Returns:
        list: Revision log as list of revision dicts

    Raises:
        swh.web.utils.exc.NotFoundExc: if no revision corresponds to the
            criterion

    """
    rev_id = _lookup_revision_id_by(origin, branch_name, timestamp)
    return lookup_revision_log(rev_id, limit)


def lookup_revision_with_context_by(
    origin, branch_name, timestamp, sha1_git, limit=100
):
    """Return information about revision sha1_git, limited to the
    sub-graph of all transitive parents of sha1_git_root.
    sha1_git_root being resolved through the lookup of a revision by origin,
    branch_name and ts.

    In other words, sha1_git is an ancestor of sha1_git_root.

    Args:
        - origin: origin of the revision.
        - branch_name: revision's branch.
        - timestamp: revision's time frame.
        - sha1_git: one of sha1_git_root's ancestors.
        - limit: limit the lookup to 100 revisions back.

    Returns:
        Pair of (root_revision, revision).
        Information on sha1_git if it is an ancestor of sha1_git_root
        including children leading to sha1_git_root

    Raises:
        - BadInputExc in case of unknown algo_hash or bad hash.
        - NotFoundExc if either revision is not found or if sha1_git is not an
        ancestor of sha1_git_root.

    """
    rev_root_id = _lookup_revision_id_by(origin, branch_name, timestamp)

    rev_root_id_bin = hashutil.hash_to_bytes(rev_root_id)

    rev_root = storage.revision_get([rev_root_id_bin])[0]
    return (
        converters.from_revision(rev_root) if rev_root else None,
        lookup_revision_with_context(rev_root, sha1_git, limit),
    )


def lookup_revision_with_context(
    sha1_git_root: Union[str, Dict[str, Any], Revision], sha1_git: str, limit: int = 100
) -> Dict[str, Any]:
    """Return information about revision sha1_git, limited to the
    sub-graph of all transitive parents of sha1_git_root.

    In other words, sha1_git is an ancestor of sha1_git_root.

    Args:
        sha1_git_root: latest revision. The type is either a sha1 (as an hex
        string) or a non converted dict.
        sha1_git: one of sha1_git_root's ancestors
        limit: limit the lookup to 100 revisions back

    Returns:
        Information on sha1_git if it is an ancestor of sha1_git_root
        including children leading to sha1_git_root

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash
        NotFoundExc if either revision is not found or if sha1_git is not an
        ancestor of sha1_git_root

    """
    sha1_git_bin = _to_sha1_bin(sha1_git)

    revision = storage.revision_get([sha1_git_bin])[0]
    if not revision:
        raise NotFoundExc(f"Revision {sha1_git} not found")

    if isinstance(sha1_git_root, str):
        sha1_git_root_bin = _to_sha1_bin(sha1_git_root)

        revision_root = storage.revision_get([sha1_git_root_bin])[0]
        if not revision_root:
            raise NotFoundExc(f"Revision root {sha1_git_root} not found")
    elif isinstance(sha1_git_root, Revision):
        sha1_git_root_bin = sha1_git_root.id
    else:
        sha1_git_root_bin = sha1_git_root["id"]

    revision_log = storage.revision_log([sha1_git_root_bin], limit=limit)

    parents: Dict[str, List[str]] = {}
    children = defaultdict(list)

    for rev in revision_log:
        rev_id = rev["id"]
        parents[rev_id] = []
        for parent_id in rev["parents"]:
            parents[rev_id].append(parent_id)
            children[parent_id].append(rev_id)

    if revision.id not in parents:
        raise NotFoundExc(f"Revision {sha1_git} is not an ancestor of {sha1_git_root}")

    revision_d = revision.to_dict()
    revision_d["children"] = children[revision.id]
    return converters.from_revision(revision_d)


def lookup_directory_with_revision(sha1_git, dir_path=None, with_data=False):
    """Return information on directory pointed by revision with sha1_git.
    If dir_path is not provided, display top level directory.
    Otherwise, display the directory pointed by dir_path (if it exists).

    Args:
        sha1_git: revision's hash.
        dir_path: optional directory pointed to by that revision.
        with_data: boolean that indicates to retrieve the raw data if the path
        resolves to a content. Default to False (for the api)

    Returns:
        Information on the directory pointed to by that revision.

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash.
        NotFoundExc either if the revision is not found or the path referenced
        does not exist.
        NotImplementedError in case of dir_path exists but do not reference a
        type 'dir' or 'file'.

    """
    sha1_git_bin = _to_sha1_bin(sha1_git)
    revision = storage.revision_get([sha1_git_bin])[0]
    if not revision:
        raise NotFoundExc(f"Revision {sha1_git} not found")
    dir_sha1_git_bin = revision.directory
    if dir_path:
        paths = dir_path.strip(os.path.sep).split(os.path.sep)
        entity = storage.directory_entry_get_by_path(
            dir_sha1_git_bin, list(map(lambda p: p.encode("utf-8"), paths))
        )
        if not entity:
            raise NotFoundExc(
                "Directory or File '%s' pointed to by revision %s not found"
                % (dir_path, sha1_git)
            )
    else:
        entity = {"type": "dir", "target": dir_sha1_git_bin}
    if entity["type"] == "dir":
        directory_entries = storage.directory_ls(entity["target"]) or []
        return {
            "type": "dir",
            "path": "." if not dir_path else dir_path,
            "revision": sha1_git,
            "content": list(map(converters.from_directory_entry, directory_entries)),
        }
    elif entity["type"] == "file":  # content
        content = _first_element(storage.content_find({"sha1_git": entity["target"]}))
        if not content:
            raise NotFoundExc(f"Content not found for revision {sha1_git}")
        content_d = content.to_dict()
        if with_data:
            data = storage.content_get_data(content.sha1)
            if data:
                content_d["data"] = data
        return {
            "type": "file",
            "path": "." if not dir_path else dir_path,
            "revision": sha1_git,
            "content": converters.from_content(content_d),
        }
    elif entity["type"] == "rev":  # revision
        revision = storage.revision_get([entity["target"]])[0]
        return {
            "type": "rev",
            "path": "." if not dir_path else dir_path,
            "revision": sha1_git,
            "content": converters.from_revision(revision) if revision else None,
        }
    else:
        raise NotImplementedError("Entity of type %s not implemented." % entity["type"])


def lookup_content(q: str) -> Dict[str, Any]:
    """Lookup the content designed by q.

    Args:
        q: The release's sha1 as hexadecimal

    Raises:
        NotFoundExc if the requested content is not found

    """
    algo, hash_ = query.parse_hash(q)
    c = _first_element(storage.content_find({algo: hash_}))
    if not c:
        hhex = hashutil.hash_to_hex(hash_)
        raise NotFoundExc(f"Content with {algo} checksum equals to {hhex} not found!")
    return converters.from_content(c.to_dict())


def lookup_content_raw(q: str) -> Dict[str, Any]:
    """Lookup the content defined by q.

    Args:
        q: query string of the form <hash_algo:hash>

    Returns:
        dict with 'sha1' and 'data' keys.
        data representing its raw data decoded.

    Raises:
        NotFoundExc if the requested content is not found or
        if the content bytes are not available in the storage

    """
    c = lookup_content(q)
    content_sha1_bytes = hashutil.hash_to_bytes(c["checksums"]["sha1"])
    content_data = storage.content_get_data(content_sha1_bytes)
    if content_data is None:
        algo, hash_ = query.parse_hash(q)
        raise NotFoundExc(
            f"Bytes of content with {algo} checksum equals "
            f"to {hashutil.hash_to_hex(hash_)} are not available!"
        )
    return converters.from_content({"sha1": content_sha1_bytes, "data": content_data})


def stat_counters():
    """Return the stat counters for Software Heritage

    Returns:
        A dict mapping textual labels to integer values.
    """
    res = {}
    if counters and config.get_config()["counters_backend"] == "swh-counters":
        res = counters.get_counts(
            ["origin", "revision", "content", "directory", "release", "person"]
        )
    else:
        res = storage.stat_counters()
    return res


def _lookup_origin_visits(
    origin_url: str, last_visit: Optional[int] = None, limit: int = 10
) -> Iterator[OriginVisitWithStatuses]:
    """Yields the origin origins' visits.

    Args:
        origin_url: origin to list visits for
        last_visit: last visit to lookup from
        limit: Number of elements max to display

    Yields:
       OriginVisit for that origin

    """
    limit = min(limit, MAX_LIMIT)
    page_token: Optional[str]
    if last_visit is not None:
        page_token = str(last_visit)
    else:
        page_token = None
    visit_page = storage.origin_visit_get_with_statuses(
        origin_url, page_token=page_token, limit=limit
    )
    yield from visit_page.results


def lookup_origin_visits(
    origin: str, last_visit: Optional[int] = None, per_page: int = 10
) -> Iterator[OriginVisitInfo]:
    """Yields the origin origins' visits.

    Args:
        origin: origin to list visits for

    Yields:
       Dictionaries of origin_visit for that origin

    """
    for visit in _lookup_origin_visits(origin, last_visit=last_visit, limit=per_page):
        yield converters.from_origin_visit(visit.statuses[-1].to_dict())


def lookup_origin_visit_latest(
    origin_url: str,
    require_snapshot: bool = False,
    type: Optional[str] = None,
    allowed_statuses: Optional[List[str]] = None,
    lookup_similar_urls: bool = True,
) -> Optional[OriginVisitInfo]:
    """Return the origin's latest visit

    Args:
        origin_url: origin to list visits for
        type: Optional visit type to filter on (e.g git, tar, dsc, svn,
            hg, npm, pypi, ...)
        allowed_statuses: list of visit statuses considered
            to find the latest visit. For instance,
            ``allowed_statuses=['full']`` will only consider visits that
            have successfully run to completion.
        require_snapshot: filter out origins without a snapshot
        lookup_similar_urls: if :const:`True`, lookup origin with and
            without trailing slash in its URL

    Returns:
       The origin visit info as dict if found

    """

    # check origin existence in the archive
    origin_url = lookup_origin(
        OriginInfo(url=origin_url), lookup_similar_urls=lookup_similar_urls
    )["url"]

    visit_status = origin_get_latest_visit_status(
        storage,
        origin_url,
        type=type,
        allowed_statuses=allowed_statuses,
        require_snapshot=require_snapshot,
    )
    return (
        converters.from_origin_visit(visit_status.to_dict()) if visit_status else None
    )


def lookup_origin_visit(
    origin_url: str,
    visit_id: int,
    lookup_similar_urls: bool = True,
) -> OriginVisitInfo:
    """Return information about visit visit_id with origin origin.

    Args:
        origin: origin concerned by the visit
        visit_id: the visit identifier to lookup
        lookup_similar_urls: if :const:`True`, lookup origin with and
            without trailing slash in its URL

    Raises:
        NotFoundExc if no origin visit matching the criteria is found

    Returns:
       The dict origin_visit concerned

    """
    # check origin existence in the archive
    origin_url = lookup_origin(
        OriginInfo(url=origin_url), lookup_similar_urls=lookup_similar_urls
    )["url"]

    visit = storage.origin_visit_get_by(origin_url, visit_id)
    visit_status = storage.origin_visit_status_get_latest(origin_url, visit_id)
    if not visit:
        raise NotFoundExc(
            f"Origin {origin_url} or its visit with id {visit_id} not found!"
        )
    return converters.from_origin_visit({**visit_status.to_dict(), "type": visit.type})


def origin_visit_find_by_date(
    origin_url: str, visit_date: datetime.datetime, greater_or_equal: bool = True
) -> Optional[OriginVisitInfo]:
    """Retrieve origin visit status whose date is most recent than the provided visit_date.

    Args:
        origin_url: origin concerned by the visit
        visit_date: provided visit date
        greater_or_equal: ensure returned visit has a date greater or equal
            than the one passed as parameter

    Returns:
       The dict origin_visit_status matching the criteria if any.

    """
    visit = storage.origin_visit_find_by_date(origin_url, visit_date)
    if greater_or_equal and visit and visit.date < visit_date:
        # when visit is anterior to the provided date, trying to find another one most
        # recent
        visits = storage.origin_visit_get(
            origin_url,
            page_token=str(visit.visit),
            limit=1,
        ).results
        visit = visits[0] if visits else None
    if not visit:
        return None
    visit_status = storage.origin_visit_status_get_latest(origin_url, visit.visit)
    return converters.from_origin_visit({**visit_status.to_dict(), "type": visit.type})


def lookup_snapshot_sizes(
    snapshot_id: str, branch_name_exclude_prefix: Optional[str] = "refs/pull/"
) -> Dict[str, int]:
    """Count the number of branches in the snapshot with the given id.

    Args:
        snapshot_id (str): sha1 identifier of the snapshot

    Returns:
        dict: A dict whose keys are the target types of branches and
        values their corresponding amount
    """
    snapshot_id_bin = _to_sha1_bin(snapshot_id)
    snapshot_sizes = dict.fromkeys(("alias", "release", "revision"), 0)
    branch_counts = storage.snapshot_count_branches(
        snapshot_id_bin,
        branch_name_exclude_prefix.encode() if branch_name_exclude_prefix else None,
    )
    # remove possible None key returned by snapshot_count_branches
    # when null branches are present in the snapshot
    branch_counts.pop(None, None)
    snapshot_sizes.update(branch_counts)

    snapshot_sizes["branch"] = sum(
        snapshot_sizes.get(target_type, 0)
        for target_type in ("content", "directory", "revision")
    )

    return snapshot_sizes


def lookup_snapshot(
    snapshot_id: str,
    branches_from: str = "",
    branches_count: int = 1000,
    target_types: Optional[List[str]] = None,
    branch_name_include_substring: Optional[str] = None,
    branch_name_exclude_prefix: Optional[str] = "refs/pull/",
) -> Dict[str, Any]:
    """Return information about a snapshot, aka the list of named
    branches found during a specific visit of an origin.

    Args:
        snapshot_id: sha1 identifier of the snapshot
        branches_from: optional parameter used to skip branches
            whose name is lesser than it before returning them
        branches_count: optional parameter used to restrain
            the amount of returned branches
        target_types: optional parameter used to filter the
            target types of branch to return (possible values that can be
            contained in that list are `'content', 'directory',
            'revision', 'release', 'snapshot', 'alias'`)
        branch_name_include_substring: if provided, only return branches whose name
            contains given substring
        branch_name_exclude_prefix: if provided, do not return branches whose name
            starts with given pattern

    Raises:
        NotFoundExc if the given snapshot_id is missing

    Returns:
        A dict filled with the snapshot content.
    """
    snapshot_id_bin = _to_sha1_bin(snapshot_id)
    if storage.snapshot_missing([snapshot_id_bin]):
        raise NotFoundExc(f"Snapshot with id {snapshot_id} not found!")

    partial_branches = storage.snapshot_get_branches(
        snapshot_id_bin,
        branches_from.encode(),
        branches_count,
        target_types,
        branch_name_include_substring.encode()
        if branch_name_include_substring
        else None,
        branch_name_exclude_prefix.encode() if branch_name_exclude_prefix else None,
    )
    return (
        converters.from_partial_branches(partial_branches) if partial_branches else None
    )


def lookup_latest_origin_snapshot(
    origin: str, allowed_statuses: List[str] = None
) -> Optional[Dict[str, Any]]:
    """Return information about the latest snapshot of an origin.

    .. warning:: At most 1000 branches contained in the snapshot
        will be returned for performance reasons.

    Args:
        origin: URL or integer identifier of the origin
        allowed_statuses: list of visit statuses considered
            to find the latest snapshot for the visit. For instance,
            ``allowed_statuses=['full']`` will only consider visits that
            have successfully run to completion.

    Returns:
        A dict filled with the snapshot content.
    """
    snp = snapshot_get_latest(
        storage, origin, allowed_statuses=allowed_statuses, branches_count=1000
    )
    return converters.from_snapshot(snp.to_dict()) if snp is not None else None


def lookup_snapshot_alias(
    snapshot_id: str, alias_name: str
) -> Optional[Dict[str, Any]]:
    """Try to resolve a branch alias in a snapshot.

    Args:
        snapshot_id: hexadecimal representation of a snapshot id
        alias_name: name of the branch alias to resolve

    Returns:
        Target branch information or None if the alias does not exist
        or target a dangling branch.
    """
    resolved_alias = snapshot_resolve_alias(
        storage, _to_sha1_bin(snapshot_id), alias_name.encode()
    )
    return (
        converters.from_swh(resolved_alias.to_dict(), hashess={"target"})
        if resolved_alias is not None
        else None
    )


def lookup_revision_through(revision, limit=100):
    """Retrieve a revision from the criterion stored in revision dictionary.

    Args:
        revision: Dictionary of criterion to lookup the revision with.
        Here are the supported combination of possible values:
        - origin_url, branch_name, ts, sha1_git
        - origin_url, branch_name, ts
        - sha1_git_root, sha1_git
        - sha1_git

    Returns:
        None if the revision is not found or the actual revision.

    """
    if (
        "origin_url" in revision
        and "branch_name" in revision
        and "ts" in revision
        and "sha1_git" in revision
    ):
        return lookup_revision_with_context_by(
            revision["origin_url"],
            revision["branch_name"],
            revision["ts"],
            revision["sha1_git"],
            limit,
        )
    if "origin_url" in revision and "branch_name" in revision and "ts" in revision:
        return lookup_revision_by(
            revision["origin_url"], revision["branch_name"], revision["ts"]
        )
    if "sha1_git_root" in revision and "sha1_git" in revision:
        return lookup_revision_with_context(
            revision["sha1_git_root"], revision["sha1_git"], limit
        )
    if "sha1_git" in revision:
        return lookup_revision(revision["sha1_git"])

    # this should not happen
    raise NotImplementedError("Should not happen!")


def lookup_directory_through_revision(revision, path=None, limit=100, with_data=False):
    """Retrieve the directory information from the revision.

    Args:
        revision: dictionary of criterion representing a revision to lookup
        path: directory's path to lookup.
        limit: optional query parameter to limit the revisions log (default to
            100). For now, note that this limit could impede the transitivity
            conclusion about sha1_git not being an ancestor of.
        with_data: indicate to retrieve the content's raw data if path resolves
            to a content.

    Returns:
        The directory pointing to by the revision criterions at path.

    """
    rev = lookup_revision_through(revision, limit)

    if not rev:
        raise NotFoundExc("Revision with criterion %s not found!" % revision)
    return (rev["id"], lookup_directory_with_revision(rev["id"], path, with_data))


def _vault_request(vault_fn, bundle_type: str, swhid: CoreSWHID, **kwargs):
    try:
        return vault_fn(bundle_type, swhid, **kwargs)
    except VaultNotFoundExc:
        return None


def vault_cook(bundle_type: str, swhid: CoreSWHID, email=None):
    """Cook a vault bundle."""
    return _vault_request(vault.cook, bundle_type, swhid, email=email)


def vault_fetch(bundle_type: str, swhid: CoreSWHID):
    """Fetch a vault bundle."""
    return _vault_request(vault.fetch, bundle_type, swhid)


def vault_progress(bundle_type: str, swhid: CoreSWHID):
    """Get the current progress of a vault bundle."""
    return _vault_request(vault.progress, bundle_type, swhid)


def diff_revision(rev_id):
    """Get the list of file changes (insertion / deletion / modification /
    renaming) for a particular revision.
    """
    rev_sha1_git_bin = _to_sha1_bin(rev_id)

    changes = diff.diff_revision(storage, rev_sha1_git_bin, track_renaming=True)

    for change in changes:
        change["from"] = converters.from_directory_entry(change["from"])
        change["to"] = converters.from_directory_entry(change["to"])
        if change["from_path"]:
            change["from_path"] = change["from_path"].decode("utf-8")
        if change["to_path"]:
            change["to_path"] = change["to_path"].decode("utf-8")

    return changes


class _RevisionsWalkerProxy(object):
    """
    Proxy class wrapping a revisions walker iterator from
    swh-storage and performing needed conversions.
    """

    def __init__(self, rev_walker_type, rev_start, *args, **kwargs):
        rev_start_bin = hashutil.hash_to_bytes(rev_start)
        self.revisions_walker = revisions_walker.get_revisions_walker(
            rev_walker_type, storage, rev_start_bin, *args, **kwargs
        )

    def export_state(self):
        return self.revisions_walker.export_state()

    def __next__(self):
        return converters.from_revision(next(self.revisions_walker))

    def __iter__(self):
        return self


def get_revisions_walker(rev_walker_type, rev_start, *args, **kwargs):
    """
    Utility function to instantiate a revisions walker of a given type,
    see :mod:`swh.storage.algos.revisions_walker`.

    Args:
        rev_walker_type (str): the type of revisions walker to return,
            possible values are: ``committer_date``, ``dfs``, ``dfs_post``,
            ``bfs`` and ``path``
        rev_start (str): hexadecimal representation of a revision identifier
        args (list): position arguments to pass to the revisions walker
            constructor
        kwargs (dict): keyword arguments to pass to the revisions walker
            constructor

    """
    # first check if the provided revision is valid
    lookup_revision(rev_start)
    return _RevisionsWalkerProxy(rev_walker_type, rev_start, *args, **kwargs)


def lookup_object(object_type: ObjectType, object_id: str) -> Dict[str, Any]:
    """
    Utility function for looking up an object in the archive by its type
    and id.

    Args:
        object_type (str): the type of object to lookup, either *content*,
            *directory*, *release*, *revision* or *snapshot*
        object_id (str): the *sha1_git* checksum identifier in hexadecimal
            form of the object to lookup

    Returns:
        Dict[str, Any]: A dictionary describing the object or a list of
        dictionary for the directory object type.

    Raises:
        swh.web.utils.exc.NotFoundExc: if the object could not be found in
            the archive
        BadInputExc: if the object identifier is invalid
    """
    if object_type == ObjectType.CONTENT:
        return lookup_content(f"sha1_git:{object_id}")
    elif object_type == ObjectType.DIRECTORY:
        return {"id": object_id, "content": list(lookup_directory(object_id))}
    elif object_type == ObjectType.RELEASE:
        return lookup_release(object_id)
    elif object_type == ObjectType.REVISION:
        return lookup_revision(object_id)
    elif object_type == ObjectType.SNAPSHOT:
        return lookup_snapshot(object_id)
    else:
        raise ValueError(f"Unexpected object type variant: {object_type}")


def lookup_missing_hashes(grouped_swhids: Dict[ObjectType, List[bytes]]) -> Set[str]:
    """Lookup missing Software Heritage persistent identifier hash, using
    batch processing.

    Args:
        A dictionary with:
        keys: object types
        values: object hashes
    Returns:
        A set(hexadecimal) of the hashes not found in the storage
    """
    missing_hashes = []

    for obj_type, obj_ids in grouped_swhids.items():
        if obj_type == ObjectType.CONTENT:
            missing_hashes.append(storage.content_missing_per_sha1_git(obj_ids))
        elif obj_type == ObjectType.DIRECTORY:
            missing_hashes.append(storage.directory_missing(obj_ids))
        elif obj_type == ObjectType.REVISION:
            missing_hashes.append(storage.revision_missing(obj_ids))
        elif obj_type == ObjectType.RELEASE:
            missing_hashes.append(storage.release_missing(obj_ids))
        elif obj_type == ObjectType.SNAPSHOT:
            missing_hashes.append(storage.snapshot_missing(obj_ids))

    missing = set(
        map(lambda x: hashutil.hash_to_hex(x), itertools.chain(*missing_hashes))
    )

    return missing


def lookup_origins_by_sha1s(sha1s: List[str]) -> Iterator[Optional[OriginInfo]]:
    """Lookup origins from the sha1 hash values of their URLs.

    Args:
        sha1s: list of sha1s hexadecimal representation

    Yields:
        origin information as dict
    """
    sha1s_bytes = [hashutil.hash_to_bytes(sha1) for sha1 in sha1s]
    origins = storage.origin_get_by_sha1(sha1s_bytes)
    for origin in origins:
        yield converters.from_origin(origin)
