# Copyright (C) 2015-2025 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from functools import partial
from typing import Any

from rest_framework import serializers
from rest_framework.request import Request

from swh.search.exc import SearchQuerySyntaxError
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.api.serializers import IRIField, SoftLimitsIntegerField
from swh.web.api.utils import (
    enrich_origin,
    enrich_origin_search_result,
    enrich_origin_visit,
)
from swh.web.api.views.utils import api_lookup
from swh.web.utils import archive, origin_visit_types, reverse
from swh.web.utils.exc import BadInputExc
from swh.web.utils.origin_visits import get_origin_visits

DOC_RETURN_ORIGIN = """
        :>json string origin_visits_url: link to in order to get information
            about the visits for that origin
        :>json string url: the origin canonical url
        :>json string metadata_authorities_url: link to
            :http:get:`/api/1/raw-extrinsic-metadata/swhid/(target)/authorities/`
            to get the list of metadata authorities providing extrinsic metadata
            on this origin (and, indirectly, to the origin's extrinsic metadata itself)
"""


DOC_RETURN_ORIGIN_ARRAY = DOC_RETURN_ORIGIN.replace(":>json", ":>jsonarr")

DOC_RETURN_ORIGIN_ARRAY_SEARCH = DOC_RETURN_ORIGIN_ARRAY + (
    "        :>jsonarr boolean has_visits: indicates if Software Heritage made at "
    "least one full visit of the origin"
)

DOC_RETURN_ORIGIN += (
    "        :>json array visit_types: set of visit types for that origin"
)

DOC_RETURN_ORIGIN_VISIT = """
        :>json string date: ISO8601/RFC3339 representation of the visit date (in UTC)
        :>json str origin: the origin canonical url
        :>json string origin_url: link to get information about the origin
        :>json string snapshot: the snapshot identifier of the visit
            (may be null if status is not **full**).
        :>json string snapshot_url: link to
            :http:get:`/api/1/snapshot/(snapshot_id)/` in order to get
            information about the snapshot of the visit
            (may be null if status is not **full**).
        :>json string status: status of the visit (either **full**,
            **partial** or **ongoing**)
        :>json string type: visit type for the origin
        :>json number visit: the unique identifier of the visit
"""

DOC_RETURN_ORIGIN_VISIT_ARRAY = DOC_RETURN_ORIGIN_VISIT.replace(":>json", ":>jsonarr")

DOC_RETURN_ORIGIN_VISIT_ARRAY += """
        :>jsonarr number id: the unique identifier of the origin
        :>jsonarr string origin_visit_url: link to
            :http:get:`/api/1/origin/(origin_url)/visit/(visit_id)/`
            in order to get information about the visit
"""


def deprecate_field(_: str):
    """Raise an error if a value is sent.

    Args:
        _: any value

    Raises:
        serializers.ValidationError: a value has been sent
    """
    raise serializers.ValidationError(
        "Please use the Link header to browse through result"
    )


class OriginsQuerySerializer(serializers.Serializer):
    """Origins query parameters serializer."""

    origin_count = SoftLimitsIntegerField(
        default=100,
        required=False,
        min_value=1,
        max_value=10000,
    )
    page_token = serializers.CharField(default=None, required=False)
    # deprecated parameter
    origin_from = serializers.CharField(
        required=False, validators=[deprecate_field], write_only=True
    )


