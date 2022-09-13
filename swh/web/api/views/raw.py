# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import HttpResponse
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

from swh.model import model
from swh.model.git_objects import (
    content_git_object,
    directory_git_object,
    release_git_object,
    revision_git_object,
    snapshot_git_object,
)
from swh.model.hashutil import hash_to_hex
from swh.model.swhids import CoreSWHID, ObjectType
from swh.storage.algos.directory import directory_get
from swh.storage.algos.snapshot import snapshot_get_all_branches
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.auth.utils import API_RAW_OBJECT_PERMISSION
from swh.web.utils import SWHID_RE, archive
from swh.web.utils.exc import NotFoundExc


@api_route(
    f"/raw/(?P<swhid>{SWHID_RE})/",
    "api-1-raw-object",
    throttle_scope="swh_raw_object",
)
@api_doc("/raw/", category="Archive")
@format_docstring()
def api_raw_object(request: Request, swhid: str):
    """
    .. http:get::  /api/1/raw/(swhid)/

        Get the object corresponding to the SWHID in raw form.

        This endpoint exposes the internal representation (see the
        ``*_git_object`` functions in :mod:`swh.model.git_objects`), and
        so can be used to fetch a binary blob which hashes to the same
        identifier.

        .. warning::
            That endpoint is not publicly available and requires authentication and
            special user permission in order to be able to request it.

        :param string swhid: the object's SWHID

        :resheader Content-Type: application/octet-stream

        :statuscode 200: no error
        :statuscode 404: the requested object can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`raw/swh:1:snp:6a3a2cf0b2b90ce7ae1cf0a221ed68035b686f5a`
    """
    if not (request.user.is_staff or request.user.has_perm(API_RAW_OBJECT_PERMISSION)):
        raise PermissionDenied()

    parsed_swhid = CoreSWHID.from_string(swhid)
    object_id = parsed_swhid.object_id
    object_type = parsed_swhid.object_type

    def not_found():
        return NotFoundExc(f"Object with id {swhid} not found.")

    if object_type == ObjectType.CONTENT:
        results = archive.storage.content_find({"sha1_git": object_id})
        if len(results) == 0:
            raise not_found()
        cnt = results[0]
        # `cnt.with_data()` unfortunately doesn't seem to work.
        if cnt.data is None:
            d = cnt.to_dict()
            d["data"] = archive.storage.content_get_data(cnt.sha1)
            cnt = model.Content.from_dict(d)
            assert cnt.data, f"Content {hash_to_hex(cnt.sha1)} ceased to exist"
        result = content_git_object(cnt)

    elif object_type == ObjectType.DIRECTORY:
        dir_ = directory_get(archive.storage, object_id)
        if dir_ is None:
            raise not_found()
        result = directory_git_object(dir_)

    elif object_type == ObjectType.REVISION:
        rev = archive.storage.revision_get([object_id], ignore_displayname=True)[0]
        if rev is None:
            raise not_found()
        result = revision_git_object(rev)

    elif object_type == ObjectType.RELEASE:
        rel = archive.storage.release_get([object_id], ignore_displayname=True)[0]
        if rel is None:
            raise not_found()
        result = release_git_object(rel)

    elif object_type == ObjectType.SNAPSHOT:
        snp = snapshot_get_all_branches(archive.storage, object_id)
        if snp is None:
            raise not_found()
        result = snapshot_git_object(snp)

    else:
        raise ValueError(f"Unexpected object type variant: {object_type}")

    response = HttpResponse(result, content_type="application/octet-stream")
    filename = swhid.replace(":", "_") + "_raw"
    response["Content-disposition"] = f"attachment; filename={filename}"

    return response
