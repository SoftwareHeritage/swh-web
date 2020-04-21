# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given

from swh.web.browse.snapshot_context import get_origin_visit_snapshot
from swh.web.common.utils import format_utc_iso_date
from swh.web.tests.strategies import origin_with_multiple_visits


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
                    {
                        "name": branch,
                        "revision": branch_data["target"],
                        "directory": rev_data["directory"],
                        "date": format_utc_iso_date(rev_data["date"]),
                        "message": rev_data["message"],
                    }
                )
            elif branch_data["target_type"] == "release":
                rel_data = archive_data.release_get(branch_data["target"])
                rev_data = archive_data.revision_get(rel_data["target"])
                releases.append(
                    {
                        "name": rel_data["name"],
                        "branch_name": branch,
                        "date": format_utc_iso_date(rel_data["date"]),
                        "id": rel_data["id"],
                        "message": rel_data["message"],
                        "target_type": rel_data["target_type"],
                        "target": rel_data["target"],
                        "directory": rev_data["directory"],
                    }
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
