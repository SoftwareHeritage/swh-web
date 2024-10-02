# Copyright (C) 2015-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import List, Optional

import yaml

from swh.indexer.bibtex import cff_to_bibtex, codemeta_to_bibtex
from swh.model.swhids import QualifiedSWHID
from swh.web.utils.archive import (
    lookup_intrinsic_citation_metadata_by_target_swhid,
    lookup_origin_intrinsic_citation_metadata,
)
from swh.web.utils.typing import IntrinsicMetadataFile, IntrinsicMetadataFiletype


def _get_bibtex_from_raw_intrinsic_metadata(
    raw_intrinsic_metadata: List[IntrinsicMetadataFile],
    swhid: Optional[QualifiedSWHID] = None,
) -> str:
    if len(raw_intrinsic_metadata) > 0:
        bibtex = ""
        metadata_file = raw_intrinsic_metadata[0]
        metadata_file_origin_type = metadata_file["type"]
        if metadata_file_origin_type == IntrinsicMetadataFiletype.CODEMETA.value:
            bibtex = codemeta_to_bibtex(metadata_file["content"], swhid)
        elif metadata_file_origin_type == IntrinsicMetadataFiletype.CFF.value:
            bibtex = cff_to_bibtex(
                yaml.dump(metadata_file["content"], default_flow_style=False), swhid
            )
        return bibtex
    else:
        # Cannot happen: metadata contains at least one of codemeta.json or citation.cff
        assert False, (
            f"lookup_origin_raw_intrinsic_metadata returned neither codemeta.json "
            f"nor citation.cff: {raw_intrinsic_metadata}"
        )


def get_bibtex_from_origin(origin_url: str) -> str:
    """
    Get citation in BibTeX format given a software origin, from found intrinsic citation
    metadata in the repository, i.e. original codemeta.json and citation.cff, for the
    latest visit snapshot main branch root directory.

    Args:
        origin_url: origin url

    Returns:
        the software citation in BibTeX format

    Raises:
        swh.web.utils.exc.NotFoundExc: when snapshot, branch or directory is missing,
            no metadata could be found or the metadata files could not be decoded
        BadInputExc: when the origin does not allow to find metadata
    """
    metadata = lookup_origin_intrinsic_citation_metadata(origin_url)
    return _get_bibtex_from_raw_intrinsic_metadata(metadata)


def get_bibtex_from_swhid(target_swhid: str) -> str:
    """
    Get citation in BibTeX format given a SWHID, from found intrinsic citation
    metadata in the repository, i.e. original codemeta.json and citation.cff, for the
    target object.

    Args:
        target_swhid: SWHID which can be qualified or not,
            if the target object is of type Content, it must be qualified with an anchor

    Returns:
        the software citation in BibTeX format

    Raises:
        swh.web.utils.exc.NotFoundExc: when snapshot, branch or directory is missing,
            no metadata could be found or the metadata files could not be decoded
        BadInputExc: when the origin does not allow to find metadata
    """
    metadata = lookup_intrinsic_citation_metadata_by_target_swhid(target_swhid)
    parsed_swhid = QualifiedSWHID.from_string(target_swhid)
    return _get_bibtex_from_raw_intrinsic_metadata(metadata, parsed_swhid)
