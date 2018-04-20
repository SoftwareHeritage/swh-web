# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from bs4 import BeautifulSoup
from htmlmin import minify


class HtmlPrettifyMiddleware(object):
    """
    Django middleware for prettifying generated HTML in
    development mode.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if 'text/html' in response.get('Content-Type', ''):
            response.content = \
                BeautifulSoup(response.content, 'lxml').prettify()

        return response


class HtmlMinifyMiddleware(object):
    """
    Django middleware for minifying generated HTML in
    production mode.
    """

    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if 'text/html' in response.get('Content-Type', ''):
            try:
                minified_html = minify(response.content.decode('utf-8'),
                                       convert_charrefs=False)
                response.content = minified_html.encode('utf-8')
            except Exception:
                pass
        return response
