# Copyright (C) 2017-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""
Django production settings for swh-web.
"""

from .common import *  # noqa
from .common import CACHES, MIDDLEWARE, REST_FRAMEWORK, WEBPACK_LOADER, swh_web_config

MIDDLEWARE += [
    "swh.web.common.middlewares.HtmlMinifyMiddleware",
]

if swh_web_config.get("throttling", {}).get("cache_uri"):
    CACHES.update(
        {
            "default": {
                "BACKEND": "django.core.cache.backends.memcached.MemcachedCache",
                "LOCATION": swh_web_config["throttling"]["cache_uri"],
            }
        }
    )

# Setup support for proxy headers
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# We're going through seven (or, in that case, 2) proxies thanks to Varnish
REST_FRAMEWORK["NUM_PROXIES"] = 2

db_conf = swh_web_config["production_db"]

# https://docs.djangoproject.com/en/1.10/ref/settings/#databases
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": db_conf.get("name"),
        "HOST": db_conf.get("host"),
        "PORT": db_conf.get("port"),
        "USER": db_conf.get("user"),
        "PASSWORD": db_conf.get("password"),
    }
}

WEBPACK_LOADER["DEFAULT"]["CACHE"] = True
