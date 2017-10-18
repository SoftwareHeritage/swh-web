# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


_swh_web_base_url = 'https://archive.softwareheritage.org'
_swh_web_api_endpoint = 'api'
_swh_web_api_version = 1
_swh_web_api_url = '%s/%s/%s/' % (_swh_web_base_url,
                                  _swh_web_api_endpoint,
                                  _swh_web_api_version)

_swh_web_browse_endpoint = 'browse'
_swh_web_browse_url = '%s/%s/' % (_swh_web_base_url,
                                  _swh_web_browse_endpoint)


def customize_sphinx_conf(sphinx_conf):
    sphinx_conf.extlinks['swh_web_api'] = (_swh_web_api_url + '%s', None)
    sphinx_conf.extlinks['swh_web_browse'] = (_swh_web_browse_url + '%s', None)
