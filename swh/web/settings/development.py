# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

# flake8: noqa

"""
Django development settings for swh-web.
"""

import os

# guard to avoid side effects on the django settings when building the
# Debian package for swh-web
if os.environ['DJANGO_SETTINGS_MODULE'] == 'swh.web.settings.development':

    from .common import *

    MIDDLEWARE += ['swh.web.common.middlewares.HtmlPrettifyMiddleware']

    from django.core.cache import cache
    cache.clear()
