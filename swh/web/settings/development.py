# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""
Django development settings for swh-web.
"""

from django.core.cache import cache

from .common import *  # noqa

AUTH_PASSWORD_VALIDATORS = []  # disable any pwd validation mechanism

cache.clear()
