# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.shortcuts import redirect

from swh.web.common.utils import resolve_swh_persistent_id
from swh.web.common.exc import handle_view_exception


def swh_id_browse(request, swh_id):
    """
    Django view enabling to browse the archive using
    :ref:`persistent-identifiers`.

    The url that points to it is :http:get:`/(swh_id)/`.
    """
    try:
        swh_id_resolved = resolve_swh_persistent_id(
            swh_id, query_params=request.GET)
    except Exception as exc:
        return handle_view_exception(request, exc)

    return redirect(swh_id_resolved['browse_url'])
