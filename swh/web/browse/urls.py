# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.shortcuts import render

import swh.web.browse.views.directory # noqa
import swh.web.browse.views.content # noqa
import swh.web.browse.views.identifiers # noqa
import swh.web.browse.views.origin # noqa
import swh.web.browse.views.person # noqa
import swh.web.browse.views.release # noqa
import swh.web.browse.views.revision # noqa
import swh.web.browse.views.snapshot # noqa

from swh.web.browse.browseurls import BrowseUrls


def default_browse_view(request):
    """Default django view used as an entry point
    for the swh browse ui web application.

    The url that point to it is /browse/.

    Args:
        request: input django http request
    """
    return render(request, 'browse.html',
                  {'heading': 'Browse the Software Heritage archive',
                   'empty_browse': True})


urlpatterns = [
    url(r'^$', default_browse_view, name='browse-homepage')
]

urlpatterns += BrowseUrls.get_url_patterns()
