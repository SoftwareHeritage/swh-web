import re

from dateutil import parser
import pytest

from swh.web.common.utils import reverse
from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.utils import check_html_get_response


@pytest.mark.parametrize("browse_context", ["log"])
def test_snapshot_browse_with_id(client, browse_context, snapshot):
    url = reverse(
        f"browse-snapshot-{browse_context}", url_args={"snapshot_id": snapshot}
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="includes/snapshot-context.html"
    )
    assert_contains(resp, f"swh:1:snp:{snapshot}")


@pytest.mark.parametrize("browse_context", ["log"])
def test_snapshot_browse_with_id_and_origin(
    client, browse_context, archive_data, origin
):
    snapshot = archive_data.snapshot_get_latest(origin["url"])
    url = reverse(
        f"browse-snapshot-{browse_context}",
        url_args={"snapshot_id": snapshot["id"]},
        query_params={"origin_url": origin["url"]},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="includes/snapshot-context.html"
    )
    assert_contains(resp, origin["url"])


@pytest.mark.parametrize("browse_context", ["log"])
def test_snapshot_browse_with_id_origin_and_timestamp(
    client, browse_context, archive_data, origin_with_multiple_visits
):
    visit = archive_data.origin_visit_get(origin_with_multiple_visits["url"])[0]
    url = reverse(
        f"browse-snapshot-{browse_context}",
        url_args={"snapshot_id": visit["snapshot"]},
        query_params={"origin_url": visit["origin"], "timestamp": visit["date"]},
    )
    resp = check_html_get_response(
        client, url, status_code=200, template_used="includes/snapshot-context.html"
    )
    requested_time = parser.parse(visit["date"]).strftime("%d %B %Y, %H:%M")
    assert_contains(resp, requested_time)
    assert_contains(resp, visit["origin"])


@pytest.mark.parametrize("browse_context", ["log"])
def test_snapshot_browse_without_id(client, browse_context, archive_data, origin):
    url = reverse(
        f"browse-snapshot-{browse_context}", query_params={"origin_url": origin["url"]}
    )
    # This will be redirected to /snapshot/<latest_snapshot_id>/log
    resp = check_html_get_response(client, url, status_code=302,)
    snapshot = archive_data.snapshot_get_latest(origin["url"])

    assert resp.url == reverse(
        f"browse-snapshot-{browse_context}",
        url_args={"snapshot_id": snapshot["id"]},
        query_params={"origin_url": origin["url"]},
    )


@pytest.mark.parametrize("browse_context", ["log"])
def test_snapshot_browse_without_id_and_origin(client, browse_context):
    url = reverse(f"browse-snapshot-{browse_context}")
    resp = check_html_get_response(client, url, status_code=400,)
    # assert_contains works only with a success response, using re.search instead
    assert re.search(
        "An origin URL must be provided as a query parameter",
        resp.content.decode("utf-8"),
    )
