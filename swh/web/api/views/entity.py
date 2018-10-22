# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common import service
from swh.web.api import utils
from swh.web.api.apidoc import api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import api_lookup


@api_route(r'/entity/(?P<uuid>.+)/', 'api-entity')
@api_doc('/entity/', tags=['hidden'])
def api_entity_by_uuid(request, uuid):
    """Return content information if content is found.

    """
    return api_lookup(
        service.lookup_entity_by_uuid, uuid,
        notfound_msg="Entity with uuid '%s' not found." % uuid,
        enrich_fn=utils.enrich_entity)
