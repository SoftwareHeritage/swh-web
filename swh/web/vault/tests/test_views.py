# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.tests.helpers import check_html_get_response
from swh.web.utils import reverse


def test_vault_view(client):
    url = reverse("vault")
    check_html_get_response(client, url, status_code=200, template_used="vault-ui.html")


def test_browse_vault_view(client):
    url = reverse("browse-vault")
    resp = check_html_get_response(client, url, status_code=302)
    assert resp["location"] == reverse("vault")
