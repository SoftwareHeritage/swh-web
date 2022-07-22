# Copyright (C) 2015-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given

from swh.model.from_disk import DentryPerms
from swh.model.hashutil import hash_to_bytes, hash_to_hex
from swh.model.model import (
    Directory,
    DirectoryEntry,
    Revision,
    RevisionType,
    TimestampWithTimezone,
)
from swh.web.api.utils import enrich_content, enrich_directory_entry, enrich_revision
from swh.web.tests.data import random_sha1
from swh.web.tests.helpers import check_api_get_responses, check_http_get_response
from swh.web.tests.strategies import new_person, new_swh_date
from swh.web.utils import reverse


def test_api_revision(api_client, archive_data, revision):
    url = reverse("api-1-revision", url_args={"sha1_git": revision})
    rv = check_api_get_responses(api_client, url, status_code=200)

    expected_revision = archive_data.revision_get(revision)

    enrich_revision(expected_revision, rv.wsgi_request)

    assert rv.data == expected_revision


def test_api_revision_not_found(api_client):
    unknown_revision_ = random_sha1()

    url = reverse("api-1-revision", url_args={"sha1_git": unknown_revision_})
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "Revision with sha1_git %s not found." % unknown_revision_,
    }


def test_api_revision_raw_ok(api_client, archive_data, revision):
    url = reverse("api-1-revision-raw-message", url_args={"sha1_git": revision})

    expected_message = archive_data.revision_get(revision)["message"]

    rv = check_http_get_response(api_client, url, status_code=200)
    assert rv["Content-Type"] == "application/octet-stream"
    assert rv.content == expected_message.encode()


def test_api_revision_raw_ko_no_rev(api_client):
    unknown_revision_ = random_sha1()

    url = reverse(
        "api-1-revision-raw-message", url_args={"sha1_git": unknown_revision_}
    )
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "Revision with sha1_git %s not found." % unknown_revision_,
    }


def test_api_revision_log(api_client, archive_data, revision):
    limit = 10

    url = reverse(
        "api-1-revision-log",
        url_args={"sha1_git": revision},
        query_params={"limit": limit},
    )

    rv = check_api_get_responses(api_client, url, status_code=200)

    expected_log = archive_data.revision_log(revision, limit=limit)
    expected_log = list(
        map(enrich_revision, expected_log, [rv.wsgi_request] * len(expected_log))
    )

    assert rv.data == expected_log


def test_api_revision_log_not_found(api_client):
    unknown_revision_ = random_sha1()

    url = reverse("api-1-revision-log", url_args={"sha1_git": unknown_revision_})

    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": "Revision with sha1_git %s not found." % unknown_revision_,
    }
    assert not rv.has_header("Link")


def test_api_revision_directory_ko_not_found(api_client):
    sha1_git = random_sha1()
    url = reverse("api-1-revision-directory", {"sha1_git": sha1_git})
    rv = check_api_get_responses(api_client, url, status_code=404)
    assert rv.data == {
        "exception": "NotFoundExc",
        "reason": f"Revision with sha1_git {sha1_git} not found.",
    }


def test_api_revision_directory_ok_returns_dir_entries(
    api_client, archive_data, revision
):
    url = reverse("api-1-revision-directory", {"sha1_git": revision})
    rv = check_api_get_responses(api_client, url, status_code=200)

    rev_data = archive_data.revision_get(revision)
    dir_content = archive_data.directory_ls(rev_data["directory"])
    dir_content = [
        enrich_directory_entry(dir_entry, request=rv.wsgi_request)
        for dir_entry in dir_content
    ]
    assert rv.data == {
        "content": dir_content,
        "path": ".",
        "type": "dir",
        "revision": revision,
    }


@given(new_person(), new_swh_date())
def test_api_revision_directory_ok_returns_content(
    api_client, archive_data, content, person, date
):
    content_path = "foo"
    _dir = Directory(
        entries=(
            DirectoryEntry(
                name=content_path.encode(),
                type="file",
                target=hash_to_bytes(content["sha1_git"]),
                perms=DentryPerms.content,
            ),
        )
    )
    archive_data.directory_add([_dir])

    revision = Revision(
        directory=_dir.id,
        author=person,
        committer=person,
        message=b"commit message",
        date=TimestampWithTimezone.from_datetime(date),
        committer_date=TimestampWithTimezone.from_datetime(date),
        synthetic=False,
        type=RevisionType.GIT,
    )
    archive_data.revision_add([revision])

    revision_id = hash_to_hex(revision.id)
    cnt_data = archive_data.content_get(content["sha1"])
    url = reverse(
        "api-1-revision-directory",
        {"sha1_git": revision_id, "dir_path": content_path},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)

    assert rv.data == {
        "content": enrich_content(cnt_data, request=rv.wsgi_request),
        "path": content_path,
        "type": "file",
        "revision": revision_id,
    }


@given(new_person(), new_swh_date())
def test_api_revision_directory_ok_returns_revision(
    api_client, archive_data, revision, person, date
):
    rev_path = "foo"
    _dir = Directory(
        entries=(
            DirectoryEntry(
                name=rev_path.encode(),
                type="rev",
                target=hash_to_bytes(revision),
                perms=DentryPerms.revision,
            ),
        )
    )
    archive_data.directory_add([_dir])

    rev = Revision(
        directory=_dir.id,
        author=person,
        committer=person,
        message=b"commit message",
        date=TimestampWithTimezone.from_datetime(date),
        committer_date=TimestampWithTimezone.from_datetime(date),
        synthetic=False,
        type=RevisionType.GIT,
    )
    archive_data.revision_add([rev])

    revision_id = hash_to_hex(rev.id)
    rev_data = archive_data.revision_get(revision)
    url = reverse(
        "api-1-revision-directory",
        {"sha1_git": revision_id, "dir_path": rev_path},
    )
    rv = check_api_get_responses(api_client, url, status_code=200)

    assert rv.data == {
        "content": enrich_revision(rev_data, request=rv.wsgi_request),
        "path": rev_path,
        "type": "rev",
        "revision": revision_id,
    }


def test_api_revision_uppercase(api_client, revision):
    url = reverse(
        "api-1-revision-uppercase-checksum", url_args={"sha1_git": revision.upper()}
    )

    resp = check_http_get_response(api_client, url, status_code=302)

    redirect_url = reverse("api-1-revision", url_args={"sha1_git": revision})

    assert resp["location"] == redirect_url
