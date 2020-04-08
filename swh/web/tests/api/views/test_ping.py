# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common.utils import reverse


def test_api_1_ping(api_client):
    url = reverse("api-1-ping")

    rv = api_client.get(url)

    assert rv.status_code == 200, rv.data
    assert rv["Content-Type"] == "application/json"
    assert rv.data == "pong"
