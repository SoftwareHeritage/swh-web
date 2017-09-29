# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url
from django.shortcuts import redirect

from swh.web.common.utils import reverse
from swh.web.browse.views import (
    directory, content, origin
)


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
    url(r'^$', default_browse_view),
    url(r'^directory/(?P<sha1_git>[0-9a-f]+)/$',
        directory.directory_browse, name='browse-directory'),
    url(r'^directory/(?P<sha1_git>[0-9a-f]+)/(?P<path>.+)/$',
        directory.directory_browse, name='browse-directory'),

    url(r'^content/(?P<sha1_git>[0-9a-f]+)/$',
        content.content_display, name='browse-content'),
    url(r'^content/(?P<sha1_git>[0-9a-f]+)/raw/$',
        content.content_raw, name='browse-content-raw'),

    url(r'^origin/(?P<origin_id>[0-9]+)/$', origin.origin_browse,
        name='browse-origin'),
    url(r'^origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/$',
        origin.origin_browse, name='browse-origin'),

    url(r'^origin/(?P<origin_id>[0-9]+)/directory/$',
        directory.origin_directory_browse,
        name='browse-origin-directory'),
    url(r'^origin/(?P<origin_id>[0-9]+)/directory/(?P<path>.+)/$',
        directory.origin_directory_browse,
        name='browse-origin-directory'),
    url(r'^origin/(?P<origin_id>[0-9]+)/visit/(?P<visit_id>[0-9]+)/directory/$', # noqa
        directory.origin_directory_browse,
        name='browse-origin-directory'),
    url(r'^origin/(?P<origin_id>[0-9]+)/visit/(?P<visit_id>[0-9]+)'
        r'/directory/(?P<path>.+)/$',
        directory.origin_directory_browse,
        name='browse-origin-directory'),
    url(r'^origin/(?P<origin_id>[0-9]+)/ts/(?P<ts>[0-9]+)/directory/$', # noqa
        directory.origin_directory_browse,
        name='browse-origin-directory'),
    url(r'^origin/(?P<origin_id>[0-9]+)/ts/(?P<ts>[0-9]+)'
        r'/directory/(?P<path>.+)/$',
        directory.origin_directory_browse,
        name='browse-origin-directory'),

    url(r'^origin/(?P<origin_id>[0-9]+)/content/(?P<path>.+)/$',
        content.origin_content_display,
        name='browse-origin-content'),
    url(r'^origin/(?P<origin_id>[0-9]+)/visit/(?P<visit_id>[0-9]+)'
        r'/content/(?P<path>.+)/$',
        content.origin_content_display,
        name='browse-origin-content'),
    url(r'^origin/(?P<origin_id>[0-9]+)/ts/(?P<ts>[0-9]+)'
        r'/content/(?P<path>.+)/$',
        content.origin_content_display,
        name='browse-origin-content'),
]
