# Copyright (C) 2015-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import timedelta
import itertools
import json

from hypothesis import given
import pytest

from swh.indexer.storage.model import OriginIntrinsicMetadataRow
from swh.model.hashutil import hash_to_bytes
from swh.model.model import Origin, OriginVisit, OriginVisitStatus
from swh.search.exc import SearchQuerySyntaxError
from swh.search.interface import PagedResult
from swh.storage.exc import StorageAPIError, StorageDBError
from swh.storage.utils import now
from swh.web.api.tests.views.utils import scroll_results
from swh.web.api.utils import enrich_origin, enrich_origin_visit
from swh.web.tests.data import (
    INDEXER_TOOL,
    ORIGIN_MASTER_DIRECTORY,
    ORIGIN_MASTER_REVISION,
    ORIGIN_METADATA_KEY,
    ORIGIN_METADATA_VALUE,
)
from swh.web.tests.helpers import check_api_get_responses
from swh.web.tests.strategies import new_origin, new_snapshots, visit_dates
from swh.web.utils import reverse
from swh.web.utils.exc import BadInputExc
from swh.web.utils.origin_visits import get_origin_visits


def test_api_lookup_origin_visits_raise_error(api_client, origin, mocker):
    mock_get_origin_visits = mocker.patch("swh.web.api.views.origin.get_origin_visits")
    err_msg = "voluntary error to check the bad request middleware."

    mock_get_origin_visits.side_effect = BadInputExc(err_msg)

    url = reverse("api-1-origin-visits", url_args={"origin_url": origin["url"]})
    rv = check_api_get_responses(api_client, url, status_code=400)
    assert rv.data == {"exception": "BadInputExc", "reason": err_msg}


def test_api_lookup_origin_visits_raise_swh_storage_error_db(
    api_client, origin, mocker
):
    mock_get_origin_visits = mocker.patch("swh.web.api.views.origin.get_origin_visits")
    err_msg = "Storage exploded! Will be back online shortly!"

    mock_get_origin_visits.side_effect = StorageDBError(err_msg)

    url = reverse("api-1-origin-visits", url_args={"origin_url": origin["url"]})
    rv = check_api_get_responses(api_client, url, status_code=503)
    assert rv.data == {
        "exception": "StorageDBError",
        "reason": "An unexpected error occurred in the backend: %s" % err_msg,
    }


def test_api_lookup_origin_visits_raise_swh_storage_error_api(
    api_client, origin, mocker
):
    mock_get_origin_visits = mocker.patch("swh.web.api.views.origin.get_origin_visits")
    err_msg = "Storage API dropped dead! Will resurrect asap!"

    mock_get_origin_visits.side_effect = StorageAPIError(err_msg)

    url = reverse("api-1-origin-visits", url_args={"origin_url": origin["url"]})
    rv = check_api_get_responses(api_client, url, status_code=503)
    assert rv.data == {
        "exception": "StorageAPIError",
        "reason": "An unexpected error occurred in the api backend: %s" % err_msg,
    }


@given(new_origin(), visit_dates(3), new_snapshots(3))
def test_api_lookup_origin_visits(
    api_client, subtest, new_origin, visit_dates, new_snapshots
):
    # ensure archive_data fixture will be reset between each hypothesis
    # example test run
    @subtest
    def test_inner(archive_data):
        archive_data.origin_add([new_origin])
        for i, visit_date in enumerate(visit_dates):
            origin_visit = archive_data.origin_visit_add(
                [
                    OriginVisit(
                        origin=new_origin.url,
                        date=visit_date,
                        type="git",
                    )
                ]
            )[0]
            archive_data.snapshot_add([new_snapshots[i]])
            visit_status = OriginVisitStatus(
                origin=new_origin.url,
                visit=origin_visit.visit,
                date=now(),
                status="full",
                snapshot=new_snapshots[i].id,
            )
            archive_data.origin_visit_status_add([visit_status])

        all_visits = list(reversed(get_origin_visits(new_origin.to_dict())))

        for last_visit, expected_visits in (
            (None, all_visits[:2]),
            (all_visits[1]["visit"], all_visits[2:]),
        ):

            url = reverse(
                "api-1-origin-visits",
                url_args={"origin_url": new_origin.url},
                query_params={"per_page": 2, "last_visit": last_visit},
            )

            rv = check_api_get_responses(api_client, url, status_code=200)

            for i in range(len(expected_visits)):
                expected_visits[i] = enrich_origin_visit(
                    expected_visits[i],
                    with_origin_link=False,
                    with_origin_visit_link=True,
                    request=rv.wsgi_request,
                )

            assert rv.data == expected_visits


