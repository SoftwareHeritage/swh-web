# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.shortcuts import redirect, render

from swh.web.browse.browseurls import BrowseUrls
from swh.web.browse.identifiers import swhid_browse
import swh.web.browse.views.content  # noqa
import swh.web.browse.views.directory  # noqa
import swh.web.browse.views.origin  # noqa
import swh.web.browse.views.release  # noqa
import swh.web.browse.views.revision  # noqa
import swh.web.browse.views.snapshot  # noqa
from swh.web.common.utils import reverse


def _browse_help_view(request):
    return render(
        request, "browse/help.html", {"heading": "How to browse the archive ?"}
    )


def _browse_search_view(request):
    return render(
        request, "browse/search.html", {"heading": "Search software origins to browse"}
    )


def _browse_vault_view(request):
    return render(
        request,
        "browse/vault-ui.html",
        {"heading": "Download archive content from the Vault"},
    )


def _browse_origin_save_view(request):
    return redirect(reverse("origin-save"))


urlpatterns = [
    url(r"^$", _browse_search_view),
    url(r"^help/$", _browse_help_view, name="browse-help"),
    url(r"^search/$", _browse_search_view, name="browse-search"),
    url(r"^vault/$", _browse_vault_view, name="browse-vault"),
    # for backward compatibility
    url(r"^origin/save/$", _browse_origin_save_view, name="browse-origin-save"),
    url(r"^(?P<swhid>swh:[0-9]+:[a-z]+:[0-9a-f]+.*)/$", swhid_browse),
]

urlpatterns += BrowseUrls.get_url_patterns()
