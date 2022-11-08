# Copyright (C) 2022 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random
import re
import string

from dateutil import parser
from hypothesis import given
import pytest

from django.utils.html import escape

from swh.model.hashutil import hash_to_bytes
from swh.model.model import (
    ObjectType,
    Origin,
    OriginVisit,
    OriginVisitStatus,
    Release,
    Revision,
    RevisionType,
    Snapshot,
    SnapshotBranch,
    TargetType,
    TimestampWithTimezone,
)
from swh.storage.utils import now
from swh.web.browse.snapshot_context import process_snapshot_branches
from swh.web.tests.data import random_sha1
from swh.web.tests.django_asserts import assert_contains, assert_not_contains
from swh.web.tests.helpers import check_html_get_response
from swh.web.tests.strategies import new_origin, new_person, new_swh_date, visit_dates
from swh.web.utils import reverse


@pytest.mark.parametrize(
    "browse_context,template_used",
    [
        ("log", "revision-log.html"),
        ("branches", "branches.html"),
        ("releases", "releases.html"),
    ],
)
def test_snapshot_browse_with_id(client, browse_context, template_used, snapshot):
    url = reverse(
        f"browse-snapshot-{browse_context}", url_args={"snapshot_id": snapshot}
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used=f"browse-{template_used}"
    )
    assert_contains(resp, f"swh:1:snp:{snapshot}")


@pytest.mark.parametrize("browse_context", ["log", "branches", "releases"])
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


@pytest.mark.parametrize("browse_context", ["log", "branches", "releases"])
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


@pytest.mark.parametrize("browse_context", ["log", "branches", "releases"])
def test_snapshot_browse_without_id(client, browse_context, archive_data, origin):
    url = reverse(
        f"browse-snapshot-{browse_context}", query_params={"origin_url": origin["url"]}
    )
    # This will be redirected to /snapshot/<latest_snapshot_id>/log
    resp = check_html_get_response(
        client,
        url,
        status_code=302,
    )
    snapshot = archive_data.snapshot_get_latest(origin["url"])

    assert resp.url == reverse(
        f"browse-snapshot-{browse_context}",
        url_args={"snapshot_id": snapshot["id"]},
        query_params={"origin_url": origin["url"]},
    )


@pytest.mark.parametrize("browse_context", ["log", "branches", "releases"])
def test_snapshot_browse_without_id_and_origin(client, browse_context):
    url = reverse(f"browse-snapshot-{browse_context}")
    resp = check_html_get_response(
        client,
        url,
        status_code=400,
    )
    # assert_contains works only with a success response, using re.search instead
    assert re.search(
        "An origin URL must be provided as a query parameter",
        resp.content.decode("utf-8"),
    )


def test_snapshot_browse_branches_targeting_revisions(client, archive_data, origin):
    _origin_branches_test_helper(client, archive_data, origin["url"])


def test_snapshot_browse_branches_targeting_multiple_types(
    client, archive_data, content_text, directory, revision
):
    snapshot = Snapshot(
        branches={
            b"content": SnapshotBranch(
                target=hash_to_bytes(content_text["sha1_git"]),
                target_type=TargetType.CONTENT,
            ),
            b"directory": SnapshotBranch(
                target=hash_to_bytes(directory),
                target_type=TargetType.DIRECTORY,
            ),
            b"revision": SnapshotBranch(
                target=hash_to_bytes(revision),
                target_type=TargetType.REVISION,
            ),
        },
    )
    archive_data.snapshot_add([snapshot])

    origin_url = "https://git.example.org/user/project"
    archive_data.origin_add([Origin(url=origin_url)])
    date = now()
    visit = OriginVisit(origin=origin_url, date=date, type="git")
    visit = archive_data.origin_visit_add([visit])[0]
    visit_status = OriginVisitStatus(
        origin=origin_url,
        visit=visit.visit,
        date=date,
        status="full",
        snapshot=snapshot.id,
    )
    archive_data.origin_visit_status_add([visit_status])

    _origin_branches_test_helper(client, archive_data, origin_url)