@given(new_origin(), visit_dates(3), new_snapshots(3))
def test_api_lookup_origin_visits_by_id(
    api_client, subtest, new_origin, visit_dates, new_snapshots
):
    # ensure archive_data fixture will be reset between each hypothesis
    # example test run
    @subtest
    def test_inner(archive_data):
        archive_data.origin_add([new_origin])
        for i, visit_date in enumerate(visit_dates):
            origin_visit = archive_data.origin_visit_add(
                [
                    OriginVisit(
                        origin=new_origin.url,
                        date=visit_date,
                        type="git",
                    )
                ]
            )[0]
            archive_data.snapshot_add([new_snapshots[i]])
            visit_status = OriginVisitStatus(
                origin=new_origin.url,
                visit=origin_visit.visit,
                date=now(),
                status="full",
                snapshot=new_snapshots[i].id,
            )
            archive_data.origin_visit_status_add([visit_status])

        all_visits = list(reversed(get_origin_visits(new_origin.to_dict())))

        for last_visit, expected_visits in (
            (None, all_visits[:2]),
            (all_visits[1]["visit"], all_visits[2:4]),
        ):

            url = reverse(
                "api-1-origin-visits",
                url_args={"origin_url": new_origin.url},
                query_params={"per_page": 2, "last_visit": last_visit},
            )

            rv = check_api_get_responses(api_client, url, status_code=200)

            for i in range(len(expected_visits)):
                expected_visits[i] = enrich_origin_visit(
                    expected_visits[i],
                    with_origin_link=False,
                    with_origin_visit_link=True,
                    request=rv.wsgi_request,
                )

            assert rv.data == expected_visits


@given(new_origin(), visit_dates(3), new_snapshots(3))
def test_api_lookup_origin_visit(
    api_client, subtest, new_origin, visit_dates, new_snapshots
):
    # ensure archive_data fixture will be reset between each hypothesis
    # example test run
    @subtest
    def test_inner(archive_data):
        archive_data.origin_add([new_origin])
        for i, visit_date in enumerate(visit_dates):
            origin_visit = archive_data.origin_visit_add(
                [
                    OriginVisit(
                        origin=new_origin.url,
                        date=visit_date,
                        type="git",
                    )
                ]
            )[0]
            visit_id = origin_visit.visit
            archive_data.snapshot_add([new_snapshots[i]])
            visit_status = OriginVisitStatus(
                origin=new_origin.url,
                visit=origin_visit.visit,
                date=visit_date + timedelta(minutes=5),
                status="full",
                snapshot=new_snapshots[i].id,
            )
            archive_data.origin_visit_status_add([visit_status])
            url = reverse(
                "api-1-origin-visit",
                url_args={"origin_url": new_origin.url, "visit_id": visit_id},
            )

            rv = check_api_get_responses(api_client, url, status_code=200)

            expected_visit = archive_data.origin_visit_get_by(new_origin.url, visit_id)

            expected_visit = enrich_origin_visit(
                expected_visit,
                with_origin_link=True,
                with_origin_visit_link=False,
                request=rv.wsgi_request,
            )

            assert rv.data == expected_visit


@given(new_origin())
def test_api_lookup_origin_visit_latest_no_visit(api_client, archive_data, new_origin):
    archive_data.origin_add([new_origin])

    url = reverse("api-1-origin-visit-latest", url_args={"origin_url": new_origin.url})

    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "No visit for origin %s found" % new_origin.url,
    }


