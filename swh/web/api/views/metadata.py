# Copyright (C) 2021-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import base64
import re
from typing import Dict, Optional

import iso8601

from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework.request import Request

from swh.model import hashutil, swhids
from swh.model.model import MetadataAuthority, MetadataAuthorityType, Origin
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.utils import SWHID_RE, archive, converters, reverse
from swh.web.utils.exc import BadInputExc, NotFoundExc


@api_route(
    f"/raw-extrinsic-metadata/swhid/(?P<target>{SWHID_RE})/",
    "api-1-raw-extrinsic-metadata-swhid",
)
@api_doc("/raw-extrinsic-metadata/swhid/", category="Metadata")
@format_docstring()
def api_raw_extrinsic_metadata_swhid(request: Request, target: str):
    """
    .. http:get:: /api/1/raw-extrinsic-metadata/swhid/(target)

        Returns raw `extrinsic metadata <https://docs.softwareheritage.org/devel/glossary.html#term-extrinsic-metadata>`__ collected on a given object.

        :param string target: The core SWHID of the object whose metadata
            should be returned
        :query string authority: A metadata authority identifier, formatted as
            ``<type> <IRI>``. Required.
        :query string after: ISO8601 representation of the minimum timestamp of metadata
            to fetch. Defaults to allowing all metadata.
        :query int limit: Maximum number of metadata objects to return.

        {common_headers}

        :>jsonarr string target: SWHID of the object described by this metadata
            (absent when ``target`` is not a core SWHID (ie. it does not have type
            ``cnt``/``dir``/``rev``/``rel``/``snp``)
        :>jsonarr string discovery_date: ISO8601/RFC3339 timestamp of the moment this
            metadata was collected.
        :>jsonarr object authority: authority this metadata is coming from
        :>jsonarr object fetcher: tool used to fetch the metadata
        :>jsonarr string format: short identifier of the format of the metadata
        :>jsonarr string metadata_url: link to download the metadata "blob" itself
        :>jsonarr string origin: URL of the origin in which context's
            the metadata is valid, if any
        :>jsonarr int visit: identifier of the visit in which context's
            the metadata is valid, if any
        :>jsonarr string snapshot: SWHID of the snapshot in which context's
            the metadata is valid, if any
        :>jsonarr string release: SWHID of the release in which context's
            the metadata is valid, if any
        :>jsonarr string revision: SWHID of the revision in which context's
            the metadata is valid, if any
        :>jsonarr string path: SWHID of the path in which context's
            is valid if any, relative to a release or revision as anchor
        :>jsonarr string directory: SWHID of the directory in which context's
            the metadata is valid, if any

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`raw-extrinsic-metadata/swhid/swh:1:dir:a2faa28028657859c16ff506924212b33f0e1307/?authority=forge%20https://pypi.org/`
    """  # noqa
    authority_str: Optional[str] = request.query_params.get("authority")
    after_str: Optional[str] = request.query_params.get("after")
    limit_str: str = request.query_params.get("limit", "100")
    page_token_str: Optional[str] = request.query_params.get("page_token")

    if authority_str is None:
        raise BadInputExc("The 'authority' query parameter is required.")
    if " " not in authority_str.strip():
        raise BadInputExc("The 'authority' query parameter should contain a space.")

    (authority_type_str, authority_url) = authority_str.split(" ", 1)
    try:
        authority_type = MetadataAuthorityType(authority_type_str)
    except ValueError:
        raise BadInputExc(
            f"Invalid 'authority' type, should be one of: "
            f"{', '.join(member.value for member in MetadataAuthorityType)}"
        )
    authority = MetadataAuthority(authority_type, authority_url)

    if after_str:
        try:
            after = iso8601.parse_date(after_str)
        except iso8601.ParseError:
            raise BadInputExc("Invalid format for 'after' parameter.") from None
    else:
        after = None

    try:
        limit = int(limit_str)
    except ValueError:
        raise BadInputExc("'limit' parameter must be an integer.") from None
    limit = min(limit, 10000)

    try:
        parsed_target = swhids.ExtendedSWHID.from_string(target)
    except swhids.ValidationError as e:
        raise BadInputExc(f"Invalid target SWHID: {e}") from None

    try:
        swhids.CoreSWHID.from_string(target)
    except swhids.ValidationError:
        # Can be parsed as an extended SWHID, but not as a core SWHID
        extended_swhid = True
    else:
        extended_swhid = False

    if page_token_str is not None:
        page_token = base64.urlsafe_b64decode(page_token_str)
    else:
        page_token = None

    result_page = archive.storage.raw_extrinsic_metadata_get(
        target=parsed_target,
        authority=authority,
        after=after,
        page_token=page_token,
        limit=limit,
    )

    filename = None
    if parsed_target.object_type == swhids.ExtendedObjectType.ORIGIN:
        origin_sha1 = hashutil.hash_to_hex(parsed_target.object_id)
        (origin_info,) = list(archive.lookup_origins_by_sha1s([origin_sha1]))
        if origin_info is not None:
            filename = re.sub("[:/_.]+", "_", origin_info["url"]) + "_metadata"
    if filename is None:
        filename = f"{target}_metadata"

    results = []

    for metadata in result_page.results:
        result = converters.from_raw_extrinsic_metadata(metadata)

        if extended_swhid:
            # Keep extended SWHIDs away from the public API as much as possible.
            # (It is part of the URL, but not documented, and only accessed via
            # the link in the response of api-1-origin)
            del result["target"]

        # We can't reliably send metadata directly, because it is a bytestring,
        # and we have to return JSON documents.
        result["metadata_url"] = reverse(
            "api-1-raw-extrinsic-metadata-get",
            url_args={"id": hashutil.hash_to_hex(metadata.id)},
            query_params={"filename": filename},
            request=request,
        )

        results.append(result)

    headers: Dict[str, str] = {}
    if result_page.next_page_token is not None:
        headers["link-next"] = reverse(
            "api-1-raw-extrinsic-metadata-swhid",
            url_args={"target": target},
            query_params=dict(
                authority=authority_str,
                after=after_str,
                limit=limit_str,
                page_token=base64.urlsafe_b64encode(
                    result_page.next_page_token.encode()
                ).decode(),
            ),
            request=request,
        )

    return {
        "results": results,
        "headers": headers,
    }


