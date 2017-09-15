# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.shortcuts import redirect

from swh.web.common.utils import reverse
from swh.web.browse.views import (
    directory, content
)


def default_browse_view(request):
    """Default django view used as an entry point
    for the swh ui web application.

    The url that point to it is /browse/.

    Currently, it points to the root directory view associated
    to the last visit of the master branch for the linux kernel
    source tree github mirror.

    Args:
        request: input django http request
    """
    linux_tree_sha1 = '3347b090b27c27082414070a9cbf08a7bb75cbc6'
    linux_tree_url = reverse('browse-directory',
                             kwargs={'sha1_git': linux_tree_sha1})
    return redirect(linux_tree_url)


urlpatterns = [
    url(r'^$', default_browse_view),
    url(r'^directory/(?P<sha1_git>[0-9a-f]+)/$',
        directory.directory_browse, name='browse-directory'),
    url(r'^directory/(?P<sha1_git>[0-9a-f]+)/(?P<path>.+)/$',
        directory.directory_browse, name='browse-directory'),
    url(r'^content/(?P<sha1_git>[0-9a-f]+)/$',
        content.content_display, name='browse-content'),
    url(r'^content/(?P<sha1_git>[0-9a-f]+)/raw/$',
        content.content_raw, name='browse-content-raw')
]
