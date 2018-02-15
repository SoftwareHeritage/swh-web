# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common import service
from swh.web.api import utils
from swh.web.api import apidoc as api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import (
    api_lookup, doc_exc_id_not_found,
    doc_exc_bad_id,
)


@api_route(r'/directory/(?P<sha1_git>[0-9a-f]+)/', 'directory')
@api_route(r'/directory/(?P<sha1_git>[0-9a-f]+)/(?P<path>.+)/', 'directory')
@api_doc.route('/directory/')
@api_doc.arg('sha1_git',
             default='1bd0e65f7d2ff14ae994de17a1e7fe65111dcad8',
             argtype=api_doc.argtypes.sha1_git,
             argdoc='directory identifier')
@api_doc.arg('path',
             default='codec/demux',
             argtype=api_doc.argtypes.path,
             argdoc='path relative to directory identified by sha1_git')
@api_doc.raises(exc=api_doc.excs.badinput, doc=doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""either a list of directory entries with their metadata,
                        or the metadata of a single directory entry""")
def api_directory(request, sha1_git, path=None):
    """Get information about directory or directory entry objects.

    Directories are identified by SHA1 checksums, compatible with Git directory
    identifiers. See the `documentation
    <https://docs.softwareheritage.org/devel/swh-model/apidoc/swh.model.html#swh.model.identifiers.directory_identifier>`_
    for details about how they are computed.

    When given only a directory identifier, this endpoint returns information
    about the directory itself, returning its content (usually a list of
    directory entries). When given a directory identifier and a path, this
    endpoint returns information about the directory entry pointed by the
    relative path, starting path resolution from the given directory.

    """
    if path:
        error_msg_path = ('Entry with path %s relative to directory '
                          'with sha1_git %s not found.') % (path, sha1_git)
        return api_lookup(
            service.lookup_directory_with_path, sha1_git, path,
            notfound_msg=error_msg_path,
            enrich_fn=utils.enrich_directory)
    else:
        error_msg_nopath = 'Directory with sha1_git %s not found.' % sha1_git
        return api_lookup(
            service.lookup_directory, sha1_git,
            notfound_msg=error_msg_nopath,
            enrich_fn=utils.enrich_directory)
