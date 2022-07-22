# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.api.apiresponse import compute_link_header
from swh.web.utils.swh_templatetags import (
    docstring_display,
    urlize_header_links,
    urlize_links_and_mails,
)


def test_urlize_http_link():
    link = "https://example.com/api/1/abc/"
    expected_content = f'<a href="{link}">{link}</a>'

    assert urlize_links_and_mails(link) == expected_content


def test_urlize_email():
    email = "someone@example.com"
    expected_content = f'<a href="mailto:{email}">{email}</a>'

    assert urlize_links_and_mails(email) == expected_content


@pytest.mark.parametrize(
    "next_link, prev_link",
    [
        ("https://example.org/api/1/abc/", "https://example.org/api/1/def/"),
        ("https://example.org/api/1/0,5/", "https://example.org/api/1/5,10/"),
    ],
)
def test_urlize_header_links(next_link, prev_link):

    link_header = f'<{next_link}>; rel="next",<{prev_link}>; rel="previous"'

    assert (
        link_header
        == compute_link_header(
            {"headers": {"link-next": next_link, "link-prev": prev_link}}, options={}
        )["Link"]
    )

    expected_content = (
        f'<<a href="{next_link}">{next_link}</a>>; rel="next"\n'
        f'<<a href="{prev_link}">{prev_link}</a>>; rel="previous"'
    )

    assert urlize_header_links(link_header) == expected_content


def test_docstring_display():
    # update api link with html links content with links
    docstring = (
        "This is my list header:\n\n"
        "    - Here is item 1, with a continuation\n"
        "      line right here\n"
        "    - Here is item 2\n\n"
        "    Here is something that is not part of the list"
    )

    expected_docstring = (
        '<div class="swh-rst">'
        "<p>This is my list header:</p>\n"
        "<blockquote>\n"
        '<ul class="simple">\n'
        "<li><p>Here is item 1, with a continuation\n"
        "line right here</p></li>\n"
        "<li><p>Here is item 2</p></li>\n"
        "</ul>\n"
        "<p>Here is something that is not part of the list</p>\n"
        "</blockquote>\n"
        "</div>"
    )

    assert docstring_display(docstring) == expected_docstring
