# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


import logging

from flask import redirect, render_template, url_for, flash, request


from swh.web.ui.main import app
from swh.web.ui import query
from swh.web.ui.controller import service


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


@app.route('/search')
def search():
    """Search for hashes in swh-storage.

    """
    q = request.args.get('q', '')
    if q:
        flash('Search hash %s posted!' % q)
        hashes = query.group_by_checksums(query.parse(q))
        if hashes != {}:
            api_backend = app.config['conf']['api_backend']
            present = service.search(api_backend, hashes)
            if present:
                message = 'Found!'
            else:
                message = 'Not found!'
        else:
            message = """This is not a hash.
Hint: hexadecimal string with length either 20 (sha1) or 32 (sha256)."""

        return render_template('search.html',
                               searched_hash=q,
                               present=message)
    return render_template('search.html',
                           searched_hash='',
                           present='')

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

    app.config.update({'conf': conf})

    app.run(host=conf['host'],
            port=conf.get('port', None),
            debug=conf['debug'])
