# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import requests
import json

from swh.web.ui.main import app


if 'conf' in app.config:
    base_url = app.config['conf']['api_backend']


session_swh = requests.Session()


MIMETYPE = "application/json"


def compute_simple_url(base_url, api_url):
    """Compute the full api url from base_url and api_url.

    """
    return '%s%s' % (base_url, api_url)


query_dispatch = {
    'post': session_swh.post,
    'put': session_swh.put,
    'get': session_swh.get
}


def execute(base_url,
            query,
            result_fn=lambda result: result.ok):
    """Execute a query to the backend.

    Args:
        base_url: is the backend url to discuss with
        query: is the computed query to execute
        result_fn: is the function to execute on the query's response result

    Returns:
        The result of the query on which the result_fn has been applied

    Raises:
        None
    """
    print(query)
    method_fn = query_dispatch[query['method']]

    print(method_fn)
    res = method_fn(compute_simple_url(base_url, query['url']),
                    data=query.get('data'),
                    headers=query.get('headers'))

    return result_fn(res)



def create_request(method, api_url, data=None):
    """Create a request model without executing it.

    Args:
        - method (post, put, get)
        - base_url, the server's base url to ask for data
        - obj_type: the nature of data we are dealing with
        - data: the data to json serialize and send to server as body (could be None)
    """
    query = {'method': method,
             'url': api_url}
    if data:
        query.update({'data': json.dumps(data) if data else '',
                      'headers': {'Content-Type': MIMETYPE}})

    return query
