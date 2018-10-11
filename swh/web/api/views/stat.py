# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common import service
from swh.web.api.apidoc import api_doc
from swh.web.api.apiurls import api_route


@api_route(r'/stat/counters/', 'stat-counters')
@api_doc('/stat/counters/', noargs=True)
def api_stats(request):
    """
    .. http:get:: /api/1/stat/counters/

        Get statistics about the content of the archive.

        :>json number content: current number of content objects (aka files) in the SWH archive
        :>json number directory: current number of directory objects in the SWH archive
        :>json number directory_entry_dir: current number of SWH directory entries
            pointing to others SWH directories in the SWH archive
        :>json number directory_entry_file: current number of SWH directory entries
            pointing to SWH content objects in the SWH archive
        :>json number directory_entry_rev: current number of SWH directory entries
            pointing to SWH revision objects (e.g. git submodules) in the SWH archive
        :>json number entity: current number of SWH entities (a SWH entity is either
            a *group_of_entities*, a *group_of_persons*, a *project*, a *person*, an *organization*,
            or a *hosting* service) in the SWH archive
        :>json number origin: current number of SWH origins (an origin is a "place" where code
            source can be found, e.g. a git repository, a tarball, ...) in the SWH archive
        :>json number person: current number of SWH persons (code source authors or committers)
            in the SWH archive
        :>json number release: current number of SWH releases objects in the SWH archive
        :>json number revision: current number of SWH revision objects (aka commits) in the SWH archive
        :>json number skipped_content: current number of content objects (aka files) which where
            not inserted in the SWH archive

        :reqheader Accept: the requested response content type,
            either *application/json* (default) or *application/yaml*
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`stat/counters/`
    """ # noqa
    return service.stat_counters()
