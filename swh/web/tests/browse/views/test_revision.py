# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import json
import random

from hypothesis import given

from django.utils.html import escape

from swh.model.hashutil import hash_to_bytes, hash_to_hex
from swh.model.model import Revision, RevisionType, TimestampWithTimezone
from swh.model.swhids import ObjectType
from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.helpers import check_html_get_response
from swh.web.tests.strategies import new_origin, new_person, new_swh_date
from swh.web.utils import format_utc_iso_date, parse_iso8601_date_to_utc, reverse
from swh.web.utils.identifiers import gen_swhid


def test_revision_browse(client, archive_data, revision):
    _revision_browse_checks(client, archive_data, revision)


def test_revision_origin_snapshot_browse(client, archive_data, swh_scheduler, origin):
    snapshot = archive_data.snapshot_get_latest(origin["url"])
    revision = archive_data.snapshot_get_head(snapshot)

    _revision_browse_checks(client, archive_data, revision, origin_url=origin["url"])
    _revision_browse_checks(client, archive_data, revision, snapshot=snapshot)
    _revision_browse_checks(
        client,
        archive_data,
        revision,
        origin_url=origin["url"],
        snapshot=snapshot,
    )

    revision = random.choice(archive_data.revision_log(revision))["id"]
    _revision_browse_checks(client, archive_data, revision, origin_url=origin["url"])


def test_revision_log_browse(client, archive_data, revision):
    per_page = 10

    revision_log = archive_data.revision_log(revision)

    revision_log_sorted = sorted(
        revision_log,
        key=lambda rev: -parse_iso8601_date_to_utc(rev["committer_date"]).timestamp(),
    )

    url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={"per_page": per_page},
    )

    next_page_url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={
            "offset": per_page,
            "per_page": per_page,
        },
    )

    nb_log_entries = per_page
    if len(revision_log_sorted) < per_page:
        nb_log_entries = len(revision_log_sorted)

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-revision-log.html"
    )
    assert_contains(resp, '<tr class="swh-revision-log-entry', count=nb_log_entries)
    assert_contains(resp, '<a class="page-link">Newer</a>')

    if len(revision_log_sorted) > per_page:
        assert_contains(
            resp,
            '<a class="page-link" href="%s">Older</a>' % escape(next_page_url),
        )

    for log in revision_log_sorted[:per_page]:
        revision_url = reverse("browse-revision", url_args={"sha1_git": log["id"]})
        assert_contains(resp, log["id"][:7])
        assert_contains(resp, log["author"]["name"])
        assert_contains(resp, format_utc_iso_date(log["date"]))
        assert_contains(resp, escape(log["message"]))
        assert_contains(resp, format_utc_iso_date(log["committer_date"]))
        assert_contains(resp, revision_url)

    if len(revision_log_sorted) <= per_page:
        return

    resp = check_html_get_response(
        client, next_page_url, status_code=200, template_used="browse-revision-log.html"
    )

    prev_page_url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={"offset": 0, "per_page": per_page},
    )
    next_page_url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={"offset": 2 * per_page, "per_page": per_page},
    )

    nb_log_entries = len(revision_log_sorted) - per_page
    if nb_log_entries > per_page:
        nb_log_entries = per_page

    assert_contains(resp, '<tr class="swh-revision-log-entry', count=nb_log_entries)

    assert_contains(
        resp, '<a class="page-link" href="%s">Newer</a>' % escape(prev_page_url)
    )

    if len(revision_log_sorted) > 2 * per_page:
        assert_contains(
            resp,
            '<a class="page-link" href="%s">Older</a>' % escape(next_page_url),
        )

    if len(revision_log_sorted) <= 2 * per_page:
        return

    resp = check_html_get_response(
        client, next_page_url, status_code=200, template_used="browse-revision-log.html"
    )

    prev_page_url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={"offset": per_page, "per_page": per_page},
    )
    next_page_url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={"offset": 3 * per_page, "per_page": per_page},
    )

    nb_log_entries = len(revision_log_sorted) - 2 * per_page
    if nb_log_entries > per_page:
        nb_log_entries = per_page

    assert_contains(resp, '<tr class="swh-revision-log-entry', count=nb_log_entries)
    assert_contains(
        resp, '<a class="page-link" href="%s">Newer</a>' % escape(prev_page_url)
    )

    if len(revision_log_sorted) > 3 * per_page:
        assert_contains(
            resp,
            '<a class="page-link" href="%s">Older</a>' % escape(next_page_url),
        )


