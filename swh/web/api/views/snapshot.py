# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common import service
from swh.web.api import apidoc as api_doc
from swh.web.api import utils
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import (
    api_lookup, doc_exc_id_not_found, doc_exc_bad_id
)


@api_route(r'/snapshot/(?P<snapshot_id>[0-9a-f]+)/', 'snapshot')
@api_doc.route('/snapshot/')
@api_doc.arg('snapshot_id',
             default='584b2fe3ce6218a96892e73bd76c2966bbc2a797',
             argtype=api_doc.argtypes.sha1,
             argdoc='snapshot identifier')
@api_doc.raises(exc=api_doc.excs.badinput, doc=doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc='dictionnary referencing the different'
                        ' named branches the snapshot contains')
def api_snapshot(request, snapshot_id):
    """Get information about a snapshot.

    A snapshot is a set of named branches, which are pointers to objects at any
    level of the Software Heritage DAG. It represents a full picture of an
    origin at a given time.

    As well as pointing to other objects in the Software Heritage DAG, branches
    can also be aliases, in which case their target is the name of another
    branch in the same snapshot, or dangling, in which case the target is
    unknown.

    A snapshot identifier is a salted sha1. See the `documentation
    <https://docs.softwareheritage.org/devel/swh-model/apidoc/swh.model.html#swh.model.identifiers.snapshot_identifier>`_
    for details about how they are computed.
    """

    def _enrich_snapshot(snapshot):
        s = snapshot.copy()
        if 'branches' in s:
            s['branches'] = {
                k: utils.enrich_object(v) if v else None
                for k, v in s['branches'].items()
            }
        return s

    return api_lookup(
        service.lookup_snapshot, snapshot_id,
        notfound_msg='Snapshot with id {} not found.'.format(snapshot_id),
        enrich_fn=_enrich_snapshot)
