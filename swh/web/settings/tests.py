# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""
Django tests settings for swh-web.
"""

import sys

from swh.web.config import get_config

scope1_limiter_rate = 3
scope1_limiter_rate_post = 1
scope2_limiter_rate = 5
scope2_limiter_rate_post = 2
scope3_limiter_rate = 1
scope3_limiter_rate_post = 1
save_origin_rate_post = 10

swh_web_config = get_config()

swh_web_config.update({
    'debug': False,
    'secret_key': 'test',
    'throttling': {
        'cache_uri': None,
        'scopes': {
            'swh_api': {
                'limiter_rate': {
                    'default': '60/min'
                },
                'exempted_networks': ['127.0.0.0/8']
            },
            'swh_api_origin_visit_latest': {
                'limiter_rate': {
                    'default': '6000/min'
                },
                'exempted_networks': ['127.0.0.0/8']
            },
            'swh_vault_cooking': {
                'limiter_rate': {
                    'default': '120/h',
                    'GET': '60/m'
                },
                'exempted_networks': ['127.0.0.0/8']
            },
            'swh_save_origin': {
                'limiter_rate': {
                    'default': '120/h',
                    'POST': '%s/h' % save_origin_rate_post,
                }
            },
            'scope1': {
                'limiter_rate': {
                    'default': '%s/min' % scope1_limiter_rate,
                    'POST': '%s/min' % scope1_limiter_rate_post,
                }
            },
            'scope2': {
                'limiter_rate': {
                    'default': '%s/min' % scope2_limiter_rate,
                    'POST': '%s/min' % scope2_limiter_rate_post
                }
            },
            'scope3': {
                'limiter_rate': {
                    'default': '%s/min' % scope3_limiter_rate,
                    'POST': '%s/min' % scope3_limiter_rate_post
                },
                'exempted_networks': ['127.0.0.0/8']
            }
        }
    }
})


from .common import * # noqa
from .common import ALLOWED_HOSTS, LOGGING # noqa

# when not running unit tests, make the webapp fetch data from memory storages
if 'pytest' not in sys.argv[0]:
    swh_web_config.update({
        'debug': True,
    })
    from swh.web.tests.data import get_tests_data, override_storages # noqa
    test_data = get_tests_data()
    override_storages(test_data['storage'], test_data['idx_storage'])
else:
    ALLOWED_HOSTS += ['testserver']

    # Silent DEBUG output when running unit tests
    LOGGING['handlers']['console']['level'] = 'INFO'
