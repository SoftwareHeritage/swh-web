# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import logging
import os

from flask import Flask

from swh.core import config

DEFAULT_CONFIG = {
    'storage_args': ('list[str]', ['http://localhost:5000/']),
    'storage_class': ('str', 'remote_storage'),
    'log_dir': ('string', '/tmp/swh/log'),
    'debug': ('bool', None),
    'host': ('string', '127.0.0.1'),
    'port': ('int', 6543),
    'secret_key': ('string', 'development key'),
}


# api's definition
app = Flask(__name__)


def read_config(config_file):
    """Read the configuration file `config_file`, update the app with
       parameters (secret_key, conf) and return the parsed configuration as a
       dict"""

    conf = config.read(config_file, DEFAULT_CONFIG)
    config.prepare_folders(conf, 'log_dir')

    if conf['storage_class'] == 'remote_storage':
        from swh.storage.api.client import RemoteStorage as Storage
    else:
        from swh.storage import Storage

    conf['storage'] = Storage(*conf['storage_args'])

    return conf


def load_controllers():
    """Load the controllers for the application"""
    from swh.web.ui import controller  # flake8: noqa


def run_from_webserver(environ, start_response):
    """Run the WSGI app from the webserver, loading the configuration."""

    load_controllers()

    config_path = '/etc/softwareheritage/webapp/webapp.ini'

    conf = read_config(config_path)

    app.secret_key = conf['secret_key']
    app.config['conf'] = conf

    logging.basicConfig(filename=os.path.join(conf['log_dir'], 'web-ui.log'),
                        level=logging.INFO)

    return app(environ, start_response)


def storage():
    """Return the current application's storage.

    """
    return app.config['conf']['storage']
