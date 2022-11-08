# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.tests.helpers import check_api_get_responses
from swh.web.utils import reverse


def test_api_1_ping(api_client):
    url = reverse("api-1-ping")
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert rv.data == "pong"
