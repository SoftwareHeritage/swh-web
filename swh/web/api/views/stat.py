# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.common import archive


@api_route(r"/stat/counters/", "api-1-stat-counters")
@api_doc("/stat/counters/", noargs=True)
@format_docstring()
def api_stats(request):
    """
    .. http:get:: /api/1/stat/counters/

        Get statistics about the content of the archive.

        :>json number content: current number of content objects (aka files)
            in the archive
        :>json number directory: current number of directory objects
            in the archive
        :>json number origin: current number of software origins
            (an origin is a "place" where code source can be found, e.g. a git
            repository, a tarball, ...) in the archive
        :>json number origin_visit: current number of visits on software
            origins to fill the archive
        :>json number person: current number of persons (code source authors
            or committers) in the archive
        :>json number release: current number of releases objects in the
            archive
        :>json number revision: current number of revision objects
            (aka commits) in the archive
        :>json number skipped_content: current number of content objects
            (aka files) which where not inserted in the archive
        :>json number snapshot: current number of snapshot objects
            (aka set of named branches) in the archive

        {common_headers}

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`stat/counters/`
    """
    return archive.stat_counters()
