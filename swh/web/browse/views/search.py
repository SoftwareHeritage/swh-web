# Copyright (C) 2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import hashlib
from urllib.parse import urlparse, urlunparse

from django_ratelimit.decorators import ratelimit

from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, QueryDict
from django.shortcuts import render

from swh.web.utils import (
    archive,
    cache_get,
    cache_set,
    origin_visit_types,
    reverse,
    strtobool,
)
from swh.web.utils.identifiers import resolve_swhid


@ratelimit(key="user_or_ip", rate="60/m")
def browse_search_view(request: HttpRequest) -> HttpResponse:
    origins: list = []
    total_results: int | None = -1
    previous_page_url = None
    next_page_url = None
    if "no_js" in request.GET:
        # apply same client side processing when javascript is disabled

        # get search parameter values
        query = request.GET.get("q", "").strip()
        with_visit = strtobool(request.GET.get("with_visit", "on"))
        with_content = strtobool(request.GET.get("with_content", "on"))
        visit_type = request.GET.get("visit_type", "any")
        use_ql = strtobool(request.GET.get("use_ql", "off"))
        search_in_metadata = strtobool(request.GET.get("search_in_metadata", "off"))
        page_token = request.GET.get("page_token")
        prev_page_token = None
        next_page_token = None
        limit = 100

        # if a SWHID is provided, try to resolve it and redirect to object page
        if query.startswith("swh:"):
            swhid_resolved = resolve_swhid(query)
            if swhid_resolved["browse_url"]:
                return HttpResponseRedirect(swhid_resolved["browse_url"])

        # if an origin URL is provided and is archived, redirect to its browsing page
        try:
            if origin_info := archive.lookup_origin_visit_latest(
                query,
                require_snapshot=True,
                type=visit_type if visit_type != "any" else None,
            ):
                return HttpResponseRedirect(
                    reverse(
                        "browse-origin",
                        query_params={"origin_url": origin_info["origin"]},
                    )
                )
        except Exception:
            pass

        if search_in_metadata:
            origins = list(
                archive.search_origin_metadata(
                    query,
                    limit,
                    return_metadata=False,
                )
            )
        else:
            origins, next_page_token, total_results = archive.search_origin(
                url_pattern=query,
                use_ql=use_ql,
                limit=limit,
                with_visit=with_visit,
                with_content=with_content,
                visit_types=[visit_type] if visit_type not in (None, "any") else None,
                page_token=page_token,
            )
            total_results = total_results or 0

        # cache page tokens for previous and next links
        key = "origin_search" + "_".join(
            map(str, [query, with_visit, with_content, visit_type, use_ql, limit])
        )
        cache_key = hashlib.md5(key.encode()).hexdigest()
        page_tokens = cache_get(cache_key) or []
        if next_page_token and (not page_tokens or page_tokens[-1] == page_token):
            page_tokens.append(next_page_token)
        cache_set(cache_key, page_tokens)

        # compute previous and next links if any
        current_url = request.build_absolute_uri()
        parsed_url = urlparse(current_url)
        query_dict = QueryDict(parsed_url.query, mutable=True)

        if page_token:
            pos = page_tokens.index(page_token)
            if pos > 0:
                prev_page_token = page_tokens[pos - 1]
                query_dict["page_token"] = prev_page_token
                previous_page_url = urlunparse(
                    parsed_url._replace(query=query_dict.urlencode(safe="/;:"))
                )
            elif pos == 0:
                query_dict.pop("page_token", None)
                previous_page_url = urlunparse(
                    parsed_url._replace(query=query_dict.urlencode(safe="/;:"))
                )

        if next_page_token:
            query_dict["page_token"] = next_page_token
            next_page_url = urlunparse(
                parsed_url._replace(query=query_dict.urlencode(safe="/;:"))
            )

    return render(
        request,
        "browse-search.html",
        {
            "heading": "Search software origins to browse",
            "visit_types": origin_visit_types(use_cache=True),
            "total_results": total_results,
            "origins": origins,
            "previous_page_url": previous_page_url,
            "next_page_url": next_page_url,
        },
    )
