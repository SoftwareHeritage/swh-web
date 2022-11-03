# Copyright (C) 2015-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from types import GeneratorType
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from django.http import HttpRequest
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

from swh.web.api.apiurls import api_route, api_urls
from swh.web.utils.exc import NotFoundExc

EnrichFunction = Callable[[Dict[str, str], Optional[HttpRequest]], Dict[str, str]]

EnrichFunctionSearchResult = Callable[
    [Tuple[List[Dict[str, Any]], Optional[str]], Optional[HttpRequest]],
    Tuple[List[Dict[str, Any]], Optional[str]],
]


def api_lookup(
    lookup_fn: Callable[..., Any],
    *args: Any,
    notfound_msg: Optional[str] = "Object not found",
    enrich_fn: Optional[Union[EnrichFunction, EnrichFunctionSearchResult]] = None,
    request: Optional[HttpRequest] = None,
    **kwargs: Any,
):
    r"""
    Capture a redundant behavior of:
        - looking up the backend with a criteria (be it an identifier or
          checksum) passed to the function lookup_fn
        - if nothing is found, raise an NotFoundExc exception with error
          message notfound_msg.
        - Otherwise if something is returned:
            - either as list, map or generator, map the enrich_fn function to
              it and return the resulting data structure as list.
            - either as dict and pass to enrich_fn and return the dict
              enriched.

    Args:
        - lookup_fn: function expects one criteria and optional supplementary
          \*args.
        - \*args: supplementary arguments to pass to lookup_fn.
        - notfound_msg: if nothing matching the criteria is found,
          raise NotFoundExc with this error message.
        - enrich_fn: Function to use to enrich the result returned by
          lookup_fn. Default to the identity function if not provided.
        - request: Input HTTP request that will be provided as parameter
          to enrich_fn.


    Raises:
        NotFoundExp or whatever `lookup_fn` raises.

    """

    def _enrich_fn_noop(x, request):
        return x

    if enrich_fn is None:
        enrich_fn = _enrich_fn_noop
    res = lookup_fn(*args, **kwargs)
    if res is None:
        raise NotFoundExc(notfound_msg)
    if isinstance(res, (list, GeneratorType)) or type(res) == map:
        return [enrich_fn(x, request) for x in res]
    return enrich_fn(res, request)


@api_view(["GET", "HEAD"])
def api_home(request: Request):
    return Response({}, template_name="api.html")


api_urls.add_url_pattern(r"^api/$", api_home, view_name="api-1-homepage")


@api_route(r"/", "api-1-endpoints")
def api_endpoints(request):
    """Display the list of opened api endpoints."""
    routes_by_category = {}
    for route, doc in api_urls.get_app_endpoints().items():
        doc["doc_intro"] = doc["docstring"].split("\n\n")[0]
        routes_by_category.setdefault(doc["category"], []).append(doc)

    for routes in routes_by_category.values():
        routes.sort(key=lambda route: route["route"])

    # sort routes by alphabetical category name, with 'miscellaneous' at the end
    misc_routes = routes_by_category.pop("Miscellaneous")
    sorted_routes = sorted(routes_by_category.items())
    sorted_routes.append(("Miscellaneous", misc_routes))

    env = {"doc_routes": sorted_routes}
    return Response(env, template_name="api-endpoints.html")