def test_revision_log_browse_snapshot_context(client, archive_data, origin):
    """Check snapshot context is preserved when browsing revision log view."""
    snapshot = archive_data.snapshot_get_latest(origin["url"])
    revision = snapshot["branches"]["refs/heads/master"]["target"]

    per_page = 10
    revision_log = archive_data.revision_log(revision)

    revision_log_sorted = sorted(
        revision_log,
        key=lambda rev: -parse_iso8601_date_to_utc(rev["committer_date"]).timestamp(),
    )

    url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={
            "per_page": per_page,
            "origin_url": origin["url"],
            "snapshot": snapshot["id"],
        },
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-revision-log.html"
    )

    for log in revision_log_sorted[:per_page]:
        revision_url = reverse(
            "browse-revision",
            url_args={
                "sha1_git": log["id"],
            },
            query_params={
                "origin_url": origin["url"],
                "snapshot": snapshot["id"],
            },
        )
        assert_contains(resp, escape(revision_url))

    if len(revision_log_sorted) <= per_page:
        return

    next_page_url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={
            "offset": per_page,
            "per_page": per_page,
            "origin_url": origin["url"],
            "snapshot": snapshot["id"],
        },
    )
    assert_contains(resp, escape(next_page_url))

    resp = check_html_get_response(
        client, next_page_url, status_code=200, template_used="browse-revision-log.html"
    )

    prev_page_url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={
            "offset": 0,
            "per_page": per_page,
            "origin_url": origin["url"],
            "snapshot": snapshot["id"],
        },
    )
    next_page_url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={
            "offset": 2 * per_page,
            "per_page": per_page,
            "origin_url": origin["url"],
            "snapshot": snapshot["id"],
        },
    )

    assert_contains(resp, escape(prev_page_url))
    assert_contains(resp, escape(next_page_url))


@given(new_origin())
def test_revision_request_errors(client, revision, unknown_revision, new_origin):
    url = reverse("browse-revision", url_args={"sha1_git": unknown_revision})

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert_contains(
        resp, "Revision with sha1_git %s not found" % unknown_revision, status_code=404
    )

    url = reverse(
        "browse-revision",
        url_args={"sha1_git": revision},
        query_params={"origin_url": new_origin.url},
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="error.html"
    )
    assert_contains(
        resp, "the origin mentioned in your request" " appears broken", status_code=404
    )


def test_revision_uppercase(client, revision):
    url = reverse(
        "browse-revision-uppercase-checksum", url_args={"sha1_git": revision.upper()}
    )

    resp = check_html_get_response(client, url, status_code=302)

    redirect_url = reverse("browse-revision", url_args={"sha1_git": revision})

    assert resp["location"] == redirect_url


