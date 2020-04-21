# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common.urlsindex import UrlsIndex


class AdminUrls(UrlsIndex):
    """
    Class to manage swh-web admin urls.
    """

    scope = "admin"


def admin_route(*url_patterns, view_name=None):
    """
    Decorator to ease the registration of a swh-web admin endpoint

    Args:
        url_patterns: list of url patterns used by Django to identify the
            admin routes
        view_name: the name of the Django view associated to the routes used
            to reverse the url
    """
    url_patterns = ["^" + url_pattern + "$" for url_pattern in url_patterns]

    def decorator(f):
        # register the route and its view in the browse endpoints index
        for url_pattern in url_patterns:
            AdminUrls.add_url_pattern(url_pattern, f, view_name)
        return f

    return decorator
