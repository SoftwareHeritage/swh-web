# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""
Django development settings for swh-web.
"""

from django.core.cache import cache

from swh.web.config import get_config

swh_web_config = get_config()

swh_web_config.update(
    {
        "show_corner_ribbon": True,
        "corner_ribbon_text": "Development",
    }
)

from .common import *  # noqa

AUTH_PASSWORD_VALIDATORS = []  # disable any pwd validation mechanism

cache.clear()