@given(new_origin(), visit_dates(2), new_snapshots(1))
def test_api_lookup_origin_visit_latest(
    api_client, subtest, new_origin, visit_dates, new_snapshots
):
    # ensure archive_data fixture will be reset between each hypothesis
    # example test run
    @subtest
    def test_inner(archive_data):
        archive_data.origin_add([new_origin])
        visit_dates.sort()
        visit_ids = []
        for i, visit_date in enumerate(visit_dates):
            origin_visit = archive_data.origin_visit_add(
                [
                    OriginVisit(
                        origin=new_origin.url,
                        date=visit_date,
                        type="git",
                    )
                ]
            )[0]
            visit_ids.append(origin_visit.visit)

        archive_data.snapshot_add([new_snapshots[0]])

        visit_status = OriginVisitStatus(
            origin=new_origin.url,
            visit=visit_ids[0],
            date=now(),
            status="full",
            snapshot=new_snapshots[0].id,
        )
        archive_data.origin_visit_status_add([visit_status])

        url = reverse(
            "api-1-origin-visit-latest", url_args={"origin_url": new_origin.url}
        )

        rv = check_api_get_responses(api_client, url, status_code=200)

        expected_visit = archive_data.origin_visit_status_get_latest(
            new_origin.url, type="git"
        )

        expected_visit = enrich_origin_visit(
            expected_visit,
            with_origin_link=True,
            with_origin_visit_link=False,
            request=rv.wsgi_request,
        )

        assert rv.data == expected_visit


@given(new_origin(), visit_dates(2), new_snapshots(1))
def test_api_lookup_origin_visit_latest_with_snapshot(
    api_client, subtest, new_origin, visit_dates, new_snapshots
):
    # ensure archive_data fixture will be reset between each hypothesis
    # example test run
    @subtest
    def test_inner(archive_data):
        archive_data.origin_add([new_origin])
        visit_dates.sort()
        visit_ids = []
        for i, visit_date in enumerate(visit_dates):
            origin_visit = archive_data.origin_visit_add(
                [
                    OriginVisit(
                        origin=new_origin.url,
                        date=visit_date,
                        type="git",
                    )
                ]
            )[0]
            visit_ids.append(origin_visit.visit)

        archive_data.snapshot_add([new_snapshots[0]])

        # Add snapshot to the latest visit
        visit_id = visit_ids[-1]
        visit_status = OriginVisitStatus(
            origin=new_origin.url,
            visit=visit_id,
            date=now(),
            status="full",
            snapshot=new_snapshots[0].id,
        )
        archive_data.origin_visit_status_add([visit_status])

        url = reverse(
            "api-1-origin-visit-latest",
            url_args={"origin_url": new_origin.url},
            query_params={"require_snapshot": True},
        )

        rv = check_api_get_responses(api_client, url, status_code=200)

        expected_visit = archive_data.origin_visit_status_get_latest(
            new_origin.url, type="git", require_snapshot=True
        )

        expected_visit = enrich_origin_visit(
            expected_visit,
            with_origin_link=True,
            with_origin_visit_link=False,
            request=rv.wsgi_request,
        )

        assert rv.data == expected_visit


def test_api_lookup_origin_visit_not_found(api_client, origin):

    all_visits = list(reversed(get_origin_visits(origin)))

    max_visit_id = max([v["visit"] for v in all_visits])

    url = reverse(
        "api-1-origin-visit",
        url_args={"origin_url": origin["url"], "visit_id": max_visit_id + 1},
    )

    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "Origin %s or its visit with id %s not found!"
        % (origin["url"], max_visit_id + 1),
    }


def test_api_origins_wrong_input(api_client, archive_data):
    """Should fail with 400 if the input is deprecated."""
    # fail if wrong input
    url = reverse("api-1-origins", query_params={"origin_from": 1})
    rv = check_api_get_responses(api_client, url, status_code=400)

    assert rv.data == {
        "exception": "BadInputExc",
        "reason": "Please use the Link header to browse through result",
    }


