# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.common import swh_templatetags
from swh.web.tests.testcase import SWHWebTestCase


class SWHTemplateTagsTest(SWHWebTestCase):
    def test_urlize_api_links_api(self):
        # update api link with html links content with links
        content = '{"url": "/api/1/abc/"}'
        expected_content = ('{"url": "<a href="/api/1/abc/">/api/1/abc/</a>"}')

        self.assertEqual(swh_templatetags.urlize_links_and_mails(content),
                         expected_content)

    def test_urlize_api_links_browse(self):
        # update /browse link with html links content with links
        content = '{"url": "/browse/def/"}'
        expected_content = ('{"url": "<a href="/browse/def/">'
                            '/browse/def/</a>"}')
        self.assertEqual(swh_templatetags.urlize_links_and_mails(content),
                         expected_content)

    def test_urlize_header_links(self):
        # update api link with html links content with links
        content = """</api/1/abc/>; rel="next"
</api/1/def/>; rel="prev"
"""
        expected_content = """<<a href="/api/1/abc/">/api/1/abc/</a>>; rel="next"
<<a href="/api/1/def/">/api/1/def/</a>>; rel="prev"
"""

        self.assertEqual(swh_templatetags.urlize_header_links(content),
                         expected_content)

    # remove deprecation warnings related to docutils
    @pytest.mark.filterwarnings('ignore:.*U.*mode is deprecated:DeprecationWarning') # noqa
    def test_safe_docstring_display(self):
        # update api link with html links content with links
        docstring = """This is my list header:

        - Here is item 1, with a continuation
          line right here
        - Here is item 2

        Here is something that is not part of the list"""

        expected_docstring = """<p>This is my list header:</p>
<ul class="docstring">
<li>Here is item 1, with a continuation
line right here</li>
<li>Here is item 2</li>
</ul>
<p>Here is something that is not part of the list</p>
"""

        self.assertEqual(swh_templatetags.safe_docstring_display(docstring),
                         expected_docstring)
