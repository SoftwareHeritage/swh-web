# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random
import textwrap

from django.utils.html import escape
from hypothesis import given

from swh.model.identifiers import DIRECTORY, REVISION, SNAPSHOT
from swh.web.common.identifiers import get_swh_persistent_id
from swh.web.common.utils import reverse, format_utc_iso_date, parse_timestamp
from swh.web.tests.django_asserts import assert_contains, assert_template_used
from swh.web.tests.strategies import origin, revision, unknown_revision, new_origin


@given(revision())
def test_revision_browse(client, archive_data, revision):
    _revision_browse_checks(client, archive_data, revision)


@given(origin())
def test_revision_origin_snapshot_browse(client, archive_data, origin):
    snapshot = archive_data.snapshot_get_latest(origin["url"])
    revision = archive_data.snapshot_get_head(snapshot)

    _revision_browse_checks(client, archive_data, revision, origin_url=origin["url"])
    _revision_browse_checks(client, archive_data, revision, snapshot=snapshot)
    _revision_browse_checks(
        client, archive_data, revision, origin_url=origin["url"], snapshot=snapshot,
    )

    revision = random.choice(archive_data.revision_log(revision))["id"]
    _revision_browse_checks(client, archive_data, revision, origin_url=origin["url"])


@given(revision())
def test_revision_log_browse(client, archive_data, revision):
    per_page = 10

    revision_log = archive_data.revision_log(revision)

    revision_log_sorted = sorted(
        revision_log,
        key=lambda rev: -parse_timestamp(rev["committer_date"]).timestamp(),
    )

    url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={"per_page": per_page},
    )

    resp = client.get(url)

    next_page_url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={"offset": per_page, "per_page": per_page},
    )

    nb_log_entries = per_page
    if len(revision_log_sorted) < per_page:
        nb_log_entries = len(revision_log_sorted)

    assert resp.status_code == 200
    assert_template_used(resp, "browse/revision-log.html")
    assert_contains(resp, '<tr class="swh-revision-log-entry', count=nb_log_entries)
    assert_contains(resp, '<a class="page-link">Newer</a>')

    if len(revision_log_sorted) > per_page:
        assert_contains(
            resp, '<a class="page-link" href="%s">Older</a>' % escape(next_page_url),
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

    resp = client.get(next_page_url)

    prev_page_url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={"per_page": per_page},
    )
    next_page_url = reverse(
        "browse-revision-log",
        url_args={"sha1_git": revision},
        query_params={"offset": 2 * per_page, "per_page": per_page},
    )

    nb_log_entries = len(revision_log_sorted) - per_page
    if nb_log_entries > per_page:
        nb_log_entries = per_page

    assert resp.status_code == 200
    assert_template_used(resp, "browse/revision-log.html")
    assert_contains(resp, '<tr class="swh-revision-log-entry', count=nb_log_entries)

    assert_contains(
        resp, '<a class="page-link" href="%s">Newer</a>' % escape(prev_page_url)
    )

    if len(revision_log_sorted) > 2 * per_page:
        assert_contains(
            resp, '<a class="page-link" href="%s">Older</a>' % escape(next_page_url),
        )

    if len(revision_log_sorted) <= 2 * per_page:
        return

    resp = client.get(next_page_url)

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

    assert resp.status_code == 200
    assert_template_used(resp, "browse/revision-log.html")
    assert_contains(resp, '<tr class="swh-revision-log-entry', count=nb_log_entries)
    assert_contains(
        resp, '<a class="page-link" href="%s">Newer</a>' % escape(prev_page_url)
    )

    if len(revision_log_sorted) > 3 * per_page:
        assert_contains(
            resp, '<a class="page-link" href="%s">Older</a>' % escape(next_page_url),
        )

    swh_rev_id = get_swh_persistent_id(REVISION, revision)
    swh_rev_id_url = reverse("browse-swh-id", url_args={"swh_id": swh_rev_id})

    assert_contains(
        resp,
        textwrap.indent(
            (
                f"Browse archived revisions history\n"
                f'<a href="{swh_rev_id_url}">\n'
                f"  {swh_rev_id}\n"
                f"</a>"
            ),
            " " * 4,
        ),
    )


