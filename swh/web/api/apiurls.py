# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import functools
from typing import Dict, List, Optional

from typing_extensions import Literal

from django.http.response import HttpResponseBase
from rest_framework.decorators import api_view

from swh.web.api import throttling
from swh.web.api.apiresponse import make_api_response
from swh.web.utils.urlsindex import UrlsIndex

CategoryId = Literal[
    "Archive", "Batch download", "Metadata", "Request archival", "Miscellaneous", "test"
]


class APIUrls(UrlsIndex):
    """Class to manage API URLs and endpoint documentation URLs."""

    apidoc_routes: Dict[str, Dict[str, str]] = {}

    def get_app_endpoints(self) -> Dict[str, Dict[str, str]]:
        return self.apidoc_routes

    def add_doc_route(
        self,
        route: str,
        category: CategoryId,
        docstring: str,
        noargs: bool = False,
        api_version: str = "1",
        **kwargs,
    ) -> None:
        """
        Add a route to the self-documenting API reference
        """
        route_name = route[1:-1].replace("/", "-")
        if not noargs:
            route_name = "%s-doc" % route_name
        route_view_name = "api-%s-%s" % (api_version, route_name)
        if route not in self.apidoc_routes:
            d = {
                "category": category,
                "docstring": docstring,
                "route": "/api/%s%s" % (api_version, route),
                "route_view_name": route_view_name,
            }
            for k, v in kwargs.items():
                d[k] = v
            self.apidoc_routes[route] = d


api_urls = APIUrls()


def api_route(
    url_pattern: str,
    view_name: str,
    methods: List[str] = ["GET", "HEAD", "OPTIONS"],
    throttle_scope: str = "swh_api",
    api_version: str = "1",
    checksum_args: Optional[List[str]] = None,
    never_cache: bool = False,
    api_urls: APIUrls = api_urls,
):
    """
    Decorator to ease the registration of an API endpoint
    using the Django REST Framework.

    Args:
        url_pattern: the url pattern used by DRF to identify the API route
        view_name: the name of the API view associated to the route used to
           reverse the url
        methods: array of HTTP methods supported by the API route
        throttle_scope: Named scope for rate limiting
        api_version: web API version
        checksum_args: list of view argument names holding checksum values
        never_cache: define if api response must be cached

    """

    url_pattern = "^api/" + api_version + url_pattern + "$"

    def decorator(f):
        # create a DRF view from the wrapped function
        @api_view(methods)
        @throttling.throttle_scope(throttle_scope)
        @functools.wraps(f)
        def api_view_f(request, **kwargs):
            # never_cache will be handled in apiresponse module
            request.never_cache = never_cache
            response = f(request, **kwargs)
            doc_data = None
            # check if response has been forwarded by api_doc decorator
            if isinstance(response, dict) and "doc_data" in response:
                doc_data = response["doc_data"]
                response = response["data"]
            # check if HTTP response needs to be created
            if not isinstance(response, HttpResponseBase):
                api_response = make_api_response(
                    request, data=response, doc_data=doc_data
                )
            else:
                api_response = response

            return api_response

        # small hacks for correctly generating API endpoints index doc
        api_view_f.__name__ = f.__name__
        api_view_f.http_method_names = methods

        # register the route and its view in the endpoints index
        api_urls.add_url_pattern(url_pattern, api_view_f, view_name)

        if checksum_args:
            api_urls.add_redirect_for_checksum_args(
                view_name, [url_pattern], checksum_args
            )
        return f

    return decorator
