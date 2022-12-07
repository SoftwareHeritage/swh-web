# Copyright (C) 2015-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import functools
import io
import os
from typing import Optional

from django.http import FileResponse
from rest_framework.request import Request

from swh.web.api import utils
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import api_lookup
from swh.web.utils import archive
from swh.web.utils.exc import NotFoundExc


@api_route(
    r"/content/(?P<q>[0-9a-z_:]*[0-9a-f]+)/filetype/",
    "api-1-content-filetype",
    checksum_args=["q"],
)
@api_doc("/content/filetype/", category="Metadata")
@format_docstring()
def api_content_filetype(request: Request, q: str):
    """
    .. http:get:: /api/1/content/[(hash_type):](hash)/filetype/

        Get information about the detected MIME type of a content object.

        :param string hash_type: optional parameter specifying which hashing algorithm
            has been used to compute the content checksum. It can be either ``sha1``,
            ``sha1_git``, ``sha256`` or ``blake2s256``. If that parameter is not
            provided, it is assumed that the hashing algorithm used is ``sha1``.
        :param string hash: hexadecimal representation of the checksum value computed
            with the specified hashing algorithm.

        :>json object content_url: link to
            :http:get:`/api/1/content/[(hash_type):](hash)/` for getting information
            about the content
        :>json string encoding: the detected content encoding
        :>json string id: the **sha1** identifier of the content
        :>json string mimetype: the detected MIME type of the content
        :>json object tool: information about the tool used to detect the content
            filetype

        {common_headers}

        :statuscode 200: no error
        :statuscode 400: an invalid **hash_type** or **hash** has been provided
        :statuscode 404: requested content can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`content/sha1:dc2830a9e72f23c1dfebef4413003221baa5fb62/filetype/`
    """
    return api_lookup(
        archive.lookup_content_filetype,
        q,
        notfound_msg="No filetype information found for content {}.".format(q),
        enrich_fn=utils.enrich_metadata_endpoint,
        request=request,
    )


@api_route(
    r"/content/(?P<q>[0-9a-z_:]*[0-9a-f]+)/language/",
    "api-1-content-language",
    checksum_args=["q"],
)
@api_doc("/content/language/", category="Metadata")
@format_docstring()
def api_content_language(request: Request, q: str):
    """
    .. http:get:: /api/1/content/[(hash_type):](hash)/language/

        Get information about the programming language used in a content object.

        Note: this endpoint currently returns no data.

        :param string hash_type: optional parameter specifying which hashing algorithm
            has been used to compute the content checksum. It can be either ``sha1``,
            ``sha1_git``, ``sha256`` or ``blake2s256``. If that parameter is not
            provided, it is assumed that the hashing algorithm used is ``sha1``.
        :param string hash: hexadecimal representation of the checksum value computed
            with the specified hashing algorithm.

        :>json object content_url: link to
            :http:get:`/api/1/content/[(hash_type):](hash)/` for getting information
            about the content
        :>json string id: the **sha1** identifier of the content
        :>json string lang: the detected programming language if any
        :>json object tool: information about the tool used to detect the programming
            language

        {common_headers}

        :statuscode 200: no error
        :statuscode 400: an invalid **hash_type** or **hash** has been provided
        :statuscode 404: requested content can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`content/sha1:dc2830a9e72f23c1dfebef4413003221baa5fb62/language/`
    """
    return api_lookup(
        archive.lookup_content_language,
        q,
        notfound_msg="No language information found for content {}.".format(q),
        enrich_fn=utils.enrich_metadata_endpoint,
        request=request,
    )


@api_route(
    r"/content/(?P<q>[0-9a-z_:]*[0-9a-f]+)/license/",
    "api-1-content-license",
    checksum_args=["q"],
)
@api_doc("/content/license/", category="Metadata")
@format_docstring()
def api_content_license(request: Request, q: str):
    """
    .. http:get:: /api/1/content/[(hash_type):](hash)/license/

        Get information about the license of a content object.

        :param string hash_type: optional parameter specifying which hashing algorithm
            has been used to compute the content checksum. It can be either ``sha1``,
            ``sha1_git``, ``sha256`` or ``blake2s256``. If that parameter is not
            provided, it is assumed that the hashing algorithm used is ``sha1``.
        :param string hash: hexadecimal representation of the checksum value computed
            with the specified hashing algorithm.

        :>json object content_url: link to
            :http:get:`/api/1/content/[(hash_type):](hash)/` for getting information
            about the content
        :>json string id: the **sha1** identifier of the content
        :>json array licenses: array of strings containing the detected license names
        :>json object tool: information about the tool used to detect the license

        {common_headers}

        :statuscode 200: no error
        :statuscode 400: an invalid **hash_type** or **hash** has been provided
        :statuscode 404: requested content can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`content/sha1:dc2830a9e72f23c1dfebef4413003221baa5fb62/license/`
    """
    return api_lookup(
        archive.lookup_content_license,
        q,
        notfound_msg="No license information found for content {}.".format(q),
        enrich_fn=utils.enrich_metadata_endpoint,
        request=request,
    )


