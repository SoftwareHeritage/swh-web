# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import logging
import os

from flask.ext.api import FlaskAPI
from swh.core import config

from swh.web.ui.renderers import RENDERERS


DEFAULT_CONFIG = {
    'storage_args': ('list[str]', ['http://localhost:5000/']),
    'storage_class': ('str', 'remote_storage'),
    'log_dir': ('string', '/tmp/swh/log'),
    'debug': ('bool', None),
    'host': ('string', '127.0.0.1'),
    'port': ('int', 6543),
    'secret_key': ('string', 'development key'),
    'max_upload_size': ('int', 16 * 1024 * 1024),
    'upload_folder': ('string', '/tmp/swh-web-ui/uploads'),
    'upload_allowed_extensions': ('list[str]', [])  # means all are accepted
}

# api's definition
app = FlaskAPI(__name__)


def read_config(config_file):
    """Read the configuration file `config_file`, update the app with
       parameters (secret_key, conf) and return the parsed configuration as a
       dict"""

    conf = config.read(config_file, DEFAULT_CONFIG)
    config.prepare_folders(conf, 'log_dir', 'upload_folder')

    if conf['storage_class'] == 'remote_storage':
        from swh.storage.api.client import RemoteStorage as Storage
    else:
        from swh.storage import Storage

    conf['storage'] = Storage(*conf['storage_args'])

    return conf


def load_controllers():
    """Load the controllers for the application"""
    from swh.web.ui import api, errorhandler, views, apidoc  # flake8: noqa
    api.install_browsable_api_endpoints()


def rules():
    """Returns rules from the application in dictionary form.

    Beware, must be called after swh.web.ui.main.load_controllers funcall.

    Returns:
        Generator of application's rules.

    """
    for rule in app.url_map._rules:
        yield {'rule': rule.rule,
               'methods': rule.methods,
               'endpoint': rule.endpoint}

def storage():
    """Return the current application's storage.

    """
    return app.config['conf']['storage']


def setup_app(app, conf):
    app.secret_key = conf['secret_key']
    app.config['conf'] = conf
    app.config['MAX_CONTENT_LENGTH'] = conf['max_upload_size']
    app.config['DEFAULT_RENDERERS'] = RENDERERS

    return app


def run_from_webserver(environ, start_response):
    """Run the WSGI app from the webserver, loading the configuration."""

    load_controllers()

    config_path = '/etc/softwareheritage/webapp/webapp.ini'

    conf = read_config(config_path)

    app.secret_key = conf['secret_key']
    app.config['conf'] = conf
    app.config['MAX_CONTENT_LENGTH'] = conf['max_upload_size']
    app.config['DEFAULT_RENDERERS'] = RENDERERS

    logging.basicConfig(filename=os.path.join(conf['log_dir'], 'web-ui.log'),
                        level=logging.INFO)

    return app(environ, start_response)


def run_debug_from(config_path, verbose=False):
    """Run the api's server in dev mode.

    Args:
        conf is a dictionary of keywords:
        - 'db_url' the db url's access (through psycopg2 format)
        - 'content_storage_dir' revisions/directories/contents storage on disk
        - 'host'   to override the default 127.0.0.1 to open or not the server
        to the world
        - 'port'   to override the default of 5000 (from the underlying layer:
        flask)
        - 'debug'  activate the verbose logs
        - 'secret_key' the flask secret key

    Returns:
        Never

    """
    load_controllers()

    conf = read_config(config_path)

    app.secret_key = conf['secret_key']
    app.config['conf'] = conf
    app.config['MAX_CONTENT_LENGTH'] = conf['max_upload_size']
    app.config['DEFAULT_RENDERERS'] = RENDERERS

    host = conf.get('host', '127.0.0.1')
    port = conf.get('port')
    debug = conf.get('debug')

    log_file = os.path.join(conf['log_dir'], 'web-ui.log')
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        handlers=[logging.FileHandler(log_file),
                                  logging.StreamHandler()])

    app.run(host=host, port=port, debug=debug)
