# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect

from swh.web.utils.identifiers import resolve_swhid


def swhid_browse(request: HttpRequest, swhid: str) -> HttpResponse:
    """
    Django view enabling to browse the archive using :ref:`persistent-identifiers`.

    The url that points to it is :http:get:`/(swhid)/`.
    """
    swhid_resolved = resolve_swhid(swhid, query_params=request.GET.dict())
    assert swhid_resolved["browse_url"]
    return redirect(swhid_resolved["browse_url"])
