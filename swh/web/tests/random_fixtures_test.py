# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import sys


def test_random_fixture_values(
    sha1,
    invalid_sha1,
    sha256,
    content,
    contents,
    unknown_content,
    unknown_contents,
    content_text,
    content_text_non_utf8,
    content_application_no_highlight,
    content_text_no_highlight,
    content_image_type,
    content_unsupported_image_type_rendering,
    content_utf8_detected_as_binary,
    directory,
    directory_with_subdirs,
    directory_with_files,
    unknown_directory,
    release,
    releases,
    unknown_release,
    revision,
    revisions,
    revisions_list,
    unknown_revision,
    ancestor_revisions,
    non_ancestor_revisions,
    snapshot,
    unknown_snapshot,
    origin,
    origin_with_multiple_visits,
    origin_with_releases,
    origin_with_pull_request_branches,
    content_swhid,
    directory_swhid,
    release_swhid,
    revision_swhid,
    snapshot_swhid,
):
    """Special test to print values of swh-web fixtures returning random data.

    It is not integrated in swh-web test suite but will be executed by explicitly
    invoking pytest in tests located in swh/web/tests/test_random_fixtures.py.
    """
    print(
        "\n".join(
            [
                sha1,
                invalid_sha1,
                sha256,
                content["sha1"],
                str([c["sha1"] for c in contents]),
                unknown_content["sha1"],
                str([c["sha1"] for c in unknown_contents]),
                content_text["sha1"],
                content_text_non_utf8["sha1"],
                content_application_no_highlight["sha1"],
                content_text_no_highlight["sha1"],
                content_image_type["sha1"],
                content_unsupported_image_type_rendering["sha1"],
                content_utf8_detected_as_binary["sha1"],
                directory,
                directory_with_subdirs,
                directory_with_files,
                unknown_directory,
                release,
                str(releases),
                unknown_release,
                revision,
                str(revisions),
                str(revisions_list(size=3)),
                unknown_revision,
                str(ancestor_revisions),
                str(non_ancestor_revisions),
                snapshot,
                unknown_snapshot,
                origin["url"],
                origin_with_multiple_visits["url"],
                origin_with_releases["url"],
                origin_with_pull_request_branches.url,
                str(content_swhid),
                str(directory_swhid),
                str(release_swhid),
                str(revision_swhid),
                str(snapshot_swhid),
            ]
        ),
        file=sys.stderr,
    )
    assert False