@api_route(
    r"/origins/", "api-1-origins", query_params_serializer=OriginsQuerySerializer
)
@api_doc("/origins/", category="Archive", noargs=True)
@format_docstring(return_origin_array=DOC_RETURN_ORIGIN_ARRAY)
def api_origins(request: Request, validated_query_params: dict[str, Any]):
    """
    .. http:get:: /api/1/origins/

        Get list of archived software origins.

        .. warning::

            This endpoint used to provide an ``origin_from`` query parameter,
            and guarantee an order on results. This is no longer true,
            and only the Link header should be used for paginating through
            results.

        :query int origin_count: The maximum number of origins to return
            (default to 100, cannot exceed 10000)

        {return_origin_array}

        {common_headers}
        {resheader_link}

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origins?origin_count=500`

    """
    page_token = validated_query_params["page_token"]
    limit = validated_query_params["origin_count"]

    page_result = archive.lookup_origins(page_token, limit)

    origins = [enrich_origin(o, request=request) for o in page_result.results]
    next_page_token = page_result.next_page_token

    headers: dict[str, str] = {}
    if next_page_token is not None:
        headers["link-next"] = reverse(
            "api-1-origins",
            query_params={"page_token": next_page_token, "origin_count": str(limit)},
            request=request,
        )
    return {"results": origins, "headers": headers}


@api_route(r"/origin/(?P<origin_url>.+)/get/", "api-1-origin")
@api_doc("/origin/", category="Archive")
@format_docstring(return_origin=DOC_RETURN_ORIGIN)
def api_origin(request: Request, origin_url: str):
    """
    .. http:get:: /api/1/origin/(origin_url)/get/

        Get information about a software origin.

        :param string origin_url: the origin url

        {return_origin}

        {common_headers}

        :statuscode 200: no error
        :statuscode 404: requested origin cannot be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/https://github.com/python/cpython/get/`

    """
    error_msg = f"Origin with url {origin_url} not found."

    return api_lookup(
        archive.lookup_origin,
        origin_url,
        lookup_similar_urls=False,
        notfound_msg=error_msg,
        enrich_fn=enrich_origin,
        request=request,
    )


def _visit_types() -> str:
    docstring = ""
    # available visit types are queried using swh-search so we do it in a try
    # block in case of failure (for instance in docker environment when
    # elasticsearch service is not available)
    try:
        visit_types = [f"**{visit_type}**" for visit_type in origin_visit_types()]
        docstring = ", ".join(visit_types[:-1]) + f", and {visit_types[-1]}"
    except Exception:
        docstring = "???"
        pass
    return docstring


class OriginSearchQuerySerializer(serializers.Serializer):
    """Origin search query parameters serializer."""

    use_ql = serializers.BooleanField(required=False, default=False)
    limit = SoftLimitsIntegerField(
        default=70,
        required=False,
        min_value=1,
        max_value=1000,
    )
    page_token = serializers.CharField(default=None, required=False)
    with_visit = serializers.BooleanField(required=False, default=False)
    # can't force a choice in values from origin_visit_types as the list might be empty
    visit_type = serializers.CharField(required=False, default=None)


@api_route(
    r"/origin/search/(?P<url_pattern>.*)/",
    "api-1-origin-search",
    throttle_scope="swh_api_origin_search",
    query_params_serializer=OriginSearchQuerySerializer,
)
@api_doc("/origin/search/", category="Archive")
@format_docstring(
    return_origin_array=DOC_RETURN_ORIGIN_ARRAY_SEARCH, visit_types=_visit_types()
)
def api_origin_search(
    request: Request,
    url_pattern: str,
    validated_query_params: dict[str, Any],
):
    """
    .. http:get:: /api/1/origin/search/(url_pattern)/

        Search for software origins whose urls contain a provided string
        pattern. The search is performed in a case insensitive way.

        .. warning::

            This endpoint used to provide an ``offset`` query parameter,
            and guarantee an order on results. This is no longer true,
            and only the Link header should be used for paginating through
            results.

        :param string url_pattern: a string pattern
        :query boolean use_ql: whether to use swh search query language or not
        :query int limit: the maximum number of found origins to return
            (bounded to 1000)
        :query boolean with_visit: if true, only return origins with at least
            one visit by Software heritage
        :query string visit_type: if provided, only return origins with that
            specific visit type (currently the supported types are {visit_types})

        {return_origin_array}

        {common_headers}
        {resheader_link}
        :resheader X-Total-Count: the total number of origins whose URL
            contains the provided string pattern

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/search/python/?limit=2`
    """
    with_visit = validated_query_params["with_visit"]
    visit_type = validated_query_params["visit_type"]
    use_ql = validated_query_params["use_ql"]
    page_token = validated_query_params["page_token"]
    limit = validated_query_params["limit"]

    try:
        (results, page_token, total_results) = api_lookup(
            archive.search_origin,
            url_pattern,
            use_ql,
            limit,
            with_visit,
            [visit_type] if visit_type else None,
            page_token,
            enrich_fn=enrich_origin_search_result,
            request=request,
        )
    except SearchQuerySyntaxError as e:
        raise BadInputExc(f"Syntax error in search query: {e.args[0]}")

    headers = {"X-Total-Count": total_results}
    if page_token is not None:
        query_params = {k: v for (k, v) in request.GET.dict().items()}
        query_params["page_token"] = page_token

        headers["link-next"] = reverse(
            "api-1-origin-search",
            url_args={"url_pattern": url_pattern},
            query_params=query_params,
            request=request,
        )

    return {"results": results, "headers": headers}


