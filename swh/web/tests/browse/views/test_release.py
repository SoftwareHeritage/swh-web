# Copyright (C) 2018-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from django.utils.html import escape
from hypothesis import given

from swh.web.common.identifiers import gen_swhid
from swh.web.common.utils import reverse, format_utc_iso_date
from swh.web.tests.django_asserts import assert_contains, assert_template_used
from swh.web.tests.strategies import release, origin_with_releases, unknown_release


@given(release())
def test_release_browse(client, archive_data, release):
    _release_browse_checks(client, release, archive_data)


@given(origin_with_releases())
def test_release_browse_with_origin_snapshot(client, archive_data, origin):
    snapshot = archive_data.snapshot_get_latest(origin["url"])
    release = random.choice(
        [
            b["target"]
            for b in snapshot["branches"].values()
            if b["target_type"] == "release"
        ]
    )

    _release_browse_checks(client, release, archive_data, origin_url=origin["url"])
    _release_browse_checks(client, release, archive_data, snapshot_id=snapshot["id"])
    _release_browse_checks(
        client,
        release,
        archive_data,
        origin_url=origin["url"],
        snapshot_id=snapshot["id"],
    )


@given(unknown_release())
def test_release_browse_not_found(client, archive_data, unknown_release):
    url = reverse("browse-release", url_args={"sha1_git": unknown_release})
    resp = client.get(url)
    assert resp.status_code == 404
    assert_template_used(resp, "error.html")
    err_msg = "Release with sha1_git %s not found" % unknown_release
    assert_contains(resp, err_msg, status_code=404)


@given(release())
def test_release_uppercase(client, release):
    url = reverse(
        "browse-release-uppercase-checksum", url_args={"sha1_git": release.upper()}
    )

    resp = client.get(url)
    assert resp.status_code == 302

    redirect_url = reverse("browse-release", url_args={"sha1_git": release})

    assert resp["location"] == redirect_url


def _release_browse_checks(
    client, release, archive_data, origin_url=None, snapshot_id=None
):
    query_params = {"origin_url": origin_url, "snapshot": snapshot_id}

    url = reverse(
        "browse-release", url_args={"sha1_git": release}, query_params=query_params
    )

    release_data = archive_data.release_get(release)

    resp = client.get(url)

    release_id = release_data["id"]
    release_name = release_data["name"]
    author_name = release_data["author"]["name"]

    release_date = release_data["date"]
    message = release_data["message"]
    target_type = release_data["target_type"]
    target = release_data["target"]

    target_url = reverse(
        "browse-revision", url_args={"sha1_git": target}, query_params=query_params
    )
    message_lines = message.split("\n")

    assert resp.status_code == 200
    assert_template_used(resp, "browse/release.html")
    assert_contains(resp, author_name)
    assert_contains(resp, format_utc_iso_date(release_date))
    assert_contains(
        resp,
        "<h6>%s</h6>%s" % (message_lines[0] or "None", "\n".join(message_lines[1:])),
    )
    assert_contains(resp, release_id)
    assert_contains(resp, release_name)
    assert_contains(resp, target_type)
    assert_contains(resp, '<a href="%s">%s</a>' % (escape(target_url), target))

    swh_rel_id = gen_swhid("release", release_id)
    swh_rel_id_url = reverse("browse-swhid", url_args={"swhid": swh_rel_id})
    assert_contains(resp, swh_rel_id)
    assert_contains(resp, swh_rel_id_url)

    if origin_url:
        browse_origin_url = reverse(
            "browse-origin", query_params={"origin_url": origin_url}
        )
        assert_contains(resp, f'href="{browse_origin_url}"')
    elif snapshot_id:
        swh_snp_id = gen_swhid("snapshot", snapshot_id)
        swh_snp_id_url = reverse("browse-swhid", url_args={"swhid": swh_snp_id})
        assert_contains(resp, f'href="{swh_snp_id_url}"')

    if release_data["target_type"] == "revision":
        if origin_url:
            directory_url = reverse(
                "browse-origin-directory",
                query_params={
                    "origin_url": origin_url,
                    "release": release_data["name"],
                    "snapshot": snapshot_id,
                },
            )
        elif snapshot_id:
            directory_url = reverse(
                "browse-snapshot-directory",
                url_args={"snapshot_id": snapshot_id},
                query_params={"release": release_data["name"],},
            )
        else:
            rev = archive_data.revision_get(release_data["target"])
            directory_url = reverse(
                "browse-directory", url_args={"sha1_git": rev["directory"]}
            )
        assert_contains(resp, escape(directory_url))
