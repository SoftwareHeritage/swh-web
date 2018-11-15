# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common.urlsindex import UrlsIndex


class BrowseUrls(UrlsIndex):
    """
    Class to manage swh-web browse application urls.
    """

    scope = 'browse'


class browse_route(object):  # noqa: N801
    """
    Decorator to ease the registration of a swh-web browse endpoint

    Args:
        url_patterns: list of url patterns used by Django to identify the browse routes
        view_name: the name of the Django view associated to the routes used to
           reverse the url
    """ # noqa

    def __init__(self, *url_patterns, view_name=None):
        super().__init__()
        self.url_patterns = []
        for url_pattern in url_patterns:
            self.url_patterns.append('^' + url_pattern + '$')
        self.view_name = view_name

    def __call__(self, f):
        # register the route and its view in the browse endpoints index
        for url_pattern in self.url_patterns:
            BrowseUrls.add_url_pattern(url_pattern, f, self.view_name)
        return f
