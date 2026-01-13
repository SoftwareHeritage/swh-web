# Copyright (C) 2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.helpers import check_html_get_response
from swh.web.utils import reverse


def test_origin_search_no_js_all_origins_with_snapshot(
    client, origins_with_non_empty_snapshot
):
    url = reverse("browse-search", query_params={"no_js": "on"})
    resp = check_html_get_response(
        client, url, template_used="browse-search.html", status_code=200
    )
    for origin in origins_with_non_empty_snapshot:
        assert_contains(resp, origin.url)