def _origin_branches_test_helper(client, archive_data, origin_url):

    snapshot = archive_data.snapshot_get_latest(origin_url)

    snapshot_sizes = archive_data.snapshot_count_branches(snapshot["id"])
    snapshot_content = process_snapshot_branches(snapshot)

    query_params = {"origin_url": origin_url, "snapshot": snapshot["id"]}

    url = reverse(
        "browse-snapshot-branches",
        url_args={"snapshot_id": snapshot["id"]},
        query_params=query_params,
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-branches.html"
    )

    origin_branches = snapshot_content[0]
    origin_releases = snapshot_content[1]
    origin_branches_url = reverse("browse-origin-branches", query_params=query_params)

    assert_contains(resp, f'href="{escape(origin_branches_url)}"')
    assert_contains(resp, f"Branches ({snapshot_sizes['branch']})")

    origin_releases_url = reverse("browse-origin-releases", query_params=query_params)

    nb_releases = len(origin_releases)
    if nb_releases > 0:
        assert_contains(resp, f'href="{escape(origin_releases_url)}">')
        assert_contains(resp, f"Releases ({snapshot_sizes['release']})")

    assert_contains(resp, '<tr class="swh-branch-entry', count=len(origin_branches))

    for branch in origin_branches:
        browse_branch_url = reverse(
            "browse-origin-directory",
            query_params={"branch": branch["name"], **query_params},
        )
        assert_contains(resp, '<a href="%s">' % escape(browse_branch_url))

        if branch["target_type"] == "revision":
            browse_revision_url = reverse(
                "browse-revision",
                url_args={"sha1_git": branch["target"]},
                query_params=query_params,
            )
            assert_contains(resp, '<a href="%s">' % escape(browse_revision_url))
        elif branch["target_type"] == "directory":
            browse_directory_url = reverse(
                "browse-directory",
                url_args={"sha1_git": branch["target"]},
                query_params=query_params,
            )
            assert_contains(resp, '<a href="%s">' % escape(browse_directory_url))
        elif branch["target_type"] == "content":
            browse_content_url = reverse(
                "browse-content",
                url_args={"query_string": f"sha1_git:{branch['target']}"},
                query_params=query_params,
            )
            assert_contains(resp, '<a href="%s">' % escape(browse_content_url))

    _check_origin_link(resp, origin_url)


def _check_origin_link(resp, origin_url):
    browse_origin_url = reverse(
        "browse-origin", query_params={"origin_url": origin_url}
    )
    assert_contains(resp, f'href="{browse_origin_url}"')


@given(
    new_origin(),
    visit_dates(),
)
def test_snapshot_branches_pagination_with_alias(
    client,
    archive_data,
    mocker,
    release,
    revisions_list,
    new_origin,
    visit_dates,
):
    """
    When a snapshot contains a branch or a release alias, pagination links
    in the branches / releases view should be displayed.
    """
    revisions = revisions_list(size=10)
    mocker.patch("swh.web.browse.snapshot_context.PER_PAGE", len(revisions) / 2)
    snp_dict = {"branches": {}, "id": hash_to_bytes(random_sha1())}
    for i in range(len(revisions)):
        branch = "".join(random.choices(string.ascii_lowercase, k=8))
        snp_dict["branches"][branch.encode()] = {
            "target_type": "revision",
            "target": hash_to_bytes(revisions[i]),
        }
    release_name = "".join(random.choices(string.ascii_lowercase, k=8))
    snp_dict["branches"][b"RELEASE_ALIAS"] = {
        "target_type": "alias",
        "target": release_name.encode(),
    }
    snp_dict["branches"][release_name.encode()] = {
        "target_type": "release",
        "target": hash_to_bytes(release),
    }
    archive_data.origin_add([new_origin])
    archive_data.snapshot_add([Snapshot.from_dict(snp_dict)])
    visit = archive_data.origin_visit_add(
        [
            OriginVisit(
                origin=new_origin.url,
                date=visit_dates[0],
                type="git",
            )
        ]
    )[0]
    visit_status = OriginVisitStatus(
        origin=new_origin.url,
        visit=visit.visit,
        date=now(),
        status="full",
        snapshot=snp_dict["id"],
    )
    archive_data.origin_visit_status_add([visit_status])
    snapshot = archive_data.snapshot_get_latest(new_origin.url)
    url = reverse(
        "browse-snapshot-branches",
        url_args={"snapshot_id": snapshot["id"]},
        query_params={"origin_url": new_origin.url},
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-branches.html"
    )
    assert_contains(resp, '<ul class="pagination')


