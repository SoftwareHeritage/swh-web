# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import HttpResponse

from swh.web.common import service
from swh.web.common.utils import reverse
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
@api_route(
    r"/revision/(?P<sha1_git>[0-9a-f]+)" r"/prev/(?P<prev_sha1s>[0-9a-f]*/*)/log/",
    "api-1-revision-log",
    checksum_args=["sha1_git", "prev_sha1s"],
)
@api_doc("/revision/log/")
@format_docstring(return_revision_array=DOC_RETURN_REVISION_ARRAY)
def api_revision_log(request, sha1_git, prev_sha1s=None):
    """
    .. http:get:: /api/1/revision/(sha1_git)[/prev/(prev_sha1s)]/log/

        Get a list of all revisions heading to a given one, in other words show
        the commit log.

        :param string sha1_git: hexadecimal representation of the revision
            **sha1_git** identifier
        :param string prev_sha1s: optional parameter representing the navigation
            breadcrumbs (descendant revisions previously visited). If multiple values,
            use / as delimiter. If provided, revisions information will be added at
            the beginning of the returned list.
        :query int per_page: number of elements in the returned list, for pagination
            purpose

        {common_headers}
        {resheader_link}

        {return_revision_array}

        :statuscode 200: no error
        :statuscode 400: an invalid **sha1_git** value has been provided
        :statuscode 404: requested revision can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`revision/e1a315fa3fa734e2a6154ed7b5b9ae0eb8987aad/log/`
    """
    result = {}
    per_page = int(request.query_params.get("per_page", "10"))

    def lookup_revision_log_with_limit(s, limit=per_page + 1):
        return service.lookup_revision_log(s, limit)

    error_msg = "Revision with sha1_git %s not found." % sha1_git
    rev_get = api_lookup(
        lookup_revision_log_with_limit,
        sha1_git,
        notfound_msg=error_msg,
        enrich_fn=utils.enrich_revision,
        request=request,
    )

    nb_rev = len(rev_get)
    if nb_rev == per_page + 1:
        rev_backward = rev_get[:-1]
        new_last_sha1 = rev_get[-1]["id"]
        query_params = {}

        if request.query_params.get("per_page"):
            query_params["per_page"] = per_page

        result["headers"] = {
            "link-next": reverse(
                "api-1-revision-log",
                url_args={"sha1_git": new_last_sha1},
                query_params=query_params,
                request=request,
            )
        }

    else:
        rev_backward = rev_get

    if not prev_sha1s:  # no nav breadcrumbs, so we're done
        revisions = rev_backward

    else:
        rev_forward_ids = prev_sha1s.split("/")
        rev_forward = api_lookup(
            service.lookup_revision_multiple,
            rev_forward_ids,
            notfound_msg=error_msg,
            enrich_fn=utils.enrich_revision,
            request=request,
        )
        revisions = rev_forward + rev_backward

    result.update({"results": revisions})
    return result
