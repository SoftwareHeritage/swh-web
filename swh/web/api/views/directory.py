# Copyright (C) 2015-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Optional

from rest_framework.request import Request

from swh.web.api import utils
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import api_lookup
from swh.web.utils import archive


@api_route(
    r"/directory/(?P<sha1_git>[0-9a-f]+)/",
    "api-1-directory",
    checksum_args=["sha1_git"],
)
@api_route(
    r"/directory/(?P<sha1_git>[0-9a-f]+)/(?P<path>.+)/",
    "api-1-directory",
    checksum_args=["sha1_git"],
)
@api_doc("/directory/", category="Archive")
@format_docstring()
def api_directory(request: Request, sha1_git: str, path: Optional[str] = None):
    """
    .. http:get:: /api/1/directory/(sha1_git)/[(path)/]

        Get information about directory objects.
        Directories are identified by **sha1** checksums, compatible with Git
        directory identifiers.
        See :func:`swh.model.git_objects.directory_git_object` in our data model
        module for details about how they are computed.

        When given only a directory identifier, this endpoint returns information
        about the directory itself, returning its content (usually a list of directory
        entries). When given a directory identifier and a path, this endpoint returns
        information about the directory entry pointed by the relative path, starting
        path resolution from the given directory.

        :param string sha1_git: hexadecimal representation of the directory
            **sha1_git** identifier
        :param string path: optional parameter to get information about the
            directory entry pointed by that relative path

        {common_headers}

        :>jsonarr object checksums: object holding the computed checksum values for
            a directory entry (only for file entries)
        :>jsonarr string dir_id: **sha1_git** identifier of the requested directory
        :>jsonarr number length: length of a directory entry in bytes (only for file
            entries) for getting information about the content MIME type
        :>jsonarr string name: the directory entry name
        :>jsonarr number perms: permissions for the directory entry
        :>jsonarr string target: **sha1_git** identifier of the directory entry
        :>jsonarr string target_url: link to
            :http:get:`/api/1/content/[(hash_type):](hash)/`
            or :http:get:`/api/1/directory/(sha1_git)/[(path)/]`
            depending on the directory entry type
        :>jsonarr string type: the type of the directory entry, can be either
            ``dir``, ``file`` or ``rev``

        :statuscode 200: no error
        :statuscode 400: an invalid **hash_type** or **hash** has been provided
        :statuscode 404: requested directory can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`directory/977fc4b98c0e85816348cebd3b12026407c368b6/`
    """
    if path:
        error_msg_path = (
            "Entry with path %s relative to directory " "with sha1_git %s not found."
        ) % (path, sha1_git)
        return api_lookup(
            archive.lookup_directory_with_path,
            sha1_git,
            path,
            notfound_msg=error_msg_path,
            enrich_fn=utils.enrich_directory_entry,
            request=request,
        )
    else:
        error_msg_nopath = "Directory with sha1_git %s not found." % sha1_git
        return api_lookup(
            archive.lookup_directory,
            sha1_git,
            notfound_msg=error_msg_nopath,
            enrich_fn=utils.enrich_directory_entry,
            request=request,
        )
