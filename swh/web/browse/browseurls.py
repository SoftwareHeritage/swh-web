# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common.urlsindex import UrlsIndex


class BrowseUrls(UrlsIndex):
    """
    Class to manage swh-web browse application urls.
    """

    scope = "browse"


def browse_route(*url_patterns, view_name=None, checksum_args=None):
    """
    Decorator to ease the registration of a swh-web browse endpoint

    Args:
        url_patterns: list of url patterns used by Django to identify the
            browse routes
        view_name: the name of the Django view associated to the routes used
            to reverse the url
    """
    url_patterns = ["^" + url_pattern + "$" for url_pattern in url_patterns]
    view_name = view_name

    def decorator(f):
        # register the route and its view in the browse endpoints index
        for url_pattern in url_patterns:
            BrowseUrls.add_url_pattern(url_pattern, f, view_name)

        if checksum_args:
            BrowseUrls.add_redirect_for_checksum_args(
                view_name, url_patterns, checksum_args
            )

        return f

    return decorator
