# Copyright (C) 2018-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.common import service
from swh.web.common.exc import LargePayloadExc
from swh.web.common.identifiers import (
    resolve_swh_persistent_id,
    get_persistent_identifier,
    group_swh_persistent_identifiers,
)


@api_route(r"/resolve/(?P<swh_id>.*)/", "api-1-resolve-swh-pid")
@api_doc("/resolve/")
@format_docstring()
def api_resolve_swh_pid(request, swh_id):
    """
    .. http:get:: /api/1/resolve/(swh_id)/

        Resolve a Software Heritage persistent identifier.

        Try to resolve a provided `persistent identifier
        <https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html>`_
        into an url for browsing the pointed archive object. If the provided
        identifier is valid, the existence of the object in the archive
        will also be checked.

        :param string swh_id: a Software Heritage persistent identifier

        :>json string browse_url: the url for browsing the pointed object
        :>json object metadata: object holding optional parts of the
            persistent identifier
        :>json string namespace: the persistent identifier namespace
        :>json string object_id: the hash identifier of the pointed object
        :>json string object_type: the type of the pointed object
        :>json number scheme_version: the scheme version of the persistent
            identifier

        {common_headers}

        :statuscode 200: no error
        :statuscode 400: an invalid persistent identifier has been provided
        :statuscode 404: the pointed object does not exist in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`resolve/swh:1:rev:96db9023b881d7cd9f379b0c154650d6c108e9a3;origin=https://github.com/openssl/openssl/`
    """
    # try to resolve the provided pid
    swh_id_resolved = resolve_swh_persistent_id(swh_id)
    # id is well-formed, now check that the pointed
    # object is present in the archive, NotFoundExc
    # will be raised otherwise
    swh_id_parsed = swh_id_resolved["swh_id_parsed"]
    object_type = swh_id_parsed.object_type
    object_id = swh_id_parsed.object_id
    service.lookup_object(object_type, object_id)
    # id is well-formed and the pointed object exists
    swh_id_data = swh_id_parsed._asdict()
    swh_id_data["browse_url"] = request.build_absolute_uri(
        swh_id_resolved["browse_url"]
    )
    return swh_id_data


@api_route(r"/known/", "api-1-known", methods=["POST"])
@api_doc("/known/")
@format_docstring()
def api_swh_pid_known(request):
    """
    .. http:post:: /api/1/known/

        Check if a list of objects are present in the Software Heritage
        archive.

        The objects to check existence must be provided using Software Heritage
        `persistent identifiers
        <https://docs.softwareheritage.org/devel/swh-model/persistent-identifiers.html>`_.

        :<jsonarr string -: input array of Software Heritage persistent
            identifiers, its length can not exceed 1000.

        :>json object <swh_pid>: an object whose keys are input persistent
            identifiers and values objects with the following keys:

                * **known (bool)**: whether the object was found

        {common_headers}

        :statuscode 200: no error
        :statuscode 400: an invalid persistent identifier was provided
        :statuscode 413: the input array of persistent identifiers is too large

    """
    limit = 1000
    if len(request.data) > limit:
        raise LargePayloadExc(
            "The maximum number of PIDs this endpoint can " "receive is %s" % limit
        )

    persistent_ids = [get_persistent_identifier(pid) for pid in request.data]

    response = {str(pid): {"known": False} for pid in persistent_ids}

    # group pids by their type
    pids_by_type = group_swh_persistent_identifiers(persistent_ids)
    # search for hashes not present in the storage
    missing_hashes = service.lookup_missing_hashes(pids_by_type)

    for pid in persistent_ids:
        if pid.object_id not in missing_hashes:
            response[str(pid)]["known"] = True

    return response
