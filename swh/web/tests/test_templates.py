# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from copy import deepcopy
import random

from swh.web.common.utils import reverse
from swh.web.config import STAGING_SERVER_NAMES, get_config
from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.utils import check_http_get_response


def test_layout_without_staging_ribbon(client):
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_not_contains(resp, "swh-corner-ribbon")


def test_layout_with_staging_ribbon(client):
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(
        client, url, status_code=200, server_name=random.choice(STAGING_SERVER_NAMES),
    )
    assert_contains(resp, "swh-corner-ribbon")


def test_layout_with_oidc_auth_enabled(client):
    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_contains(resp, reverse("oidc-login"))


def test_layout_without_oidc_auth_enabled(client, mocker):
    config = deepcopy(get_config())
    config["keycloak"]["server_url"] = ""
    mock_get_config = mocker.patch("swh.web.common.utils.get_config")
    mock_get_config.return_value = config

    url = reverse("swh-web-homepage")
    resp = check_http_get_response(client, url, status_code=200)
    assert_contains(resp, reverse("login"))
