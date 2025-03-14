# Copyright (C) 2022-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.http import HttpResponse
from rest_framework.request import Request

from swh.model import model
from swh.model.git_objects import (
    content_git_object,
    directory_git_object,
    release_git_object,
    revision_git_object,
    snapshot_git_object,
)
from swh.model.swhids import ObjectType
from swh.storage.algos.directory import directory_get
from swh.storage.algos.snapshot import snapshot_get_all_branches
from swh.web import config
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.utils import archive
from swh.web.utils.exc import NotFoundExc
from swh.web.utils.identifiers import parse_core_swhid


@api_route(
    "/raw/<swhid:swhid>/",
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

        :param string swhid: the object's SWHID

        :resheader Content-Type: application/octet-stream

        :statuscode 200: no error
        :statuscode 404: the requested object cannot be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`raw/swh:1:snp:6a3a2cf0b2b90ce7ae1cf0a221ed68035b686f5a`
    """
    parsed_swhid = parse_core_swhid(swhid)
    object_id = parsed_swhid.object_id
    object_type = parsed_swhid.object_type

    storage = config.storage()

    def not_found():
        return NotFoundExc(f"Object with id {swhid} not found.")

    if object_type == ObjectType.CONTENT:
        # fetching content metadata
        try:
            cnt_dict = archive.lookup_content(
                f"sha1_git:{object_id.hex()}", json_convert=False, with_data=True
            )
        except NotFoundExc:
            raise not_found()
        cnt = model.Content.from_dict(cnt_dict)
        result = content_git_object(cnt)

    elif object_type == ObjectType.DIRECTORY:
        dir_ = directory_get(storage, object_id)
        if dir_ is None:
            raise not_found()
        result = directory_git_object(dir_)

    elif object_type == ObjectType.REVISION:
        rev = storage.revision_get([object_id])[0]
        if rev is None:
            raise not_found()
        result = revision_git_object(rev)

    elif object_type == ObjectType.RELEASE:
        rel = storage.release_get([object_id])[0]
        if rel is None:
            raise not_found()
        result = release_git_object(rel)

    elif object_type == ObjectType.SNAPSHOT:
        snp = snapshot_get_all_branches(storage, object_id)
        if snp is None:
            raise not_found()
        result = snapshot_git_object(snp)

    else:
        raise ValueError(f"Unexpected object type variant: {object_type}")

    response = HttpResponse(result, content_type="application/octet-stream")
    filename = swhid.replace(":", "_") + "_raw"
    response["Content-disposition"] = f"attachment; filename={filename}"

    return response