def test_pull_request_branches_filtering(
    client, origin_with_pull_request_branches, archive_data
):
    origin_url = origin_with_pull_request_branches.url
    # check no pull request branches are displayed in the Branches / Releases dropdown
    url = reverse("browse-origin-directory", query_params={"origin_url": origin_url})
    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-directory.html"
    )
    assert_not_contains(resp, "refs/pull/")

    snapshot = archive_data.snapshot_get_latest(origin_url)
    # check no pull request branches are displayed in the branches view
    url = reverse(
        "browse-snapshot-branches",
        url_args={"snapshot_id": snapshot["id"]},
        query_params={"origin_url": origin_url},
    )
    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-branches.html"
    )
    assert_not_contains(resp, "refs/pull/")


def test_snapshot_browse_releases(client, archive_data, origin):
    origin_visits = archive_data.origin_visit_get(origin["url"])

    visit = origin_visits[-1]
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    snapshot_sizes = archive_data.snapshot_count_branches(snapshot["id"])
    snapshot_content = process_snapshot_branches(snapshot)

    _origin_releases_test_helper(
        client, origin, snapshot_content, snapshot_sizes, snapshot_id=visit["snapshot"]
    )


def _origin_releases_test_helper(
    client, origin_info, origin_snapshot, snapshot_sizes, snapshot_id=None
):
    query_params = {"origin_url": origin_info["url"], "snapshot": snapshot_id}

    url = reverse(
        "browse-snapshot-releases",
        url_args={"snapshot_id": snapshot_id},
        query_params=query_params,
    )

    resp = check_html_get_response(
        client, url, status_code=200, template_used="browse-releases.html"
    )

    origin_releases = origin_snapshot[1]

    origin_branches_url = reverse("browse-origin-branches", query_params=query_params)

    assert_contains(resp, f'href="{escape(origin_branches_url)}"')
    assert_contains(resp, f"Branches ({snapshot_sizes['revision']})")

    origin_releases_url = reverse("browse-origin-releases", query_params=query_params)

    nb_releases = len(origin_releases)
    if nb_releases > 0:
        assert_contains(resp, f'href="{escape(origin_releases_url)}"')
        assert_contains(resp, f"Releases ({snapshot_sizes['release']}")

    assert_contains(resp, '<tr class="swh-release-entry', count=nb_releases)
    assert_contains(resp, 'title="The release', count=nb_releases)

    for release in origin_releases:
        query_params["release"] = release["name"]
        browse_release_url = reverse(
            "browse-release",
            url_args={"sha1_git": release["id"]},
            query_params=query_params,
        )
        browse_revision_url = reverse(
            "browse-revision",
            url_args={"sha1_git": release["target"]},
            query_params=query_params,
        )

        assert_contains(resp, '<a href="%s">' % escape(browse_release_url))
        assert_contains(resp, '<a href="%s">' % escape(browse_revision_url))

    _check_origin_link(resp, origin_info["url"])


def test_snapshot_content_redirect(client, snapshot):
    qry = {"extra-arg": "extra"}
    url = reverse(
        "browse-snapshot-content", url_args={"snapshot_id": snapshot}, query_params=qry
    )
    resp = check_html_get_response(client, url, status_code=301)
    assert resp.url == reverse(
        "browse-content", query_params={**{"snapshot_id": snapshot}, **qry}
    )


