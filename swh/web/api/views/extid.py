# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from rest_framework.request import Request

from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.api.utils import enrich_extid
from swh.web.api.views.utils import api_lookup
from swh.web.utils import archive
from swh.web.utils.exc import BadInputExc


@api_route(
    "/extid/target/<swhid:swhid>/",
    "api-1-extid-target",
)
@api_doc("/extid/target/", category="External IDentifiers")
@format_docstring()
def api_extid_target(request: Request, swhid: str):
    """
    .. http:get:: /api/1/extid/target/(swhid)/

        Get information about external identifiers targeting an archived object.

        An `external identifier
        <https://docs.softwareheritage.org/devel/glossary.html#term-external-identifier>`_
        is used by a system that does not fit the Software Heritage data model.

        :param string swhid: a SWHID to check if external identifiers target it
        :query string extid_type: optional external identifier type to use as a filter,
            must be provided if ``extid_version`` parameter is.
        :query number extid_version: optional version number of external identifier type,
            must be provided if ``extid_type`` parameter is.
        :query string extid_format: the format used to encode an extid to an ASCII string,
            either ``base64url``, ``hex`` or ``raw`` (default to ``hex``).

        {common_headers}

        :>jsonarr string extid_type: the type of the external identifier
        :>jsonarr string extid: the value of the external identifier
        :>jsonarr string target: the SWHID of the archived object targeted by the
            external identifier
        :>jsonarr string target_url: URL to browse the targeted archived object
        :>jsonarr number extid_version: the version of the external identifier

        :statuscode 200: no error
        :statuscode 400: provided parameters are invalid
        :statuscode 404: external identifier targeting SWHID cannot be found

        **Example:**

        .. parsed-literal::

            :swh_web_api:`extid/target/swh:1:rev:a2903689803b2c07890a930284425838436425a6/?extid_format=raw`
            :swh_web_api:`extid/target/swh:1:rev:6b29add7cb6b5f6045df308c43e4177f1f854a56/?extid_format=hex`

    """
    extid_type = request.GET.get("extid_type")
    extid_version = request.GET.get("extid_version")
    if (extid_version is not None and extid_type is None) or (
        extid_version is None and extid_type is not None
    ):
        raise BadInputExc(
            "Both extid_type and extid_version query parameters must be provided"
        )

    return api_lookup(
        archive.lookup_extid_by_target,
        swhid,
        extid_type=extid_type,
        extid_version=int(extid_version) if extid_version is not None else None,
        extid_format=request.GET.get("extid_format", "hex"),
        enrich_fn=enrich_extid,
        request=request,
    )


@api_route(
    r"/extid/(?P<extid_type>.+?)/(?P<extid_format>.+?):(?P<extid>.+)/",
    "api-1-extid",
)
@api_doc("/extid/", category="External IDentifiers")
@format_docstring(hg_template="'{node}'")
def api_extid(request: Request, extid_type: str, extid_format: str, extid: str):
    """
    .. http:get:: /api/1/extid/(extid_type)/(extid_format):(extid)/

        Get information about an external identifier.

        An `external identifier
        <https://docs.softwareheritage.org/devel/glossary.html#term-external-identifier>`_
        is used by a system that does not fit the Software Heritage data model.

        As an external identifier is stored in binary into the archive database, the format
        used to decode its ASCII representation must be explicitly specified. The available
        formats are the following:

        - ``base64url``: the external identifier is encoded to `base64url
          <https://datatracker.ietf.org/doc/html/rfc4648#section-5>`_.
        - ``hex``: the external identifier is a checksum in hexadecimal representation
        - ``raw``: the external identifier is an ASCII string

        The types of external identifier that can be requested are given below.

        VCS related:

        - ``bzr-nodeid``: Revision ASCII identifier of a Bazaar repository, to get such
          identifiers use the following command in your Bazaar repository:
          ``bzr log --show-ids``.

        - ``hg-nodeid``: Node hash identifier for the revision of a Mercurial repository,
          to get such identifier execute the following command in your Mercurial repository:
          ``hg id -r <rev_num> --template {hg_template}``.

        `Guix <https://guix.gnu.org/manual/en/html_node/Invoking-guix-hash.html>`_ and
        `Nix <https://nixos.wiki/wiki/Nix_Hash>`_ related (must be queried with the
        **extid_version** query parameter set to **1** to ensure correctness):

        - ``nar-sha256``: sha256 checksum of a `Nix Archive (NAR)
          <https://edolstra.github.io/pubs/phd-thesis.pdf#page=101>`_, used to deterministically
          identifies the contents of a source tree (corresponds to *recursive* hash mode used
          by Guix and Nix)

        - ``checksum-sha256``: sha256 checksum of a file, typically a tarball (corresponds to
          *flat* hash mode used by Guix and Nix)

        - ``checksum-sha512``: sha512 checksum of a file, typically a tarball (corresponds to
          *flat* hash mode used by Guix and Nix)

        :param string extid_type: the type of external identifier
        :param string extid_format: the format used to encode the extid to an ASCII string,
            either ``base64url``, ``hex`` or ``raw``
        :param string extid: the external identifier value
        :query number extid_version: optional version number of external identifier type

        {common_headers}

        :>json string extid_type: the type of the external identifier
        :>json string extid: the value of the external identifier
        :>json string target: the SWHID of the archived object targeted by the
            external identifier
        :>json string target_url: URL to browse the targeted archived object
        :>json number extid_version: the version of the external identifier

        :statuscode 200: no error
        :statuscode 404: requested external identifier cannot be found

        **Example:**

        .. parsed-literal::

            :swh_web_api:`extid/bzr-nodeid/raw:rodney.dawes@canonical.com-20090512192901-f22ja60nsgq9j5a4/`
            :swh_web_api:`extid/hg-nodeid/hex:1ce49c60732c9020ce2f98d03a7a71ec8d5be191/`
            :swh_web_api:`extid/checksum-sha256/base64url:s4lFKlaGmGiN2jiAIGg3ihbBXEr5sVPN2ZtlORKSu8c/?extid_version=1`
            :swh_web_api:`extid/nar-sha256/base64url:AAAlhKVqm86FeTUVYEKY-LOx6Ul-APxjYaDC5zHAY_M/?extid_version=1`
            :swh_web_api:`extid/checksum-sha512/base64url:AL5bxZ-gStT5UpzSc1dN-XVxxWN9FHtvBlZoFeFFMowwgMKWq9GLZHV8DWX-g7ugiKxlKa2ph2oTQCqvhixDQw/?extid_version=1`

    """

    extid_version = request.GET.get("extid_version")

    return api_lookup(
        archive.lookup_extid,
        extid_type,
        extid_format,
        extid,
        extid_version=int(extid_version) if extid_version else None,
        enrich_fn=enrich_extid,
        request=request,
    )