def test_api_origins(api_client, archive_data):
    page_result = archive_data.origin_list(limit=10000)
    origins = page_result.results
    origin_urls = {origin.url for origin in origins}

    # Get only one
    url = reverse("api-1-origins", query_params={"origin_count": 1})
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert len(rv.data) == 1
    assert {origin["url"] for origin in rv.data} <= origin_urls

    # Get all
    url = reverse("api-1-origins", query_params={"origin_count": len(origins)})
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert len(rv.data) == len(origins)
    assert {origin["url"] for origin in rv.data} == origin_urls

    # Get "all + 10"
    url = reverse("api-1-origins", query_params={"origin_count": len(origins) + 10})
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert len(rv.data) == len(origins)
    assert {origin["url"] for origin in rv.data} == origin_urls


@pytest.mark.parametrize("origin_count", [1, 2, 10, 100])
def test_api_origins_scroll(api_client, archive_data, origin_count):
    page_result = archive_data.origin_list(limit=10000)
    origins = page_result.results
    origin_urls = {origin.url for origin in origins}

    url = reverse("api-1-origins", query_params={"origin_count": origin_count})

    results = scroll_results(api_client, url)

    assert len(results) == len(origins)
    assert {origin["url"] for origin in results} == origin_urls


def test_api_origin_by_url(api_client, archive_data, origin):
    origin_url = origin["url"]
    url = reverse("api-1-origin", url_args={"origin_url": origin_url})
    rv = check_api_get_responses(api_client, url, status_code=200)
    expected_origin = archive_data.origin_get([origin_url])[0]
    expected_origin = enrich_origin(expected_origin, rv.wsgi_request)

    assert rv.data == expected_origin


@given(new_origin())
def test_api_origin_not_found(api_client, new_origin):

    url = reverse("api-1-origin", url_args={"origin_url": new_origin.url})
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "Origin with url %s not found!" % new_origin.url,
    }


@pytest.mark.parametrize("backend", ["swh-search", "swh-storage"])
def test_api_origin_search(api_client, mocker, backend):
    if backend != "swh-search":
        # equivalent to not configuring search in the config
        mocker.patch("swh.web.utils.archive.search", None)

    expected_origins = {
        "https://github.com/wcoder/highlightjs-line-numbers.js",
        "https://github.com/memononen/libtess2",
    }

    # Search for 'github.com', get only one
    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": "github.com"},
        query_params={"limit": 1},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert len(rv.data) == 1
    assert {origin["url"] for origin in rv.data} <= expected_origins
    assert rv.data == [
        enrich_origin({"url": origin["url"]}, request=rv.wsgi_request)
        for origin in rv.data
    ]

    # Search for 'github.com', get all
    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": "github.com"},
        query_params={"limit": 2},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert {origin["url"] for origin in rv.data} == expected_origins
    assert rv.data == [
        enrich_origin({"url": origin["url"]}, request=rv.wsgi_request)
        for origin in rv.data
    ]

    # Search for 'github.com', get more than available
    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": "github.com"},
        query_params={"limit": 10},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert {origin["url"] for origin in rv.data} == expected_origins
    assert rv.data == [
        enrich_origin({"url": origin["url"]}, request=rv.wsgi_request)
        for origin in rv.data
    ]


@pytest.mark.parametrize("backend", ["swh-search", "swh-storage"])
def test_api_origin_search_words(api_client, mocker, backend):
    if backend != "swh-search":
        # equivalent to not configuring search in the config
        mocker.patch("swh.web.utils.archive.search", None)

    expected_origins = {
        "https://github.com/wcoder/highlightjs-line-numbers.js",
        "https://github.com/memononen/libtess2",
    }

    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": "github com"},
        query_params={"limit": 2},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert {origin["url"] for origin in rv.data} == expected_origins

    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": "com github"},
        query_params={"limit": 2},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert {origin["url"] for origin in rv.data} == expected_origins

    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": "memononen libtess2"},
        query_params={"limit": 2},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert len(rv.data) == 1
    assert {origin["url"] for origin in rv.data} == {
        "https://github.com/memononen/libtess2"
    }

    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": "libtess2 memononen"},
        query_params={"limit": 2},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert len(rv.data) == 1
    assert {origin["url"] for origin in rv.data} == {
        "https://github.com/memononen/libtess2"
    }


