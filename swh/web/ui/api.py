# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import logging

from flask import Flask, redirect, render_template, url_for, flash, request

from swh.web.ui.model import content
from swh.web.ui.controller import service
from swh.web.ui import query


SECRET_KEY = 'development key'


# api's definition
app = Flask(__name__)
app.config.from_object(__name__)


@app.route('/')
def main():
    """Main application view.
    At the moment, redirect to the content search view.
    """
    return redirect(url_for('info'))


@app.route('/info')
def info():
    """A simple api to define what the server is all about.

    """
    logging.info('Dev SWH UI')
    return 'Dev SWH UI'


@app.route('/public')
def public():
    """Main application view.
    At the moment, redirect to the content search view.
    """
    return redirect(url_for('search'))


@app.route('/public/search')
def search():
    nb_hashes = request.args.get('nb_hashes')
    if nb_hashes:
        nb_hashes, hashes = query.parse(request.args)
        flash('Search hashes %s posted!' % hashes)
        resp_result = service.search(content.Content(hashes))
    else:
        hashes = []
        resp_result = []

    return render_template('search.html',
                           searched_hash=hashes,
                           entries=resp_result)


def run(conf):
    """Run the api's server.

    Args:
        conf is a dictionary of keywords:
        - 'db_url' the db url's access (through psycopg2 format)
        - 'content_storage_dir' revisions/directories/contents storage on disk
        - 'host'   to override the default 127.0.0.1 to open or not the server
        to the world
        - 'port'   to override the default of 5000 (from the underlying layer:
        flask)
        - 'debug'  activate the verbose logs

    Returns:
        Never

    Raises:
        ?

    """
    print("""SWH Web UI run
host: %s
port: %s
debug: %s""" % (conf['host'], conf.get('port', None), conf['debug']))

    # app.config is the app's state (accessible)
    app.config.update({'conf': conf})

    app.run(host=conf['host'],
            port=conf.get('port', None),
            debug=conf['debug'])
