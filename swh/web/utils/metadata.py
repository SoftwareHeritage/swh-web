# Copyright (C) 2015-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import yaml

from swh.indexer.bibtex import cff_to_bibtex, codemeta_to_bibtex
from swh.model.swhids import QualifiedSWHID
from swh.web.utils.archive import (
    lookup_origin_raw_intrinsic_metadata,
    lookup_raw_intrinsic_metadata_by_target_swhid,
)


def get_bibtex_from_origin(origin_url: str) -> str:
    """
    Get citation in BibTeX format given a software origin, from found raw intrinsic
    metadata in the repository, i.e. original codemeta.json and citation.cff, for the
    latest visit snapshot main branch root directory.

    Args:
        origin_url: origin url

    Returns:
        The software citation in BibTeX format (cannot be empty: it contains at least
        an entry type and an entry key)

    Raises:
        swh.web.utils.exc.NotFoundExc: when snapshot, branch or directory is missing,
            no metadata could be found or the metadata files could not be decoded.
        BadInputExc: when the origin does not allow to find metadata.
    """
    metadata = lookup_origin_raw_intrinsic_metadata(origin_url)
    if metadata.get("codemeta.json"):
        bibtex = codemeta_to_bibtex(metadata["codemeta.json"])
    elif metadata.get("citation.cff"):
        bibtex = cff_to_bibtex(
            yaml.dump(metadata["citation.cff"], default_flow_style=False)
        )
    else:
        # Cannot happen: metadata contains at least one of codemeta.json or citation.cff
        assert False, (
            f"lookup_origin_raw_intrinsic_metadata returned neither codemeta.json "
            f"nor citation.cff: {metadata}"
        )
    return bibtex


def get_bibtex_from_swhid(target_swhid: str) -> str:
    """
    Get citation in BibTeX format given a SWHID, from found raw intrinsic
    metadata in the repository, i.e. original codemeta.json and citation.cff, for the
    target object.

    Args:
        target_swhid: SWHID which target object cannot be of type Content and which can
        be qualified or no

    Returns:
        The software citation in BibTeX format (cannot be empty: it contains at least
        an entry type and an entry key)

    Raises:
        swh.web.utils.exc.NotFoundExc: when snapshot, branch or directory is missing,
            no metadata could be found or the metadata files could not be decoded.
        BadInputExc: when the origin does not allow to find metadata.
    """
    metadata = lookup_raw_intrinsic_metadata_by_target_swhid(target_swhid)
    parsed_swhid = QualifiedSWHID.from_string(target_swhid)
    if metadata.get("codemeta.json"):
        bibtex = codemeta_to_bibtex(metadata["codemeta.json"], parsed_swhid)
    elif metadata.get("citation.cff"):
        bibtex = cff_to_bibtex(
            yaml.dump(metadata["citation.cff"], default_flow_style=False), parsed_swhid
        )
    else:
        # Cannot happen: metadata contains at least one of codemeta.json or citation.cff
        assert False, (
            f"lookup_origin_raw_intrinsic_metadata returned neither codemeta.json "
            f"nor citation.cff: {metadata}"
        )
    return bibtex
