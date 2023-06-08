# Copyright (C) 2023  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from importlib import reload
import os
import shutil
import tempfile

import pytest

from django.conf import settings
from django.contrib.staticfiles import finders

from swh.web.config import get_config
from swh.web.settings import common as common_settings
from swh.web.settings import tests as tests_settings
from swh.web.tests.django_asserts import assert_contains
from swh.web.utils import reverse

partner_name = "Example"
mirror_config = {
    "partner_name": partner_name,
    "static_path": tempfile.mkdtemp(),
    "partner_logo_static_path": "mirror-partner-logo.png",
}


@pytest.fixture(autouse=True)
def mirror_config_setter(mocker):
    """Plug mirror config in django settings and reload the latters"""
    config = get_config()
    config["mirror_config"] = mirror_config
    mocker.patch("swh.web.settings.common.get_config").return_value = config
    reload(common_settings)
    reload(tests_settings)
    settings._setup()
    finders.get_finder.cache_clear()


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


def test_pages_contain_mirror_logo(client):
    url = reverse("swh-web-homepage")
    response = client.get(url)
    assert_contains(response, "img/swh-mirror.png")


def test_pages_contain_mirror_partner_logo(client):
    swh_logo_path = finders.find("img/swh-logo.png")
    swh_partner_logo_path = os.path.join(
        mirror_config["static_path"], mirror_config["partner_logo_static_path"]
    )
    shutil.copyfile(swh_logo_path, swh_partner_logo_path)

    assert finders.find(mirror_config["partner_logo_static_path"]) is not None

    url = reverse("swh-web-homepage")
    response = client.get(url)
    assert_contains(response, mirror_config["partner_logo_static_path"])
