# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.api import service
from swh.web.api import apidoc as api_doc
from swh.web.api.apiurls import api_route


@api_route(r'/stat/counters/', 'stat-counters')
@api_doc.route('/stat/counters/', noargs=True)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""dictionary mapping object types to the amount of
                 corresponding objects currently available in the archive""")
def api_stats(request):
    """Get statistics about the content of the archive.

    """
    return service.stat_counters()
