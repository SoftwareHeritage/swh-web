# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.core import config
from swh.storage import get_storage

DEFAULT_CONFIG = {
    'storage': ('dict', {
        'cls': 'remote',
        'args': {
            'url': 'http://127.0.0.1:5002/',
        },
    }),
    'log_dir': ('string', '/tmp/swh/log'),
    'debug': ('bool', True),
    'host': ('string', '127.0.0.1'),
    'port': ('int', 8000),
    'secret_key': ('string', 'development key'),
    'limiter_rate': ('string', '60/min')
}

swhweb_config = None


def get_config(config_file=None):
    """Read the configuration file `config_file`, update the app with
       parameters (secret_key, conf) and return the parsed configuration as a
       dict. If no configuration file is provided, return a default
       configuration."""

    global swhweb_config
    if not swhweb_config or config_file:
        swhweb_config = config.read(config_file, DEFAULT_CONFIG)
        config.prepare_folders(swhweb_config, 'log_dir')
        swhweb_config['storage'] = get_storage(**swhweb_config['storage'])
    return swhweb_config


def storage():
    """Return the current application's SWH storage.

    """
    return get_config()['storage']
