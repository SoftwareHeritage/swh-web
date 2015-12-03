# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import yaml

from flask import make_response, request
from flask.ext.api import renderers, parsers
from flask_api.mediatypes import MediaType
from swh.web.ui import utils


class SWHFilterEnricher():
    """Global filter on fields.

    """
    def filter_by_fields(self, data):
        """Extract a request parameter 'fields' if it exists to permit the
           filtering on the data dict's keys.

           If such field is not provided, returns the data as is.

        """
        fields = request.args.get('fields')
        if fields:
            fields = set(fields.split(','))
            data = utils.filter_field_keys(data, fields)

        return data


class PlainRenderer(renderers.BaseRenderer):
    """Renderer for plain/text, do nothing but send the data as is.

    """
    media_type = 'text/plain'

    def render(self, data, media_type, **options):
        return data


class YAMLRenderer(renderers.BaseRenderer, SWHFilterEnricher):
    """Renderer for application/yaml.
    Orchestrate from python data structure to yaml.

    """
    media_type = 'application/yaml'

    def render(self, data, media_type, **options):
        data = self.filter_by_fields(data)
        return yaml.dump(data, encoding=self.charset)


class JSONPEnricher():
    """JSONP rendering.

    """
    def enrich_with_jsonp(self, data):
        """Defines a jsonp function that extracts a potential 'callback'
           request parameter holding the function name and wraps the data
           inside a call to such function

           e.g:
           GET /blah/foo/bar renders: {'output': 'wrapped'}
           GET /blah/foo/bar?callback=fn renders: fn({'output': 'wrapped'})
        """
        jsonp = request.args.get('callback')
        if jsonp:
            return '%s(%s)' % (jsonp, data)

        return data


class SWHJSONRenderer(renderers.JSONRenderer,
                      SWHFilterEnricher,
                      JSONPEnricher):
    """Renderer for application/json.
    Serializes in json the data and returns it.

    Also deals with jsonp.  If callback is found in request parameter,
    wrap the result as a function with name the value of the parameter
    query 'callback'.

    """
    def render(self, data, media_type, **options):
        data = self.filter_by_fields(data)
        res = super().render(data, media_type, **options)
        return self.enrich_with_jsonp(res)


class SWHBrowsableAPIRenderer(renderers.BrowsableAPIRenderer):
    """SWH's browsable api renderer.

    """
    template = "api.html"


RENDERERS = [
    'swh.web.ui.renderers.SWHJSONRenderer',
    'swh.web.ui.renderers.SWHBrowsableAPIRenderer',
    'flask.ext.api.parsers.URLEncodedParser',
    'swh.web.ui.renderers.YAMLRenderer',
    'swh.web.ui.renderers.PlainRenderer',
]


RENDERERS_INSTANCE = [
    SWHJSONRenderer(),
    SWHBrowsableAPIRenderer(),
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
