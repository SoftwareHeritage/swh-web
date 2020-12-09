# Copyright (C) 2015-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import timedelta

from hypothesis import given
import pytest
from requests.utils import parse_header_links

from swh.indexer.storage.model import OriginIntrinsicMetadataRow
from swh.model.hashutil import hash_to_bytes
from swh.model.model import Origin, OriginVisit, OriginVisitStatus
from swh.storage.exc import StorageAPIError, StorageDBError
from swh.storage.utils import now
from swh.web.api.utils import enrich_origin, enrich_origin_visit
from swh.web.common.exc import BadInputExc
from swh.web.common.origin_visits import get_origin_visits
from swh.web.common.utils import reverse
from swh.web.tests.data import (
    INDEXER_TOOL,
    ORIGIN_MASTER_REVISION,
    ORIGIN_METADATA_KEY,
    ORIGIN_METADATA_VALUE,
)
from swh.web.tests.strategies import new_origin, new_snapshots, origin, visit_dates
from swh.web.tests.utils import check_api_get_responses


def _scroll_results(api_client, url):
    """Iterates through pages of results, and returns them all."""
    results = []

    while True:
        rv = check_api_get_responses(api_client, url, status_code=200)

        results.extend(rv.data)

        if "Link" in rv:
            for link in parse_header_links(rv["Link"]):
                if link["rel"] == "next":
                    # Found link to next page of results
                    url = link["url"]
                    break
            else:
                # No link with 'rel=next'
                break
        else:
            # No Link header
            break

    return results


def test_api_lookup_origin_visits_raise_error(api_client, mocker):
    mock_get_origin_visits = mocker.patch("swh.web.api.views.origin.get_origin_visits")
    err_msg = "voluntary error to check the bad request middleware."

    mock_get_origin_visits.side_effect = BadInputExc(err_msg)

    url = reverse("api-1-origin-visits", url_args={"origin_url": "http://foo"})
    rv = check_api_get_responses(api_client, url, status_code=400)
    assert rv.data == {"exception": "BadInputExc", "reason": err_msg}


def test_api_lookup_origin_visits_raise_swh_storage_error_db(api_client, mocker):
    mock_get_origin_visits = mocker.patch("swh.web.api.views.origin.get_origin_visits")
    err_msg = "Storage exploded! Will be back online shortly!"

    mock_get_origin_visits.side_effect = StorageDBError(err_msg)

    url = reverse("api-1-origin-visits", url_args={"origin_url": "http://foo"})
    rv = check_api_get_responses(api_client, url, status_code=503)
    assert rv.data == {
        "exception": "StorageDBError",
        "reason": "An unexpected error occurred in the backend: %s" % err_msg,
    }


def test_api_lookup_origin_visits_raise_swh_storage_error_api(api_client, mocker):
    mock_get_origin_visits = mocker.patch("swh.web.api.views.origin.get_origin_visits")
    err_msg = "Storage API dropped dead! Will resurrect asap!"

    mock_get_origin_visits.side_effect = StorageAPIError(err_msg)

    url = reverse("api-1-origin-visits", url_args={"origin_url": "http://foo"})
    rv = check_api_get_responses(api_client, url, status_code=503)
    assert rv.data == {
        "exception": "StorageAPIError",
        "reason": "An unexpected error occurred in the api backend: %s" % err_msg,
    }


