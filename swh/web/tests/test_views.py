# Copyright (C) 2023  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.tests.helpers import check_api_post_response
from swh.web.utils import reverse


def test_add_origin_with_contents(api_client, archive_data):
    origin_url = "https://git.example.org/simple_repo"
    contents = [{"path": "test/bar", "data": "foo"}]
    url = reverse(
        "tests-add-origin-with-contents", query_params={"origin_url": origin_url}
    )
    check_api_post_response(api_client, url, data=contents, status_code=200)
    assert archive_data.origin_get([origin_url])
    snapshot = archive_data.snapshot_get_latest(origin_url)
    revision = archive_data.revision_get(snapshot["branches"]["main"]["target"])
    entries = archive_data.directory_ls(revision["directory"], recursive=True)
    assert {entry["name"] for entry in entries} == {"test", "test/bar"}