class OriginMetadataSearchQuerySerializer(serializers.Serializer):
    """Origin query parameters serializer."""

    limit = SoftLimitsIntegerField(
        default=70,
        required=False,
        min_value=1,
        max_value=100,
    )
    fulltext = serializers.CharField(
        required=True,
        # min_length=?  XXX we should probably set a min length
        # max_length=?  XXX we should probably set a max length
    )


@api_route(
    r"/origin/metadata-search/",
    "api-1-origin-metadata-search",
    query_params_serializer=OriginMetadataSearchQuerySerializer,
)
@api_doc("/origin/metadata-search/", category="Metadata", noargs=True)
@format_docstring(return_origin_array=DOC_RETURN_ORIGIN_ARRAY)
def api_origin_metadata_search(request: Request, validated_query_params: dict):
    """
    .. http:get:: /api/1/origin/metadata-search/

        Search for software origins whose metadata (expressed as a
        JSON-LD/CodeMeta dictionary) match the provided criteria.
        For now, only full-text search on this dictionary is supported.

        :query str fulltext: a string that will be matched against origin
            metadata; results are ranked and ordered starting with the best
            ones.
        :query int limit: the maximum number of found origins to return
            (bounded to 100)

        {return_origin_array}

        {common_headers}

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/metadata-search/?limit=2&fulltext=node-red-nodegen`
    """
    fulltext = validated_query_params["fulltext"]
    limit = validated_query_params["limit"]
    fields = request.query_params.get("fields", "")
    return_metadata = not fields or "metadata" in fields

    results = api_lookup(
        archive.search_origin_metadata,
        fulltext,
        limit,
        return_metadata,
        request=request,
    )

    return {
        "results": results,
    }


class OriginVisitsQuerySerializer(serializers.Serializer):
    """Origins visits query parameters serializer."""

    per_page = SoftLimitsIntegerField(
        default=10,
        required=False,
        min_value=1,
        max_value=100,
    )
    last_visit = serializers.IntegerField(required=False, default=None)