@given(new_origin(), visit_dates(3), new_snapshots(3))
def test_api_lookup_origin_visits(
    api_client, archive_data, new_origin, visit_dates, new_snapshots
):

    archive_data.origin_add([new_origin])
    for i, visit_date in enumerate(visit_dates):
        origin_visit = archive_data.origin_visit_add(
            [OriginVisit(origin=new_origin.url, date=visit_date, type="git",)]
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
    api_client, archive_data, new_origin, visit_dates, new_snapshots
):
    archive_data.origin_add([new_origin])
    for i, visit_date in enumerate(visit_dates):
        origin_visit = archive_data.origin_visit_add(
            [OriginVisit(origin=new_origin.url, date=visit_date, type="git",)]
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
    api_client, archive_data, new_origin, visit_dates, new_snapshots
):
    archive_data.origin_add([new_origin])
    for i, visit_date in enumerate(visit_dates):
        origin_visit = archive_data.origin_visit_add(
            [OriginVisit(origin=new_origin.url, date=visit_date, type="git",)]
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
    api_client, archive_data, new_origin, visit_dates, new_snapshots
):
    archive_data.origin_add([new_origin])
    visit_dates.sort()
    visit_ids = []
    for i, visit_date in enumerate(visit_dates):
        origin_visit = archive_data.origin_visit_add(
            [OriginVisit(origin=new_origin.url, date=visit_date, type="git",)]
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

    url = reverse("api-1-origin-visit-latest", url_args={"origin_url": new_origin.url})

    rv = check_api_get_responses(api_client, url, status_code=200)

    expected_visit = archive_data.origin_visit_get_by(new_origin.url, visit_ids[1])

    expected_visit = enrich_origin_visit(
        expected_visit,
        with_origin_link=True,
        with_origin_visit_link=False,
        request=rv.wsgi_request,
    )

    assert rv.data == expected_visit


@given(new_origin(), visit_dates(2), new_snapshots(1))
def test_api_lookup_origin_visit_latest_with_snapshot(
    api_client, archive_data, new_origin, visit_dates, new_snapshots
):
    archive_data.origin_add([new_origin])
    visit_dates.sort()
    visit_ids = []
    for i, visit_date in enumerate(visit_dates):
        origin_visit = archive_data.origin_visit_add(
            [OriginVisit(origin=new_origin.url, date=visit_date, type="git",)]
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


@given(origin())
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
    """Should fail with 400 if the input is deprecated.

    """
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

    results = _scroll_results(api_client, url)

    assert len(results) == len(origins)
    assert {origin["url"] for origin in results} == origin_urls


@given(origin())
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
        mocker.patch("swh.web.common.archive.search", None)

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
        mocker.patch("swh.web.common.archive.search", None)

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
@pytest.mark.parametrize("limit", [1, 2, 3, 10])
def test_api_origin_search_scroll(api_client, archive_data, mocker, limit, backend):

    if backend != "swh-search":
        # equivalent to not configuring search in the config
        mocker.patch("swh.web.common.archive.search", None)

    expected_origins = {
        "https://github.com/wcoder/highlightjs-line-numbers.js",
        "https://github.com/memononen/libtess2",
    }

    url = reverse(
        "api-1-origin-search",
        url_args={"url_pattern": "github.com"},
        query_params={"limit": limit},
    )

    results = _scroll_results(api_client, url)

    assert {origin["url"] for origin in results} == expected_origins


@pytest.mark.parametrize("backend", ["swh-search", "swh-storage"])
def test_api_origin_search_limit(api_client, archive_data, tests_data, mocker, backend):
    if backend == "swh-search":
        tests_data["search"].origin_update(
            [{"url": "http://foobar/{}".format(i)} for i in range(2000)]
        )
    else:
        # equivalent to not configuring search in the config
        mocker.patch("swh.web.common.archive.search", None)

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


def test_api_origin_metadata_search(api_client):

    url = reverse(
        "api-1-origin-metadata-search", query_params={"fulltext": ORIGIN_METADATA_VALUE}
    )
    rv = check_api_get_responses(api_client, url, status_code=200)

    expected_data = [
        {
            "url": origin_url,
            "metadata": {
                "from_revision": master_rev,
                "tool": {
                    "name": INDEXER_TOOL["tool_name"],
                    "version": INDEXER_TOOL["tool_version"],
                    "configuration": INDEXER_TOOL["tool_configuration"],
                    "id": INDEXER_TOOL["id"],
                },
                "metadata": {ORIGIN_METADATA_KEY: ORIGIN_METADATA_VALUE},
                "mappings": [],
            },
        }
        for origin_url, master_rev in ORIGIN_MASTER_REVISION.items()
    ]

    assert rv.data == expected_data


def test_api_origin_metadata_search_limit(api_client, mocker):
    mock_idx_storage = mocker.patch("swh.web.common.archive.idx_storage")
    oimsft = mock_idx_storage.origin_intrinsic_metadata_search_fulltext

    oimsft.side_effect = lambda conjunction, limit: [
        OriginIntrinsicMetadataRow(
            id=origin_url,
            from_revision=hash_to_bytes(master_rev),
            indexer_configuration_id=INDEXER_TOOL["id"],
            metadata={ORIGIN_METADATA_KEY: ORIGIN_METADATA_VALUE},
            mappings=[],
        )
        for origin_url, master_rev in ORIGIN_MASTER_REVISION.items()
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


@given(origin())
def test_api_origin_intrinsic_metadata(api_client, origin):

    url = reverse(
        "api-origin-intrinsic-metadata", url_args={"origin_url": origin["url"]}
    )
    rv = check_api_get_responses(api_client, url, status_code=200)

    expected_data = {ORIGIN_METADATA_KEY: ORIGIN_METADATA_VALUE}
    assert rv.data == expected_data


def test_api_origin_metadata_search_invalid(api_client, mocker):
    mock_idx_storage = mocker.patch("swh.web.common.archive.idx_storage")
    url = reverse("api-1-origin-metadata-search")
    check_api_get_responses(api_client, url, status_code=400)
    mock_idx_storage.assert_not_called()
