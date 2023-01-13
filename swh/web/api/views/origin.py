# Copyright (C) 2015-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from distutils.util import strtobool
from functools import partial
from typing import Dict

from rest_framework.request import Request

from swh.search.exc import SearchQuerySyntaxError
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.api.utils import (
    enrich_origin,
    enrich_origin_search_result,
    enrich_origin_visit,
)
from swh.web.api.views.utils import api_lookup
from swh.web.utils import archive, origin_visit_types, reverse
from swh.web.utils.exc import BadInputExc
from swh.web.utils.origin_visits import get_origin_visits
from swh.web.utils.typing import OriginInfo

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

DOC_RETURN_ORIGIN_VISIT = """
        :>json string date: ISO8601/RFC3339 representation of the visit date (in UTC)
        :>json str origin: the origin canonical url
        :>json string origin_url: link to get information about the origin
        :>jsonarr string snapshot: the snapshot identifier of the visit
            (may be null if status is not **full**).
        :>jsonarr string snapshot_url: link to
            :http:get:`/api/1/snapshot/(snapshot_id)/` in order to get
            information about the snapshot of the visit
            (may be null if status is not **full**).
        :>json string status: status of the visit (either **full**,
            **partial** or **ongoing**)
        :>json number visit: the unique identifier of the visit
"""

DOC_RETURN_ORIGIN_VISIT_ARRAY = DOC_RETURN_ORIGIN_VISIT.replace(":>json", ":>jsonarr")

DOC_RETURN_ORIGIN_VISIT_ARRAY += """
        :>jsonarr number id: the unique identifier of the origin
        :>jsonarr string origin_visit_url: link to
            :http:get:`/api/1/origin/(origin_url)/visit/(visit_id)/`
            in order to get information about the visit
"""


