# Copyright (C) 2020-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.request import Request

from swh.web.api.apidoc import api_doc
from swh.web.api.apiurls import api_route


@api_route(r"/ping/", "api-1-ping")
@api_doc("/ping/", category="Miscellaneous", noargs=True)
def ping(request: Request):
    """
    .. http:get:: /api/1/ping/

        A simple endpoint used to check if the API is working.

    :statuscode 200: no error

    """
    return "pong"
