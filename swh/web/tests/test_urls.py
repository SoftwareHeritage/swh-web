# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.urls import get_resolver


def test_swh_web_urls_have_trailing_slash():
    urls = set(value[1] for value in get_resolver().reverse_dict.values())
    for url in urls:
        if url != "$":
            assert url.endswith("/$")
