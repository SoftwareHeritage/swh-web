# Copyright (C) 2023  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.test.utils import override_settings

from swh.web.tests.django_asserts import assert_contains
from swh.web.utils import reverse

partner_name = "Example"
mirror_config = {"partner_name": partner_name}


@override_settings(SWH_MIRROR_CONFIG=mirror_config)
def test_page_titles_contain_mirror_partner_name(client):
    url = reverse("swh-web-homepage")
    response = client.get(url)

    mirror_info = f"{partner_name} Mirror of the Software Heritage archive"
    page_title = f"Welcome to the {mirror_info}"

    # welcome sentence in page title and navbar content
    assert_contains(response, page_title, count=2)

    url = reverse("browse-search")
    response = client.get(url)
    # mirror info in page title only
    assert_contains(response, mirror_info, count=1)


@override_settings(SWH_MIRROR_CONFIG=mirror_config)
def test_pages_contain_mirror_logo(client):
    url = reverse("swh-web-homepage")
    response = client.get(url)
    assert_contains(response, "img/swh-mirror.png")
