# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


import os
from swh.web.ui import utils, main
from swh.web.ui.main import app


def _create_url_doc_endpoints(rules):
    def split_path(path, acc):
        rpath = os.path.dirname(path)
        if rpath == '/':
            yield from acc
        else:
            acc.append(rpath+'/')
            yield from split_path(rpath, acc)

    url_doc_endpoints = set()
    for rule in rules:
        url_rule = rule['rule']
        url_doc_endpoints.add(url_rule)
        if '<' in url_rule or '>' in url_rule:
            continue
        acc = []
        for rpath in split_path(url_rule, acc):
            if rpath in url_doc_endpoints:
                continue
            yield rpath
            url_doc_endpoints.add(rpath)


def install_browsable_api_endpoints():
    """Install browsable endpoints.

    """
    url_doc_endpoints = _create_url_doc_endpoints(main.rules())
    for url_doc in url_doc_endpoints:
        endpoint_name = 'doc_api_' + url_doc.strip('/').replace('/', '_')

        def view_func(url_doc=url_doc):
            return utils.filter_endpoints(main.rules(),
                                          url_doc)
        app.add_url_rule(rule=url_doc,
                         endpoint=endpoint_name,
                         view_func=view_func,
                         methods=['GET'])