@pytest.mark.parametrize("backend", ["swh-search", "swh-storage"])
def test_api_origin_search_visit_type(api_client, mocker, backend):
    if backend != "swh-search":
        # equivalent to not configuring search in the config
        mocker.patch("swh.web.utils.archive.search", None)

    expected_origins = {
        "https://github.com/wcoder/highlightjs-line-numbers.js",
        "https://github.com/memononen/libtess2",
    }

    url = reverse(
        "api-1-origin-search",
        url_args={
            "url_pattern": "github com",
        },
        query_params={"visit_type": "git"},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert {origin["url"] for origin in rv.data} == expected_origins

    url = reverse(
        "api-1-origin-search",
        url_args={
            "url_pattern": "github com",
        },
        query_params={"visit_type": "foo"},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert rv.data == []


def test_api_origin_search_use_ql(api_client, mocker):
    expected_origins = {
        "https://github.com/wcoder/highlightjs-line-numbers.js",
        "https://github.com/memononen/libtess2",
    }

    ORIGINS = [{"url": origin} for origin in expected_origins]

    mock_archive_search = mocker.patch("swh.web.utils.archive.search")
    mock_archive_search.origin_search.return_value = PagedResult(
        results=ORIGINS,
        next_page_token=None,
    )

    query = "origin : 'github.com'"

    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": query},
        query_params={"visit_type": "git", "use_ql": "true"},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert {origin["url"] for origin in rv.data} == expected_origins

    mock_archive_search.origin_search.assert_called_with(
        query=query, page_token=None, with_visit=False, visit_types=["git"], limit=70
    )


def test_api_origin_search_ql_syntax_error(api_client, mocker):
    mock_archive_search = mocker.patch("swh.web.utils.archive.search")
    mock_archive_search.origin_search.side_effect = SearchQuerySyntaxError(
        "Invalid syntax"
    )

    query = "this is not a valid query"

    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": query},
        query_params={"visit_type": "git", "use_ql": "true"},
    )
    rv = check_api_get_responses(api_client, url, status_code=400)
    assert rv.data == {
        "exception": "BadInputExc",
        "reason": "Syntax error in search query: Invalid syntax",
    }

    mock_archive_search.origin_search.assert_called_with(
        query=query, page_token=None, with_visit=False, visit_types=["git"], limit=70
    )


@pytest.mark.parametrize("backend", ["swh-search", "swh-storage"])
@pytest.mark.parametrize("limit", [1, 2, 3, 10])
def test_api_origin_search_scroll(api_client, archive_data, mocker, limit, backend):

    if backend != "swh-search":
        # equivalent to not configuring search in the config
        mocker.patch("swh.web.utils.archive.search", None)

    expected_origins = {
        "https://github.com/wcoder/highlightjs-line-numbers.js",
        "https://github.com/memononen/libtess2",
    }

    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": "github.com"},
        query_params={"limit": limit},
    )

    results = scroll_results(api_client, url)

    assert {origin["url"] for origin in results} == expected_origins


@pytest.mark.parametrize("backend", ["swh-search", "swh-storage"])
def test_api_origin_search_limit(api_client, archive_data, tests_data, mocker, backend):
    if backend == "swh-search":
        tests_data["search"].origin_update(
            [{"url": "http://foobar/{}".format(i)} for i in range(2000)]
        )
    else:
        # equivalent to not configuring search in the config
        mocker.patch("swh.web.utils.archive.search", None)

        archive_data.origin_add(
            [Origin(url="http://foobar/{}".format(i)) for i in range(2000)]
        )

    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": "foobar"},
        query_params={"limit": 1050},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert len(rv.data) == 1000