@api_route(
    r"/content/(?P<q>[0-9a-z_:]*[0-9a-f]+)/raw/",
    "api-1-content-raw",
    checksum_args=["q"],
)
@api_doc("/content/raw/", category="Archive")
def api_content_raw(request: Request, q: str):
    """
    .. http:get:: /api/1/content/[(hash_type):](hash)/raw/

        Get the raw content of a content object (aka a "blob"), as a byte sequence.

        :param string hash_type: optional parameter specifying which hashing algorithm
            has been used to compute the content checksum. It can be either ``sha1``,
            ``sha1_git``, ``sha256`` or ``blake2s256``. If that parameter is not
            provided, it is assumed that the hashing algorithm used is ``sha1``.
        :param string hash: hexadecimal representation of the checksum value computed
            with the specified hashing algorithm.
        :query string filename: if provided, the downloaded content will get that
            filename

        :resheader Content-Type: application/octet-stream

        :statuscode 200: no error
        :statuscode 400: an invalid **hash_type** or **hash** has been provided
        :statuscode 404: requested content can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`content/sha1:dc2830a9e72f23c1dfebef4413003221baa5fb62/raw/`
    """
    content_raw = archive.lookup_content_raw(q)
    if not content_raw:
        raise NotFoundExc("Content %s is not found." % q)

    filename = request.query_params.get("filename")
    if not filename:
        filename = "content_%s_raw" % q.replace(":", "_")

    return FileResponse(
        io.BytesIO(content_raw["data"]),  # not copied, as this is never modified
        filename=os.path.basename(filename),
        content_type="application/octet-stream",
        as_attachment=True,
    )


@api_route(r"/content/known/search/", "api-1-content-known", methods=["POST"])
@api_route(r"/content/known/(?P<q>(?!search).+)/", "api-1-content-known")
@api_doc("/content/known/", category="Archive", tags=["hidden"])
@format_docstring()
def api_check_content_known(request: Request, q: Optional[str] = None):
    """
    .. http:get:: /api/1/content/known/(sha1)[,(sha1), ...,(sha1)]/

        Check whether some content(s) (aka "blob(s)") is present in the archive
        based on its **sha1** checksum.

        :param string sha1: hexadecimal representation of the **sha1** checksum value
            for the content to check existence. Multiple values can be provided
            separated by ','.

        {common_headers}

        :>json array search_res: array holding the search result for each provided
            **sha1**
        :>json object search_stats: some statistics regarding the number of **sha1**
            provided and the percentage of those found in the archive

        :statuscode 200: no error
        :statuscode 400: an invalid **sha1** has been provided

        **Example:**

        .. parsed-literal::

            :swh_web_api:`content/known/dc2830a9e72f23c1dfebef4413003221baa5fb62,0c3f19cb47ebfbe643fb19fa94c874d18fa62d12/`
    """
    search_stats = {"nbfiles": 0, "pct": 0}
    search_res = None

    queries = []
    # GET: Many hash separated values request
    if q:
        hashes = q.split(",")
        for v in hashes:
            queries.append({"filename": None, "sha1": v})

    # POST: Many hash requests in post form submission
    elif request.method == "POST":
        data = request.data
        # Remove potential inputs with no associated value
        for k, v in data.items():
            if v is not None:
                if k == "q" and len(v) > 0:
                    queries.append({"filename": None, "sha1": v})
                elif v != "":
                    queries.append({"filename": k, "sha1": v})

    if queries:
        lookup = archive.lookup_multiple_hashes(queries)
        result = []
        nb_queries = len(queries)
        for el in lookup:
            res_d = {"sha1": el["sha1"], "found": el["found"]}
            if "filename" in el and el["filename"]:
                res_d["filename"] = el["filename"]
            result.append(res_d)
            search_res = result
            nbfound = len([x for x in lookup if x["found"]])
            search_stats["nbfiles"] = nb_queries
            search_stats["pct"] = int((nbfound / nb_queries) * 100)

    return {"search_res": search_res, "search_stats": search_stats}


@api_route(
    r"/content/(?P<q>[0-9a-z_:]*[0-9a-f]+)/", "api-1-content", checksum_args=["q"]
)
@api_doc("/content/", category="Archive")
@format_docstring()
def api_content_metadata(request: Request, q: str):
    """
    .. http:get:: /api/1/content/[(hash_type):](hash)/

        Get information about a content (aka a "blob") object.
        In the archive, a content object is identified based on checksum
        values computed using various hashing algorithms.

        :param string hash_type: optional parameter specifying which hashing algorithm
            has been used to compute the content checksum. It can be either ``sha1``,
            ``sha1_git``, ``sha256`` or ``blake2s256``. If that parameter is not
            provided, it is assumed that the hashing algorithm used is ``sha1``.
        :param string hash: hexadecimal representation of the checksum value computed
            with the specified hashing algorithm.

        {common_headers}

        :>json object checksums: object holding the computed checksum values for the
            requested content
        :>json string data_url: link to
            :http:get:`/api/1/content/[(hash_type):](hash)/raw/`
            for downloading the content raw bytes
        :>json string filetype_url: link to
            :http:get:`/api/1/content/[(hash_type):](hash)/filetype/`
            for getting information about the content MIME type
        :>json string language_url: link to
            :http:get:`/api/1/content/[(hash_type):](hash)/language/`
            for getting information about the programming language used in the content
        :>json number length: length of the content in bytes
        :>json string license_url: link to
            :http:get:`/api/1/content/[(hash_type):](hash)/license/`
            for getting information about the license of the content

        :statuscode 200: no error
        :statuscode 400: an invalid **hash_type** or **hash** has been provided
        :statuscode 404: requested content can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`content/sha1_git:fe95a46679d128ff167b7c55df5d02356c5a1ae1/`
    """
    return api_lookup(
        archive.lookup_content,
        q,
        notfound_msg="Content with {} not found.".format(q),
        enrich_fn=functools.partial(utils.enrich_content, query_string=q),
        request=request,
    )
