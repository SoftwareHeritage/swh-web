# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.common.swh_templatetags import (
    urlize_links_and_mails, urlize_header_links, safe_docstring_display
)


def test_urlize_api_links_api():
    # update api link with html links content with links
    content = '{"url": "/api/1/abc/"}'
    expected_content = ('{"url": "<a href="/api/1/abc/">/api/1/abc/</a>"}')

    assert urlize_links_and_mails(content) == expected_content


def test_urlize_api_links_browse():
    # update /browse link with html links content with links
    content = '{"url": "/browse/def/"}'
    expected_content = ('{"url": "<a href="/browse/def/">'
                        '/browse/def/</a>"}')
    assert urlize_links_and_mails(content) == expected_content


def test_urlize_header_links():
    # update api link with html links content with links
    content = '</api/1/abc/>; rel="next"\n</api/1/def/>; rel="prev"'

    expected_content = ('<<a href="/api/1/abc/">/api/1/abc/</a>>; rel="next"\n'
                        '<<a href="/api/1/def/">/api/1/def/</a>>; rel="prev"')

    assert urlize_header_links(content) == expected_content


# remove deprecation warnings related to docutils
@pytest.mark.filterwarnings(
    'ignore:.*U.*mode is deprecated:DeprecationWarning')
def test_safe_docstring_display():
    # update api link with html links content with links
    docstring = (
        'This is my list header:\n\n'
        '    - Here is item 1, with a continuation\n'
        '      line right here\n'
        '    - Here is item 2\n\n'
        '    Here is something that is not part of the list'
    )

    expected_docstring = (
        '<p>This is my list header:</p>\n'
        '<ul class="docstring">\n'
        '<li>Here is item 1, with a continuation\n'
        'line right here</li>\n'
        '<li>Here is item 2</li>\n'
        '</ul>\n'
        '<p>Here is something that is not part of the list</p>\n'
    )

    assert safe_docstring_display(docstring) == expected_docstring
