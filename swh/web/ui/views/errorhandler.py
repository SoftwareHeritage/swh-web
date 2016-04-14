# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.storage.exc import StorageDBError, StorageAPIError

from .. import renderers
from ..exc import NotFoundExc
from ..main import app


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


@app.errorhandler(StorageDBError)
@app.errorhandler(StorageAPIError)
def backend_problem(error):
    """Compute a not found and add body as payload.

    """
    return renderers.error_response('Unexpected problem in SWH Storage.',
                                    503,
                                    error)
