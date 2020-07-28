# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from django.utils.html import escape
from hypothesis import given

from swh.model.identifiers import DIRECTORY, RELEASE, REVISION, SNAPSHOT
from swh.web.browse.snapshot_context import process_snapshot_branches
from swh.web.common.identifiers import gen_swhid
from swh.web.common.utils import gen_path_info, reverse
from swh.web.tests.django_asserts import assert_contains, assert_template_used
from swh.web.tests.strategies import (
    directory,
    directory_with_subdirs,
    invalid_sha1,
    unknown_directory,
    origin_with_multiple_visits,
)


@given(directory())
def test_root_directory_view(client, archive_data, directory):
    _directory_view_checks(client, directory, archive_data.directory_ls(directory))


@given(directory_with_subdirs())
def test_sub_directory_view(client, archive_data, directory):
    dir_content = archive_data.directory_ls(directory)
    subdir = random.choice([e for e in dir_content if e["type"] == "dir"])
    subdir_content = archive_data.directory_ls(subdir["target"])
    _directory_view_checks(client, directory, subdir_content, subdir["name"])


@given(invalid_sha1(), unknown_directory())
def test_directory_request_errors(client, invalid_sha1, unknown_directory):
    dir_url = reverse("browse-directory", url_args={"sha1_git": invalid_sha1})

    resp = client.get(dir_url)
    assert resp.status_code == 400
    assert_template_used(resp, "error.html")

    dir_url = reverse("browse-directory", url_args={"sha1_git": unknown_directory})

    resp = client.get(dir_url)
    assert resp.status_code == 404
    assert_template_used(resp, "error.html")


@given(directory())
def test_directory_uppercase(client, directory):
    url = reverse(
        "browse-directory-uppercase-checksum", url_args={"sha1_git": directory.upper()}
    )

    resp = client.get(url)
    assert resp.status_code == 302

    redirect_url = reverse("browse-directory", url_args={"sha1_git": directory})

    assert resp["location"] == redirect_url


@given(directory())
def test_permalink_box_context(client, tests_data, directory):
    origin_url = random.choice(tests_data["origins"])["url"]
    url = reverse(
        "browse-directory",
        url_args={"sha1_git": directory},
        query_params={"origin_url": origin_url},
    )

    resp = client.get(url)

    assert resp.status_code == 200
    assert_contains(resp, 'id="swhid-context-option-directory"')


@given(origin_with_multiple_visits())
def test_directory_origin_snapshot_branch_browse(client, archive_data, origin):
    visits = archive_data.origin_visit_get(origin["url"])
    visit = random.choice(visits)
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    branches, releases = process_snapshot_branches(snapshot)
    branch_info = random.choice(branches)

    directory = archive_data.revision_get(branch_info["revision"])["directory"]
    directory_content = archive_data.directory_ls(directory)
    directory_subdir = random.choice(
        [e for e in directory_content if e["type"] == "dir"]
    )

    url = reverse(
        "browse-directory",
        url_args={"sha1_git": directory},
        query_params={
            "origin_url": origin["url"],
            "snapshot": snapshot["id"],
            "branch": branch_info["name"],
            "path": directory_subdir["name"],
        },
    )

    resp = client.get(url)

    assert resp.status_code == 200
    assert_template_used(resp, "browse/directory.html")
    _check_origin_snapshot_related_html(resp, origin, snapshot, branches, releases)
    assert_contains(resp, directory_subdir["name"])
    assert_contains(resp, f"Branch: <strong>{branch_info['name']}</strong>")

    dir_swhid = gen_swhid(
        DIRECTORY,
        directory_subdir["target"],
        metadata={
            "origin": origin["url"],
            "visit": gen_swhid(SNAPSHOT, snapshot),
            "anchor": gen_swhid(REVISION, branch_info["revision"]),
            "path": "/",
        },
    )
    assert_contains(resp, dir_swhid)

    rev_swhid = gen_swhid(
        REVISION,
        branch_info["revision"],
        metadata={"origin": origin["url"], "visit": gen_swhid(SNAPSHOT, snapshot),},
    )
    assert_contains(resp, rev_swhid)

    snp_swhid = gen_swhid(SNAPSHOT, snapshot, metadata={"origin": origin["url"],},)
    assert_contains(resp, snp_swhid)


@given(origin_with_multiple_visits())
def test_content_origin_snapshot_release_browse(client, archive_data, origin):
    visits = archive_data.origin_visit_get(origin["url"])
    visit = random.choice(visits)
    snapshot = archive_data.snapshot_get(visit["snapshot"])
    branches, releases = process_snapshot_branches(snapshot)
    release_info = random.choice(releases)

    directory = release_info["directory"]
    directory_content = archive_data.directory_ls(directory)
    directory_subdir = random.choice(
        [e for e in directory_content if e["type"] == "dir"]
    )

    url = reverse(
        "browse-directory",
        url_args={"sha1_git": directory},
        query_params={
            "origin_url": origin["url"],
            "snapshot": snapshot["id"],
            "release": release_info["name"],
            "path": directory_subdir["name"],
        },
    )

    resp = client.get(url)
    assert resp.status_code == 200
    assert_template_used(resp, "browse/directory.html")
    _check_origin_snapshot_related_html(resp, origin, snapshot, branches, releases)
    assert_contains(resp, directory_subdir["name"])
    assert_contains(resp, f"Release: <strong>{release_info['name']}</strong>")

    dir_swhid = gen_swhid(
        DIRECTORY,
        directory_subdir["target"],
        metadata={
            "origin": origin["url"],
            "visit": gen_swhid(SNAPSHOT, snapshot),
            "anchor": gen_swhid(RELEASE, release_info["id"]),
            "path": "/",
        },
    )
    assert_contains(resp, dir_swhid)

    rev_swhid = gen_swhid(
        REVISION,
        release_info["target"],
        metadata={"origin": origin["url"], "visit": gen_swhid(SNAPSHOT, snapshot),},
    )
    assert_contains(resp, rev_swhid)

    rel_swhid = gen_swhid(
        RELEASE,
        release_info["id"],
        metadata={"origin": origin["url"], "visit": gen_swhid(SNAPSHOT, snapshot),},
    )
    assert_contains(resp, rel_swhid)

    snp_swhid = gen_swhid(SNAPSHOT, snapshot, metadata={"origin": origin["url"],},)
    assert_contains(resp, snp_swhid)


