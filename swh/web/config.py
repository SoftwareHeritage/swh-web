# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

from swh.core import config
from swh.storage import get_storage
from swh.indexer.storage import get_indexer_storage
from swh.vault import get_vault
from swh.scheduler import get_scheduler


DEFAULT_CONFIG = {
    'allowed_hosts': ('list', []),
    'storage': ('dict', {
        'cls': 'remote',
        'args': {
            'url': 'http://127.0.0.1:5002/',
            'timeout': 10,
        },
    }),
    'indexer_storage': ('dict', {
        'cls': 'remote',
        'args': {
            'url': 'http://127.0.0.1:5007/',
            'timeout': 1,
        }
    }),
    'log_dir': ('string', '/tmp/swh/log'),
    'debug': ('bool', False),
    'serve_assets': ('bool', False),
    'host': ('string', '127.0.0.1'),
    'port': ('int', 5004),
    'secret_key': ('string', 'development key'),
    # do not display code highlighting for content > 1MB
    'content_display_max_size': ('int', 1024 * 1024),
    'snapshot_content_max_size': ('int', 1000),
    'throttling': ('dict', {
        'cache_uri': None,  # production: memcached as cache (127.0.0.1:11211)
                            # development: in-memory cache so None
        'scopes': {
            'swh_api': {
                'limiter_rate': {
                    'default': '120/h'
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
                    'POST': '10/h'
                },
                'exempted_networks': ['127.0.0.0/8']
            }
        }
    }),
    'vault': ('dict', {
        'cls': 'remote',
        'args': {
            'url': 'http://127.0.0.1:5005/',
        }
    }),
    'scheduler': ('dict', {
        'cls': 'remote',
        'args': {
            'url': 'http://127.0.0.1:5008/'
        }
    }),
    'grecaptcha': ('dict', {
        'activated': True,
        'validation_url': 'https://www.google.com/recaptcha/api/siteverify',
        'site_key': '',
        'private_key': ''
    }),
    'production_db': ('string', '/var/lib/swh/web.sqlite3'),
    'deposit': ('dict', {
        'private_api_url': 'https://deposit.softwareheritage.org/1/private/',
        'private_api_user': 'swhworker',
        'private_api_password': ''
    }),
    'coverage_count_origins': ('bool', False)
}

swhweb_config = {}


def get_config(config_file='web/web'):
    """Read the configuration file `config_file`.

       If an environment variable SWH_CONFIG_FILENAME is defined, this
       takes precedence over the config_file parameter.

       In any case, update the app with parameters (secret_key, conf)
       and return the parsed configuration as a dict.

       If no configuration file is provided, return a default
       configuration.

    """

    if not swhweb_config:
        config_filename = os.environ.get('SWH_CONFIG_FILENAME')
        if config_filename:
            config_file = config_filename
        cfg = config.load_named_config(config_file, DEFAULT_CONFIG)
        swhweb_config.update(cfg)
        config.prepare_folders(swhweb_config, 'log_dir')
        swhweb_config['storage'] = get_storage(**swhweb_config['storage'])
        swhweb_config['vault'] = get_vault(**swhweb_config['vault'])
        swhweb_config['indexer_storage'] = \
            get_indexer_storage(**swhweb_config['indexer_storage'])
        swhweb_config['scheduler'] = get_scheduler(
            **swhweb_config['scheduler'])
    return swhweb_config


def storage():
    """Return the current application's storage.

    """
    return get_config()['storage']


def vault():
    """Return the current application's vault.

    """
    return get_config()['vault']


def indexer_storage():
    """Return the current application's indexer storage.

    """
    return get_config()['indexer_storage']


def scheduler():
    """Return the current application's scheduler.

    """
    return get_config()['scheduler']
