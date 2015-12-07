# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.ui import renderers
from swh.web.ui.exc import NotFoundExc
from swh.web.ui.main import app


@app.errorhandler(ValueError)
def value_error_as_bad_request(error):
    """Compute a bad request and add body as payload.

    """
    return renderers.error_response('Bad request', 400, error)


@app.errorhandler(NotFoundExc)
def value_not_found(error):
    """Compute a not found and add body as payload.

    """
    return renderers.error_response('Not found', 404, error)
