# Copyright (C) 2016 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import flask

from ..main import app


@app.route('/')
def homepage():
    """Home page

    """
    return flask.redirect(flask.url_for('api_doc'))


# @app.route('/about/')
# def about():
#     return flask.render_template('about.html')
