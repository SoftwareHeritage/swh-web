# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

from sphinxcontrib import httpdomain

from sphinx.ext import autodoc

# guard to avoid ImportError when running tests through sbuild
# as there is no Debian package built for swh-docs
try:
    from swh.docs.sphinx.conf import setup as orig_setup
except Exception:
    pass


class SimpleDocumenter(autodoc.FunctionDocumenter):
    """
    Custom autodoc directive to display a docstring unindented
    and without function signature header.
    """
    objtype = "simple"
    # ensure the priority is lesser than the base FunctionDocumenter
    # to avoid side effects with autodoc processing
    priority = -1

    # do not indent the content
    content_indent = ""

    # do not add a header to the docstring
    def add_directive_header(self, sig):
        pass


_swh_web_base_url = 'https://archive.softwareheritage.org'
_swh_web_api_endpoint = 'api'
_swh_web_api_version = 1
_swh_web_api_url = '%s/%s/%s/' % (_swh_web_base_url,
                                  _swh_web_api_endpoint,
                                  _swh_web_api_version)

_swh_web_browse_endpoint = 'browse'
_swh_web_browse_url = '%s/%s/' % (_swh_web_base_url,
                                  _swh_web_browse_endpoint)


def setup(app):
    orig_setup(app)
    app.add_autodocumenter(SimpleDocumenter)
    # set an environment variable indicating we are currently
    # building the swh-web documentation
    os.environ['SWH_WEB_DOC_BUILD'] = '1'


def customize_sphinx_conf(sphinx_conf):
    """
    Utility function used to customize the sphinx doc build for swh-web
    globally (when building doc from swh-docs) or locally (when building doc
    from swh-web).

    Args:
        sphinx_conf (module): a reference to the sphinx conf.py module
            used to build the doc.
    """
    # fix for sphinxcontrib.httpdomain 1.3
    if 'Link' not in httpdomain.HEADER_REFS:
        httpdomain.HEADER_REFS['Link'] = httpdomain.IETFRef(5988, '5')
    sphinx_conf.extlinks['swh_web'] = (_swh_web_base_url + '/%s', None)
    sphinx_conf.extlinks['swh_web_api'] = (_swh_web_api_url + '%s', None)
    sphinx_conf.extlinks['swh_web_browse'] = (_swh_web_browse_url + '%s', None)
    sphinx_conf.setup = setup
