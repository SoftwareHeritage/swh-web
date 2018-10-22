# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.response import Response
from rest_framework.decorators import api_view

from types import GeneratorType

from swh.web.common.exc import NotFoundExc
from swh.web.api.apiurls import APIUrls, api_route


def api_lookup(lookup_fn, *args,
               notfound_msg='Object not found',
               enrich_fn=None):
    """
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
        - notfound_msg: if nothing matching the criteria is found,
          raise NotFoundExc with this error message.
        - enrich_fn: Function to use to enrich the result returned by
          lookup_fn. Default to the identity function if not provided.
        - \*args: supplementary arguments to pass to lookup_fn.

    Raises:
        NotFoundExp or whatever `lookup_fn` raises.

    """ # noqa
    if enrich_fn is None:
        enrich_fn = (lambda x: x)
    res = lookup_fn(*args)
    if not res:
        raise NotFoundExc(notfound_msg)
    if isinstance(res, (map, list, GeneratorType)):
        return [enrich_fn(x) for x in res]
    return enrich_fn(res)


@api_view(['GET', 'HEAD'])
def api_home(request):
    return Response({}, template_name='api/api.html')


APIUrls.add_url_pattern(r'^$', api_home, view_name='api-homepage')


@api_route(r'/', 'api-endpoints')
def api_endpoints(request):
    """Display the list of opened api endpoints.

    """
    routes = APIUrls.get_app_endpoints().copy()
    for route, doc in routes.items():
        doc['doc_intro'] = doc['docstring'].split('\n\n')[0]
    # Return a list of routes with consistent ordering
    env = {
        'doc_routes': sorted(routes.items())
    }
    return Response(env, template_name="api/endpoints.html")
