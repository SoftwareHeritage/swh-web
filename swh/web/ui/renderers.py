# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import yaml

from flask import make_response, request
from flask.ext.api import renderers, parsers
from flask_api.mediatypes import MediaType


class YAMLRenderer(renderers.BaseRenderer):
    media_type = 'application/yaml'

    def render(self, data, media_type, **options):
        return yaml.dump(data, encoding=self.charset)


RENDERERS = [
    'flask.ext.api.renderers.JSONRenderer',
    'flask.ext.api.renderers.BrowsableAPIRenderer',
    'flask.ext.api.parsers.URLEncodedParser',
    'swh.web.ui.renderers.YAMLRenderer',
]


RENDERERS_INSTANCE = [
    renderers.JSONRenderer(),
    renderers.BrowsableAPIRenderer(),
    parsers.URLEncodedParser(),
    YAMLRenderer(),
]


RENDERERS_BY_TYPE = {
    r.media_type: r
    for r in RENDERERS_INSTANCE
}


def error_response(default_error_msg, error_code, error):
    """Private function to create a custom error response.

    """
    # if nothing is requested by client, use json
    default_application_type = 'application/json'
    accept_type = request.headers.get('Accept', default_application_type)
    renderer = RENDERERS_BY_TYPE.get(
        accept_type,
        RENDERERS_BY_TYPE[default_application_type])

    # for edge cases, use the elected renderer's media type
    accept_type = renderer.media_type
    response = make_response(default_error_msg, error_code)
    response.headers['Content-Type'] = accept_type
    response.data = renderer.render({"error": str(error)},
                                    media_type=MediaType(accept_type),
                                    status=error_code,
                                    headers={'Content-Type': accept_type})

    return response
