# Copyright (C) 2015-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json

from swh.indexer.citation import CitationFormat
from swh.web.utils.citation import get_citation_from_origin, get_citation_from_swhid


def test_get_bibtex_from_origin(origin_with_metadata_file):
    citation = get_citation_from_origin(
        CitationFormat.BIBTEX, origin_with_metadata_file["url"]
    )
    bibtex = citation["content"]

    assert "@software" in bibtex
    assert 'title = "Test Software"' in bibtex


def test_get_bibtex_from_swhid(objects_with_metadata_file):
    citation = get_citation_from_swhid(
        CitationFormat.BIBTEX, str(objects_with_metadata_file[0])
    )
    bibtex = citation["content"]

    assert "@software" in bibtex
    assert 'title = "Test Software"' in bibtex
    assert (
        'swhid = "swh:1:snp:89cb4bc962dd297a70053c9288f98d3fde8db740;'
        r'origin=https://git.example.org/repo\_with\_metadata\_file"' in bibtex
    )


def test_get_bibtex_from_codemeta_with_unknown_context(
    origin_url_with_unknown_codemeta_context,
):
    citation = get_citation_from_origin(
        CitationFormat.BIBTEX, origin_url_with_unknown_codemeta_context
    )

    assert citation["content"].startswith("@softwareversion{swh-dir-")
    assert (
        citation["warning"] is not None
        and "Unknown context URL: https://example.org/codemeta/3.0"
        in citation["warning"]
    )


def test_get_csl_from_origin(origin_with_metadata_file):
    citation = get_citation_from_origin(
        CitationFormat.CSL, origin_with_metadata_file["url"]
    )
    csl = json.loads(citation["content"])

    assert csl["type"] == "software"
    assert csl["title"] == "Test Software"


def test_get_csl_from_swhid(objects_with_metadata_file):
    source_swhid = str(objects_with_metadata_file[0])
    citation = get_citation_from_swhid(CitationFormat.CSL, source_swhid)
    csl = json.loads(citation["content"])

    assert csl["type"] == "software"
    assert csl["title"] == "Test Software"
    assert csl["id"] == source_swhid


def test_get_csl_from_codemeta_with_unknown_context(
    origin_url_with_unknown_codemeta_context,
):
    citation = get_citation_from_origin(
        CitationFormat.CSL, origin_url_with_unknown_codemeta_context
    )
    csl = json.loads(citation["content"])

    assert csl["type"] == "software"
    assert (
        citation["warning"] is not None
        and "Unknown context URL: https://example.org/codemeta/3.0"
        in citation["warning"]
    )