def test_snapshot_content_legacy_redirect(client, snapshot):
    qry = {"extra-arg": "extra"}
    url_args = {"snapshot_id": snapshot, "path": "test.txt"}
    url = reverse("browse-snapshot-content-legacy", url_args=url_args, query_params=qry)
    resp = check_html_get_response(client, url, status_code=301)
    assert resp.url == reverse("browse-content", query_params={**url_args, **qry})


def test_browse_snapshot_log_no_revisions(client, archive_data, directory):
    release_name = "v1.0.0"
    release = Release(
        name=release_name.encode(),
        message=f"release {release_name}".encode(),
        target=hash_to_bytes(directory),
        target_type=ObjectType.DIRECTORY,
        synthetic=True,
    )
    archive_data.release_add([release])

    snapshot = Snapshot(
        branches={
            b"HEAD": SnapshotBranch(
                target=release_name.encode(), target_type=TargetType.ALIAS
            ),
            release_name.encode(): SnapshotBranch(
                target=release.id, target_type=TargetType.RELEASE
            ),
        },
    )
    archive_data.snapshot_add([snapshot])

    snp_url = reverse(
        "browse-snapshot-directory", url_args={"snapshot_id": snapshot.id.hex()}
    )
    log_url = reverse(
        "browse-snapshot-log", url_args={"snapshot_id": snapshot.id.hex()}
    )

    resp = check_html_get_response(
        client, snp_url, status_code=200, template_used="browse-directory.html"
    )
    assert_not_contains(resp, log_url)

    resp = check_html_get_response(
        client, log_url, status_code=404, template_used="error.html"
    )
    assert_contains(
        resp,
        "No revisions history found in the current snapshot context.",
        status_code=404,
    )


@given(new_person(), new_swh_date())
def test_browse_snapshot_log_when_revisions(
    client, archive_data, directory, person, date
):

    revision = Revision(
        directory=hash_to_bytes(directory),
        author=person,
        committer=person,
        message=b"commit message",
        date=TimestampWithTimezone.from_datetime(date),
        committer_date=TimestampWithTimezone.from_datetime(date),
        synthetic=False,
        type=RevisionType.GIT,
    )
    archive_data.revision_add([revision])

    snapshot = Snapshot(
        branches={
            b"HEAD": SnapshotBranch(
                target=revision.id, target_type=TargetType.REVISION
            ),
        },
    )
    archive_data.snapshot_add([snapshot])

    snp_url = reverse(
        "browse-snapshot-directory", url_args={"snapshot_id": snapshot.id.hex()}
    )
    log_url = reverse(
        "browse-snapshot-log", url_args={"snapshot_id": snapshot.id.hex()}
    )

    resp = check_html_get_response(
        client, snp_url, status_code=200, template_used="browse-directory.html"
    )
    assert_contains(resp, log_url)


