# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common import service
from swh.web.common.utils import reverse
from swh.web.config import get_config
from swh.web.api.apidoc import api_doc
from swh.web.api import utils
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import api_lookup


@api_route(r'/snapshot/(?P<snapshot_id>[0-9a-f]+)/', 'api-snapshot')
@api_doc('/snapshot/')
def api_snapshot(request, snapshot_id):
    """
    .. http:get:: /api/1/snapshot/(snapshot_id)/

        Get information about a snapshot in the archive.

        A snapshot is a set of named branches, which are pointers to objects at any
        level of the Software Heritage DAG. It represents a full picture of an
        origin at a given time.

        As well as pointing to other objects in the Software Heritage DAG, branches
        can also be aliases, in which case their target is the name of another
        branch in the same snapshot, or dangling, in which case the target is
        unknown.

        A snapshot identifier is a salted sha1. See :func:`swh.model.identifiers.snapshot_identifier`
        in our data model module for details about how they are computed.

        :param sha1 snapshot_id: a snapshot identifier
        :query str branches_from: optional parameter used to skip branches
            whose name is lesser than it before returning them
        :query int branches_count: optional parameter used to restrain
            the amount of returned branches (default to 1000)
        :query str target_types: optional comma separated list parameter
            used to filter the target types of branch to return (possible values
            that can be contained in that list are ``content``, ``directory``,
            ``revision``, ``release``, ``snapshot`` or ``alias``)

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request
        :resheader Link: indicates that a subsequent result page is available and contains
            the url pointing to it

        :>json object branches: object containing all branches associated to the snapshot,
            for each of them the associated target type and id are given but also
            a link to get information about that target
        :>json string id: the unique identifier of the snapshot

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 400: an invalid snapshot identifier has been provided
        :statuscode 404: requested snapshot can not be found in the archive

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
            for k, v in s['branches'].items():
                if v and v['target_type'] == 'alias':
                    if v['target'] in s['branches']:
                        branch_alias = s['branches'][v['target']]
                        v['target_url'] = branch_alias['target_url']
                    else:
                        snp = \
                            service.lookup_snapshot(s['id'],
                                                    branches_from=v['target'],
                                                    branches_count=1)
                        if snp and v['target'] in snp['branches']:
                            branch = snp['branches'][v['target']]
                            branch = utils.enrich_object(branch)
                            v['target_url'] = branch['target_url']
        return s

    snapshot_content_max_size = get_config()['snapshot_content_max_size']

    branches_from = request.GET.get('branches_from', '')
    branches_count = int(request.GET.get('branches_count',
                                         snapshot_content_max_size))
    target_types = request.GET.get('target_types', None)
    target_types = target_types.split(',') if target_types else None

    results = api_lookup(
        service.lookup_snapshot, snapshot_id, branches_from,
        branches_count+1, target_types,
        notfound_msg='Snapshot with id {} not found.'.format(snapshot_id),
        enrich_fn=_enrich_snapshot)

    next_branch = None
    if len(results['branches']) > branches_count:
        next_branch = sorted(results['branches'].keys())[-1]
        del results['branches'][next_branch]

    response = {'results': results, 'headers': {}}

    if next_branch:
        response['headers']['link-next'] = \
            reverse('api-snapshot',
                    url_args={'snapshot_id': snapshot_id},
                    query_params={'branches_from': next_branch,
                                  'branches_count': branches_count,
                                  'target_types': target_types})

    return response
