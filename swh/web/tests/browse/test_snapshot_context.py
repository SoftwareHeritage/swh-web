# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from hypothesis import given

from swh.web.browse.snapshot_context import (
    _get_release,
    get_origin_visit_snapshot,
    get_snapshot_content,
    get_snapshot_context,
)
from swh.web.browse.utils import gen_revision_url
from swh.web.common.identifiers import gen_swhid
from swh.web.common.origin_visits import get_origin_visit, get_origin_visits
from swh.web.common.typing import (
    SnapshotBranchInfo,
    SnapshotContext,
    SnapshotReleaseInfo,
)
from swh.web.common.utils import format_utc_iso_date, reverse
from swh.web.tests.strategies import (
    origin_with_multiple_visits,
    origin_with_releases,
    snapshot,
)


@given(origin_with_multiple_visits())
def test_get_origin_visit_snapshot_simple(archive_data, origin):
    visits = archive_data.origin_visit_get(origin["url"])

    for visit in visits:

        snapshot = archive_data.snapshot_get(visit["snapshot"])
        branches = []
        releases = []

        def _process_branch_data(branch, branch_data, alias=False):
            if branch_data["target_type"] == "revision":
                rev_data = archive_data.revision_get(branch_data["target"])
                branches.append(
                    SnapshotBranchInfo(
                        name=branch,
                        alias=alias,
                        revision=branch_data["target"],
                        directory=rev_data["directory"],
                        date=format_utc_iso_date(rev_data["date"]),
                        message=rev_data["message"],
                        url=None,
                    )
                )
            elif branch_data["target_type"] == "release":
                rel_data = archive_data.release_get(branch_data["target"])
                rev_data = archive_data.revision_get(rel_data["target"])
                releases.append(
                    SnapshotReleaseInfo(
                        name=rel_data["name"],
                        alias=alias,
                        branch_name=branch,
                        date=format_utc_iso_date(rel_data["date"]),
                        id=rel_data["id"],
                        message=rel_data["message"],
                        target_type=rel_data["target_type"],
                        target=rel_data["target"],
                        directory=rev_data["directory"],
                        url=None,
                    )
                )

        aliases = {}

        for branch in sorted(snapshot["branches"].keys()):
            branch_data = snapshot["branches"][branch]
            if branch_data["target_type"] == "alias":
                target_data = snapshot["branches"][branch_data["target"]]
                aliases[branch] = target_data
                _process_branch_data(branch, target_data, alias=True)
            else:
                _process_branch_data(branch, branch_data)

        assert branches and releases, "Incomplete test data."

        origin_visit_branches = get_origin_visit_snapshot(
            origin, visit_id=visit["visit"]
        )

        assert origin_visit_branches == (branches, releases, aliases)


@given(snapshot())
def test_get_snapshot_context_no_origin(archive_data, snapshot):

    for browse_context, kwargs in (
        ("content", {"snapshot_id": snapshot, "path": "/some/path"}),
        ("directory", {"snapshot_id": snapshot}),
        ("log", {"snapshot_id": snapshot}),
    ):

        url_args = {"snapshot_id": snapshot}

        query_params = dict(kwargs)
        query_params.pop("snapshot_id")

        snapshot_context = get_snapshot_context(**kwargs, browse_context=browse_context)

        branches, releases, _ = get_snapshot_content(snapshot)
        releases = list(reversed(releases))
        revision_id = None
        root_directory = None
        for branch in branches:
            if branch["name"] == "HEAD":
                revision_id = branch["revision"]
                root_directory = branch["directory"]
            branch["url"] = reverse(
                f"browse-snapshot-{browse_context}",
                url_args=url_args,
                query_params={"branch": branch["name"], **query_params},
            )
        for release in releases:
            release["url"] = reverse(
                f"browse-snapshot-{browse_context}",
                url_args=url_args,
                query_params={"release": release["name"], **query_params},
            )

        branches_url = reverse("browse-snapshot-branches", url_args=url_args)
        releases_url = reverse("browse-snapshot-releases", url_args=url_args)
        is_empty = not branches and not releases
        snapshot_swhid = gen_swhid("snapshot", snapshot)
        snapshot_sizes = archive_data.snapshot_count_branches(snapshot)

        expected = SnapshotContext(
            branch="HEAD",
            branch_alias=True,
            branches=branches,
            branches_url=branches_url,
            is_empty=is_empty,
            origin_info=None,
            origin_visits_url=None,
            release=None,
            release_alias=False,
            release_id=None,
            query_params=query_params,
            releases=releases,
            releases_url=releases_url,
            revision_id=revision_id,
            revision_info=_get_revision_info(archive_data, revision_id),
            root_directory=root_directory,
            snapshot_id=snapshot,
            snapshot_sizes=snapshot_sizes,
            snapshot_swhid=snapshot_swhid,
            url_args=url_args,
            visit_info=None,
        )

        if revision_id:
            expected["revision_info"]["revision_url"] = gen_revision_url(
                revision_id, snapshot_context
            )

        assert snapshot_context == expected

        _check_branch_release_revision_parameters(
            archive_data, expected, browse_context, kwargs, branches, releases
        )


