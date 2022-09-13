# Copyright (C) 2019-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from base64 import b64encode
from typing import Optional, cast

from pybadges import badge

from django.contrib.staticfiles import finders
from django.http import HttpRequest, HttpResponse

from swh.model.exceptions import ValidationError
from swh.model.hashutil import hash_to_bytes, hash_to_hex
from swh.model.swhids import CoreSWHID, ObjectType, QualifiedSWHID
from swh.web.utils import archive, reverse
from swh.web.utils.exc import BadInputExc, NotFoundExc
from swh.web.utils.identifiers import parse_object_type, resolve_swhid

_orange = "#f36a24"
_blue = "#0172b2"
_red = "#cd5741"

_swh_logo_data = None

badge_config = {
    "content": {
        "color": _blue,
        "title": "Archived source file",
    },
    "directory": {
        "color": _blue,
        "title": "Archived source tree",
    },
    "origin": {
        "color": _orange,
        "title": "Archived software repository",
    },
    "release": {
        "color": _blue,
        "title": "Archived software release",
    },
    "revision": {
        "color": _blue,
        "title": "Archived commit",
    },
    "snapshot": {
        "color": _blue,
        "title": "Archived software repository snapshot",
    },
    "error": {"color": _red, "title": "An error occurred when generating the badge"},
}


def get_logo_data() -> str:
    """
    Get data-URI for Software Heritage SVG logo to embed it in
    the generated badges.
    """
    global _swh_logo_data
    if _swh_logo_data is None:
        swh_logo_path = cast(str, finders.find("img/swh-logo-white.svg"))
        with open(swh_logo_path, "rb") as swh_logo_file:
            _swh_logo_data = "data:image/svg+xml;base64,%s" % b64encode(
                swh_logo_file.read()
            ).decode("ascii")
    return _swh_logo_data


def swh_badge(
    request: HttpRequest,
    object_type: str,
    object_id: str,
    object_swhid: Optional[str] = "",
) -> HttpResponse:
    """
    Generate a Software Heritage badge for a given object type and id.

    Args:
        request: input http request
        object_type: The type of swh object to generate a badge for,
            either *content*, *directory*, *revision*, *release*, *origin*
            or *snapshot*
        object_id: The id of the swh object, either an url for origin
            type or a *sha1* for other object types
        object_swhid: If provided, the object SWHID will not be recomputed

    Returns:
        HTTP response with content type *image/svg+xml* containing the SVG
        badge data. If the provided parameters are invalid, HTTP 400 status
        code will be returned. If the object can not be found in the archive,
        HTTP 404 status code will be returned.

    """
    left_text = "error"
    whole_link = None

    try:
        if object_type == "origin":
            archive.lookup_origin({"url": object_id})
            right_text = "repository"
            whole_link = reverse(
                "browse-origin", query_params={"origin_url": object_id}
            )
        else:
            # when SWHID is provided, object type and id will be parsed
            # from it
            if object_swhid:
                parsed_swhid = QualifiedSWHID.from_string(object_swhid)
                parsed_object_type = parsed_swhid.object_type
                object_id = hash_to_hex(parsed_swhid.object_id)
                swh_object = archive.lookup_object(parsed_swhid.object_type, object_id)
                # remove SWHID qualified if any for badge text
                right_text = str(
                    CoreSWHID(
                        object_type=parsed_swhid.object_type,
                        object_id=parsed_swhid.object_id,
                    )
                )
                object_type = parsed_swhid.object_type.name.lower()
            else:
                parsed_object_type = parse_object_type(object_type)
                right_text = str(
                    CoreSWHID(
                        object_type=parsed_object_type,
                        object_id=hash_to_bytes(object_id),
                    )
                )
                swh_object = archive.lookup_object(parsed_object_type, object_id)

            whole_link = resolve_swhid(str(right_text))["browse_url"]
            # use release name for badge text
            if parsed_object_type == ObjectType.RELEASE:
                right_text = "release %s" % swh_object["name"]
        left_text = "archived"
    except (BadInputExc, ValidationError):
        right_text = f'invalid {object_type if object_type else "object"} id'
        object_type = "error"
    except NotFoundExc:
        right_text = f'{object_type if object_type else "object"} not found'
        object_type = "error"

    badge_data = badge(
        left_text=left_text,
        right_text=right_text,
        right_color=badge_config[object_type]["color"],
        whole_link=request.build_absolute_uri(whole_link),
        whole_title=badge_config[object_type]["title"],
        logo=get_logo_data(),
        embed_logo=True,
    )

    return HttpResponse(badge_data, content_type="image/svg+xml")


def swh_badge_swhid(request: HttpRequest, object_swhid: str) -> HttpResponse:
    """
    Generate a Software Heritage badge for a given object SWHID.

    Args:
        request (django.http.HttpRequest): input http request
        object_swhid (str): a SWHID of an archived object

    Returns:
        django.http.HttpResponse: An http response with content type
            *image/svg+xml* containing the SVG badge data. If any error
            occurs, a status code of 400 will be returned.
    """
    return swh_badge(request, "", "", object_swhid)
