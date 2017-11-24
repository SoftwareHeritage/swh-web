# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.shortcuts import redirect

from swh.web.common.utils import reverse

import swh.web.browse.views.directory # noqa
import swh.web.browse.views.content # noqa
import swh.web.browse.views.origin # noqa
import swh.web.browse.views.person # noqa
import swh.web.browse.views.revision # noqa

from swh.web.browse.browseurls import BrowseUrls


def default_browse_view(request):
    """Default django view used as an entry point
    for the swh browse ui web application.

    The url that point to it is /browse/.

    Currently, it points to the origin view for the linux kernel
    source tree github mirror.

    Args:
        request: input django http request
    """
    linux_origin_id = '2'
    linux_origin_url = reverse('browse-origin',
                               kwargs={'origin_id': linux_origin_id})
    return redirect(linux_origin_url)


urlpatterns = [
    url(r'^$', default_browse_view, name='browse-homepage')
]

urlpatterns += BrowseUrls.get_url_patterns()
