# Copyright (C) 2024-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict, List, Optional

import yaml

from swh.indexer.citation import CitationFormat, codemeta_to_citation
from swh.indexer.citation.exceptions import CitationError
from swh.indexer.metadata_mapping.cff import CffMapping
from swh.model.hashutil import hash_to_bytes
from swh.model.swhids import CoreSWHID, ObjectType, QualifiedSWHID
from swh.web.browse.snapshot_context import get_snapshot_context
from swh.web.utils.archive import (
    lookup_intrinsic_citation_metadata_by_target_swhid,
    lookup_origin_intrinsic_citation_metadata,
    lookup_snapshot,
    lookup_snapshot_alias,
)
from swh.web.utils.identifiers import get_swhids_info
from swh.web.utils.typing import (
    Citation,
    IntrinsicMetadataFile,
    IntrinsicMetadataFiletype,
    SWHObjectInfo,
)


def _get_citation_from_intrinsic_citation_metadata(
    format: CitationFormat,
    raw_intrinsic_metadata: List[IntrinsicMetadataFile],
    swhid: Optional[QualifiedSWHID] = None,
) -> Citation:

    # Should not happen: metadata contains at least one of codemeta.json or citation.cff
    assert len(raw_intrinsic_metadata) > 0, (
        f"lookup_origin_raw_intrinsic_metadata returned neither codemeta.json "
        f"nor citation.cff: {raw_intrinsic_metadata}"
    )

    metadata_file = raw_intrinsic_metadata[0]
    metadata_file_origin_type = metadata_file["type"]
    metadata_file_id = metadata_file["id"]

    source_swhid_params: Dict[str, Any] = {
        "object_type": ObjectType.CONTENT,
        "object_id": hash_to_bytes(metadata_file_id),
    }
    if swhid is not None:
        if swhid.origin:
            source_swhid_params["origin"] = swhid.origin
        if swhid.visit:
            source_swhid_params["visit"] = swhid.visit
        if swhid.anchor:
            source_swhid_params["anchor"] = swhid.anchor
        elif swhid.object_type in (
            ObjectType.DIRECTORY,
            ObjectType.RELEASE,
            ObjectType.REVISION,
        ):
            source_swhid_params["anchor"] = CoreSWHID(
                object_type=swhid.object_type, object_id=swhid.object_id
            )
        elif swhid.object_type == ObjectType.SNAPSHOT:
            source_swhid_params["visit"] = str(
                CoreSWHID(object_type=ObjectType.SNAPSHOT, object_id=swhid.object_id)
            )
            snapshot = lookup_snapshot(
                swhid.object_id.hex(), branches_from="HEAD", branches_count=1
            )
            if "HEAD" in snapshot["branches"]:
                branch_target = snapshot["branches"]["HEAD"]["target"]
                branch_target_type = snapshot["branches"]["HEAD"]["target_type"]
                if branch_target_type == "alias":
                    branch = lookup_snapshot_alias(swhid.object_id.hex(), "HEAD")
                    if branch:
                        branch_target = branch["target"]
                        branch_target_type = branch["target_type"]
                source_swhid_params["anchor"] = str(
                    CoreSWHID(
                        object_type=ObjectType[branch_target_type.upper()],
                        object_id=hash_to_bytes(branch_target),
                    )
                )
        source_swhid_params["path"] = "/" + metadata_file["name"]

    citation = Citation(
        format=format.name.lower(),
        content="",
        source_swhid=str(QualifiedSWHID(**source_swhid_params)),
        error=metadata_file["parsing_error"],
        warning=None,
    )

    metadata_file_content: Dict[str, Any] = {}

    if citation["error"] is None:
        # Convert CFF to CodeMeta
        try:
            if metadata_file_origin_type == IntrinsicMetadataFiletype.CFF.value:
                cff_to_codemeta = CffMapping().translate(
                    raw_content=yaml.dump(
                        metadata_file["content"], default_flow_style=False
                    ).encode("utf-8")
                )
                metadata_file_content = (
                    {} if cff_to_codemeta is None else cff_to_codemeta
                )
            elif metadata_file_origin_type == IntrinsicMetadataFiletype.CODEMETA.value:
                metadata_file_content = metadata_file["content"]
        except Exception as e:
            citation["error"] = str(e)

        # Convert CodeMeta to the requested format
        try:
            citation["content"] = codemeta_to_citation(
                metadata_file_content, format, swhid
            )
        except CitationError as e:
            citation["content"] = codemeta_to_citation(
                metadata_file_content, format, swhid, force_codemeta_context=True
            )
            citation["warning"] = (
                "An error occurred when parsing the codemeta.json file but it was "
                "mitigated by overriding the JSON-LD context to the CodeMeta v3.0 one "
                "and executing parsing again.\n\n"
                "Details about the mitigated error can be found below:\n\n"
            ) + str(e)
        except Exception as e:
            citation["error"] = str(e)

    return citation


def get_citation_from_origin(
    format: CitationFormat,
    origin_url: str,
) -> Citation:
    """
    Get citation in the requested format given a software origin, from found intrinsic citation
    metadata in the repository, i.e. original codemeta.json and citation.cff, for the
    latest visit snapshot main branch root directory.

    Args:
        origin_url: origin url

    Returns:
        the software citation in the requested format

    Raises:
        swh.web.utils.exc.NotFoundExc: when snapshot, branch or directory is missing,
            no metadata could be found or the metadata files could not be decoded
        BadInputExc: when the origin does not allow to find metadata
    """

    metadata = lookup_origin_intrinsic_citation_metadata(origin_url)

    # compute a target SWHID from latest origin snapshot
    target_object_info = None
    target_swhid = None
    snapshot_context = get_snapshot_context(origin_url=origin_url)
    if snapshot_context["revision_id"] is not None:
        target_object_info = SWHObjectInfo(
            object_type=ObjectType.REVISION,
            object_id=snapshot_context["revision_id"],
        )
    elif snapshot_context["release_id"] is not None:
        target_object_info = SWHObjectInfo(
            object_type=ObjectType.RELEASE,
            object_id=snapshot_context["release_id"],
        )
    elif snapshot_context["root_directory"] is not None:
        target_object_info = SWHObjectInfo(
            object_type=ObjectType.DIRECTORY,
            object_id=snapshot_context["root_directory"],
        )
    if target_object_info:
        swhids_info = get_swhids_info(
            [target_object_info], snapshot_context=snapshot_context
        )
        swhid_with_context = swhids_info[0]["swhid_with_context"]
        if swhid_with_context:
            target_swhid = QualifiedSWHID.from_string(swhid_with_context)

    return _get_citation_from_intrinsic_citation_metadata(
        format, metadata, target_swhid
    )


def get_citation_from_swhid(
    format: CitationFormat,
    target_swhid: str,
) -> Citation:
    """
    Get citation in requested format given a SWHID, from found intrinsic citation
    metadata in the repository, i.e. original codemeta.json and citation.cff, for the
    target object.

    Args:
        target_swhid: SWHID which can be qualified or not, if the target object is
            of type Content, it must be qualified with an anchor

    Returns:
        the software citation in the requested format

    Raises:
        swh.web.utils.exc.NotFoundExc: when snapshot, branch or directory is missing,
            no metadata could be found or the metadata files could not be decoded
        BadInputExc: when the origin does not allow to find metadata
    """
    metadata = lookup_intrinsic_citation_metadata_by_target_swhid(target_swhid)
    parsed_swhid = QualifiedSWHID.from_string(target_swhid)
    return _get_citation_from_intrinsic_citation_metadata(
        format, metadata, parsed_swhid
    )
