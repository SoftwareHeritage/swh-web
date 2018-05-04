# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.conf.urls import url


class UrlsIndex(object):
    """
    Simple helper class for centralizing url patterns of a Django
    web application.

    Derived classes should override the 'scope' class attribute otherwise
    all declared patterns will be grouped under the default one.
    """

    _urlpatterns = {}
    scope = 'default'

    @classmethod
    def add_url_pattern(cls, url_pattern, view, view_name):
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
            cls._urlpatterns[cls.scope].append(url(url_pattern, view,
                                                   name=view_name))
        else:
            cls._urlpatterns[cls.scope].append(url(url_pattern, view))

    @classmethod
    def get_url_patterns(cls):
        """
        Class method that returns the list of url pattern associated to
        the current scope.

        Returns:
            The list of url patterns associated to the current scope
        """
        return cls._urlpatterns[cls.scope]
