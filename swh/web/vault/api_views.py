# Copyright (C) 2015-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Any, Dict

from django.http import HttpResponse
from django.shortcuts import redirect
from rest_framework.request import Request

from swh.model.hashutil import hash_to_hex
from swh.model.swhids import CoreSWHID, ObjectType
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import APIUrls, api_route
from swh.web.api.views.utils import api_lookup
from swh.web.utils import SWHID_RE, archive, query, reverse
from swh.web.utils.exc import BadInputExc

######################################################
# Common


# XXX: a bit spaghetti. Would be better with class-based views.
def _dispatch_cook_progress(request, bundle_type: str, swhid: CoreSWHID):
    if request.method == "GET":
        return api_lookup(
            archive.vault_progress,
            bundle_type,
            swhid,
            notfound_msg=f"Cooking of {swhid} was never requested.",
            request=request,
        )
    elif request.method == "POST":
        email = request.POST.get("email", request.GET.get("email", None))
        return api_lookup(
            archive.vault_cook,
            bundle_type,
            swhid,
            email,
            notfound_msg=f"{swhid} not found.",
            request=request,
        )


def _vault_response(
    vault_response: Dict[str, Any], add_legacy_items: bool
) -> Dict[str, Any]:
    d = {
        "fetch_url": vault_response["fetch_url"],
        "progress_message": vault_response["progress_msg"],
        "id": vault_response["task_id"],
        "status": vault_response["task_status"],
        "swhid": str(vault_response["swhid"]),
    }

    if add_legacy_items:
        d["obj_type"] = vault_response["swhid"].object_type.name.lower()
        d["obj_id"] = hash_to_hex(vault_response["swhid"].object_id)

    return d


vault_api_urls = APIUrls()

######################################################
# Flat bundles


@api_route(
    f"/vault/flat/(?P<swhid>{SWHID_RE})/",
    "api-1-vault-cook-flat",
    methods=["GET", "POST"],
    throttle_scope="swh_vault_cooking",
    never_cache=True,
    api_urls=vault_api_urls,
)
@api_doc("/vault/flat/", category="Batch download")
@format_docstring()
def api_vault_cook_flat(request: Request, swhid: str):
    """
    .. http:get:: /api/1/vault/flat/(swhid)/
    .. http:post:: /api/1/vault/flat/(swhid)/

        Request the cooking of a simple archive, typically for a directory.

        That endpoint enables to create a vault cooking task for a directory
        through a POST request or check the status of a previously created one
        through a GET request.

        Once the cooking task has been executed, the resulting archive can
        be downloaded using the dedicated endpoint
        :http:get:`/api/1/vault/flat/(swhid)/raw/`.

        Then to extract the cooked directory in the current one, use::

            $ tar xvf path/to/swh_1_*.tar.gz

        :param string swhid: the object's SWHID

        :query string email: e-mail to notify when the archive is ready

        {common_headers}

        :>json string fetch_url: the url from which to download the archive
            once it has been cooked
            (see :http:get:`/api/1/vault/flat/(swhid)/raw/`)
        :>json string progress_message: message describing the cooking task
            progress
        :>json number id: the cooking task id
        :>json string status: the cooking task status
            (either **new**, **pending**, **done** or **failed**)
        :>json string swhid: the identifier of the object to cook

        :statuscode 200: no error
        :statuscode 400: an invalid directory identifier has been provided
        :statuscode 404: requested directory did not receive any cooking
            request yet (in case of GET) or can not be found in the archive
            (in case of POST)
    """
    parsed_swhid = CoreSWHID.from_string(swhid)
    if parsed_swhid.object_type == ObjectType.DIRECTORY:
        res = _dispatch_cook_progress(request, "flat", parsed_swhid)
        res["fetch_url"] = reverse(
            "api-1-vault-fetch-flat",
            url_args={"swhid": swhid},
            request=request,
        )
        return _vault_response(res, add_legacy_items=False)
    elif parsed_swhid.object_type == ObjectType.CONTENT:
        raise BadInputExc(
            "Content objects do not need to be cooked, "
            "use `/api/1/content/raw/` instead."
        )
    elif parsed_swhid.object_type == ObjectType.REVISION:
        # TODO: support revisions too? (the vault allows it)
        raise BadInputExc(
            "Only directories can be cooked as 'flat' bundles. "
            "Use `/api/1/vault/gitfast/` to cook revisions, as gitfast bundles."
        )
    else:
        raise BadInputExc("Only directories can be cooked as 'flat' bundles.")


