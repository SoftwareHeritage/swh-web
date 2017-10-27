# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

# flake8: noqa

from swh.web.config import get_config

scope1_limiter_rate = 3
scope2_limiter_rate = 5

swh_web_config = get_config()

swh_web_config.update({
    'debug': True,
    'secret_key': 'test',
    'throttling': {
        'cache_uri': None,
        'scopes': {
            'swh_api': {
                'limiter_rate': '60/min',
                'exempted_networks': ['127.0.0.0/8']
            },
            'scope1': {
                'limiter_rate': '%s/min' % scope1_limiter_rate
            },
            'scope2': {
                'limiter_rate': '%s/min' % scope2_limiter_rate,
                'exempted_networks': ['127.0.0.0/8']
            }
        }
    }
})

from .common import *

ALLOWED_HOSTS += ['testserver']  # noqa