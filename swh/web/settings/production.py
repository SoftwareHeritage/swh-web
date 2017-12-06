# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from .common import *  # noqa
from .common import swh_web_config

# activate per-site caching
MIDDLEWARE += ['django.middleware.cache.UpdateCacheMiddleware', # noqa
               'django.middleware.common.CommonMiddleware',
               'django.middleware.cache.FetchFromCacheMiddleware']

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': swh_web_config['throttling']['cache_uri'],
    }
}

# Setup support for proxy headers
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ALLOWED_HOSTS += ['archive.softwareheritage.org']  # noqa