@api_route(
    r"/vault/directory/(?P<dir_id>[0-9a-f]+)/",
    "api-1-vault-cook-directory",
    methods=["GET", "POST"],
    checksum_args=["dir_id"],
    throttle_scope="swh_vault_cooking",
    never_cache=True,
    api_urls=vault_api_urls,
)
@api_doc("/vault/directory/", category="Batch download", tags=["deprecated"])
@format_docstring()
def api_vault_cook_directory(request: Request, dir_id: str):
    """
    .. http:get:: /api/1/vault/directory/(dir_id)/

        This endpoint was replaced by :http:get:`/api/1/vault/flat/(swhid)/`
    """
    _, obj_id = query.parse_hash_with_algorithms_or_throws(
        dir_id, ["sha1"], "Only sha1_git is supported."
    )

    swhid = f"swh:1:dir:{obj_id.hex()}"
    res = _dispatch_cook_progress(request, "flat", CoreSWHID.from_string(swhid))
    res["fetch_url"] = reverse(
        "api-1-vault-fetch-flat",
        url_args={"swhid": swhid},
        request=request,
    )
    return _vault_response(res, add_legacy_items=True)


@api_route(
    f"/vault/flat/(?P<swhid>{SWHID_RE})/raw/",
    "api-1-vault-fetch-flat",
    api_urls=vault_api_urls,
)
@api_doc("/vault/flat/raw/", category="Batch download")
def api_vault_fetch_flat(request: Request, swhid: str):
    """
    .. http:get:: /api/1/vault/flat/(swhid)/raw/

        Fetch the cooked archive for a flat bundle.

        See :http:get:`/api/1/vault/flat/(swhid)/` to get more
        details on 'flat' bundle cooking.

        :param string swhid: the SWHID of the object to cook

        :resheader Content-Type: application/gzip

        :statuscode 200: no error
        :statuscode 404: requested directory did not receive any cooking
            request yet (in case of GET) or can not be found in the archive
            (in case of POST)
    """
    res = api_lookup(
        archive.vault_fetch,
        "flat",
        CoreSWHID.from_string(swhid),
        notfound_msg=f"Cooked archive for {swhid} not found.",
        request=request,
    )
    fname = "{}.tar.gz".format(swhid)
    response = HttpResponse(res, content_type="application/gzip")
    response["Content-disposition"] = "attachment; filename={}".format(
        fname.replace(":", "_")
    )
    return response


@api_route(
    r"/vault/directory/(?P<dir_id>[0-9a-f]+)/raw/",
    "api-1-vault-fetch-directory",
    checksum_args=["dir_id"],
    api_urls=vault_api_urls,
)
@api_doc(
    "/vault/directory/raw/", category="Batch download", tags=["hidden", "deprecated"]
)
def api_vault_fetch_directory(request: Request, dir_id: str):
    """
    .. http:get:: /api/1/vault/directory/(dir_id)/raw/

        This endpoint was replaced by :http:get:`/api/1/vault/flat/(swhid)/raw/`
    """
    _, obj_id = query.parse_hash_with_algorithms_or_throws(
        dir_id, ["sha1"], "Only sha1_git is supported."
    )
    rev_flat_raw_url = reverse(
        "api-1-vault-fetch-flat", url_args={"swhid": f"swh:1:dir:{dir_id}"}
    )
    return redirect(rev_flat_raw_url)


######################################################
# gitfast bundles


