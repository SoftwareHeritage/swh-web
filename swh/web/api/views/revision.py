# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import HttpResponse

from swh.web.common import service
from swh.web.api import utils
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import api_lookup


DOC_RETURN_REVISION = """
        :>json object author: information about the author of the revision
        :>json object committer: information about the committer of the
            revision
        :>json string committer_date: ISO representation of the commit date
            (in UTC)
        :>json string date: ISO representation of the revision date (in UTC)
        :>json string directory: the unique identifier that revision points to
        :>json string directory_url: link to
            :http:get:`/api/1/directory/(sha1_git)/[(path)/]` to get
            information about the directory associated to the revision
        :>json string id: the revision unique identifier
        :>json boolean merge: whether or not the revision corresponds to a
            merge commit
        :>json string message: the message associated to the revision
        :>json array parents: the parents of the revision, i.e. the previous
            revisions that head directly to it, each entry of that array
            contains an unique parent revision identifier but also a link to
            :http:get:`/api/1/revision/(sha1_git)/` to get more information
            about it
        :>json string type: the type of the revision
"""

DOC_RETURN_REVISION_ARRAY = DOC_RETURN_REVISION.replace(":>json", ":>jsonarr")


def _revision_directory_by(revision, path, request_path, limit=100, with_data=False):
    """
    Compute the revision matching criterion's directory or content data.

    Args:
        revision: dictionary of criterions representing a revision to lookup
        path: directory's path to lookup
        request_path: request path which holds the original context to
        limit: optional query parameter to limit the revisions log
        (default to 100). For now, note that this limit could impede the
        transitivity conclusion about sha1_git not being an ancestor of
        with_data: indicate to retrieve the content's raw data if path resolves
        to a content.

    """

    def enrich_directory_local(dir, context_url=request_path):
        return utils.enrich_directory(dir, context_url)

    rev_id, result = service.lookup_directory_through_revision(
        revision, path, limit=limit, with_data=with_data
    )

    content = result["content"]
    if result["type"] == "dir":  # dir_entries
        result["content"] = list(map(enrich_directory_local, content))
    elif result["type"] == "file":  # content
        result["content"] = utils.enrich_content(content)
    elif result["type"] == "rev":  # revision
        result["content"] = utils.enrich_revision(content)

    return result


@api_route(
    r"/revision/(?P<sha1_git>[0-9a-f]+)/", "api-1-revision", checksum_args=["sha1_git"]
)
@api_doc("/revision/")
@format_docstring(return_revision=DOC_RETURN_REVISION)
def api_revision(request, sha1_git):
    """
    .. http:get:: /api/1/revision/(sha1_git)/

        Get information about a revision in the archive. Revisions are
        identified by **sha1** checksums, compatible with Git commit
        identifiers.
        See :func:`swh.model.identifiers.revision_identifier` in our data model
        module for details about how they are computed.

        :param string sha1_git: hexadecimal representation of the revision
            **sha1_git** identifier

        {common_headers}

        {return_revision}

        :statuscode 200: no error
        :statuscode 400: an invalid **sha1_git** value has been provided
        :statuscode 404: requested revision can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`revision/aafb16d69fd30ff58afdd69036a26047f3aebdc6/`
    """
    return api_lookup(
        service.lookup_revision,
        sha1_git,
        notfound_msg="Revision with sha1_git {} not found.".format(sha1_git),
        enrich_fn=utils.enrich_revision,
        request=request,
    )


@api_route(
    r"/revision/(?P<sha1_git>[0-9a-f]+)/raw/",
    "api-1-revision-raw-message",
    checksum_args=["sha1_git"],
)
@api_doc("/revision/raw/", tags=["hidden"], handle_response=True)
def api_revision_raw_message(request, sha1_git):
    """Return the raw data of the message of revision identified by sha1_git
    """
    raw = service.lookup_revision_message(sha1_git)
    response = HttpResponse(raw["message"], content_type="application/octet-stream")
    response["Content-disposition"] = "attachment;filename=rev_%s_raw" % sha1_git
    return response


@api_route(
    r"/revision/(?P<sha1_git>[0-9a-f]+)/directory/",
    "api-1-revision-directory",
    checksum_args=["sha1_git"],
)
@api_route(
    r"/revision/(?P<sha1_git>[0-9a-f]+)/directory/(?P<dir_path>.+)/",
    "api-1-revision-directory",
    checksum_args=["sha1_git"],
)
@api_doc("/revision/directory/")
@format_docstring()
def api_revision_directory(request, sha1_git, dir_path=None, with_data=False):
    """
    .. http:get:: /api/1/revision/(sha1_git)/directory/[(path)/]

        Get information about directory (entry) objects associated to revisions.
        Each revision is associated to a single "root" directory.
        This endpoint behaves like :http:get:`/api/1/directory/(sha1_git)/[(path)/]`,
        but operates on the root directory associated to a given revision.

        :param string sha1_git: hexadecimal representation of the revision
            **sha1_git** identifier
        :param string path: optional parameter to get information about the
            directory entry pointed by that relative path

        {common_headers}

        :>json array content: directory entries as returned by
            :http:get:`/api/1/directory/(sha1_git)/[(path)/]`
        :>json string path: path of directory from the revision root one
        :>json string revision: the unique revision identifier
        :>json string type: the type of the directory

        :statuscode 200: no error
        :statuscode 400: an invalid **sha1_git** value has been provided
        :statuscode 404: requested revision can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`revision/f1b94134a4b879bc55c3dacdb496690c8ebdc03f/directory/`
    """
    return _revision_directory_by(
        {"sha1_git": sha1_git}, dir_path, request.path, with_data=with_data
    )


@api_route(
    r"/revision/(?P<sha1_git>[0-9a-f]+)/log/",
    "api-1-revision-log",
    checksum_args=["sha1_git"],
)
@api_doc("/revision/log/")
@format_docstring(return_revision_array=DOC_RETURN_REVISION_ARRAY)
def api_revision_log(request, sha1_git):
    """
    .. http:get:: /api/1/revision/(sha1_git)/log/

        Get a list of all revisions heading to a given one, in other words show
        the commit log.

        The revisions are returned in the breadth-first search order while
        visiting the revision graph. The number of revisions to return is also
        bounded by the **limit** query parameter.

        .. warning::
            To get the full BFS traversal of the revision graph when the
            total number of revisions is greater than 1000, it is up to
            the client to keep track of the multiple branches of history
            when there's merge revisions in the returned objects.
            In other words, identify all the continuation points that need
            to be followed to get the full history through recursion.

        :param string sha1_git: hexadecimal representation of the revision
            **sha1_git** identifier
        :query int limit: maximum number of revisions to return when performing
            BFS traversal on the revision graph (default to 10, can not exceed 1000)

        {common_headers}

        {return_revision_array}

        :statuscode 200: no error
        :statuscode 400: an invalid **sha1_git** value has been provided
        :statuscode 404: head revision can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`revision/e1a315fa3fa734e2a6154ed7b5b9ae0eb8987aad/log/`
    """
    limit = int(request.query_params.get("limit", "10"))
    limit = min(limit, 1000)

    error_msg = "Revision with sha1_git %s not found." % sha1_git
    revisions = api_lookup(
        service.lookup_revision_log,
        sha1_git,
        limit,
        notfound_msg=error_msg,
        enrich_fn=utils.enrich_revision,
        request=request,
    )

    return {"results": revisions}