@api_route(
    "/raw-extrinsic-metadata/get/(?P<id>[0-9a-z]+)/",
    "api-1-raw-extrinsic-metadata-get",
)
def api_raw_extrinsic_metadata_get(request: Request, id: str):
    # This is an internal endpoint that should only be accessed via URLs given
    # by /raw-extrinsic-metadata/swhid/; so it is not documented.
    metadata = archive.storage.raw_extrinsic_metadata_get_by_ids(
        [hashutil.hash_to_bytes(id)]
    )
    if not metadata:
        raise NotFoundExc(
            "Metadata not found. Use /raw-extrinsic-metadata/swhid/ to access metadata."
        )

    response = HttpResponse(
        metadata[0].metadata, content_type="application/octet-stream"
    )

    filename = request.query_params.get("filename")
    if filename and re.match("[a-zA-Z0-9:._-]+", filename):
        response["Content-disposition"] = f'attachment; filename="{filename}"'
    else:
        # It should always be not-None and match the regexp if the URL was created by
        # /raw-extrinsic-metadata/swhid/, but we're better safe than sorry.
        response["Content-disposition"] = "attachment"

    return response


@api_route(
    f"/raw-extrinsic-metadata/swhid/(?P<target>{SWHID_RE})/authorities/",
    "api-1-raw-extrinsic-metadata-swhid-authorities",
)
@api_doc("/raw-extrinsic-metadata/swhid/authorities/", category="Metadata")
@format_docstring()
def api_raw_extrinsic_metadata_swhid_authorities(request: Request, target: str):
    """
    .. http:get:: /api/1/raw-extrinsic-metadata/swhid/(target)/authorities/

        Returns a list of metadata authorities that provided metadata on
        the given target.
        They can then be used to get the raw `extrinsic metadata <https://docs.softwareheritage.org/devel/glossary.html#term-extrinsic-metadata>`__ collected on
        that object from each of the authorities.

        This endpoint should only be used directly to retrieve metadata from
        core SWHIDs (with type ``cnt``, ``dir``, ``rev``, ``rel``, and ``snp``).
        For "extended" SWHIDs such as origins,
        :http:get:`/api/1/raw-extrinsic-metadata/origin/(origin_url)/authorities/`
        should be used instead of building this URL directly.

        :param string target: The core SWHID of the object whose metadata-providing
          authorities should be returned

        {common_headers}

        :>jsonarr string type: Type of authority (deposit_client, forge, registry)
        :>jsonarr string url: Unique IRI identifying the authority
        :>jsonarr object metadata_list_url: URL to get the list of metadata objects
          on the given object from this authority

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`raw-extrinsic-metadata/swhid/swh:1:dir:a2faa28028657859c16ff506924212b33f0e1307/authorities/`
    """  # noqa

    try:
        parsed_target = swhids.ExtendedSWHID.from_string(target)
    except swhids.ValidationError as e:
        raise BadInputExc(f"Invalid target SWHID: {e}") from None

    authorities = archive.storage.raw_extrinsic_metadata_get_authorities(
        target=parsed_target
    )
    results = [
        {
            **authority.to_dict(),
            "metadata_list_url": reverse(
                "api-1-raw-extrinsic-metadata-swhid",
                url_args={"target": target},
                query_params={"authority": f"{authority.type.value} {authority.url}"},
                request=request,
            ),
        }
        for authority in authorities
    ]

    return {
        "results": results,
        "headers": {},
    }


@api_route(
    "/raw-extrinsic-metadata/origin/(?P<origin_url>.*)/authorities/",
    "api-1-raw-extrinsic-metadata-origin-authorities",
)
@api_doc("/raw-extrinsic-metadata/origin/authorities/", category="Metadata")
@format_docstring()
def api_raw_extrinsic_metadata_origin_authorities(request: Request, origin_url: str):
    """
    .. http:get:: /api/1/raw-extrinsic-metadata/origin/(origin_url)/authorities/

        Similar to
        :http:get:`/api/1/raw-extrinsic-metadata/swhid/(target)/authorities/`
        but to get metadata on origins instead of objects

        :param string origin_url: The URL of the origin whose metadata-providing
          authorities should be returned

        {common_headers}

        :>jsonarr string type: Type of authority (deposit_client, forge, registry)
        :>jsonarr string url: Unique IRI identifying the authority
        :>jsonarr object metadata_list_url: URL to get the list of metadata objects
          on the given object from this authority

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`raw-extrinsic-metadata/origin/https://github.com/rdicosmo/parmap/authorities/`
    """  # noqa
    url = reverse(
        "api-1-raw-extrinsic-metadata-swhid-authorities",
        url_args={"target": Origin(url=origin_url).swhid()},
    )
    return redirect(url)
