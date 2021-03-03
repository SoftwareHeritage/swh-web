# Copyright (C) 2018-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.model.hashutil import hash_to_bytes, hash_to_hex
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.common import archive
from swh.web.common.exc import LargePayloadExc
from swh.web.common.identifiers import get_swhid, group_swhids, resolve_swhid


@api_route(r"/resolve/(?P<swhid>.*)/", "api-1-resolve-swhid")
@api_doc("/resolve/")
@format_docstring()
def api_resolve_swhid(request, swhid):
    """
    .. http:get:: /api/1/resolve/(swhid)/

        Resolve a SoftWare Heritage persistent IDentifier (SWHID)

        Try to resolve a provided `SoftWare Heritage persistent IDentifier
        <https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html>`_
        into an url for browsing the pointed archive object.

        If the provided identifier is valid, the existence of the object in
        the archive will also be checked.

        :param string swhid: a SoftWare Heritage persistent IDentifier

        :>json string browse_url: the url for browsing the pointed object
        :>json object metadata: object holding optional parts of the SWHID
        :>json string namespace: the SWHID namespace
        :>json string object_id: the hash identifier of the pointed object
        :>json string object_type: the type of the pointed object
        :>json number scheme_version: the scheme version of the SWHID

        {common_headers}

        :statuscode 200: no error
        :statuscode 400: an invalid SWHID has been provided
        :statuscode 404: the pointed object does not exist in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`resolve/swh:1:rev:96db9023b881d7cd9f379b0c154650d6c108e9a3;origin=https://github.com/openssl/openssl/`
    """
    # try to resolve the provided swhid
    swhid_resolved = resolve_swhid(swhid)
    # id is well-formed, now check that the pointed
    # object is present in the archive, NotFoundExc
    # will be raised otherwise
    swhid_parsed = swhid_resolved["swhid_parsed"]
    object_type = swhid_parsed.object_type.name.lower()
    object_id = hash_to_hex(swhid_parsed.object_id)
    archive.lookup_object(object_type, object_id)
    # id is well-formed and the pointed object exists
    return {
        "namespace": swhid_parsed.namespace,
        "scheme_version": swhid_parsed.scheme_version,
        "object_type": object_type,
        "object_id": object_id,
        "metadata": swhid_parsed.qualifiers(),
        "browse_url": request.build_absolute_uri(swhid_resolved["browse_url"]),
    }


@api_route(r"/known/", "api-1-known", methods=["POST"])
@api_doc("/known/")
@format_docstring()
def api_swhid_known(request):
    """
    .. http:post:: /api/1/known/

        Check if a list of objects are present in the Software Heritage
        archive.

        The objects to check existence must be provided using
        `SoftWare Heritage persistent IDentifiers
        <https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html>`_.

        :<jsonarr string -: input array of SWHIDs, its length can not exceed 1000.

        :>json object <swhid>: an object whose keys are input SWHIDs and values
            objects with the following keys:

                * **known (bool)**: whether the object was found

        {common_headers}

        :statuscode 200: no error
        :statuscode 400: an invalid SWHID was provided
        :statuscode 413: the input array of SWHIDs is too large

    """
    limit = 1000
    if len(request.data) > limit:
        raise LargePayloadExc(
            "The maximum number of SWHIDs this endpoint can receive is %s" % limit
        )

    swhids = [get_swhid(swhid) for swhid in request.data]

    response = {str(swhid): {"known": False} for swhid in swhids}

    # group swhids by their type
    swhids_by_type = group_swhids(swhids)
    # search for hashes not present in the storage
    missing_hashes = set(
        map(hash_to_bytes, archive.lookup_missing_hashes(swhids_by_type))
    )

    for swhid in swhids:
        if swhid.object_id not in missing_hashes:
            response[str(swhid)]["known"] = True

    return response
