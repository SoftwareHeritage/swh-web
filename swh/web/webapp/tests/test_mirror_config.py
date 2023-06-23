# Copyright (C) 2023  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
from pathlib import Path
import shutil

import pytest

from django.contrib.staticfiles import finders

from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.helpers import check_html_get_response
from swh.web.utils import reverse

partner_name = "Example"
swh_extra_django_apps = [
    "swh.web.badges",
    "swh.web.jslicenses",
    "swh.web.vault",
]


@pytest.fixture
def mirror_config(tmp_path):
    static_path = os.path.join(tmp_path, "static")
    templates_path = os.path.join(tmp_path, "templates")
    os.makedirs(static_path)
    os.makedirs(templates_path)
    Path(os.path.join(templates_path, "mirror-homepage.html")).touch()
    Path(os.path.join(templates_path, "mirror-footer.html")).touch()

    return {
        "partner_name": partner_name,
        "partner_url": "https://example.org",
        "static_path": static_path,
        "partner_logo_static_path": "mirror-partner-logo.png",
        "templates_path": templates_path,
    }


@pytest.fixture(autouse=True)
def mirror_config_setter(mirror_config, config_updater):
    """Plug mirror config in django settings and reload the latters"""
    config_updater(
        {"mirror_config": mirror_config, "swh_extra_django_apps": swh_extra_django_apps}
    )


def test_page_titles_contain_mirror_partner_name(client):
    url = reverse("swh-web-homepage")
    response = client.get(url)

    mirror_info = f"{partner_name} Mirror of the Software Heritage archive"
    page_title = f"Welcome to the {mirror_info}"

    # welcome sentence in page title and navbar content
    assert_contains(response, page_title, count=2)

    url = reverse("browse-search")
    response = check_html_get_response(client, url, status_code=200)
    # mirror info in page title only
    assert_contains(response, mirror_info, count=1)


def test_pages_contain_mirror_logo(client):
    url = reverse("swh-web-homepage")
    response = check_html_get_response(client, url, status_code=200)
    assert_contains(response, "img/swh-mirror.png")


def test_pages_contain_mirror_partner_logo(client, mirror_config):
    swh_logo_path = finders.find("img/swh-logo.png")
    swh_partner_logo_path = os.path.join(
        mirror_config["static_path"], mirror_config["partner_logo_static_path"]
    )
    shutil.copyfile(swh_logo_path, swh_partner_logo_path)

    assert finders.find(mirror_config["partner_logo_static_path"]) is not None

    url = reverse("swh-web-homepage")
    response = check_html_get_response(client, url, status_code=200)
    assert_contains(response, mirror_config["partner_logo_static_path"])
    assert_contains(response, mirror_config["partner_url"])


def test_pages_contain_save_code_now_external_link(client, origin):
    save_code_now_link = "https://archive.softwareheritage.org/save"
    url = reverse("swh-web-homepage")
    response = check_html_get_response(client, url, status_code=200)
    assert_contains(response, save_code_now_link)

    url = reverse("browse-origin-directory", query_params={"origin_url": origin["url"]})
    response = check_html_get_response(client, url, status_code=200)
    assert_contains(response, save_code_now_link + f"?origin_url={origin['url']}")


def test_admin_menu_is_not_available(client, admin_user):
    client.force_login(admin_user)
    url = reverse("swh-web-homepage")
    response = check_html_get_response(client, url, status_code=200)
    assert_not_contains(response, '<li class="nav-header">Administration</li>')


def test_pages_contain_add_forge_now_external_link(client):
    add_forge_now_link = (
        "https://archive.softwareheritage.org/add-forge/request/create/"
    )
    url = reverse("swh-web-homepage")
    response = check_html_get_response(client, url, status_code=200)
    assert_contains(response, add_forge_now_link)


def test_mirror_custom_homepage_and_footer(client, mirror_config):
    mirror_homepage_html = "<h4>Mirror section</h4>\n"
    mirror_footer_html = "<span>Mirror footer</span>\n"
    templates_path = mirror_config["templates_path"]
    with open(
        os.path.join(templates_path, "mirror-homepage.html"), "w"
    ) as mirror_homepage:
        mirror_homepage.write(mirror_homepage_html)

    with open(os.path.join(templates_path, "mirror-footer.html"), "w") as mirror_footer:
        mirror_footer.write(mirror_footer_html)
    url = reverse("swh-web-homepage")
    response = check_html_get_response(client, url, status_code=200)
    assert_contains(response, mirror_homepage_html)
    assert_contains(response, mirror_footer_html)