@given(revision(), unknown_revision(), new_origin())
def test_revision_request_errors(client, revision, unknown_revision, new_origin):
    url = reverse("browse-revision", url_args={"sha1_git": unknown_revision})
    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, "error.html")
    assert_contains(
        resp, "Revision with sha1_git %s not found" % unknown_revision, status_code=404
    )

    url = reverse(
        "browse-revision",
        url_args={"sha1_git": revision},
        query_params={"origin_url": new_origin.url},
    )

    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, "error.html")
    assert_contains(
        resp, "the origin mentioned in your request" " appears broken", status_code=404
    )


@given(revision())
def test_revision_uppercase(client, revision):
    url = reverse(
        "browse-revision-uppercase-checksum", url_args={"sha1_git": revision.upper()}
    )

    resp = client.get(url)
    assert resp.status_code == 302

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
            "browse-origin-log", query_params={"revision": revision, **query_params},
        )
    elif snapshot:
        history_url = reverse(
            "browse-snapshot-log",
            url_args={"snapshot_id": snapshot["id"]},
            query_params={"revision": revision},
        )
    else:
        history_url = reverse("browse-revision-log", url_args={"sha1_git": revision})

    resp = client.get(url)

    assert resp.status_code == 200
    assert_template_used(resp, "browse/revision.html")
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

    swh_rev_id = get_swh_persistent_id("revision", revision)
    swh_rev_id_url = reverse("browse-swh-id", url_args={"swh_id": swh_rev_id})
    assert_contains(resp, swh_rev_id)
    assert_contains(resp, swh_rev_id_url)

    swh_dir_id = get_swh_persistent_id("directory", dir_id)
    swh_dir_id_url = reverse("browse-swh-id", url_args={"swh_id": swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)

    if origin_url:
        assert_contains(resp, "swh-take-new-snapshot")

    swh_rev_id = get_swh_persistent_id(REVISION, revision)
    swh_rev_id_url = reverse("browse-swh-id", url_args={"swh_id": swh_rev_id})

    if origin_url:
        browse_origin_url = reverse(
            "browse-origin", query_params={"origin_url": origin_url}
        )
        title = (
            f"Browse archived revision for origin\n"
            f'<a href="{browse_origin_url}">\n'
            f"  {origin_url}\n"
            f"</a>"
        )
        indent = " " * 6
    elif snapshot:
        swh_snp_id = get_swh_persistent_id("snapshot", snapshot["id"])
        swh_snp_id_url = reverse("browse-swh-id", url_args={"swh_id": swh_snp_id})
        title = (
            f"Browse archived revision for snapshot\n"
            f'<a href="{swh_snp_id_url}">\n'
            f"  {swh_snp_id}\n"
            f"</a>"
        )
        indent = " " * 6
    else:
        title = (
            f"Browse archived revision\n"
            f'<a href="{swh_rev_id_url}">\n'
            f"  {swh_rev_id}\n"
            f"</a>"
        )
        indent = " " * 4

    assert_contains(
        resp, textwrap.indent(title, indent),
    )

    swhid_context = {}
    if origin_url:
        swhid_context["origin"] = origin_url
    if snapshot:
        swhid_context["visit"] = get_swh_persistent_id(SNAPSHOT, snapshot["id"])

    swh_rev_id = get_swh_persistent_id(REVISION, revision, metadata=swhid_context)
    swh_rev_id_url = reverse("browse-swh-id", url_args={"swh_id": swh_rev_id})
    assert_contains(resp, swh_rev_id)
    assert_contains(resp, swh_rev_id_url)

    swhid_context["anchor"] = get_swh_persistent_id(REVISION, revision)
    swhid_context["path"] = "/"

    swh_dir_id = get_swh_persistent_id(DIRECTORY, dir_id, metadata=swhid_context)
    swh_dir_id_url = reverse("browse-swh-id", url_args={"swh_id": swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)
