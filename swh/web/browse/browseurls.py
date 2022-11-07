# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import List, Optional

from swh.web.utils.urlsindex import UrlsIndex

browse_urls = UrlsIndex()


def browse_route(
    *url_patterns: str,
    view_name: Optional[str] = None,
    checksum_args: Optional[List[str]] = None,
):
    """
    Decorator to ease the registration of a swh-web browse endpoint

    Args:
        url_patterns: list of url patterns used by Django to identify the
            browse routes
        view_name: the name of the Django view associated to the routes used
            to reverse the url
    """
    url_patterns = tuple("^browse/" + url_pattern + "$" for url_pattern in url_patterns)
    view_name = view_name

    def decorator(f):
        # register the route and its view in the browse endpoints index
        for url_pattern in url_patterns:
            browse_urls.add_url_pattern(url_pattern, f, view_name)

        if checksum_args:
            browse_urls.add_redirect_for_checksum_args(
                view_name, url_patterns, checksum_args
            )

        return f

    return decorator