@api_route(
    r"/origin/(?P<origin_url>.+)/visits/",
    "api-1-origin-visits",
    query_params_serializer=OriginVisitsQuerySerializer,
)
@api_doc("/origin/visits/", category="Archive")
@format_docstring(return_origin_visit_array=DOC_RETURN_ORIGIN_VISIT_ARRAY)
def api_origin_visits(request: Request, origin_url: str, validated_query_params: dict):
    """
    .. http:get:: /api/1/origin/(origin_url)/visits/

        Get information about all visits of a software origin.
        Visits are returned sorted in descending order according
        to their date.

        :param str origin_url: a software origin URL
        :query int per_page: specify the number of visits to list, for
            pagination purposes
        :query int last_visit: visit to start listing from, for pagination
            purposes

        {common_headers}
        {resheader_link}

        {return_origin_visit_array}

        :statuscode 200: no error
        :statuscode 404: requested origin cannot be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/https://github.com/hylang/hy/visits/`

    """

    per_page = validated_query_params["per_page"]
    last_visit = validated_query_params["last_visit"]

    result = {}

    def _lookup_origin_visits(origin_url, last_visit=last_visit, per_page=per_page):
        all_visits = get_origin_visits(origin_url, lookup_similar_urls=False)
        all_visits.reverse()
        visits = []
        if not last_visit:
            visits = all_visits[:per_page]
        else:
            for i, v in enumerate(all_visits):
                if v["visit"] == last_visit:
                    visits = all_visits[i + 1 : i + 1 + per_page]
                    break
        for v in visits:
            yield v

    results = api_lookup(
        _lookup_origin_visits,
        origin_url,
        notfound_msg=f"No origin {origin_url} found",
        enrich_fn=partial(
            enrich_origin_visit, with_origin_link=False, with_origin_visit_link=True
        ),
        request=request,
    )

    if results:
        nb_results = len(results)
        if nb_results == per_page:
            new_last_visit = results[-1]["visit"]
            query_params = {}
            query_params["last_visit"] = new_last_visit

            if request.query_params.get("per_page"):
                query_params["per_page"] = per_page

            result["headers"] = {
                "link-next": reverse(
                    "api-1-origin-visits",
                    url_args={"origin_url": origin_url},
                    query_params=query_params,
                    request=request,
                )
            }

    result.update({"results": results})

    return result


class OriginsVisitLatestQuerySerializer(serializers.Serializer):
    """Origins visit latest query parameters serializer."""

    require_snapshot = serializers.BooleanField(required=False, default=False)
    visit_type = serializers.CharField(required=False, default=None)


@api_route(
    r"/origin/(?P<origin_url>.+)/visit/latest/",
    "api-1-origin-visit-latest",
    throttle_scope="swh_api_origin_visit_latest",
    query_params_serializer=OriginsVisitLatestQuerySerializer,
)
@api_doc("/origin/visit/latest/", category="Archive")
@format_docstring(return_origin_visit=DOC_RETURN_ORIGIN_VISIT)
def api_origin_visit_latest(
    request: Request, origin_url: str, validated_query_params: dict
):
    """
    .. http:get:: /api/1/origin/(origin_url)/visit/latest/

        Get information about the latest visit of a software origin.

        :param str origin_url: a software origin URL
        :query boolean require_snapshot: if true, only return a visit
            with a snapshot
        :query str visit_type: if provided, filter visits by type

        {common_headers}

        {return_origin_visit}

        :statuscode 200: no error
        :statuscode 404: requested origin or visit cannot be found in the
            archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/https://github.com/hylang/hy/visit/latest/`
    """

    return api_lookup(
        archive.lookup_origin_visit_latest,
        origin_url,
        validated_query_params["require_snapshot"],
        type=validated_query_params["visit_type"],
        lookup_similar_urls=False,
        notfound_msg=("No visit for origin {} found".format(origin_url)),
        enrich_fn=partial(
            enrich_origin_visit, with_origin_link=True, with_origin_visit_link=False
        ),
        request=request,
    )


@api_route(
    r"/origin/(?P<origin_url>.+)/visit/(?P<visit_id>[0-9]+)/", "api-1-origin-visit"
)
@api_doc("/origin/visit/", category="Archive")
@format_docstring(return_origin_visit=DOC_RETURN_ORIGIN_VISIT)
def api_origin_visit(request: Request, visit_id: str, origin_url: str):
    """
    .. http:get:: /api/1/origin/(origin_url)/visit/(visit_id)/

        Get information about a specific visit of a software origin.

        :param str origin_url: a software origin URL
        :param int visit_id: a visit identifier

        {common_headers}

        {return_origin_visit}

        :statuscode 200: no error
        :statuscode 404: requested origin or visit cannot be found in the
            archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/https://github.com/hylang/hy/visit/1/`
    """

    return api_lookup(
        archive.lookup_origin_visit,
        origin_url,
        int(visit_id),
        lookup_similar_urls=False,
        notfound_msg=("No visit {} for origin {} found".format(visit_id, origin_url)),
        enrich_fn=partial(
            enrich_origin_visit, with_origin_link=True, with_origin_visit_link=False
        ),
        request=request,
    )


