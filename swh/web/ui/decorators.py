# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from functools import wraps
from flask import request, current_app


def jsonp(func):
    """Wraps JSONified output for JSONP requests."""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            res = func(*args, **kwargs)
            if hasattr(res, 'data'):  # for a response object, data
                data = res.data
                if isinstance(data, bytes):  # we're dealing in utf-8 bytes
                    data = data.decode('utf-8')
                else:
                    data = str(data)
            else:  # fallback case...
                data = str(res)

            content = ''.join([str(callback), '(', data, ')'])
            return current_app.response_class(
                content,
                mimetype='application/javascript')
        return func(*args, **kwargs)
    return decorated_function
