# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common import service
from swh.web.api import apidoc as api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import (
    _api_lookup, _doc_exc_id_not_found,
)


@api_route(r'/person/(?P<person_id>[0-9]+)/', 'person')
@api_doc.route('/person/')
@api_doc.arg('person_id',
             default=42,
             argtype=api_doc.argtypes.int,
             argdoc='person identifier')
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc='The metadata of the person identified by person_id')
def api_person(request, person_id):
    """Get information about a person.

    """
    return _api_lookup(
        service.lookup_person, person_id,
        notfound_msg='Person with id {} not found.'.format(person_id))