@pytest.mark.parametrize("backend", ["swh-search", "swh-indexer-storage"])
def test_api_origin_metadata_search(api_client, mocker, backend):

    mock_config = mocker.patch("swh.web.utils.archive.config")
    mock_config.get_config.return_value = {
        "search_config": {"metadata_backend": backend}
    }

    url = reverse(
        "api-1-origin-metadata-search", query_params={"fulltext": ORIGIN_METADATA_VALUE}
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    rv.data = sorted(rv.data, key=lambda d: d["url"])

    expected_data = sorted(
        [
            {
                "url": origin_url,
                "metadata": {
                    "from_directory": ORIGIN_MASTER_DIRECTORY[origin_url],
                    "tool": {
                        "name": INDEXER_TOOL["tool_name"],
                        "version": INDEXER_TOOL["tool_version"],
                        "configuration": INDEXER_TOOL["tool_configuration"],
                        "id": INDEXER_TOOL["id"],
                    },
                    "mappings": [],
                },
            }
            for origin_url in sorted(ORIGIN_MASTER_REVISION.keys())
        ],
        key=lambda d: d["url"],
    )

    for i in range(len(expected_data)):
        expected = expected_data[i]
        response = rv.data[i]
        metadata = response["metadata"].pop("metadata")

        assert any(
            [ORIGIN_METADATA_VALUE in json.dumps(val) for val in metadata.values()]
        )

        assert response == expected


def test_api_origin_metadata_search_not_in_idx_storage(api_client, mocker):
    """Tests the origin search for results present in swh-search but not
    returned by ``origin_intrinsic_metadata_get`` (which happens when results
    come from extrinsic metadata).
    """

    mock_idx_storage = mocker.patch("swh.web.utils.archive.idx_storage")
    mock_idx_storage.origin_intrinsic_metadata_get.return_value = []
    mock_idx_storage.origin_intrinsic_metadata_search_fulltext.side_effect = (
        AssertionError("origin_intrinsic_metadata_search_fulltext was called")
    )

    mock_config = mocker.patch("swh.web.utils.archive.config")
    mock_config.get_config.return_value = {
        "search_config": {"metadata_backend": "swh-search"}
    }

    url = reverse(
        "api-1-origin-metadata-search",
        query_params={"fulltext": ORIGIN_METADATA_VALUE},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    rv.data = sorted(rv.data, key=lambda d: d["url"])

    expected_data = sorted(
        [
            {"url": origin_url, "metadata": {}}
            for origin_url in sorted(ORIGIN_MASTER_REVISION.keys())
        ],
        key=lambda d: d["url"],
    )

    assert expected_data == rv.data


@pytest.mark.parametrize(
    "backend,fields",
    itertools.product(["swh-search", "swh-indexer-storage"], ["url", "url,foobar"]),
)
def test_api_origin_metadata_search_url_only(api_client, mocker, backend, fields):
    """Checks that idx_storage.origin_intrinsic_metadata_get is not called when
    its results are not needed"""
    mocker.patch(
        "swh.web.utils.archive.idx_storage.origin_intrinsic_metadata_get",
        side_effect=AssertionError("origin_intrinsic_metadata_get was called"),
    )

    mock_config = mocker.patch("swh.web.utils.archive.config")
    mock_config.get_config.return_value = {
        "search_config": {"metadata_backend": backend}
    }

    url = reverse(
        "api-1-origin-metadata-search",
        query_params={"fulltext": ORIGIN_METADATA_VALUE, "fields": fields},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    rv.data = sorted(rv.data, key=lambda d: d["url"])

    expected_data = sorted(
        [{"url": origin_url} for origin_url in sorted(ORIGIN_MASTER_REVISION.keys())],
        key=lambda d: d["url"],
    )

    assert expected_data == rv.data


def test_api_origin_metadata_search_limit(api_client, mocker):
    mock_idx_storage = mocker.patch("swh.web.utils.archive.idx_storage")
    oimsft = mock_idx_storage.origin_intrinsic_metadata_search_fulltext

    oimsft.side_effect = lambda conjunction, limit: [
        OriginIntrinsicMetadataRow(
            id=origin_url,
            from_directory=hash_to_bytes(directory),
            indexer_configuration_id=INDEXER_TOOL["id"],
            metadata={ORIGIN_METADATA_KEY: ORIGIN_METADATA_VALUE},
            mappings=[],
        )
        for origin_url, directory in ORIGIN_MASTER_DIRECTORY.items()
    ]

    url = reverse(
        "api-1-origin-metadata-search", query_params={"fulltext": ORIGIN_METADATA_VALUE}
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert len(rv.data) == len(ORIGIN_MASTER_REVISION)
    oimsft.assert_called_with(conjunction=[ORIGIN_METADATA_VALUE], limit=70)

    url = reverse(
        "api-1-origin-metadata-search",
        query_params={"fulltext": ORIGIN_METADATA_VALUE, "limit": 10},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert len(rv.data) == len(ORIGIN_MASTER_REVISION)
    oimsft.assert_called_with(conjunction=[ORIGIN_METADATA_VALUE], limit=10)

    url = reverse(
        "api-1-origin-metadata-search",
        query_params={"fulltext": ORIGIN_METADATA_VALUE, "limit": 987},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)
    assert len(rv.data) == len(ORIGIN_MASTER_REVISION)
    oimsft.assert_called_with(conjunction=[ORIGIN_METADATA_VALUE], limit=100)


def test_api_origin_intrinsic_metadata(api_client, origin):

    url = reverse(
        "api-origin-intrinsic-metadata", url_args={"origin_url": origin["url"]}
    )
    rv = check_api_get_responses(api_client, url, status_code=200)

    assert ORIGIN_METADATA_KEY in rv.data
    assert rv.data[ORIGIN_METADATA_KEY] == ORIGIN_METADATA_VALUE


def test_api_origin_metadata_search_invalid(api_client, mocker):
    mock_idx_storage = mocker.patch("swh.web.utils.archive.idx_storage")
    url = reverse("api-1-origin-metadata-search")
    check_api_get_responses(api_client, url, status_code=400)
    mock_idx_storage.assert_not_called()


@pytest.mark.parametrize("backend", ["swh-counters", "swh-storage"])
def test_api_stat_counters(api_client, mocker, backend):

    mock_config = mocker.patch("swh.web.utils.archive.config")
    mock_config.get_config.return_value = {"counters_backend": backend}

    url = reverse("api-1-stat-counters")
    rv = check_api_get_responses(api_client, url, status_code=200)

    counts = json.loads(rv.content)

    for obj in ["content", "origin", "release", "directory", "revision"]:
        assert counts.get(obj, 0) > 0


@pytest.fixture
def archived_origins(archive_data):
    page_result = archive_data.origin_list(page_token=None, limit=10000)
    origins = [origin.to_dict() for origin in page_result.results]
    for origin in origins:
        ovs = archive_data.origin_visit_get_with_statuses(origin["url"]).results
        del origin["id"]
        origin["type"] = ovs[0].visit.type

    return origins


def test_api_origin_search_empty_pattern(api_client, archived_origins):
    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": ""},
        query_params={"limit": 10000},
    )

    rv = check_api_get_responses(api_client, url, status_code=200)

    assert {o["url"] for o in rv.data} == {o["url"] for o in archived_origins}


def test_api_origin_search_empty_pattern_and_visit_type(api_client, archived_origins):

    visit_types = {o["type"] for o in archived_origins}

    for visit_type in visit_types:

        url = reverse(
            "api-1-origin-search",
            url_args={"url_pattern": ""},
            query_params={"visit_type": visit_type, "limit": 10000},
        )

        rv = check_api_get_responses(api_client, url, status_code=200)

        assert {o["url"] for o in rv.data} == {
            o["url"] for o in archived_origins if o["type"] == visit_type
        }


@pytest.mark.parametrize(
    "view_name, extra_args",
    [
        ("api-1-origin", {}),
        ("api-1-origin-visits", {}),
        ("api-1-origin-visit", {"visit_id": 1}),
        ("api-1-origin-visit-latest", {}),
        ("api-origin-intrinsic-metadata", {}),
    ],
)
def test_api_origin_by_url_with_extra_trailing_slash(
    api_client, origin, view_name, extra_args
):
    origin_url = origin["url"]
    assert not origin_url.endswith("/")
    origin_url = origin_url + "/"
    url = reverse(view_name, url_args={"origin_url": origin_url, **extra_args})
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": f"Origin with url {origin_url} not found!",
    }