@api_route(r"/origins/", "api-1-origins")
@api_doc("/origins/", category="Archive", noargs=True)
@format_docstring(return_origin_array=DOC_RETURN_ORIGIN_ARRAY)
def api_origins(request: Request):
    """
    .. http:get:: /api/1/origins/

        Get list of archived software origins.

        .. warning::

            This endpoint used to provide an ``origin_from`` query parameter,
            and guarantee an order on results. This is no longer true,
            and only the Link header should be used for paginating through
            results.

        :query int origin_count: The maximum number of origins to return
            (default to 100, can not exceed 10000)

        {return_origin_array}

        {common_headers}
        {resheader_link}

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origins?origin_count=500`

    """
    old_param_origin_from = request.query_params.get("origin_from")

    if old_param_origin_from:
        raise BadInputExc("Please use the Link header to browse through result")

    page_token = request.query_params.get("page_token", None)
    limit = min(int(request.query_params.get("origin_count", "100")), 10000)

    page_result = archive.lookup_origins(page_token, limit)
    origins = [enrich_origin(o, request=request) for o in page_result.results]
    next_page_token = page_result.next_page_token

    headers: Dict[str, str] = {}
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
        :statuscode 404: requested origin can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/https://github.com/python/cpython/get/`

    """
    ori_dict = {"url": origin_url}

    error_msg = "Origin with url %s not found." % ori_dict["url"]

    return api_lookup(
        archive.lookup_origin,
        ori_dict,
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


@api_route(
    r"/origin/search/(?P<url_pattern>.*)/",
    "api-1-origin-search",
    throttle_scope="swh_api_origin_search",
)
@api_doc("/origin/search/", category="Archive")
@format_docstring(
    return_origin_array=DOC_RETURN_ORIGIN_ARRAY, visit_types=_visit_types()
)
def api_origin_search(request: Request, url_pattern: str):
    """
    .. http:get:: /api/1/origin/search/(url_pattern)/

        Search for software origins whose urls contain a provided string
        pattern or match a provided regular expression.
        The search is performed in a case insensitive way.

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

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/search/python/?limit=2`
    """
    result = {}
    limit = min(int(request.query_params.get("limit", "70")), 1000)
    page_token = request.query_params.get("page_token")
    use_ql = request.query_params.get("use_ql", "false")
    with_visit = request.query_params.get("with_visit", "false")
    visit_type = request.query_params.get("visit_type")

    try:
        (results, page_token) = api_lookup(
            archive.search_origin,
            url_pattern,
            bool(strtobool(use_ql)),
            limit,
            bool(strtobool(with_visit)),
            [visit_type] if visit_type else None,
            page_token,
            enrich_fn=enrich_origin_search_result,
            request=request,
        )
    except SearchQuerySyntaxError as e:
        raise BadInputExc(f"Syntax error in search query: {e.args[0]}")

    if page_token is not None:
        query_params = {k: v for (k, v) in request.GET.dict().items()}
        query_params["page_token"] = page_token

        result["headers"] = {
            "link-next": reverse(
                "api-1-origin-search",
                url_args={"url_pattern": url_pattern},
                query_params=query_params,
                request=request,
            )
        }

    result.update({"results": results})

    return result


@api_route(r"/origin/metadata-search/", "api-1-origin-metadata-search")
@api_doc("/origin/metadata-search/", category="Metadata", noargs=True)
@format_docstring(return_origin_array=DOC_RETURN_ORIGIN_ARRAY)
def api_origin_metadata_search(request: Request):
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

            :swh_web_api:`origin/metadata-search/?limit=2&fulltext=Jane%20Doe`
    """
    fulltext = request.query_params.get("fulltext", None)
    limit = min(int(request.query_params.get("limit", "70")), 100)
    fields = request.query_params.get("fields")
    if not fulltext:
        content = '"fulltext" must be provided and non-empty.'
        raise BadInputExc(content)

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


@api_route(r"/origin/(?P<origin_url>.+)/visits/", "api-1-origin-visits")
@api_doc("/origin/visits/", category="Archive")
@format_docstring(return_origin_visit_array=DOC_RETURN_ORIGIN_VISIT_ARRAY)
def api_origin_visits(request: Request, origin_url: str):
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
        :statuscode 404: requested origin can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/https://github.com/hylang/hy/visits/`

    """
    result = {}
    origin_query = OriginInfo(url=origin_url)
    notfound_msg = "No origin {} found".format(origin_url)
    url_args_next = {"origin_url": origin_url}
    per_page = int(request.query_params.get("per_page", "10"))
    last_visit_str = request.query_params.get("last_visit")
    last_visit = int(last_visit_str) if last_visit_str else None

    def _lookup_origin_visits(origin_query, last_visit=last_visit, per_page=per_page):
        all_visits = get_origin_visits(origin_query, lookup_similar_urls=False)
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
        origin_query,
        notfound_msg=notfound_msg,
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
                    url_args=url_args_next,
                    query_params=query_params,
                    request=request,
                )
            }

    result.update({"results": results})

    return result


@api_route(
    r"/origin/(?P<origin_url>.+)/visit/latest/",
    "api-1-origin-visit-latest",
    throttle_scope="swh_api_origin_visit_latest",
)
@api_doc("/origin/visit/latest/", category="Archive")
@format_docstring(return_origin_visit=DOC_RETURN_ORIGIN_VISIT)
def api_origin_visit_latest(request: Request, origin_url: str):
    """
    .. http:get:: /api/1/origin/(origin_url)/visit/latest/

        Get information about the latest visit of a software origin.

        :param str origin_url: a software origin URL
        :query boolean require_snapshot: if true, only return a visit
            with a snapshot

        {common_headers}

        {return_origin_visit}

        :statuscode 200: no error
        :statuscode 404: requested origin or visit can not be found in the
            archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/https://github.com/hylang/hy/visit/latest/`
    """

    require_snapshot = request.query_params.get("require_snapshot", "false")
    return api_lookup(
        archive.lookup_origin_visit_latest,
        origin_url,
        bool(strtobool(require_snapshot)),
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
        :statuscode 404: requested origin or visit can not be found in the
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
    r"/origin/(?P<origin_url>.+)/intrinsic-metadata/", "api-origin-intrinsic-metadata"
)
@api_doc("/origin/intrinsic-metadata/", category="Metadata")
@format_docstring()
def api_origin_intrinsic_metadata(request: Request, origin_url: str):
    """
    .. http:get:: /api/1/origin/(origin_url)/intrinsic-metadata

        Get intrinsic metadata of a software origin (as a JSON-LD/CodeMeta dictionary).

        :param string origin_url: the origin url

        :>json string ???: intrinsic metadata field of the origin

        {common_headers}

        :statuscode 200: no error
        :statuscode 404: requested origin can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/https://github.com/python/cpython/intrinsic-metadata`
    """
    return api_lookup(
        archive.lookup_origin_intrinsic_metadata,
        origin_url,
        notfound_msg=f"Origin with url {origin_url} not found",
        enrich_fn=enrich_origin,
        request=request,
    )
