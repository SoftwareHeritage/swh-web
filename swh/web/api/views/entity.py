# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common import service
from swh.web.api import utils
from swh.web.api import apidoc as api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import (
    _api_lookup, _doc_exc_id_not_found,
    _doc_exc_bad_id
)


@api_route(r'/entity/(?P<uuid>.+)/', 'entity')
@api_doc.route('/entity/', tags=['hidden'])
@api_doc.arg('uuid',
             default='5f4d4c51-498a-4e28-88b3-b3e4e8396cba',
             argtype=api_doc.argtypes.uuid,
             argdoc="The entity's uuid identifier")
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc='The metadata of the entity identified by uuid')
def api_entity_by_uuid(request, uuid):
    """Return content information if content is found.

    """
    return _api_lookup(
        service.lookup_entity_by_uuid, uuid,
        notfound_msg="Entity with uuid '%s' not found." % uuid,
        enrich_fn=utils.enrich_entity)
