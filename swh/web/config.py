# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.core import config
from swh.storage import get_storage
from swh.indexer.storage import get_indexer_storage
from swh.vault.api.client import RemoteVaultClient


DEFAULT_CONFIG = {
    'allowed_hosts': ('list', []),
    'storage': ('dict', {
        'cls': 'remote',
        'args': {
            'url': 'http://127.0.0.1:5002/',
        },
    }),
    'indexer_storage': ('dict', {
        'cls': 'remote',
        'args': {
            'url': 'http://127.0.0.1:5007/',
        }
    }),
    'vault': ('string', 'http://127.0.0.1:5005/'),
    'log_dir': ('string', '/tmp/swh/log'),
    'debug': ('bool', False),
    'host': ('string', '127.0.0.1'),  # development property
    'port': ('int', 5003),            # development property
    'secret_key': ('string', 'development key'),
    'throttling': ('dict', {
        'cache_uri': None,  # production: memcached as cache (127.0.0.1:11211)
                            # development: in-memory cache so None
        'scopes': {
            'swh_api': {
                'limiter_rate': '120/h',
                'exempted_networks': ['127.0.0.0/8']
            }
        }
    })
}

swhweb_config = {}


def get_config(config_file='webapp/webapp'):
    """Read the configuration file `config_file`, update the app with
       parameters (secret_key, conf) and return the parsed configuration as a
       dict. If no configuration file is provided, return a default
       configuration."""

    if not swhweb_config:
        cfg = config.load_named_config(config_file, DEFAULT_CONFIG)
        swhweb_config.update(cfg)
        config.prepare_folders(swhweb_config, 'log_dir')
        swhweb_config['storage'] = get_storage(**swhweb_config['storage'])
        swhweb_config['vault'] = RemoteVaultClient(swhweb_config['vault'])
        swhweb_config['indexer_storage'] = get_indexer_storage(
            **swhweb_config['indexer_storage'])
    return swhweb_config


def storage():
    """Return the current application's SWH storage.

    """
    return get_config()['storage']


def vault():
    """Return the current application's SWH vault.

    """
    return get_config()['vault']


def indexer_storage():
    """Return the current application's SWH indexer storage.

    """
    return get_config()['indexer_storage']