@pytest.mark.parametrize(
    "aliased,with_origin,with_branch_query_param",
    [
        (False, False, False),
        (False, False, True),
        (False, True, False),
        (False, True, True),
        (True, False, False),
        (True, False, True),
        (True, True, False),
        (True, True, True),
    ],
)
def test_browse_snapshot_single_branch_targeting_content(
    client, archive_data, content_text, aliased, with_origin, with_branch_query_param
):

    branch_name = "HEAD"

    if not aliased:
        snapshot = Snapshot(
            branches={
                branch_name.encode(): SnapshotBranch(
                    target=hash_to_bytes(content_text["sha1_git"]),
                    target_type=TargetType.CONTENT,
                ),
            },
        )
    else:
        snapshot = Snapshot(
            branches={
                branch_name.encode(): SnapshotBranch(
                    target=b"content",
                    target_type=TargetType.ALIAS,
                ),
                branch_name.encode(): SnapshotBranch(
                    target=hash_to_bytes(content_text["sha1_git"]),
                    target_type=TargetType.CONTENT,
                ),
            },
        )

    archive_data.snapshot_add([snapshot])

    query_params = {}
    if with_branch_query_param:
        query_params["branch"] = branch_name

    if with_origin:
        origin_url = "https://git.example.org/user/project"
        archive_data.origin_add([Origin(url=origin_url)])
        date = now()
        visit = OriginVisit(origin=origin_url, date=date, type="git")
        visit = archive_data.origin_visit_add([visit])[0]
        visit_status = OriginVisitStatus(
            origin=origin_url,
            visit=visit.visit,
            date=date,
            status="full",
            snapshot=snapshot.id,
        )
        archive_data.origin_visit_status_add([visit_status])
        query_params["origin_url"] = origin_url
        url = reverse("browse-origin-directory", query_params=query_params)
    else:
        url = reverse(
            "browse-snapshot-directory",
            url_args={"snapshot_id": snapshot.id.hex()},
            query_params=query_params,
        )

    resp = check_html_get_response(
        client,
        url,
        status_code=302,
    )

    if with_origin:
        query_params["origin_url"] = origin_url
    else:
        query_params["snapshot"] = snapshot.id.hex()

    assert resp["location"] == reverse(
        "browse-content",
        url_args={"query_string": f"sha1_git:{content_text['sha1_git']}"},
        query_params=query_params,
    )

    resp = check_html_get_response(
        client,
        resp["location"],
        status_code=200,
    )

    assert_contains(resp, escape(content_text["raw_data"].decode()))

    if with_origin:
        log_url = reverse("browse-origin-log", query_params=query_params)
    else:
        log_url = reverse(
            "browse-snapshot-log",
            url_args={"snapshot_id": snapshot.id.hex()},
            query_params=query_params,
        )

    assert_not_contains(resp, log_url)


@pytest.mark.parametrize(
    "aliased,with_origin,with_branch_query_param",
    [
        (False, False, False),
        (False, False, True),
        (False, True, False),
        (False, True, True),
        (True, False, False),
        (True, False, True),
        (True, True, False),
        (True, True, True),
    ],
)
def test_browse_snapshot_single_branch_targeting_directory(
    client, archive_data, directory, aliased, with_origin, with_branch_query_param
):

    branch_name = "HEAD"

    if not aliased:
        snapshot = Snapshot(
            branches={
                branch_name.encode(): SnapshotBranch(
                    target=hash_to_bytes(directory),
                    target_type=TargetType.DIRECTORY,
                ),
            },
        )
    else:
        snapshot = Snapshot(
            branches={
                branch_name.encode(): SnapshotBranch(
                    target=b"directory",
                    target_type=TargetType.ALIAS,
                ),
                b"directory": SnapshotBranch(
                    target=hash_to_bytes(directory),
                    target_type=TargetType.DIRECTORY,
                ),
            },
        )

    archive_data.snapshot_add([snapshot])

    query_params = {}
    if with_branch_query_param:
        query_params["branch"] = branch_name

    if with_origin:
        origin_url = "https://git.example.org/user/project"
        archive_data.origin_add([Origin(url=origin_url)])
        date = now()
        visit = OriginVisit(origin=origin_url, date=date, type="git")
        visit = archive_data.origin_visit_add([visit])[0]
        visit_status = OriginVisitStatus(
            origin=origin_url,
            visit=visit.visit,
            date=date,
            status="full",
            snapshot=snapshot.id,
        )
        archive_data.origin_visit_status_add([visit_status])
        query_params["origin_url"] = origin_url
        url = reverse("browse-origin-directory", query_params=query_params)
    else:
        url = reverse(
            "browse-snapshot-directory",
            url_args={"snapshot_id": snapshot.id.hex()},
            query_params=query_params,
        )

    resp = check_html_get_response(
        client,
        url,
        status_code=200,
    )

    directory_data = archive_data.directory_get(directory)

    for entry in directory_data["content"]:
        assert_contains(resp, entry["name"])

    if with_origin:
        log_url = reverse("browse-origin-log", query_params=query_params)
    else:
        log_url = reverse(
            "browse-snapshot-log",
            url_args={"snapshot_id": snapshot.id.hex()},
            query_params=query_params,
        )

    assert_not_contains(resp, log_url)
