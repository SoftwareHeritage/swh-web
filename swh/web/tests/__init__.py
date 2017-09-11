# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
import django

from swh.web.config import get_config

swh_web_config = get_config()

swh_web_config['debug'] = False
swh_web_config['secret_key'] = 'test'

swh_web_config['limiters'] = {
    'cache_uri': None,
    'limits': {
        'swh_api': {
            'limiter_rate': '60/min',
            'exempted_networks': ['127.0.0.0/8']
        },
        'scope1': {
            'limiter_rate': '3/min'
        },
        'scope2': {
            'limiter_rate': '5/min',
            'exempted_networks': ['127.0.0.0/8']
        }
    }
}

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "swh.web.settings.development")
django.setup()

scope1_limiter_rate = 3
scope2_limiter_rate = 5