@given(origin_with_multiple_visits())
def test_get_snapshot_context_with_origin(archive_data, origin):

    origin_visits = get_origin_visits(origin)

    timestamp = format_utc_iso_date(origin_visits[0]["date"], "%Y-%m-%dT%H:%M:%SZ")
    visit_id = origin_visits[1]["visit"]

    for browse_context, kwargs in (
        ("content", {"origin_url": origin["url"], "path": "/some/path"}),
        ("directory", {"origin_url": origin["url"]}),
        ("log", {"origin_url": origin["url"]}),
        ("directory", {"origin_url": origin["url"], "timestamp": timestamp,},),
        ("directory", {"origin_url": origin["url"], "visit_id": visit_id,},),
    ):

        visit_id = kwargs["visit_id"] if "visit_id" in kwargs else None
        visit_ts = kwargs["timestamp"] if "timestamp" in kwargs else None
        visit_info = get_origin_visit(
            {"url": kwargs["origin_url"]}, visit_ts=visit_ts, visit_id=visit_id
        )

        snapshot = visit_info["snapshot"]

        snapshot_context = get_snapshot_context(**kwargs, browse_context=browse_context)

        query_params = dict(kwargs)

        branches, releases, _ = get_snapshot_content(snapshot)
        releases = list(reversed(releases))
        revision_id = None
        root_directory = None
        for branch in branches:
            if branch["name"] == "HEAD":
                revision_id = branch["revision"]
                root_directory = branch["directory"]
            branch["url"] = reverse(
                f"browse-origin-{browse_context}",
                query_params={"branch": branch["name"], **query_params},
            )
        for release in releases:
            release["url"] = reverse(
                f"browse-origin-{browse_context}",
                query_params={"release": release["name"], **query_params},
            )

        query_params.pop("path", None)

        branches_url = reverse("browse-origin-branches", query_params=query_params)
        releases_url = reverse("browse-origin-releases", query_params=query_params)
        origin_visits_url = reverse(
            "browse-origin-visits", query_params={"origin_url": kwargs["origin_url"]}
        )
        is_empty = not branches and not releases
        snapshot_swhid = gen_swhid("snapshot", snapshot)
        snapshot_sizes = archive_data.snapshot_count_branches(snapshot)

        visit_info["url"] = reverse(
            "browse-origin-directory", query_params=query_params
        )
        visit_info["formatted_date"] = format_utc_iso_date(visit_info["date"])

        if "path" in kwargs:
            query_params["path"] = kwargs["path"]

        expected = SnapshotContext(
            branch="HEAD",
            branch_alias=True,
            branches=branches,
            branches_url=branches_url,
            is_empty=is_empty,
            origin_info={"url": origin["url"]},
            origin_visits_url=origin_visits_url,
            release=None,
            release_alias=False,
            release_id=None,
            query_params=query_params,
            releases=releases,
            releases_url=releases_url,
            revision_id=revision_id,
            revision_info=_get_revision_info(archive_data, revision_id),
            root_directory=root_directory,
            snapshot_id=snapshot,
            snapshot_sizes=snapshot_sizes,
            snapshot_swhid=snapshot_swhid,
            url_args={},
            visit_info=visit_info,
        )

        if revision_id:
            expected["revision_info"]["revision_url"] = gen_revision_url(
                revision_id, snapshot_context
            )

        assert snapshot_context == expected

        _check_branch_release_revision_parameters(
            archive_data, expected, browse_context, kwargs, branches, releases
        )


