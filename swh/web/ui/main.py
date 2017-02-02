# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import logging
import os

from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from swh.core import config

from swh.web.ui.renderers import urlize_api_links, safe_docstring_display
from swh.web.ui.renderers import revision_id_from_url, highlight_source
from swh.web.ui.renderers import SWHMultiResponse, urlize_header_links
from swh.storage import get_storage


DEFAULT_CONFIG = {
    'storage': ('dict', {
        'cls': 'remote',
        'args': {
            'url': 'http://127.0.0.1:5002/',
        },
    }),
    'log_dir': ('string', '/tmp/swh/log'),
    'debug': ('bool', None),
    'host': ('string', '127.0.0.1'),
    'port': ('int', 6543),
    'secret_key': ('string', 'development key'),
    'max_log_revs': ('int', 25),
    'limiter': ('dict', {
        'global_limits': ['60 per minute'],
        'headers_enabled': True,
        'strategy': 'moving-window',
        'storage_uri': 'memory://',
        'storage_options': {},
        'in_memory_fallback': ['60 per minute'],
    }),
}

class SWHFlask(Flask):
    """SWH's flask application.

    """
    response_class = SWHMultiResponse


app = SWHFlask(__name__)
app.add_template_filter(urlize_api_links)
app.add_template_filter(urlize_header_links)
app.add_template_filter(safe_docstring_display)
app.add_template_filter(revision_id_from_url)
app.add_template_filter(highlight_source)

def read_config(config_file):
    """Read the configuration file `config_file`, update the app with
       parameters (secret_key, conf) and return the parsed configuration as a
       dict"""

    conf = config.read(config_file, DEFAULT_CONFIG)
    config.prepare_folders(conf, 'log_dir')
    conf['storage'] = get_storage(**conf['storage'])

    return conf

def load_controllers():
    """Load the controllers for the application.

    """
    from swh.web.ui import views, apidoc  # flake8: noqa


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

def prepare_limiter():
    """Prepare Flask Limiter from configuration and App configuration"""
    if hasattr(app, 'limiter'):
        return

    limiter = Limiter(
        app,
        key_func=get_remote_address,
        **app.config['conf']['limiter']
    )
    app.limiter = limiter


def run_from_webserver(environ, start_response):
    """Run the WSGI app from the webserver, loading the configuration.

    Note: This function is called on a per-request basis so beware the side
    effects here!
    """

    if 'conf' not in app.config:
        load_controllers()

        config_path = '/etc/softwareheritage/webapp/webapp.yml'

        conf = read_config(config_path)

        app.secret_key = conf['secret_key']
        app.config['conf'] = conf

        prepare_limiter()

        logging.basicConfig(filename=os.path.join(conf['log_dir'], 'web-ui.log'),
                            level=logging.INFO)

    return app(environ, start_response)


def run_debug_from(config_path, verbose=False):
    """Run the api's server in dev mode.

    Note: This is called only once (contrast with the production mode
    in run_from_webserver function)

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

    host = conf.get('host', '127.0.0.1')
    port = conf.get('port')
    debug = conf.get('debug')

    prepare_limiter()

    log_file = os.path.join(conf['log_dir'], 'web-ui.log')
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        handlers=[logging.FileHandler(log_file),
                                  logging.StreamHandler()])

    app.run(host=host, port=port, debug=debug)
