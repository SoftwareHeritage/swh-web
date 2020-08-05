# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.core.api.classes import PagedResult as CorePagedResult

from typing import Any, Dict, List, Optional, TypeVar, Union
from typing_extensions import TypedDict

from django.http import QueryDict

QueryParameters = Union[Dict[str, Any], QueryDict]


class OriginInfo(TypedDict):
    url: str
    """URL of the origin"""


class OriginMetadataInfo(TypedDict):
    url: str
    """URL of the origin"""
    metadata: Dict[str, Any]
    """Origin metadata associated to the origin"""


class OriginVisitInfo(TypedDict):
    date: str
    """date of the visit in iso format"""
    formatted_date: str
    """formatted date of the visit"""
    metadata: Dict[str, Any]
    """metadata associated to the visit"""
    origin: str
    """visited origin URL"""
    snapshot: str
    """snapshot identifier computed during the visit"""
    status: str
    """status of the visit ("ongoing", "full" or "partial") """
    type: str
    """visit type (git, hg, debian, ...)"""
    url: str
    """URL to browse the snapshot"""
    visit: int
    """visit identifier"""


class SnapshotBranchInfo(TypedDict):
    date: Optional[str]
    """"author date of branch heading revision"""
    directory: Optional[str]
    """directory associated to branch heading revision"""
    message: Optional[str]
    """message of branch heading revision"""
    name: Optional[str]
    """branch name"""
    revision: str
    """branch heading revision"""
    url: Optional[str]
    """optional browse URL (content, directory, ...) scoped to branch"""


class SnapshotReleaseInfo(TypedDict):
    branch_name: str
    """branch name associated to release in snapshot"""
    date: str
    """release date"""
    directory: Optional[str]
    """optional directory associatd to the release"""
    id: str
    """release identifier"""
    message: str
    """release message"""
    name: str
    """release name"""
    target: str
    """release target"""
    target_type: str
    """release target_type"""
    url: Optional[str]
    """optional browse URL (content, directory, ...) scoped to release"""


class SnapshotContext(TypedDict):
    branch: Optional[str]
    """optional branch name set when browsing snapshot in that scope"""
    branches: List[SnapshotBranchInfo]
    """list of snapshot branches (possibly truncated)"""
    branches_url: str
    """snapshot branches list browse URL"""
    is_empty: bool
    """indicates if the snapshot is empty"""
    origin_info: Optional[OriginInfo]
    """optional origin info associated to the snapshot"""
    origin_visits_url: Optional[str]
    """optional origin visits URL"""
    query_params: QueryParameters
    """common query parameters when browsing snapshot content"""
    release: Optional[str]
    """optional release name set when browsing snapshot in that scope"""
    release_id: Optional[str]
    """optional release identifier set when browsing snapshot in that scope"""
    releases: List[SnapshotReleaseInfo]
    """list of snapshot releases (possibly truncated)"""
    releases_url: str
    """snapshot releases list browse URL"""
    revision_id: Optional[str]
    """optional revision identifier set when browsing snapshot in that scope"""
    revision_info: Optional[Dict[str, Any]]
    """optional revision info set when browsing snapshot in that scope"""
    root_directory: Optional[str]
    """optional root directory identifier set when browsing snapshot content"""
    snapshot_id: str
    """snapshot identifier"""
    snapshot_sizes: Dict[str, int]
    """snapshot sizes grouped by branch target type"""
    snapshot_swhid: str
    """snapshot SWHID"""
    url_args: Dict[str, Any]
    """common URL arguments when browsing snapshot content"""
    visit_info: Optional[OriginVisitInfo]
    """optional origin visit info associated to the snapshot"""


class SWHObjectInfo(TypedDict):
    object_type: str
    object_id: str


class SWHIDContext(TypedDict, total=False):
    origin: str
    anchor: str
    visit: str
    path: str
    lines: str


class SWHIDInfo(SWHObjectInfo):
    swhid: str
    swhid_url: str
    context: SWHIDContext
    swhid_with_context: Optional[str]
    swhid_with_context_url: Optional[str]


class SWHObjectInfoMetadata(TypedDict, total=False):
    origin_url: Optional[str]
    visit_date: Optional[str]
    visit_type: Optional[str]
    directory_url: Optional[str]
    revision_url: Optional[str]
    release_url: Optional[str]
    snapshot_url: Optional[str]


class ContentMetadata(SWHObjectInfo, SWHObjectInfoMetadata):
    sha1: str
    sha1_git: str
    sha256: str
    blake2s256: str
    content_url: str
    mimetype: str
    encoding: str
    size: str
    language: str
    licenses: str
    path: Optional[str]
    filename: Optional[str]
    directory: Optional[str]
    root_directory: Optional[str]
    revision: Optional[str]
    release: Optional[str]
    snapshot: Optional[str]


class DirectoryMetadata(SWHObjectInfo, SWHObjectInfoMetadata):
    directory: str
    nb_files: int
    nb_dirs: int
    sum_file_sizes: str
    root_directory: Optional[str]
    path: str
    revision: Optional[str]
    revision_found: Optional[bool]
    release: Optional[str]
    snapshot: Optional[str]


class ReleaseMetadata(SWHObjectInfo, SWHObjectInfoMetadata):
    release: str
    author: str
    author_url: str
    date: str
    name: str
    synthetic: bool
    target: str
    target_type: str
    target_url: str
    snapshot: Optional[str]


class RevisionMetadata(SWHObjectInfo, SWHObjectInfoMetadata):
    revision: str
    author: str
    author_url: str
    committer: str
    committer_url: str
    date: str
    committer_date: str
    directory: str
    merge: bool
    metadata: str
    parents: List[str]
    synthetic: bool
    type: str
    snapshot: Optional[str]


TResult = TypeVar("TResult")


PagedResult = CorePagedResult[TResult, str]
