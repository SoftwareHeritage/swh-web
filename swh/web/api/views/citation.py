# Copyright (C) 2024 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information
from django.core.exceptions import ValidationError
from rest_framework.request import Request

from swh.model.swhids import QualifiedSWHID
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.utils import BadInputExc
from swh.web.utils.metadata import get_bibtex_from_origin, get_bibtex_from_swhid


@api_route(
    "/raw-intrinsic-metadata/citation/origin/",
    "api-1-raw-intrinsic-citation-origin-get",
)
@api_doc("/raw-intrinsic-metadata/citation/origin/", category="Metadata")
@format_docstring()
def api_raw_intrinsic_citation_origin_get(request: Request):
    """
    .. http:get:: /api/1/raw-intrinsic-metadata/citation/origin/

        Get a software citation, given a format (only currently supported format is BibTeX)
        and a software origin. This citation will refer to the latest visit snapshot
        version of the main branch of the software repository.

        :query string citation_format: the citation expected format (currently bibtex)
        :query string origin_url: the URL of the software origin

        :<json string the software citation in the expected format

        {common_headers}

        :statuscode 200: no error
        :statuscode 400: the requested software origin is invalid
        :statuscode 404: the requested software origin cannot be found in the archive
         or metadata for citation is missing, or citation is empty

        **Example:**

        .. parsed-literal::

            :swh_web_api:`raw-intrinsic-metadata/citation/origin/?citation_format=bibtex&origin_url=https://github.com/rdicosmo/parmap`
    """
    origin_url = request.GET.get("origin_url")
    if origin_url is None:
        raise BadInputExc("Missing origin URL as query parameter.")
    citation_format = request.GET.get("citation_format")
    if citation_format != "bibtex":
        raise BadInputExc(
            "Invalid citation format: only BibTeX format is currently supported."
        )
    bibtex = get_bibtex_from_origin(origin_url)
    return bibtex


@api_route(
    "/raw-intrinsic-metadata/citation/swhid/",
    "api-1-raw-intrinsic-citation-swhid-get",
)
@api_doc("/raw-intrinsic-metadata/citation/swhid/", category="Metadata")
@format_docstring()
def api_raw_intrinsic_citation_swhid_get(request: Request):
    """
    .. http:get:: /api/1/raw-intrinsic-metadata/citation/swhid/

        Get a software citation, given an object SWHID and a format (only currently
        supported format is BibTeX).

        :query string target_swhid: The SWHID, with or without qualifiers, of the
         software object to cite
        :query string citation_format: the citation expected format (currently bibtex)

        :<json string the software citation in the expected format

        {common_headers}

        :statuscode 200: no error
        :statuscode 400: the requested software origin is invalid
        :statuscode 404: the requested software origin cannot be found in the archive
         or metadata for citation is missing, or citation is empty

        **Example:**

        .. parsed-literal::

            :swh_web_api:`raw-intrinsic-metadata/citation/swhid/target_swhid=swh:1:dir:2dc0f462d191524530f5612d2935851505af41dd;origin=https://github.com/rdicosmo/parmap;visit=swh:1:snp:2128ed4f25f2d7ae7c8b7950a611d69cf4429063/&citation_format=bibtex`
    """
    target_swhid = request.GET.get("target_swhid", "")
    try:
        QualifiedSWHID.from_string(target_swhid)
    except ValidationError as e:
        raise BadInputExc(f"Invalid target SWHID {target_swhid}: {e.message}.")
    citation_format = request.GET.get("citation_format")
    if citation_format != "bibtex":
        raise BadInputExc(
            "Invalid citation format: only BibTeX format is currently supported."
        )
    bibtex = get_bibtex_from_swhid(target_swhid)
    return bibtex
