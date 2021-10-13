# Copyright (C) 2018-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random
from urllib.parse import quote

from swh.model.model import Origin
from swh.model.swhids import ObjectType
from swh.web.common.identifiers import gen_swhid
from swh.web.common.utils import reverse
from swh.web.tests.django_asserts import assert_contains
from swh.web.tests.utils import check_html_get_response


def test_content_id_browse(client, content):
    cnt_sha1_git = content["sha1_git"]
    swhid = gen_swhid(ObjectType.CONTENT, cnt_sha1_git)

    for swhid_ in (swhid, swhid.upper()):
        url = reverse("browse-swhid", url_args={"swhid": swhid_})

        query_string = "sha1_git:" + cnt_sha1_git
        content_browse_url = reverse(
            "browse-content", url_args={"query_string": query_string}
        )

        resp = check_html_get_response(client, url, status_code=302)
        assert resp["location"] == content_browse_url


def test_directory_id_browse(client, directory):
    swhid = gen_swhid(ObjectType.DIRECTORY, directory)

    for swhid_ in (swhid, swhid.upper()):
        url = reverse("browse-swhid", url_args={"swhid": swhid_})

        directory_browse_url = reverse(
            "browse-directory", url_args={"sha1_git": directory}
        )

        resp = check_html_get_response(client, url, status_code=302)
        assert resp["location"] == directory_browse_url


def test_revision_id_browse(client, revision):
    swhid = gen_swhid(ObjectType.REVISION, revision)

    for swhid_ in (swhid, swhid.upper()):
        url = reverse("browse-swhid", url_args={"swhid": swhid_})

        revision_browse_url = reverse(
            "browse-revision", url_args={"sha1_git": revision}
        )

        resp = check_html_get_response(client, url, status_code=302)
        assert resp["location"] == revision_browse_url

        query_params = {"origin_url": "https://github.com/user/repo"}
        url = reverse(
            "browse-swhid", url_args={"swhid": swhid_}, query_params=query_params
        )

        revision_browse_url = reverse(
            "browse-revision",
            url_args={"sha1_git": revision},
            query_params=query_params,
        )

        resp = check_html_get_response(client, url, status_code=302)
        assert resp["location"] == revision_browse_url


def test_release_id_browse(client, release):
    swhid = gen_swhid(ObjectType.RELEASE, release)

    for swhid_ in (swhid, swhid.upper()):
        url = reverse("browse-swhid", url_args={"swhid": swhid_})

        release_browse_url = reverse("browse-release", url_args={"sha1_git": release})

        resp = check_html_get_response(client, url, status_code=302)
        assert resp["location"] == release_browse_url

        query_params = {"origin_url": "https://github.com/user/repo"}

        url = reverse(
            "browse-swhid", url_args={"swhid": swhid_}, query_params=query_params
        )

        release_browse_url = reverse(
            "browse-release", url_args={"sha1_git": release}, query_params=query_params
        )

        resp = check_html_get_response(client, url, status_code=302)
        assert resp["location"] == release_browse_url


def test_snapshot_id_browse(client, snapshot):
    swhid = gen_swhid(ObjectType.SNAPSHOT, snapshot)

    for swhid_ in (swhid, swhid.upper()):
        url = reverse("browse-swhid", url_args={"swhid": swhid_})

        snapshot_browse_url = reverse(
            "browse-snapshot", url_args={"snapshot_id": snapshot}
        )

        resp = check_html_get_response(client, url, status_code=302)
        assert resp["location"] == snapshot_browse_url

        query_params = {"origin_url": "https://github.com/user/repo"}

        url = reverse(
            "browse-swhid", url_args={"swhid": swhid_}, query_params=query_params
        )

        release_browse_url = reverse(
            "browse-snapshot",
            url_args={"snapshot_id": snapshot},
            query_params=query_params,
        )

        resp = check_html_get_response(client, url, status_code=302)
        assert resp["location"] == release_browse_url


def test_bad_id_browse(client, release):
    swhid = f"swh:1:foo:{release}"
    url = reverse("browse-swhid", url_args={"swhid": swhid})

    check_html_get_response(client, url, status_code=400)


def test_content_id_optional_parts_browse(client, archive_data, content):
    cnt_sha1_git = content["sha1_git"]
    origin_url = "https://github.com/user/repo"

    archive_data.origin_add([Origin(url=origin_url)])

    swhid = gen_swhid(
        ObjectType.CONTENT,
        cnt_sha1_git,
        metadata={"lines": "4-20", "origin": origin_url},
    )
    url = reverse("browse-swhid", url_args={"swhid": swhid})

    query_string = "sha1_git:" + cnt_sha1_git
    content_browse_url = reverse(
        "browse-content",
        url_args={"query_string": query_string},
        query_params={"origin_url": origin_url},
    )
    content_browse_url += "#L4-L20"

    resp = check_html_get_response(client, url, status_code=302)
    assert resp["location"] == content_browse_url


def test_origin_id_not_resolvable(client, release):
    swhid = "swh:1:ori:8068d0075010b590762c6cb5682ed53cb3c13deb"
    url = reverse("browse-swhid", url_args={"swhid": swhid})

    check_html_get_response(client, url, status_code=400)


def test_legacy_swhid_browse(archive_data, client, origin):
    snapshot = archive_data.snapshot_get_latest(origin["url"])
    revision = archive_data.snapshot_get_head(snapshot)
    directory = archive_data.revision_get(revision)["directory"]
    directory_content = archive_data.directory_ls(directory)
    directory_file = random.choice(
        [e for e in directory_content if e["type"] == "file"]
    )
    legacy_swhid = gen_swhid(
        ObjectType.CONTENT,
        directory_file["checksums"]["sha1_git"],
        metadata={"origin": origin["url"]},
    )

    url = reverse("browse-swhid", url_args={"swhid": legacy_swhid})

    resp = check_html_get_response(client, url, status_code=302)
    resp = check_html_get_response(
        client, resp["location"], status_code=200, template_used="browse/content.html"
    )

    swhid = gen_swhid(
        ObjectType.CONTENT,
        directory_file["checksums"]["sha1_git"],
        metadata={
            "origin": origin["url"],
            "visit": gen_swhid(ObjectType.SNAPSHOT, snapshot["id"]),
            "anchor": gen_swhid(ObjectType.REVISION, revision),
        },
    )

    assert_contains(resp, swhid)

    # also check legacy SWHID URL with trailing slash
    url = reverse("browse-swhid-legacy", url_args={"swhid": swhid})

    resp = check_html_get_response(client, url, status_code=302)
    resp = check_html_get_response(
        client, resp["location"], status_code=200, template_used="browse/content.html"
    )

    assert_contains(resp, swhid)


def test_browse_swhid_special_characters_escaping(client, archive_data, directory):
    origin = "http://example.org/?project=abc;"
    archive_data.origin_add([Origin(url=origin)])
    origin_swhid_escaped = quote(origin, safe="/?:@&")
    origin_swhid_url_escaped = quote(origin, safe="/:@;")
    swhid = gen_swhid(
        ObjectType.DIRECTORY, directory, metadata={"origin": origin_swhid_escaped}
    )
    url = reverse("browse-swhid", url_args={"swhid": swhid})

    resp = check_html_get_response(client, url, status_code=302)
    assert origin_swhid_url_escaped in resp["location"]
