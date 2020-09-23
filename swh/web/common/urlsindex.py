# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Dict, List

from django.conf.urls import url
from django.shortcuts import redirect
import django.urls


class UrlsIndex(object):
    """
    Simple helper class for centralizing url patterns of a Django
    web application.

    Derived classes should override the 'scope' class attribute otherwise
    all declared patterns will be grouped under the default one.
    """

    _urlpatterns = {}  # type: Dict[str, List[django.urls.URLPattern]]
    scope = "default"

    @classmethod
    def add_url_pattern(cls, url_pattern, view, view_name=None):
        """
        Class method that adds an url pattern to the current scope.

        Args:
            url_pattern: regex describing a Django url
            view: function implementing the Django view
            view_name: name of the view used to reverse the url
        """
        if cls.scope not in cls._urlpatterns:
            cls._urlpatterns[cls.scope] = []
        if view_name:
            cls._urlpatterns[cls.scope].append(url(url_pattern, view, name=view_name))
        else:
            cls._urlpatterns[cls.scope].append(url(url_pattern, view))

    @classmethod
    def add_redirect_for_checksum_args(cls, view_name, url_patterns, checksum_args):
        """
        Class method that redirects to view with lowercase checksums
        when upper/mixed case checksums are passed as url arguments.

        Args:
            view_name (str): name of the view to redirect requests
            url_patterns (List[str]): regexps describing the view urls
            checksum_args (List[str]): url argument names corresponding
                                       to checksum values
        """
        new_view_name = view_name + "-uppercase-checksum"
        for url_pattern in url_patterns:
            url_pattern_upper = url_pattern.replace("[0-9a-f]", "[0-9a-fA-F]")

            def view_redirect(request, *args, **kwargs):
                for checksum_arg in checksum_args:
                    checksum_upper = kwargs[checksum_arg]
                    kwargs[checksum_arg] = checksum_upper.lower()
                return redirect(view_name, *args, **kwargs)

            cls.add_url_pattern(url_pattern_upper, view_redirect, new_view_name)

    @classmethod
    def get_url_patterns(cls):
        """
        Class method that returns the list of url pattern associated to
        the current scope.

        Returns:
            The list of url patterns associated to the current scope
        """
        return cls._urlpatterns[cls.scope]
