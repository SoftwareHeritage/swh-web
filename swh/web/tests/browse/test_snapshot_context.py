# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from hypothesis import given

from swh.web.browse.snapshot_context import (
    get_origin_visit_snapshot,
    get_snapshot_content,
    get_snapshot_context,
)
from swh.web.common.identifiers import get_swh_persistent_id
from swh.web.common.origin_visits import get_origin_visit, get_origin_visits
from swh.web.common.typing import (
    SnapshotBranchInfo,
    SnapshotReleaseInfo,
    SnapshotContext,
)
from swh.web.common.utils import format_utc_iso_date, reverse
from swh.web.tests.strategies import origin_with_multiple_visits, snapshot


@given(origin_with_multiple_visits())
def test_get_origin_visit_snapshot_simple(archive_data, origin):
    visits = archive_data.origin_visit_get(origin["url"])

    for visit in visits:

        snapshot = archive_data.snapshot_get(visit["snapshot"])
        branches = []
        releases = []

        def _process_branch_data(branch, branch_data):
            if branch_data["target_type"] == "revision":
                rev_data = archive_data.revision_get(branch_data["target"])
                branches.append(
                    SnapshotBranchInfo(
                        name=branch,
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

        for branch in sorted(snapshot["branches"].keys()):
            branch_data = snapshot["branches"][branch]
            if branch_data["target_type"] == "alias":
                target_data = snapshot["branches"][branch_data["target"]]
                _process_branch_data(branch, target_data)
            else:
                _process_branch_data(branch, branch_data)

        assert branches and releases, "Incomplete test data."

        origin_visit_branches = get_origin_visit_snapshot(
            origin, visit_id=visit["visit"]
        )

        assert origin_visit_branches == (branches, releases)


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

        branches, releases = get_snapshot_content(snapshot)
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
        snapshot_swhid = get_swh_persistent_id("snapshot", snapshot)
        snapshot_sizes = {"revision": len(branches), "release": len(releases)}

        expected = SnapshotContext(
            branch="HEAD",
            branches=branches,
            branches_url=branches_url,
            is_empty=is_empty,
            origin_info=None,
            origin_visits_url=None,
            release=None,
            release_id=None,
            query_params=query_params,
            releases=releases,
            releases_url=releases_url,
            revision_id=revision_id,
            root_directory=root_directory,
            snapshot_id=snapshot,
            snapshot_sizes=snapshot_sizes,
            snapshot_swhid=snapshot_swhid,
            url_args=url_args,
            visit_info=None,
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

        branches, releases = get_snapshot_content(snapshot)
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
        snapshot_swhid = get_swh_persistent_id("snapshot", snapshot)
        snapshot_sizes = {"revision": len(branches), "release": len(releases)}

        visit_info["url"] = reverse(
            "browse-origin-directory", query_params=query_params
        )
        visit_info["formatted_date"] = format_utc_iso_date(visit_info["date"])

        if "path" in kwargs:
            query_params["path"] = kwargs["path"]

        expected = SnapshotContext(
            branch="HEAD",
            branches=branches,
            branches_url=branches_url,
            is_empty=is_empty,
            origin_info={"url": origin["url"]},
            origin_visits_url=origin_visits_url,
            release=None,
            release_id=None,
            query_params=query_params,
            releases=releases,
            releases_url=releases_url,
            revision_id=revision_id,
            root_directory=root_directory,
            snapshot_id=snapshot,
            snapshot_sizes=snapshot_sizes,
            snapshot_swhid=snapshot_swhid,
            url_args={},
            visit_info=visit_info,
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
    expected_branch["revision_id"] = branch["revision"]
    expected_branch["root_directory"] = branch["directory"]
    expected_branch["query_params"] = {"branch": branch["name"], **query_params}

    assert snapshot_context == expected_branch

    if releases:

        release = random.choice(releases)

        snapshot_context = get_snapshot_context(
            **kwargs, browse_context=browse_context, release_name=release["name"]
        )

        expected_release = dict(base_expected_context)
        expected_release["branch"] = None
        expected_release["release"] = release["name"]
        expected_release["release_id"] = release["id"]
        if release["target_type"] == "revision":
            expected_release["revision_id"] = release["target"]
        expected_release["root_directory"] = release["directory"]
        expected_release["query_params"] = {"release": release["name"], **query_params}

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
            revision=revision["id"],
            directory=revision["directory"],
            date=revision["date"],
            message=revision["message"],
            url=revision_browse_url,
        )
    )

    expected_revision = dict(base_expected_context)
    expected_revision["branch"] = revision["id"]
    expected_revision["branches"] = branches
    expected_revision["revision_id"] = revision["id"]
    expected_revision["root_directory"] = revision["directory"]
    expected_revision["query_params"] = {"revision": revision["id"], **query_params}

    assert snapshot_context == expected_revision
