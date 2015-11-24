# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import yaml

from flask.ext.api import renderers, parsers


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
