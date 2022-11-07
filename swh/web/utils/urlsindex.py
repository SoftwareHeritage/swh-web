# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Callable, List

from django.http.response import HttpResponseBase
from django.shortcuts import redirect
from django.urls import URLPattern
from django.urls import re_path as url


class UrlsIndex:
    """Simple helper class for centralizing URL patterns of a Django web application."""

    def __init__(self):
        self.urlpatterns: List[URLPattern] = []

    def add_url_pattern(
        self,
        url_pattern: str,
        view: Callable[..., HttpResponseBase],
        view_name: str = "",
    ) -> None:
        """
        Adds an URL pattern.

        Args:
            url_pattern: regex describing a Django URL
            view: function implementing the Django view
            view_name: name of the view used to reverse the URL
        """
        if view_name:
            self.urlpatterns.append(url(url_pattern, view, name=view_name))
        else:
            self.urlpatterns.append(url(url_pattern, view))

    def add_redirect_for_checksum_args(
        self, view_name: str, url_patterns: List[str], checksum_args: List[str]
    ) -> None:
        """
        Adds redirection to view with lowercase checksums when upper/mixed case
        checksums are passed as url arguments.

        Args:
            view_name: name of the view to redirect requests
            url_patterns: regexps describing the view URLs
            checksum_args: url argument names corresponding to checksum values
        """
        new_view_name = view_name + "-uppercase-checksum"
        for url_pattern in url_patterns:
            url_pattern_upper = url_pattern.replace("[0-9a-f]", "[0-9a-fA-F]")

            def view_redirect(request, *args, **kwargs):
                for checksum_arg in checksum_args:
                    checksum_upper = kwargs[checksum_arg]
                    kwargs[checksum_arg] = checksum_upper.lower()
                return redirect(view_name, *args, **kwargs)

            self.add_url_pattern(url_pattern_upper, view_redirect, new_view_name)

    def get_url_patterns(self) -> List[URLPattern]:
        """
        Returns the list of registered URL patterns.
        """
        return self.urlpatterns