@api_route(
    f"/vault/gitfast/(?P<swhid>{SWHID_RE})/",
    "api-1-vault-cook-gitfast",
    methods=["GET", "POST"],
    throttle_scope="swh_vault_cooking",
    never_cache=True,
    api_urls=vault_api_urls,
)
@api_doc("/vault/gitfast/", category="Batch download")
@format_docstring()
def api_vault_cook_gitfast(request: Request, swhid: str):
    """
    .. http:get:: /api/1/vault/gitfast/(swhid)/
    .. http:post:: /api/1/vault/gitfast/(swhid)/

        Request the cooking of a gitfast archive for a revision or check
        its cooking status.

        That endpoint enables to create a vault cooking task for a revision
        through a POST request or check the status of a previously created one
        through a GET request.

        Once the cooking task has been executed, the resulting gitfast archive
        can be downloaded using the dedicated endpoint
        :http:get:`/api/1/vault/gitfast/(swhid)/raw/`.

        Then to import the revision in the current directory, use::

            $ git init
            $ zcat path/to/swh_1_rev_*.gitfast.gz | git fast-import
            $ git checkout HEAD

        :param string swhid: the revision's permanent identifiers

        :query string email: e-mail to notify when the gitfast archive is ready

        {common_headers}

        :>json string fetch_url: the url from which to download the archive
            once it has been cooked
            (see :http:get:`/api/1/vault/gitfast/(swhid)/raw/`)
        :>json string progress_message: message describing the cooking task
            progress
        :>json number id: the cooking task id
        :>json string status: the cooking task status (new/pending/done/failed)
        :>json string swhid: the identifier of the object to cook

        :statuscode 200: no error
        :statuscode 404: requested directory did not receive any cooking
            request yet (in case of GET) or can not be found in the archive
            (in case of POST)
    """
    parsed_swhid = CoreSWHID.from_string(swhid)
    if parsed_swhid.object_type == ObjectType.REVISION:
        res = _dispatch_cook_progress(request, "gitfast", parsed_swhid)
        res["fetch_url"] = reverse(
            "api-1-vault-fetch-gitfast",
            url_args={"swhid": swhid},
            request=request,
        )
        return _vault_response(res, add_legacy_items=False)
    elif parsed_swhid.object_type == ObjectType.CONTENT:
        raise BadInputExc(
            "Content objects do not need to be cooked, "
            "use `/api/1/content/raw/` instead."
        )
    elif parsed_swhid.object_type == ObjectType.DIRECTORY:
        raise BadInputExc(
            "Only revisions can be cooked as 'gitfast' bundles. "
            "Use `/api/1/vault/flat/` to cook directories, as flat bundles."
        )
    else:
        raise BadInputExc("Only revisions can be cooked as 'gitfast' bundles.")


@api_route(
    r"/vault/revision/(?P<rev_id>[0-9a-f]+)/gitfast/",
    "api-1-vault-cook-revision_gitfast",
    methods=["GET", "POST"],
    checksum_args=["rev_id"],
    throttle_scope="swh_vault_cooking",
    never_cache=True,
    api_urls=vault_api_urls,
)
@api_doc("/vault/revision/gitfast/", category="Batch download", tags=["deprecated"])
@format_docstring()
def api_vault_cook_revision_gitfast(request: Request, rev_id: str):
    """
    .. http:get:: /api/1/vault/revision/(rev_id)/gitfast/

        This endpoint was replaced by :http:get:`/api/1/vault/gitfast/(swhid)/`
    """
    _, obj_id = query.parse_hash_with_algorithms_or_throws(
        rev_id, ["sha1"], "Only sha1_git is supported."
    )

    swhid = f"swh:1:rev:{obj_id.hex()}"
    res = _dispatch_cook_progress(request, "gitfast", CoreSWHID.from_string(swhid))
    res["fetch_url"] = reverse(
        "api-1-vault-fetch-gitfast",
        url_args={"swhid": swhid},
        request=request,
    )
    return _vault_response(res, add_legacy_items=True)


@api_route(
    f"/vault/gitfast/(?P<swhid>{SWHID_RE})/raw/",
    "api-1-vault-fetch-gitfast",
    api_urls=vault_api_urls,
)
@api_doc("/vault/gitfast/raw/", category="Batch download")
def api_vault_fetch_revision_gitfast(request: Request, swhid: str):
    """
    .. http:get:: /api/1/vault/gitfast/(swhid)/raw/

        Fetch the cooked gitfast archive for a revision.

        See :http:get:`/api/1/vault/gitfast/(swhid)/` to get more
        details on gitfast cooking.

        :param string rev_id: the revision's sha1 identifier

        :resheader Content-Type: application/gzip

        :statuscode 200: no error
        :statuscode 404: requested directory did not receive any cooking
            request yet (in case of GET) or can not be found in the archive
            (in case of POST)
    """
    res = api_lookup(
        archive.vault_fetch,
        "gitfast",
        CoreSWHID.from_string(swhid),
        notfound_msg="Cooked archive for {} not found.".format(swhid),
        request=request,
    )
    fname = "{}.gitfast.gz".format(swhid)
    response = HttpResponse(res, content_type="application/gzip")
    response["Content-disposition"] = "attachment; filename={}".format(
        fname.replace(":", "_")
    )
    return response


@api_route(
    r"/vault/revision/(?P<rev_id>[0-9a-f]+)/gitfast/raw/",
    "api-1-vault-fetch-revision_gitfast",
    checksum_args=["rev_id"],
    api_urls=vault_api_urls,
)
@api_doc(
    "/vault/revision_gitfast/raw/",
    category="Batch download",
    tags=["hidden", "deprecated"],
)
def _api_vault_revision_gitfast_raw(request: Request, rev_id: str):
    """
    .. http:get:: /api/1/vault/revision/(rev_id)/gitfast/raw/

        This endpoint was replaced by :http:get:`/api/1/vault/gitfast/(swhid)/raw/`
    """
    rev_gitfast_raw_url = reverse(
        "api-1-vault-fetch-gitfast", url_args={"swhid": f"swh:1:rev:{rev_id}"}
    )
    return redirect(rev_gitfast_raw_url)


