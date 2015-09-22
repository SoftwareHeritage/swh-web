# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


from flask import Flask


SECRET_KEY = 'development key'


# api's definition
app = Flask(__name__)
app.config.from_object(__name__)
