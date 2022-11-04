# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.storage.exc import StorageAPIError, StorageDBError
from swh.web.tests.helpers import check_api_get_responses
from swh.web.utils import reverse
from swh.web.utils.exc import BadInputExc


def test_api_1_stat_counters_raise_error(api_client, mocker):
    mock_archive = mocker.patch("swh.web.api.views.stat.archive")
    mock_archive.stat_counters.side_effect = BadInputExc(
        "voluntary error to check the bad request middleware."
    )

    url = reverse("api-1-stat-counters")
    rv = check_api_get_responses(api_client, url, status_code=400)
    assert rv.data == {
        "exception": "BadInputExc",
        "reason": "voluntary error to check the bad request middleware.",
    }


def test_api_1_stat_counters_raise_from_db(api_client, mocker):
    mock_archive = mocker.patch("swh.web.api.views.stat.archive")
    mock_archive.stat_counters.side_effect = StorageDBError(
        "Storage exploded! Will be back online shortly!"
    )

    url = reverse("api-1-stat-counters")
    rv = check_api_get_responses(api_client, url, status_code=503)
    assert rv.data == {
        "exception": "StorageDBError",
        "reason": "An unexpected error occurred in the backend: "
        "Storage exploded! Will be back online shortly!",
    }


def test_api_1_stat_counters_raise_from_api(api_client, mocker):
    mock_archive = mocker.patch("swh.web.api.views.stat.archive")
    mock_archive.stat_counters.side_effect = StorageAPIError(
        "Storage API dropped dead! Will resurrect from its ashes asap!"
    )

    url = reverse("api-1-stat-counters")
    rv = check_api_get_responses(api_client, url, status_code=503)
    assert rv.data == {
        "exception": "StorageAPIError",
        "reason": "An unexpected error occurred in the api backend: "
        "Storage API dropped dead! Will resurrect from its ashes asap!",
    }


def test_api_1_stat_counters(api_client, archive_data):
    url = reverse("api-1-stat-counters")
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert rv.data == archive_data.stat_counters()