def _check_origin_snapshot_related_html(resp, origin, snapshot, branches, releases):
    browse_origin_url = reverse(
        "browse-origin", query_params={"origin_url": origin["url"]}
    )

    assert_contains(resp, f'href="{browse_origin_url}"')

    origin_branches_url = reverse(
        "browse-origin-branches",
        query_params={"origin_url": origin["url"], "snapshot": snapshot["id"]},
    )

    assert_contains(resp, f'href="{escape(origin_branches_url)}"')
    assert_contains(resp, f"Branches ({len(branches)})")

    origin_releases_url = reverse(
        "browse-origin-releases",
        query_params={"origin_url": origin["url"], "snapshot": snapshot["id"]},
    )

    assert_contains(resp, f'href="{escape(origin_releases_url)}"')
    assert_contains(resp, f"Releases ({len(releases)})")

    assert_contains(resp, '<li class="swh-branch">', count=len(branches))
    assert_contains(resp, '<li class="swh-release">', count=len(releases))


def _directory_view_checks(
    client,
    root_directory_sha1,
    directory_entries,
    path=None,
    origin_url=None,
    snapshot_id=None,
):
    dirs = [e for e in directory_entries if e["type"] in ("dir", "rev")]
    files = [e for e in directory_entries if e["type"] == "file"]

    url_args = {"sha1_git": root_directory_sha1}
    query_params = {"path": path, "origin_url": origin_url, "snapshot": snapshot_id}

    url = reverse("browse-directory", url_args=url_args, query_params=query_params)

    root_dir_url = reverse(
        "browse-directory", url_args={"sha1_git": root_directory_sha1}
    )

    resp = client.get(url)

    assert resp.status_code == 200
    assert_template_used(resp, "browse/directory.html")
    assert_contains(
        resp, '<a href="' + root_dir_url + '">' + root_directory_sha1[:7] + "</a>"
    )
    assert_contains(resp, '<td class="swh-directory">', count=len(dirs))
    assert_contains(resp, '<td class="swh-content">', count=len(files))

    for d in dirs:
        if d["type"] == "rev":
            dir_url = reverse("browse-revision", url_args={"sha1_git": d["target"]})
        else:
            dir_path = d["name"]
            if path:
                dir_path = "%s/%s" % (path, d["name"])
            dir_url = reverse(
                "browse-directory",
                url_args={"sha1_git": root_directory_sha1},
                query_params={"path": dir_path},
            )
        assert_contains(resp, dir_url)

    for f in files:
        file_path = "%s/%s" % (root_directory_sha1, f["name"])
        if path:
            file_path = "%s/%s/%s" % (root_directory_sha1, path, f["name"])
        query_string = "sha1_git:" + f["target"]
        file_url = reverse(
            "browse-content",
            url_args={"query_string": query_string},
            query_params={"path": file_path},
        )
        assert_contains(resp, file_url)

    path_info = gen_path_info(path)

    assert_contains(resp, '<li class="swh-path">', count=len(path_info) + 1)
    assert_contains(
        resp, '<a href="%s">%s</a>' % (root_dir_url, root_directory_sha1[:7])
    )

    for p in path_info:
        dir_url = reverse(
            "browse-directory",
            url_args={"sha1_git": root_directory_sha1},
            query_params={"path": p["path"]},
        )
        assert_contains(resp, '<a href="%s">%s</a>' % (dir_url, p["name"]))

    assert_contains(resp, "vault-cook-directory")

    swh_dir_id = gen_swhid(DIRECTORY, directory_entries[0]["dir_id"])
    swh_dir_id_url = reverse("browse-swhid", url_args={"swhid": swh_dir_id})

    swhid_context = {}
    if root_directory_sha1 != directory_entries[0]["dir_id"]:
        swhid_context["anchor"] = gen_swhid(DIRECTORY, root_directory_sha1)

    swhid_context["path"] = f"/{path}/" if path else "/"

    if root_directory_sha1 != directory_entries[0]["dir_id"]:
        swhid_context["anchor"] = gen_swhid(DIRECTORY, root_directory_sha1)

    swh_dir_id = gen_swhid(
        DIRECTORY, directory_entries[0]["dir_id"], metadata=swhid_context
    )
    swh_dir_id_url = reverse("browse-swhid", url_args={"swhid": swh_dir_id})
    assert_contains(resp, swh_dir_id)
    assert_contains(resp, swh_dir_id_url)
