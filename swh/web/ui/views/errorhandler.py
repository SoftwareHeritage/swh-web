# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.storage.exc import StorageDBError, StorageAPIError

from .. import renderers
from ..exc import NotFoundExc, ForbiddenExc
from ..main import app


@app.errorhandler(ValueError)
def value_error_as_bad_request(error):
    """Compute a bad request response and add body as payload.

    """
    return renderers.error_response(400, error)


@app.errorhandler(NotFoundExc)
def value_not_found(error):
    """Compute a not found response and add body as payload.

    """
    return renderers.error_response(404, error)


@app.errorhandler(ForbiddenExc)
def value_forbidden(error):
    """Compute a forbidden response and add body as payload.

    """
    return renderers.error_response(403, error)


@app.errorhandler(StorageDBError)
@app.errorhandler(StorageAPIError)
def backend_problem(error):
    """Compute a not found and add body as payload.

    """
    return renderers.error_response(503, error)
