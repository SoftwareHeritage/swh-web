# Copyright (C) 2021-2025 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re
from typing import Any, Dict

from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework import serializers
from rest_framework.request import Request

from swh.model import hashutil, swhids
from swh.model.model import MetadataAuthority, MetadataAuthorityType, Origin
from swh.web import config
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.api.serializers import SoftLimitsIntegerField
from swh.web.utils import archive, reverse
from swh.web.utils.exc import BadInputExc, NotFoundExc


class MetadataAuthorityField(serializers.Field):
    """A DRF field to handle metadata authorities."""

    def to_representation(self, value: MetadataAuthority) -> str:
        """Serialize value.

        Args:
            value: a MetadataAuthority

        Returns:
            A metadata authority identifier, formatted as ``type IRI``
        """
        return f"{value.type.value} {value.url}"

    def to_internal_value(self, data: str) -> MetadataAuthority:
        """From ``type IRI`` to MetadataAuthority.

        Handles serialization and validation of a metadata authority.

        Args:
            data: A metadata authority identifier, formatted as ``type IRI``

        Raises:
            serializers.ValidationError: invalid value (missing space, invalid type).

        Returns:
            A MetadataAuthority
        """
        authority = data.strip()
        if " " not in authority:
            raise serializers.ValidationError(
                "The 'authority' query parameter must contain a space."
            )
        type_, url = authority.split(" ", 1)
        type_choices = [e.value for e in MetadataAuthorityType]
        if type_ not in type_choices:
            raise serializers.ValidationError(
                f"Invalid type {type_}, must be one of: {', '.join(type_choices)}"
            )
        return MetadataAuthority(MetadataAuthorityType(type_), url)


class RawExtrinsicMetadataQuerySerializer(serializers.Serializer):
    """Raw Extrinsic Metadata query parameters serializer."""

    authority = MetadataAuthorityField(required=True)
    after = serializers.DateTimeField(required=False, default=None)
    limit = SoftLimitsIntegerField(
        required=False, default=100, min_value=1, max_value=10000
    )
    page_token = serializers.CharField(required=False, default=None)


@api_route(
    "/raw-extrinsic-metadata/swhid/<swhid:target>/",
    "api-1-raw-extrinsic-metadata-swhid",
    query_params_serializer=RawExtrinsicMetadataQuerySerializer,
)
@api_doc("/raw-extrinsic-metadata/swhid/", category="Metadata")
@format_docstring()
def api_raw_extrinsic_metadata_swhid(
    request: Request,
    target: str,
    validated_query_params: dict[str, Any],
):
    """
    .. http:get:: /api/1/raw-extrinsic-metadata/swhid/(target)

        Returns raw `extrinsic metadata <https://docs.softwareheritage.org/devel/glossary.html#term-extrinsic-metadata>`__ collected on a given object.

        :param string target: The core SWHID of the object whose metadata
            should be returned
        :query string authority: A metadata authority identifier, formatted as
            ``<type> <IRI>``. Required.
        :query string after: ISO8601 representation of the minimum timestamp of metadata
            to fetch. Defaults to allowing all metadata.
        :query int limit: Maximum number of metadata objects to return (default to 100).
        :query string page_token: optional opaque token, used to get the next page of
            results

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
    """  # noqa B950

    authority = validated_query_params["authority"]
    after = validated_query_params["after"]
    page_token = validated_query_params["page_token"]
    limit = validated_query_params["limit"]

    try:
        parsed_target = swhids.ExtendedSWHID.from_string(target)
    except swhids.ValidationError as e:
        raise BadInputExc(f"Invalid target SWHID: {e}") from None

    result_page = archive.lookup_raw_extrinsic_metadata(
        parsed_target, authority, after, page_token, limit
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
        # We can't reliably send metadata directly, because it is a bytestring,
        # and we have to return JSON documents.
        metadata["metadata_url"] = reverse(
            "api-1-raw-extrinsic-metadata-get",
            url_args={"id": metadata["id"]},
            query_params={"filename": filename},
            request=request,
        )

        del metadata["id"]
        results.append(metadata)

    headers: Dict[str, str] = {}
    if result_page.next_page_token is not None:
        headers["link-next"] = reverse(
            "api-1-raw-extrinsic-metadata-swhid",
            url_args={"target": target},
            query_params=dict(
                authority=request.query_params["authority"],
                after=str(after) if after else None,
                limit=limit,
                page_token=result_page.next_page_token,
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
    metadata = config.storage().raw_extrinsic_metadata_get_by_ids(
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
    "/raw-extrinsic-metadata/swhid/<swhid:target>/authorities/",
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

    authorities = config.storage().raw_extrinsic_metadata_get_authorities(
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
