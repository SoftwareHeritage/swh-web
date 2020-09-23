# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""
Django production settings for swh-web.
"""

from .common import *  # noqa
from .common import CACHES, MIDDLEWARE, REST_FRAMEWORK, WEBPACK_LOADER, swh_web_config

# activate per-site caching
if "GZip" in MIDDLEWARE[0]:
    MIDDLEWARE.insert(1, "django.middleware.cache.UpdateCacheMiddleware")
else:
    MIDDLEWARE.insert(0, "django.middleware.cache.UpdateCacheMiddleware")

MIDDLEWARE += [
    "swh.web.common.middlewares.HtmlMinifyMiddleware",
    "django.middleware.cache.FetchFromCacheMiddleware",
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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": swh_web_config["production_db"],
    }
}

WEBPACK_LOADER["DEFAULT"]["CACHE"] = True
