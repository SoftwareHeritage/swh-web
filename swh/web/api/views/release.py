# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common import service
from swh.web.api import utils
from swh.web.api import apidoc as api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import (
    _api_lookup, _doc_exc_id_not_found, _doc_exc_bad_id
)


@api_route(r'/release/(?P<sha1_git>[0-9a-f]+)/', 'release')
@api_doc.route('/release/')
@api_doc.arg('sha1_git',
             default='7045404f3d1c54e6473c71bbb716529fbad4be24',
             argtype=api_doc.argtypes.sha1_git,
             argdoc='release identifier')
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc='The metadata of the release identified by sha1_git')
def api_release(request, sha1_git):
    """Get information about a release.

    Releases are identified by SHA1 checksums, compatible with Git tag
    identifiers. See ``release_identifier`` in our `data model module
    <https://forge.softwareheritage.org/source/swh-model/browse/master/swh/model/identifiers.py>`_
    for details about how they are computed.

    """
    error_msg = 'Release with sha1_git %s not found.' % sha1_git
    return _api_lookup(
        service.lookup_release, sha1_git,
        notfound_msg=error_msg,
        enrich_fn=utils.enrich_release)
