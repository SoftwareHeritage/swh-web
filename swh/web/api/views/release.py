# Copyright (C) 2015-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from rest_framework.request import Request

from swh.web.api import utils
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import api_lookup
from swh.web.utils import archive


@api_route(
    r"/release/(?P<sha1_git>[0-9a-f]+)/", "api-1-release", checksum_args=["sha1_git"]
)
@api_doc("/release/", category="Archive")
@format_docstring()
def api_release(request: Request, sha1_git: str):
    """
    .. http:get:: /api/1/release/(sha1_git)/

        Get information about a release in the archive. Releases are identified
        by **sha1** checksums, compatible with Git tag identifiers. See
        :func:`swh.model.git_objects.release_git_object` in our data model
        module for details about how they are computed.

        :param string sha1_git: hexadecimal representation of the release
            **sha1_git** identifier

        {common_headers}

        :>json object author: information about the author of the release
        :>json string date: RFC3339 representation of the release date
        :>json string id: the release unique identifier
        :>json string message: the message associated to the release
        :>json string name: the name of the release
        :>json string target: the target identifier of the release
        :>json string target_type: the type of the target, can be either
            **release**, **revision**, **content**, **directory**
        :>json string target_url: a link to the adequate api url based on the
            target type

        :statuscode 200: no error
        :statuscode 400: an invalid **sha1_git** value has been provided
        :statuscode 404: requested release can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`release/208f61cc7a5dbc9879ae6e5c2f95891e270f09ef/`
    """
    error_msg = "Release with sha1_git %s not found." % sha1_git
    return api_lookup(
        archive.lookup_release,
        sha1_git,
        notfound_msg=error_msg,
        enrich_fn=utils.enrich_release,
        request=request,
    )