def _revision_browse_checks(
    client, archive_data, revision, origin_url=None, snapshot=None
):

    query_params = {}
    if origin_url:
        query_params["origin_url"] = origin_url
    if snapshot:
        query_params["snapshot"] = snapshot["id"]

    url = reverse(
        "browse-revision", url_args={"sha1_git": revision}, query_params=query_params
    )

    revision_data = archive_data.revision_get(revision)

    author_name = revision_data["author"]["name"]
    committer_name = revision_data["committer"]["name"]
    dir_id = revision_data["directory"]

    if origin_url:
        snapshot = archive_data.snapshot_get_latest(origin_url)
        history_url = reverse(
            "browse-origin-log",
            query_params={"revision": revision, **query_params},
        )
    elif snapshot:
        history_url = reverse(
            "browse-snapshot-log",
            url_args={"snapshot_id": snapshot["id"]},
            query_params={"revision": revision},
        )
    else:
        history_url = reverse("browse-revision-log", url_args={"sha1_git": revision})

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-revision.html"
    )
    assert_contains(resp, author_name)
    assert_contains(resp, committer_name)
    assert_contains(resp, history_url)

    for parent in revision_data["parents"]:
        parent_url = reverse(
            "browse-revision", url_args={"sha1_git": parent}, query_params=query_params
        )
        assert_contains(resp, '<a href="%s">%s</a>' % (escape(parent_url), parent[:7]))

    author_date = revision_data["date"]
    committer_date = revision_data["committer_date"]

    message_lines = revision_data["message"].split("\n")

    assert_contains(resp, format_utc_iso_date(author_date))
    assert_contains(resp, format_utc_iso_date(committer_date))
    assert_contains(resp, escape(message_lines[0]))
    assert_contains(resp, escape("\n".join(message_lines[1:])))

    assert_contains(resp, "vault-cook-directory")
    assert_contains(resp, "vault-cook-revision")

    swh_rev_id = gen_swhid(ObjectType.REVISION, revision)
    swh_rev_id_url = reverse("browse-swhid", url_args={"swhid": swh_rev_id})
    assert_contains(resp, swh_rev_id)
    assert_contains(resp, swh_rev_id_url)

    swh_dir_id = gen_swhid(ObjectType.DIRECTORY, dir_id)
    swh_dir_id_url = reverse("browse-swhid", url_args={"swhid": swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)

    if origin_url:
        assert_contains(resp, "swh-take-new-snapshot")

    swh_rev_id = gen_swhid(ObjectType.REVISION, revision)
    swh_rev_id_url = reverse("browse-swhid", url_args={"swhid": swh_rev_id})

    if origin_url:
        browse_origin_url = reverse(
            "browse-origin", query_params={"origin_url": origin_url}
        )
        assert_contains(resp, f'href="{browse_origin_url}"')
    elif snapshot:
        swh_snp_id = gen_swhid(ObjectType.SNAPSHOT, snapshot["id"])
        swh_snp_id_url = reverse("browse-swhid", url_args={"swhid": swh_snp_id})
        assert_contains(resp, f'href="{swh_snp_id_url}"')

    swhid_context = {}
    if origin_url:
        swhid_context["origin"] = origin_url
    if snapshot:
        swhid_context["visit"] = gen_swhid(ObjectType.SNAPSHOT, snapshot["id"])

    swh_rev_id = gen_swhid(ObjectType.REVISION, revision, metadata=swhid_context)
    swh_rev_id_url = reverse("browse-swhid", url_args={"swhid": swh_rev_id})
    assert_contains(resp, swh_rev_id)
    assert_contains(resp, swh_rev_id_url)

    swhid_context["anchor"] = gen_swhid(ObjectType.REVISION, revision)

    swh_dir_id = gen_swhid(ObjectType.DIRECTORY, dir_id, metadata=swhid_context)
    swh_dir_id_url = reverse("browse-swhid", url_args={"swhid": swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)


def test_revision_invalid_path(client, archive_data, revision):
    path = "foo/bar"
    url = reverse(
        "browse-revision", url_args={"sha1_git": revision}, query_params={"path": path}
    )

    resp = check_html_get_response(
        client, url, status_code=404, template_used="browse-revision.html"
    )

    directory = archive_data.revision_get(revision)["directory"]
    error_message = (
        f"Directory entry with path {path} from root directory {directory} not found"
    )
    assert_contains(resp, error_message, status_code=404)
    assert_not_contains(resp, "swh-metadata-popover", status_code=404)


@given(new_person(), new_swh_date())
def test_revision_metadata_display(archive_data, client, directory, person, date):
    metadata = {"foo": "bar"}
    revision = Revision(
        directory=hash_to_bytes(directory),
        author=person,
        committer=person,
        message=b"commit message",
        date=TimestampWithTimezone.from_datetime(date),
        committer_date=TimestampWithTimezone.from_datetime(date),
        synthetic=False,
        type=RevisionType.GIT,
        metadata=metadata,
    )
    archive_data.revision_add([revision])

    url = reverse("browse-revision", url_args={"sha1_git": hash_to_hex(revision.id)})

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-revision.html"
    )
    assert_contains(resp, "swh-metadata-popover")
    assert_contains(resp, escape(json.dumps(metadata, indent=4)))
