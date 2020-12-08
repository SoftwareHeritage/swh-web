# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from hypothesis import given

from swh.web.api.utils import enrich_directory_entry
from swh.web.common.utils import reverse
from swh.web.tests.data import random_sha1
from swh.web.tests.strategies import directory
from swh.web.tests.utils import check_api_get_responses, check_http_get_response


@given(directory())
def test_api_directory(api_client, archive_data, directory):

    url = reverse("api-1-directory", url_args={"sha1_git": directory})
    rv = check_api_get_responses(api_client, url, status_code=200)

    dir_content = list(archive_data.directory_ls(directory))
    expected_data = list(
        map(enrich_directory_entry, dir_content, [rv.wsgi_request] * len(dir_content))
    )

    assert rv.data == expected_data


def test_api_directory_not_found(api_client):
    unknown_directory_ = random_sha1()

    url = reverse("api-1-directory", url_args={"sha1_git": unknown_directory_})
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "Directory with sha1_git %s not found" % unknown_directory_,
    }


@given(directory())
def test_api_directory_with_path_found(api_client, archive_data, directory):

    directory_content = archive_data.directory_ls(directory)
    dir_entry = random.choice(directory_content)

    url = reverse(
        "api-1-directory", url_args={"sha1_git": directory, "path": dir_entry["name"]}
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert rv.data == enrich_directory_entry(dir_entry, rv.wsgi_request)


@given(directory())
def test_api_directory_with_path_not_found(api_client, directory):

    path = "some/path/to/nonexistent/dir/"
    url = reverse("api-1-directory", url_args={"sha1_git": directory, "path": path})
    rv = check_api_get_responses(api_client, url, status_code=404)
    reason = (
        f"Directory entry with path {path} from root directory {directory} not found"
    )
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": reason,
    }


@given(directory())
def test_api_directory_uppercase(api_client, directory):
    url = reverse(
        "api-1-directory-uppercase-checksum", url_args={"sha1_git": directory.upper()}
    )

    resp = check_http_get_response(api_client, url, status_code=302)

    redirect_url = reverse("api-1-directory", url_args={"sha1_git": directory})

    assert resp["location"] == redirect_url
