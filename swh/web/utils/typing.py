# Copyright (C) 2020-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict, TypeVar

from swh.core.api.classes import PagedResult as CorePagedResult
from swh.model.swhids import ObjectType


class OriginInfo(TypedDict):
    url: str
    """URL of the origin"""
    visit_types: List[str]
    """Visit types associated to the origin"""


class OriginMetadataInfo(OriginInfo):
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
    name: str
    """branch name"""
    alias: bool
    """define if the branch is an alias"""
    target_type: str
    """branch target type: content, directory or revision"""
    target: str
    """branch target id"""
    url: Optional[str]
    """optional browse URL (content, directory, ...) scoped to branch"""


class SnapshotReleaseInfo(TypedDict):
    branch_name: str
    """branch name associated to release in snapshot"""
    date: str
    """release date"""
    directory: Optional[str]
    """optional directory associated to the release"""
    id: str
    """release identifier"""
    message: str
    """release message"""
    name: str
    """release name"""
    alias: bool
    """define if the branch is an alias"""
    target: str
    """release target"""
    target_type: str
    """release target_type"""
    url: Optional[str]
    """optional browse URL (content, directory, ...) scoped to release"""


class SnapshotContext(TypedDict):
    branch: Optional[str]
    """optional branch name set when browsing snapshot in that scope"""
    branch_alias: bool
    """indicates if the focused branch is an alias"""
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
    query_params: Dict[str, Optional[str]]
    """common query parameters when browsing snapshot content"""
    release: Optional[str]
    """optional release name set when browsing snapshot in that scope"""
    release_alias: bool
    """indicates if the focused release is an alias"""
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
    browse_url: Optional[str]
    """optional browse URL associated to the snapshot"""


class SWHObjectInfo(TypedDict):
    object_type: ObjectType
    object_id: Optional[str]


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


class ContentMetadata(SWHObjectInfo, SWHObjectInfoMetadata):
    sha1: str
    sha1_git: str
    sha256: str
    blake2s256: str
    content_url: str
    mimetype: str
    encoding: str
    size: int
    language: str
    path: Optional[str]
    filename: Optional[str]
    directory: Optional[str]
    root_directory: Optional[str]
    revision: Optional[str]
    release: Optional[str]
    snapshot: Optional[str]


class DirectoryMetadata(SWHObjectInfo, SWHObjectInfoMetadata):
    directory: Optional[str]
    nb_files: Optional[int]
    nb_dirs: Optional[int]
    sum_file_sizes: Optional[int]
    root_directory: Optional[str]
    path: Optional[str]
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


class SaveOriginRequestInfo(TypedDict, total=False):
    id: int
    """Unique key"""
    save_request_date: str
    """Date of the creation request"""
    visit_type: str
    """Type of the visit"""
    visit_status: Optional[str]
    """Status of the visit"""
    origin_url: str
    """Origin to ingest"""
    save_request_status: str
    """Status of the request"""
    loading_task_id: Optional[int]
    """Identifier of the loading task in the scheduler if scheduled"""
    visit_date: Optional[str]
    """End of the visit if terminated"""
    save_task_status: str
    """Status of the scheduled task"""
    note: Optional[str]
    """Optional note associated to the request, for instance rejection reason"""
    from_webhook: bool
    """Indicates if request was created from a webhook receiver"""
    webhook_origin: Optional[str]
    """Indicates from which forge type a webhook was received"""
    snapshot_swhid: Optional[str]
    """SWHID of snapshot associated to the visit"""
    next_run: Optional[datetime]
    """Date and time from which the request is executed"""


class OriginExistenceCheckInfo(TypedDict):
    origin_url: str
    """Origin to check"""
    exists: bool
    """Does the url exist?"""
    content_length: Optional[int]
    """content length of the artifact"""
    last_modified: Optional[str]
    """Last modification time reported by the server (as iso8601 string)"""


class IntrinsicMetadataFiletype(Enum):
    CODEMETA = "codemeta.json"
    CFF = "citation.cff"


class IntrinsicMetadataFile(TypedDict):
    type: IntrinsicMetadataFiletype
    """Intrinsic metadata file type"""
    name: str
    """Intrinsic metadata file name"""
    id: str
    """Intrinsic metadata file id (sha1 git)"""
    content: dict[str, Any]
    """Intrinsic metadata file content"""
    parsing_error: Optional[str]
    """Error message indicating why metadata could not be parsed"""


class Citation(TypedDict):
    format: str
    """Citation format (currently bibtex)"""
    content: str
    """Formatted citation string content"""
    source_swhid: str
    """Qualified SWHID of citation metadata source file"""
    error: Optional[str]
    """Error message indicating why citation could not be generated"""
