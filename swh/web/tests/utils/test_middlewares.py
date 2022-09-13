# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from django.test import modify_settings

from swh.web.utils import reverse


@modify_settings(
    MIDDLEWARE={"remove": ["swh.web.utils.middlewares.ExceptionMiddleware"]}
)
def test_exception_middleware_disabled(client, mocker, snapshot):
    mock_browse_snapshot_directory = mocker.patch(
        "swh.web.browse.views.snapshot.browse_snapshot_directory"
    )
    mock_browse_snapshot_directory.side_effect = Exception("Something went wrong")

    url = reverse("browse-snapshot-directory", url_args={"snapshot_id": snapshot})

    with pytest.raises(Exception, match="Something went wrong"):
        client.get(url)


def test_exception_middleware_enabled(client, mocker, snapshot):
    mock_browse_snapshot_directory = mocker.patch(
        "swh.web.browse.views.snapshot.browse_snapshot_directory"
    )
    mock_browse_snapshot_directory.side_effect = Exception("Something went wrong")

    url = reverse("browse-snapshot-directory", url_args={"snapshot_id": snapshot})

    resp = client.get(url)
    assert resp.status_code == 500
    assert hasattr(resp, "traceback")
    assert "Traceback" in getattr(resp, "traceback")