def _check_branch_release_revision_parameters(
    archive_data, base_expected_context, browse_context, kwargs, branches, releases,
):
    branch = random.choice(branches)

    snapshot_context = get_snapshot_context(
        **kwargs, browse_context=browse_context, branch_name=branch["name"]
    )

    url_args = dict(kwargs)
    url_args.pop("path", None)
    url_args.pop("timestamp", None)
    url_args.pop("visit_id", None)
    url_args.pop("origin_url", None)

    query_params = dict(kwargs)
    query_params.pop("snapshot_id", None)

    expected_branch = dict(base_expected_context)
    expected_branch["branch"] = branch["name"]
    expected_branch["branch_alias"] = branch["alias"]
    expected_branch["revision_id"] = branch["revision"]
    expected_branch["revision_info"] = _get_revision_info(
        archive_data, branch["revision"]
    )
    expected_branch["root_directory"] = branch["directory"]
    expected_branch["query_params"] = {"branch": branch["name"], **query_params}
    expected_branch["revision_info"]["revision_url"] = gen_revision_url(
        branch["revision"], expected_branch
    )

    assert snapshot_context == expected_branch

    if releases:

        release = random.choice(releases)

        snapshot_context = get_snapshot_context(
            **kwargs, browse_context=browse_context, release_name=release["name"]
        )

        expected_release = dict(base_expected_context)
        expected_release["branch"] = None
        expected_release["branch_alias"] = False
        expected_release["release"] = release["name"]
        expected_release["release_id"] = release["id"]
        if release["target_type"] == "revision":
            expected_release["revision_id"] = release["target"]
            expected_release["revision_info"] = _get_revision_info(
                archive_data, release["target"]
            )
        expected_release["root_directory"] = release["directory"]
        expected_release["query_params"] = {"release": release["name"], **query_params}
        expected_release["revision_info"]["revision_url"] = gen_revision_url(
            release["target"], expected_release
        )

        assert snapshot_context == expected_release

    revision_log = archive_data.revision_log(branch["revision"])
    revision = revision_log[-1]

    snapshot_context = get_snapshot_context(
        **kwargs, browse_context=browse_context, revision_id=revision["id"]
    )

    if "origin_url" in kwargs:
        view_name = f"browse-origin-{browse_context}"
    else:
        view_name = f"browse-snapshot-{browse_context}"

    kwargs.pop("visit_id", None)

    revision_browse_url = reverse(
        view_name,
        url_args=url_args,
        query_params={"revision": revision["id"], **query_params},
    )

    branches.append(
        SnapshotBranchInfo(
            name=revision["id"],
            alias=False,
            revision=revision["id"],
            directory=revision["directory"],
            date=revision["date"],
            message=revision["message"],
            url=revision_browse_url,
        )
    )

    expected_revision = dict(base_expected_context)
    expected_revision["branch"] = None
    expected_revision["branch_alias"] = False
    expected_revision["branches"] = branches
    expected_revision["revision_id"] = revision["id"]
    expected_revision["revision_info"] = _get_revision_info(
        archive_data, revision["id"]
    )
    expected_revision["root_directory"] = revision["directory"]
    expected_revision["query_params"] = {"revision": revision["id"], **query_params}
    expected_revision["revision_info"]["revision_url"] = gen_revision_url(
        revision["id"], expected_revision
    )

    assert snapshot_context == expected_revision


@given(origin_with_releases())
def test_get_release_large_snapshot(archive_data, origin):
    snapshot = archive_data.snapshot_get_latest(origin["url"])
    release_id = random.choice(
        [
            v["target"]
            for v in snapshot["branches"].values()
            if v["target_type"] == "release"
        ]
    )
    release_data = archive_data.release_get(release_id)
    # simulate large snapshot processing by providing releases parameter
    # as an empty list
    release = _get_release(
        releases=[], release_name=release_data["name"], snapshot_id=snapshot["id"]
    )

    assert release_data["name"] == release["name"]
    assert release_data["id"] == release["id"]


def _get_revision_info(archive_data, revision_id):
    revision_info = None
    if revision_id:
        revision_info = archive_data.revision_get(revision_id)
        revision_info["message_header"] = revision_info["message"].split("\n")[0]
        revision_info["date"] = format_utc_iso_date(revision_info["date"])
        revision_info["committer_date"] = format_utc_iso_date(
            revision_info["committer_date"]
        )
    return revision_info
