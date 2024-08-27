# Copyright (C) 2015-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import io
from typing import Any, Dict

from django.http import FileResponse
from django.shortcuts import redirect
from rest_framework.request import Request

from swh.model.hashutil import hash_to_hex
from swh.model.swhids import CoreSWHID, ObjectType
from swh.vault.cookers.git_bare import RootObjectType
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import APIUrls, api_route
from swh.web.api.views.utils import api_lookup
from swh.web.utils import archive, query, reverse
from swh.web.utils.exc import BadInputExc
from swh.web.utils.identifiers import parse_core_swhid
from swh.web.utils.url_path_converters import register_url_path_converters

register_url_path_converters()

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


def _vault_download(
    request: Request, swhid: str, bundle_type: str, filename: str, content_type: str
):
    bundle_download_url = archive.vault_download_url(
        bundle_type,
        parse_core_swhid(swhid),
        filename,
    )
    if bundle_download_url is not None:
        # vault cache offers direct download link, redirect to it
        return redirect(bundle_download_url)
    else:
        # fallback fetching bundle and sending it to client otherwise
        bundle_bytes = api_lookup(
            archive.vault_download,
            bundle_type,
            parse_core_swhid(swhid),
            notfound_msg=f"Cooked archive for {swhid} not found.",
            request=request,
        )

        return FileResponse(
            io.BytesIO(bundle_bytes),
            content_type=content_type,
            filename=filename,
            as_attachment=True,
        )


vault_api_urls = APIUrls()

######################################################
# Flat bundles


