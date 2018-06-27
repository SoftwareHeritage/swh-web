# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common import service
from swh.web.api.apidoc import api_doc
from swh.web.api import utils
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import api_lookup


@api_route(r'/snapshot/(?P<snapshot_id>[0-9a-f]+)/', 'snapshot')
@api_doc('/snapshot/')
def api_snapshot(request, snapshot_id):
    """
    .. http:get:: /api/1/snapshot/(snapshot_id)/

        Get information about a snapshot in the SWH archive.

        A snapshot is a set of named branches, which are pointers to objects at any
        level of the Software Heritage DAG. It represents a full picture of an
        origin at a given time.

        As well as pointing to other objects in the Software Heritage DAG, branches
        can also be aliases, in which case their target is the name of another
        branch in the same snapshot, or dangling, in which case the target is
        unknown.

        A snapshot identifier is a salted sha1. See :func:`swh.model.identifiers.snapshot_identifier`
        in our data model module for details about how they are computed.

        :param sha1 snapshot_id: a SWH snapshot identifier

        :reqheader Accept: the requested response content type,
            either *application/json* (default) or *application/yaml*
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        :>json object branches: object containing all branches associated to the snapshot,
            for each of them the associated SWH target type and id are given but also
            a link to get information about that target
        :>json string id: the unique identifier of the snapshot

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 400: an invalid snapshot identifier has been provided
        :statuscode 404: requested snapshot can not be found in the SWH archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`snapshot/6a3a2cf0b2b90ce7ae1cf0a221ed68035b686f5a/`
    """ # noqa

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