@api_route(
    r"/origin/(?P<origin_url>.+)/intrinsic-metadata/",
    "api-origin-intrinsic-metadata-legacy",
)
@api_doc("/origin/intrinsic-metadata/", category="Metadata", tags=["deprecated"])
@format_docstring()
def api_origin_intrinsic_metadata_legacy(request: Request, origin_url: str):
    """
    .. http:get:: /api/1/origin/(origin_url)/intrinsic-metadata

        This route is deprecated; use http:get:/api/1/intrinsic-metadata/origin/ instead

        Get intrinsic metadata of a software origin (as a JSON-LD/CodeMeta dictionary).
    """
    response = api_lookup(
        archive.lookup_origin_intrinsic_metadata,
        origin_url,
        lookup_similar_urls=False,
        notfound_msg=f"Origin with url {origin_url} not found",
        enrich_fn=enrich_origin,
        request=request,
    )
    return response[0]


class OriginUrlQuerySerializer(serializers.Serializer):
    """Origin url query parameters serializer."""

    origin_url = IRIField(required=True)


@api_route(
    r"/intrinsic-metadata/origin/",
    "api-origin-intrinsic-metadata",
    query_params_serializer=OriginUrlQuerySerializer,
)
@api_doc("/intrinsic-metadata/origin/", category="Metadata")
@format_docstring()
def api_origin_intrinsic_metadata(
    request: Request, validated_query_params: dict[str, str]
):
    """
    .. http:get:: /api/1/intrinsic-metadata/origin/

        Get intrinsic metadata of a software origin (as a JSON-LD/CodeMeta dictionary).

        :query string origin_url: the URL of the origin

        :>jsonarr ??? ???: intrinsic metadata field of the origin

        {common_headers}

        :statuscode 200: no error
        :statuscode 404: requested origin cannot be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`intrinsic-metadata/origin/?origin_url=https://github.com/node-red/node-red-nodegen`
    """
    origin_url = validated_query_params["origin_url"]
    return api_lookup(
        archive.lookup_origin_intrinsic_metadata,
        origin_url,
        lookup_similar_urls=False,
        notfound_msg=f"Origin with url {origin_url} not found",
        enrich_fn=enrich_origin,
        request=request,
    )


@api_route(
    r"/extrinsic-metadata/origin/",
    "api-origin-extrinsic-metadata",
    query_params_serializer=OriginUrlQuerySerializer,
)
@api_doc("/extrinsic-metadata/origin/", category="Metadata")
@format_docstring()
def api_origin_extrinsic_metadata(
    request: Request, validated_query_params: dict[str, str]
):
    """
    .. http:get:: /api/1/extrinsic-metadata/origin/

        Get extrinsic metadata of a software origin (as a JSON-LD/CodeMeta dictionary).

        :query str origin_url: parameter for origin url

        :>jsonarr ??? ???: extrinsic metadata field of the origin

        {common_headers}

        :statuscode 200: no error
        :statuscode 404: requested origin cannot be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`extrinsic-metadata/origin/?origin_url=https://github.com/node-red/node-red-nodegen`
    """
    origin_url = validated_query_params["origin_url"]
    return api_lookup(
        archive.lookup_origin_extrinsic_metadata,
        origin_url,
        lookup_similar_urls=False,
        notfound_msg=f"Origin with url {origin_url} not found",
        enrich_fn=enrich_origin,
        request=request,
    )