@api_route(
    "/vault/flat/<swhid:swhid>/",
    "api-1-vault-cook-flat",
    methods=["GET", "POST"],
    throttle_scope="swh_vault_cooking",
    never_cache=True,
    api_urls=vault_api_urls,
)
@api_doc("/vault/flat/", category="Batch download")
@format_docstring(base_url="https://archive.softwareheritage.org")
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
        :http:get:`/api/1/vault/flat/(swhid)/raw/`::

            $ curl -LOJ {base_url}/api/1/vault/flat/swh:1:dir:*/raw/

        Then to extract the cooked directory in the current one, use::

            $ tar xvf path/to/swh_1_*.tar.gz

        (replace ``swh:1:dir:*`` with the SWHID of the requested directory).

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
            request yet (in case of GET) or cannot be found in the archive
            (in case of POST)
    """
    parsed_swhid = parse_core_swhid(swhid)
    if parsed_swhid.object_type == ObjectType.DIRECTORY:
        res = _dispatch_cook_progress(request, "flat", parsed_swhid)
        res["fetch_url"] = reverse(
            "api-1-vault-download-flat",
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
    res = _dispatch_cook_progress(request, "flat", parse_core_swhid(swhid))
    res["fetch_url"] = reverse(
        "api-1-vault-download-flat",
        url_args={"swhid": swhid},
        request=request,
    )
    return _vault_response(res, add_legacy_items=True)


@api_route(
    "/vault/flat/<swhid:swhid>/raw/",
    "api-1-vault-download-flat",
    api_urls=vault_api_urls,
)
@api_doc("/vault/flat/raw/", category="Batch download")
def api_vault_download_flat(request: Request, swhid: str):
    """
    .. http:get:: /api/1/vault/flat/(swhid)/raw/

        Fetch the cooked archive for a flat bundle.

        See :http:get:`/api/1/vault/flat/(swhid)/` to get more
        details on 'flat' bundle cooking.

        :param string swhid: the SWHID of the object to cook

        :resheader Content-Type: application/gzip

        :statuscode 200: no error
        :statuscode 404: requested directory did not receive any cooking
            request yet (in case of GET) or cannot be found in the archive
            (in case of POST)
    """
    fname = "{}.tar.gz".format(swhid).replace(":", "_")
    return _vault_download(
        request,
        swhid,
        bundle_type="flat",
        filename=fname,
        content_type="application/gzip",
    )


@api_route(
    r"/vault/directory/(?P<dir_id>[0-9a-f]+)/raw/",
    "api-1-vault-download-directory",
    checksum_args=["dir_id"],
    api_urls=vault_api_urls,
)
@api_doc(
    "/vault/directory/raw/", category="Batch download", tags=["hidden", "deprecated"]
)
def api_vault_download_directory(request: Request, dir_id: str):
    """
    .. http:get:: /api/1/vault/directory/(dir_id)/raw/

        This endpoint was replaced by :http:get:`/api/1/vault/flat/(swhid)/raw/`
    """
    _, obj_id = query.parse_hash_with_algorithms_or_throws(
        dir_id, ["sha1"], "Only sha1_git is supported."
    )
    rev_flat_raw_url = reverse(
        "api-1-vault-download-flat", url_args={"swhid": f"swh:1:dir:{dir_id}"}
    )
    return redirect(rev_flat_raw_url)


######################################################
# gitfast bundles


@api_route(
    "/vault/gitfast/<swhid:swhid>/",
    "api-1-vault-cook-gitfast",
    methods=["GET", "POST"],
    throttle_scope="swh_vault_cooking",
    never_cache=True,
    api_urls=vault_api_urls,
)
@api_doc("/vault/gitfast/", category="Batch download")
@format_docstring(base_url="https://archive.softwareheritage.org")
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
        :http:get:`/api/1/vault/gitfast/(swhid)/raw/`::

            $ curl -LOJ {base_url}/api/1/vault/gitfast/swh:1:rev:*/raw/

        Then to import the revision in the current directory, use::

            $ git init
            $ zcat path/to/swh_1_rev_*.gitfast.gz | git fast-import
            $ git checkout HEAD

        (replace ``swh:1:rev:*`` with the SWHID of the requested revision).

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
            request yet (in case of GET) or cannot be found in the archive
            (in case of POST)
    """
    parsed_swhid = parse_core_swhid(swhid)
    if parsed_swhid.object_type == ObjectType.REVISION:
        res = _dispatch_cook_progress(request, "gitfast", parsed_swhid)
        res["fetch_url"] = reverse(
            "api-1-vault-download-gitfast",
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
    res = _dispatch_cook_progress(request, "gitfast", parse_core_swhid(swhid))
    res["fetch_url"] = reverse(
        "api-1-vault-download-gitfast",
        url_args={"swhid": swhid},
        request=request,
    )
    return _vault_response(res, add_legacy_items=True)


@api_route(
    "/vault/gitfast/<swhid:swhid>/raw/",
    "api-1-vault-download-gitfast",
    api_urls=vault_api_urls,
)
@api_doc("/vault/gitfast/raw/", category="Batch download")
def api_vault_download_revision_gitfast(request: Request, swhid: str):
    """
    .. http:get:: /api/1/vault/gitfast/(swhid)/raw/

        Fetch the cooked gitfast archive for a revision.

        See :http:get:`/api/1/vault/gitfast/(swhid)/` to get more
        details on gitfast cooking.

        :param string rev_id: the revision's sha1 identifier

        :resheader Content-Type: application/gzip

        :statuscode 200: no error
        :statuscode 404: requested directory did not receive any cooking
            request yet (in case of GET) or cannot be found in the archive
            (in case of POST)
    """
    fname = "{}.gitfast.gz".format(swhid).replace(":", "_")
    return _vault_download(
        request,
        swhid,
        bundle_type="gitfast",
        filename=fname,
        content_type="application/gzip",
    )


@api_route(
    r"/vault/revision/(?P<rev_id>[0-9a-f]+)/gitfast/raw/",
    "api-1-vault-download-revision_gitfast",
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
        "api-1-vault-download-gitfast", url_args={"swhid": f"swh:1:rev:{rev_id}"}
    )
    return redirect(rev_gitfast_raw_url)


######################################################
# git_bare bundles


@api_route(
    "/vault/git-bare/<swhid:swhid>/",
    "api-1-vault-cook-git-bare",
    methods=["GET", "POST"],
    throttle_scope="swh_vault_cooking",
    never_cache=True,
    api_urls=vault_api_urls,
)
@api_doc("/vault/git-bare/", category="Batch download")
@format_docstring(base_url="https://archive.softwareheritage.org")
def api_vault_cook_git_bare(request: Request, swhid: str):
    """
    .. http:get:: /api/1/vault/git-bare/(swhid)/
    .. http:post:: /api/1/vault/git-bare/(swhid)/

        Request the cooking of a git-bare archive or check its cooking status.

        That endpoint enables to create a git-bare archive cooking task for a:

        - **revision**: produced repository only includes a single branch
          heading to the revision

        - **release**: produced repository only includes a single branch
          heading to the release

        - **snapshot**: produced repository includes all branches and releases
          contained in the snapshot

        - **directory**: produced repository only includes a single branch
          with a single commit targeting the directory

        A cooking task must be created through a POST request while checking
        the status of a previously created one can be done through a GET request.

        Once the cooking task has been executed, the resulting git-bare archive
        can be downloaded using the dedicated endpoint
        :http:get:`/api/1/vault/git-bare/(swhid)/raw/`::

            $ curl -LOJ {base_url}/api/1/vault/git-bare/swh:1:*/raw/

        Then to import the repository in the current directory, use::

            $ tar -xf path/to/swh_1_*.git.tar
            $ git clone swh:1:*.git new_repository

        (replace ``swh:1:*`` with the SWHID of the requested revision or snapshot).

        This will create a directory called ``new_repository``, which is a git
        repository containing the requested objects.

        :param string swhid: the revision's or snapshot's permanent identifier

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
            request yet (in case of GET) or cannot be found in the archive
            (in case of POST)
    """
    parsed_swhid = parse_core_swhid(swhid)
    if parsed_swhid.object_type.name in (v.name for v in RootObjectType):
        res = _dispatch_cook_progress(request, "git_bare", parsed_swhid)
        res["fetch_url"] = reverse(
            "api-1-vault-download-git-bare",
            url_args={"swhid": swhid},
            request=request,
        )
        return _vault_response(res, add_legacy_items=False)
    else:
        raise BadInputExc(
            f"Object type {parsed_swhid.object_type.name} "
            "cannot be cooked as 'git-bare' bundle."
        )


@api_route(
    "/vault/git-bare/<swhid:swhid>/raw/",
    "api-1-vault-download-git-bare",
    api_urls=vault_api_urls,
)
@api_doc("/vault/git-bare/raw/", category="Batch download")
def api_vault_download_revision_git_bare(request: Request, swhid: str):
    """
    .. http:get:: /api/1/vault/git-bare/(swhid)/raw/

        Fetch the cooked git-bare archive for a revision.

        See :http:get:`/api/1/vault/git-bare/(swhid)/` to get more
        details on git-bare cooking.

        :param string swhid: the revision's permanent identifier

        :resheader Content-Type: application/x-tar

        :statuscode 200: no error
        :statuscode 404: requested directory did not receive any cooking
            request yet (in case of GET) or cannot be found in the archive
            (in case of POST)
    """
    fname = "{}.git.tar".format(swhid).replace(":", "_")
    return _vault_download(
        request,
        swhid,
        bundle_type="git_bare",
        filename=fname,
        content_type="application/x-tar",
    )
