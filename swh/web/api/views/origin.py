# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from distutils.util import strtobool
from functools import partial

from swh.web.common import service
from swh.web.common.exc import BadInputExc
from swh.web.common.origin_visits import get_origin_visits
from swh.web.common.utils import reverse
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.api.utils import enrich_origin, enrich_origin_visit
from swh.web.api.views.utils import api_lookup


DOC_RETURN_ORIGIN = """
        :>json string origin_visits_url: link to in order to get information
            about the visits for that origin
        :>json string url: the origin canonical url
"""

DOC_RETURN_ORIGIN_ARRAY = DOC_RETURN_ORIGIN.replace(":>json", ":>jsonarr")

DOC_RETURN_ORIGIN_VISIT = """
        :>json string date: ISO representation of the visit date (in UTC)
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
@api_doc("/origins/", noargs=True)
@format_docstring(return_origin_array=DOC_RETURN_ORIGIN_ARRAY)
def api_origins(request):
    """
    .. http:get:: /api/1/origins/

        Get list of archived software origins.

        .. warning::

            This endpoint used to provide an `origin_from` query parameter,
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

    page_result = service.lookup_origins(page_token, limit)
    origins = [enrich_origin(o, request=request) for o in page_result.results]
    next_page_token = page_result.next_page_token

    response = {"results": origins, "headers": {}}
    if next_page_token is not None:
        response["headers"]["link-next"] = reverse(
            "api-1-origins",
            query_params={"page_token": next_page_token, "origin_count": limit},
            request=request,
        )
    return response


@api_route(r"/origin/(?P<origin_url>.+)/get/", "api-1-origin")
@api_doc("/origin/")
@format_docstring(return_origin=DOC_RETURN_ORIGIN)
def api_origin(request, origin_url):
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
        service.lookup_origin,
        ori_dict,
        notfound_msg=error_msg,
        enrich_fn=enrich_origin,
        request=request,
    )


@api_route(
    r"/origin/search/(?P<url_pattern>.+)/",
    "api-1-origin-search",
    throttle_scope="swh_api_origin_search",
)
@api_doc("/origin/search/")
@format_docstring(return_origin_array=DOC_RETURN_ORIGIN_ARRAY)
def api_origin_search(request, url_pattern):
    """
    .. http:get:: /api/1/origin/search/(url_pattern)/

        Search for software origins whose urls contain a provided string
        pattern or match a provided regular expression.
        The search is performed in a case insensitive way.

        .. warning::

            This endpoint used to provide an `offset` query parameter,
            and guarantee an order on results. This is no longer true,
            and only the Link header should be used for paginating through
            results.

        :param string url_pattern: a string pattern
        :query int limit: the maximum number of found origins to return
            (bounded to 1000)
        :query boolean with_visit: if true, only return origins with at least
            one visit by Software heritage

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
    with_visit = request.query_params.get("with_visit", "false")

    (results, page_token) = api_lookup(
        service.search_origin,
        url_pattern,
        limit,
        bool(strtobool(with_visit)),
        page_token,
        enrich_fn=enrich_origin,
        request=request,
    )

    if page_token is not None:
        query_params = {}
        query_params["limit"] = limit
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
@api_doc("/origin/metadata-search/", noargs=True, need_params=True)
@format_docstring(return_origin_array=DOC_RETURN_ORIGIN_ARRAY)
def api_origin_metadata_search(request):
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

    if not fulltext:
        content = '"fulltext" must be provided and non-empty.'
        raise BadInputExc(content)

    results = api_lookup(
        service.search_origin_metadata, fulltext, limit, request=request
    )

    return {
        "results": results,
    }


@api_route(r"/origin/(?P<origin_url>.*)/visits/", "api-1-origin-visits")
@api_doc("/origin/visits/")
@format_docstring(return_origin_visit_array=DOC_RETURN_ORIGIN_VISIT_ARRAY)
def api_origin_visits(request, origin_url):
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
    origin_query = {"url": origin_url}
    notfound_msg = "No origin {} found".format(origin_url)
    url_args_next = {"origin_url": origin_url}
    per_page = int(request.query_params.get("per_page", "10"))
    last_visit = request.query_params.get("last_visit")
    if last_visit:
        last_visit = int(last_visit)

    def _lookup_origin_visits(origin_query, last_visit=last_visit, per_page=per_page):
        all_visits = get_origin_visits(origin_query)
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
    r"/origin/(?P<origin_url>.*)/visit/latest/",
    "api-1-origin-visit-latest",
    throttle_scope="swh_api_origin_visit_latest",
)
@api_doc("/origin/visit/latest/")
@format_docstring(return_origin_visit=DOC_RETURN_ORIGIN_VISIT)
def api_origin_visit_latest(request, origin_url=None):
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
        service.lookup_origin_visit_latest,
        origin_url,
        bool(strtobool(require_snapshot)),
        notfound_msg=("No visit for origin {} found".format(origin_url)),
        enrich_fn=partial(
            enrich_origin_visit, with_origin_link=True, with_origin_visit_link=False
        ),
        request=request,
    )


@api_route(
    r"/origin/(?P<origin_url>.*)/visit/(?P<visit_id>[0-9]+)/", "api-1-origin-visit"
)
@api_doc("/origin/visit/")
@format_docstring(return_origin_visit=DOC_RETURN_ORIGIN_VISIT)
def api_origin_visit(request, visit_id, origin_url):
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
        service.lookup_origin_visit,
        origin_url,
        int(visit_id),
        notfound_msg=("No visit {} for origin {} found".format(visit_id, origin_url)),
        enrich_fn=partial(
            enrich_origin_visit, with_origin_link=True, with_origin_visit_link=False
        ),
        request=request,
    )


@api_route(
    r"/origin/(?P<origin_url>.+)" "/intrinsic-metadata", "api-origin-intrinsic-metadata"
)
@api_doc("/origin/intrinsic-metadata/")
@format_docstring()
def api_origin_intrinsic_metadata(request, origin_url):
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
        service.lookup_origin_intrinsic_metadata,
        origin_url,
        notfound_msg=f"Origin with url {origin_url} not found",
        enrich_fn=enrich_origin,
        request=request,
    )
