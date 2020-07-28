# Copyright (C) 2018-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from hypothesis import given

from swh.model.identifiers import CONTENT, REVISION, SNAPSHOT
from swh.web.common.identifiers import gen_swhid
from swh.web.common.utils import reverse
from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.strategies import (
    content,
    directory,
    origin,
    revision,
    release,
    snapshot,
)

swhid_prefix = "swh:1:"


@given(content())
def test_content_id_browse(client, content):
    cnt_sha1_git = content["sha1_git"]
    swhid = swhid_prefix + "cnt:" + cnt_sha1_git
    url = reverse("browse-swhid", url_args={"swhid": swhid})

    query_string = "sha1_git:" + cnt_sha1_git
    content_browse_url = reverse(
        "browse-content", url_args={"query_string": query_string}
    )

    resp = client.get(url)

    assert resp.status_code == 302
    assert resp["location"] == content_browse_url


@given(directory())
def test_directory_id_browse(client, directory):
    swhid = swhid_prefix + "dir:" + directory
    url = reverse("browse-swhid", url_args={"swhid": swhid})

    directory_browse_url = reverse("browse-directory", url_args={"sha1_git": directory})

    resp = client.get(url)

    assert resp.status_code == 302
    assert resp["location"] == directory_browse_url


@given(revision())
def test_revision_id_browse(client, revision):
    swhid = swhid_prefix + "rev:" + revision
    url = reverse("browse-swhid", url_args={"swhid": swhid})

    revision_browse_url = reverse("browse-revision", url_args={"sha1_git": revision})

    resp = client.get(url)

    assert resp.status_code == 302
    assert resp["location"] == revision_browse_url

    query_params = {"origin_url": "https://github.com/user/repo"}

    url = reverse("browse-swhid", url_args={"swhid": swhid}, query_params=query_params)

    revision_browse_url = reverse(
        "browse-revision", url_args={"sha1_git": revision}, query_params=query_params
    )

    resp = client.get(url)
    assert resp.status_code == 302
    assert resp["location"] == revision_browse_url


@given(release())
def test_release_id_browse(client, release):
    swhid = swhid_prefix + "rel:" + release
    url = reverse("browse-swhid", url_args={"swhid": swhid})

    release_browse_url = reverse("browse-release", url_args={"sha1_git": release})

    resp = client.get(url)

    assert resp.status_code == 302
    assert resp["location"] == release_browse_url

    query_params = {"origin_url": "https://github.com/user/repo"}

    url = reverse("browse-swhid", url_args={"swhid": swhid}, query_params=query_params)

    release_browse_url = reverse(
        "browse-release", url_args={"sha1_git": release}, query_params=query_params
    )

    resp = client.get(url)
    assert resp.status_code == 302
    assert resp["location"] == release_browse_url


@given(snapshot())
def test_snapshot_id_browse(client, snapshot):
    swhid = swhid_prefix + "snp:" + snapshot
    url = reverse("browse-swhid", url_args={"swhid": swhid})

    snapshot_browse_url = reverse("browse-snapshot", url_args={"snapshot_id": snapshot})

    resp = client.get(url)

    assert resp.status_code == 302
    assert resp["location"] == snapshot_browse_url

    query_params = {"origin_url": "https://github.com/user/repo"}

    url = reverse("browse-swhid", url_args={"swhid": swhid}, query_params=query_params)

    release_browse_url = reverse(
        "browse-snapshot", url_args={"snapshot_id": snapshot}, query_params=query_params
    )

    resp = client.get(url)
    assert resp.status_code == 302
    assert resp["location"] == release_browse_url


@given(release())
def test_bad_id_browse(client, release):
    swhid = swhid_prefix + "foo:" + release
    url = reverse("browse-swhid", url_args={"swhid": swhid})

    resp = client.get(url)
    assert resp.status_code == 400


@given(content())
def test_content_id_optional_parts_browse(client, content):
    cnt_sha1_git = content["sha1_git"]
    optional_parts = ";lines=4-20;origin=https://github.com/user/repo"
    swhid = swhid_prefix + "cnt:" + cnt_sha1_git + optional_parts
    url = reverse("browse-swhid", url_args={"swhid": swhid})

    query_string = "sha1_git:" + cnt_sha1_git
    content_browse_url = reverse(
        "browse-content",
        url_args={"query_string": query_string},
        query_params={"origin_url": "https://github.com/user/repo"},
    )
    content_browse_url += "#L4-L20"

    resp = client.get(url)

    assert resp.status_code == 302
    assert resp["location"] == content_browse_url


@given(release())
def test_origin_id_not_resolvable(client, release):
    swhid = "swh:1:ori:8068d0075010b590762c6cb5682ed53cb3c13deb"
    url = reverse("browse-swhid", url_args={"swhid": swhid})
    resp = client.get(url)
    assert resp.status_code == 400


@given(origin())
def test_legacy_swhid_browse(archive_data, client, origin):
    snapshot = archive_data.snapshot_get_latest(origin["url"])
    revision = archive_data.snapshot_get_head(snapshot)
    directory = archive_data.revision_get(revision)["directory"]
    directory_content = archive_data.directory_ls(directory)
    directory_file = random.choice(
        [e for e in directory_content if e["type"] == "file"]
    )
    legacy_swhid = gen_swhid(
        CONTENT,
        directory_file["checksums"]["sha1_git"],
        metadata={"origin": origin["url"]},
    )

    url = reverse("browse-swhid", url_args={"swhid": legacy_swhid})
    resp = client.get(url)
    assert resp.status_code == 302

    resp = client.get(resp["location"])

    swhid = gen_swhid(
        CONTENT,
        directory_file["checksums"]["sha1_git"],
        metadata={
            "origin": origin["url"],
            "visit": gen_swhid(SNAPSHOT, snapshot),
            "anchor": gen_swhid(REVISION, revision),
        },
    )

    assert_contains(resp, swhid)