######################################################
# git_bare bundles


@api_route(
    f"/vault/git-bare/(?P<swhid>{SWHID_RE})/",
    "api-1-vault-cook-git-bare",
    methods=["GET", "POST"],
    throttle_scope="swh_vault_cooking",
    never_cache=True,
    api_urls=vault_api_urls,
)
@api_doc("/vault/git-bare/", category="Batch download")
@format_docstring()
def api_vault_cook_git_bare(request: Request, swhid: str):
    """
    .. http:get:: /api/1/vault/git-bare/(swhid)/
    .. http:post:: /api/1/vault/git-bare/(swhid)/

        Request the cooking of a git-bare archive for a revision or check
        its cooking status.

        That endpoint enables to create a vault cooking task for a revision
        through a POST request or check the status of a previously created one
        through a GET request.

        Once the cooking task has been executed, the resulting git-bare archive
        can be downloaded using the dedicated endpoint
        :http:get:`/api/1/vault/git-bare/(swhid)/raw/`.

        Then to import the revision in the current directory, use::

            $ tar -xf path/to/swh_1_rev_*.git.tar
            $ git clone swh:1:rev:*.git new_repository

        (replace ``swh:1:rev:*`` with the SWHID of the requested revision)

        This will create a directory called ``new_repository``, which is a git
        repository containing the requested objects.

        :param string swhid: the revision's permanent identifier

        :query string email: e-mail to notify when the git-bare archive is ready

        {common_headers}

        :>json string fetch_url: the url from which to download the archive
            once it has been cooked
            (see :http:get:`/api/1/vault/git-bare/(swhid)/raw/`)
        :>json string progress_message: message describing the cooking task
            progress
        :>json number id: the cooking task id
        :>json string status: the cooking task status (new/pending/done/failed)
        :>json string swhid: the identifier of the object to cook

        :statuscode 200: no error
        :statuscode 404: requested directory did not receive any cooking
            request yet (in case of GET) or can not be found in the archive
            (in case of POST)
    """
    parsed_swhid = CoreSWHID.from_string(swhid)
    if parsed_swhid.object_type == ObjectType.REVISION:
        res = _dispatch_cook_progress(request, "git_bare", parsed_swhid)
        res["fetch_url"] = reverse(
            "api-1-vault-fetch-git-bare",
            url_args={"swhid": swhid},
            request=request,
        )
        return _vault_response(res, add_legacy_items=False)
    elif parsed_swhid.object_type == ObjectType.CONTENT:
        raise BadInputExc(
            "Content objects do not need to be cooked, "
            "use `/api/1/content/raw/` instead."
        )
    elif parsed_swhid.object_type == ObjectType.DIRECTORY:
        raise BadInputExc(
            "Only revisions can be cooked as 'git-bare' bundles. "
            "Use `/api/1/vault/flat/` to cook directories, as flat bundles."
        )
    else:
        raise BadInputExc("Only revisions can be cooked as 'git-bare' bundles.")


@api_route(
    f"/vault/git-bare/(?P<swhid>{SWHID_RE})/raw/",
    "api-1-vault-fetch-git-bare",
    api_urls=vault_api_urls,
)
@api_doc("/vault/git-bare/raw/", category="Batch download")
def api_vault_fetch_revision_git_bare(request: Request, swhid: str):
    """
    .. http:get:: /api/1/vault/git-bare/(swhid)/raw/

        Fetch the cooked git-bare archive for a revision.

        See :http:get:`/api/1/vault/git-bare/(swhid)/` to get more
        details on git-bare cooking.

        :param string swhid: the revision's permanent identifier

        :resheader Content-Type: application/x-tar

        :statuscode 200: no error
        :statuscode 404: requested directory did not receive any cooking
            request yet (in case of GET) or can not be found in the archive
            (in case of POST)
    """
    res = api_lookup(
        archive.vault_fetch,
        "git_bare",
        CoreSWHID.from_string(swhid),
        notfound_msg="Cooked archive for {} not found.".format(swhid),
        request=request,
    )
    fname = "{}.git.tar".format(swhid)
    response = HttpResponse(res, content_type="application/x-tar")
    response["Content-disposition"] = "attachment; filename={}".format(
        fname.replace(":", "_")
    )
    return response
