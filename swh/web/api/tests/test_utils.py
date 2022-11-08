# Copyright (C) 2015-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import random

from swh.model.hashutil import DEFAULT_ALGORITHMS
from swh.model.model import Origin
from swh.web.api import utils
from swh.web.utils import resolve_branch_alias, reverse
from swh.web.utils.origin_visits import get_origin_visits

url_map = [
    {
        "rule": "/other/<slug>",
        "methods": set(["GET", "POST", "HEAD"]),
        "endpoint": "foo",
    },
    {
        "rule": "/some/old/url/<slug>",
        "methods": set(["GET", "POST"]),
        "endpoint": "blablafn",
    },
    {
        "rule": "/other/old/url/<int:id>",
        "methods": set(["GET", "HEAD"]),
        "endpoint": "bar",
    },
    {"rule": "/other", "methods": set([]), "endpoint": None},
    {"rule": "/other2", "methods": set([]), "endpoint": None},
]


def test_filter_field_keys_dict_unknown_keys():
    actual_res = utils.filter_field_keys(
        {"directory": 1, "file": 2, "link": 3}, {"directory1", "file2"}
    )

    assert actual_res == {}


def test_filter_field_keys_dict():
    actual_res = utils.filter_field_keys(
        {"directory": 1, "file": 2, "link": 3}, {"directory", "link"}
    )

    assert actual_res == {"directory": 1, "link": 3}


def test_filter_field_keys_list_unknown_keys():
    actual_res = utils.filter_field_keys(
        [{"directory": 1, "file": 2, "link": 3}, {"1": 1, "2": 2, "link": 3}], {"d"}
    )

    assert actual_res == [{}, {}]


def test_filter_field_keys_map():
    actual_res = utils.filter_field_keys(
        map(
            lambda x: {"i": x["i"] + 1, "j": x["j"]},
            [{"i": 1, "j": None}, {"i": 2, "j": None}, {"i": 3, "j": None}],
        ),
        {"i"},
    )

    assert list(actual_res) == [{"i": 2}, {"i": 3}, {"i": 4}]


def test_filter_field_keys_list():
    actual_res = utils.filter_field_keys(
        [{"directory": 1, "file": 2, "link": 3}, {"dir": 1, "fil": 2, "lin": 3}],
        {"directory", "dir"},
    )

    assert actual_res == [{"directory": 1}, {"dir": 1}]


def test_filter_field_keys_other():
    input_set = {1, 2}

    actual_res = utils.filter_field_keys(input_set, {"a", "1"})

    assert actual_res == input_set


def test_person_to_string():
    assert (
        utils.person_to_string({"name": "raboof", "email": "foo@bar"})
        == "raboof <foo@bar>"
    )


def test_enrich_release_empty():
    actual_release = utils.enrich_release({})

    assert actual_release == {}


def test_enrich_release_content_target(api_request_factory, archive_data, release):

    release_data = archive_data.release_get(release)
    release_data["target_type"] = "content"

    url = reverse("api-1-release", url_args={"sha1_git": release})
    request = api_request_factory.get(url)

    actual_release = utils.enrich_release(release_data, request)

    release_data["target_url"] = reverse(
        "api-1-content",
        url_args={"q": f'sha1_git:{release_data["target"]}'},
        request=request,
    )

    assert actual_release == release_data


def test_enrich_release_directory_target(api_request_factory, archive_data, release):

    release_data = archive_data.release_get(release)
    release_data["target_type"] = "directory"

    url = reverse("api-1-release", url_args={"sha1_git": release})
    request = api_request_factory.get(url)

    actual_release = utils.enrich_release(release_data, request)

    release_data["target_url"] = reverse(
        "api-1-directory",
        url_args={"sha1_git": release_data["target"]},
        request=request,
    )

    assert actual_release == release_data


def test_enrich_release_revision_target(api_request_factory, archive_data, release):

    release_data = archive_data.release_get(release)
    release_data["target_type"] = "revision"

    url = reverse("api-1-release", url_args={"sha1_git": release})
    request = api_request_factory.get(url)

    actual_release = utils.enrich_release(release_data, request)

    release_data["target_url"] = reverse(
        "api-1-revision", url_args={"sha1_git": release_data["target"]}, request=request
    )

    assert actual_release == release_data


def test_enrich_release_release_target(api_request_factory, archive_data, release):

    release_data = archive_data.release_get(release)
    release_data["target_type"] = "release"

    url = reverse("api-1-release", url_args={"sha1_git": release})
    request = api_request_factory.get(url)

    actual_release = utils.enrich_release(release_data, request)

    release_data["target_url"] = reverse(
        "api-1-release", url_args={"sha1_git": release_data["target"]}, request=request
    )

    assert actual_release == release_data


def test_enrich_directory_entry_no_type():
    assert utils.enrich_directory_entry({"id": "dir-id"}) == {"id": "dir-id"}


def test_enrich_directory_entry_with_type(api_request_factory, archive_data, directory):

    dir_content = archive_data.directory_ls(directory)

    dir_entry = random.choice(dir_content)

    url = reverse("api-1-directory", url_args={"sha1_git": directory})
    request = api_request_factory.get(url)

    actual_directory = utils.enrich_directory_entry(dir_entry, request)

    if dir_entry["type"] == "file":
        dir_entry["target_url"] = reverse(
            "api-1-content",
            url_args={"q": f'sha1_git:{dir_entry["target"]}'},
            request=request,
        )

    elif dir_entry["type"] == "dir":
        dir_entry["target_url"] = reverse(
            "api-1-directory",
            url_args={"sha1_git": dir_entry["target"]},
            request=request,
        )

    elif dir_entry["type"] == "rev":
        dir_entry["target_url"] = reverse(
            "api-1-revision",
            url_args={"sha1_git": dir_entry["target"]},
            request=request,
        )

    assert actual_directory == dir_entry


def test_enrich_content_without_hashes():
    assert utils.enrich_content({"id": "123"}) == {"id": "123"}


def test_enrich_content_with_hashes(api_request_factory, content):

    for algo in DEFAULT_ALGORITHMS:

        content_data = dict(content)

        query_string = "%s:%s" % (algo, content_data[algo])

        url = reverse("api-1-content", url_args={"q": query_string})
        request = api_request_factory.get(url)

        enriched_content = utils.enrich_content(
            content_data, query_string=query_string, request=request
        )

        content_data["data_url"] = reverse(
            "api-1-content-raw", url_args={"q": query_string}, request=request
        )

        content_data["filetype_url"] = reverse(
            "api-1-content-filetype", url_args={"q": query_string}, request=request
        )

        content_data["language_url"] = reverse(
            "api-1-content-language", url_args={"q": query_string}, request=request
        )

        content_data["license_url"] = reverse(
            "api-1-content-license", url_args={"q": query_string}, request=request
        )

        assert enriched_content == content_data


def test_enrich_content_with_hashes_and_top_level_url(api_request_factory, content):

    for algo in DEFAULT_ALGORITHMS:

        content_data = dict(content)

        query_string = "%s:%s" % (algo, content_data[algo])

        url = reverse("api-1-content", url_args={"q": query_string})
        request = api_request_factory.get(url)

        enriched_content = utils.enrich_content(
            content_data, query_string=query_string, top_url=True, request=request
        )

        content_data["content_url"] = reverse(
            "api-1-content", url_args={"q": query_string}, request=request
        )

        content_data["data_url"] = reverse(
            "api-1-content-raw", url_args={"q": query_string}, request=request
        )

        content_data["filetype_url"] = reverse(
            "api-1-content-filetype", url_args={"q": query_string}, request=request
        )

        content_data["language_url"] = reverse(
            "api-1-content-language", url_args={"q": query_string}, request=request
        )

        content_data["license_url"] = reverse(
            "api-1-content-license", url_args={"q": query_string}, request=request
        )

        assert enriched_content == content_data


def test_enrich_revision_without_children_or_parent(
    api_request_factory, archive_data, revision
):

    revision_data = archive_data.revision_get(revision)
    del revision_data["parents"]

    url = reverse("api-1-revision", url_args={"sha1_git": revision})
    request = api_request_factory.get(url)

    actual_revision = utils.enrich_revision(revision_data, request)

    revision_data["url"] = reverse(
        "api-1-revision", url_args={"sha1_git": revision}, request=request
    )

    revision_data["history_url"] = reverse(
        "api-1-revision-log", url_args={"sha1_git": revision}, request=request
    )

    revision_data["directory_url"] = reverse(
        "api-1-directory",
        url_args={"sha1_git": revision_data["directory"]},
        request=request,
    )

    assert actual_revision == revision_data


def test_enrich_revision_with_children_and_parent_no_dir(
    api_request_factory, archive_data, revisions_list
):
    revision, parent_revision, child_revision = revisions_list(size=3)
    revision_data = archive_data.revision_get(revision)
    del revision_data["directory"]
    revision_data["parents"] = revision_data["parents"] + (parent_revision,)
    revision_data["children"] = child_revision

    url = reverse("api-1-revision", url_args={"sha1_git": revision})
    request = api_request_factory.get(url)

    actual_revision = utils.enrich_revision(revision_data, request)

    revision_data["url"] = reverse(
        "api-1-revision", url_args={"sha1_git": revision}, request=request
    )

    revision_data["history_url"] = reverse(
        "api-1-revision-log", url_args={"sha1_git": revision}, request=request
    )

    revision_data["parents"] = tuple(
        {
            "id": p["id"],
            "url": reverse(
                "api-1-revision", url_args={"sha1_git": p["id"]}, request=request
            ),
        }
        for p in revision_data["parents"]
    )

    revision_data["children_urls"] = [
        reverse(
            "api-1-revision", url_args={"sha1_git": child_revision}, request=request
        )
    ]

    assert actual_revision == revision_data


def test_enrich_revisionno_context(api_request_factory, revisions_list):
    revision, parent_revision, child_revision = revisions_list(size=3)
    revision_data = {
        "id": revision,
        "parents": [parent_revision],
        "children": [child_revision],
    }

    url = reverse("api-1-revision", url_args={"sha1_git": revision})
    request = api_request_factory.get(url)

    actual_revision = utils.enrich_revision(revision_data, request)

    revision_data["url"] = reverse(
        "api-1-revision", url_args={"sha1_git": revision}, request=request
    )

    revision_data["history_url"] = reverse(
        "api-1-revision-log", url_args={"sha1_git": revision}, request=request
    )

    revision_data["parents"] = tuple(
        {
            "id": parent_revision,
            "url": reverse(
                "api-1-revision",
                url_args={"sha1_git": parent_revision},
                request=request,
            ),
        }
    )

    revision_data["children_urls"] = [
        reverse(
            "api-1-revision", url_args={"sha1_git": child_revision}, request=request
        )
    ]

    assert actual_revision == revision_data


def test_enrich_revision_with_no_message(
    api_request_factory, archive_data, revisions_list
):
    revision, parent_revision, child_revision = revisions_list(size=3)
    revision_data = archive_data.revision_get(revision)
    revision_data["message"] = None
    revision_data["parents"] = revision_data["parents"] + (parent_revision,)
    revision_data["children"] = child_revision

    url = reverse("api-1-revision", url_args={"sha1_git": revision})
    request = api_request_factory.get(url)

    actual_revision = utils.enrich_revision(revision_data, request)

    revision_data["url"] = reverse(
        "api-1-revision", url_args={"sha1_git": revision}, request=request
    )

    revision_data["directory_url"] = reverse(
        "api-1-directory",
        url_args={"sha1_git": revision_data["directory"]},
        request=request,
    )

    revision_data["history_url"] = reverse(
        "api-1-revision-log", url_args={"sha1_git": revision}, request=request
    )

    revision_data["parents"] = tuple(
        {
            "id": p["id"],
            "url": reverse(
                "api-1-revision", url_args={"sha1_git": p["id"]}, request=request
            ),
        }
        for p in revision_data["parents"]
    )

    revision_data["children_urls"] = [
        reverse(
            "api-1-revision", url_args={"sha1_git": child_revision}, request=request
        )
    ]

    assert actual_revision == revision_data


def test_enrich_revision_with_invalid_message(
    api_request_factory, archive_data, revisions_list
):
    revision, parent_revision, child_revision = revisions_list(size=3)
    revision_data = archive_data.revision_get(revision)
    revision_data["decoding_failures"] = ["message"]
    revision_data["parents"] = revision_data["parents"] + (parent_revision,)
    revision_data["children"] = child_revision

    url = reverse("api-1-revision", url_args={"sha1_git": revision})
    request = api_request_factory.get(url)

    actual_revision = utils.enrich_revision(revision_data, request)

    revision_data["url"] = reverse(
        "api-1-revision", url_args={"sha1_git": revision}, request=request
    )

    revision_data["message_url"] = reverse(
        "api-1-revision-raw-message", url_args={"sha1_git": revision}, request=request
    )

    revision_data["directory_url"] = reverse(
        "api-1-directory",
        url_args={"sha1_git": revision_data["directory"]},
        request=request,
    )

    revision_data["history_url"] = reverse(
        "api-1-revision-log", url_args={"sha1_git": revision}, request=request
    )

    revision_data["parents"] = tuple(
        {
            "id": p["id"],
            "url": reverse(
                "api-1-revision", url_args={"sha1_git": p["id"]}, request=request
            ),
        }
        for p in revision_data["parents"]
    )

    revision_data["children_urls"] = [
        reverse(
            "api-1-revision", url_args={"sha1_git": child_revision}, request=request
        )
    ]

    assert actual_revision == revision_data


def test_enrich_snapshot(api_request_factory, archive_data, snapshot):
    snapshot_data = archive_data.snapshot_get(snapshot)

    url = reverse("api-1-snapshot", url_args={"snapshot_id": snapshot})
    request = api_request_factory.get(url)

    actual_snapshot = utils.enrich_snapshot(snapshot_data, request)

    for _, b in snapshot_data["branches"].items():
        if b["target_type"] in ("directory", "revision", "release"):
            b["target_url"] = reverse(
                f'api-1-{b["target_type"]}',
                url_args={"sha1_git": b["target"]},
                request=request,
            )
        elif b["target_type"] == "content":
            b["target_url"] = reverse(
                "api-1-content",
                url_args={"q": f'sha1_git:{b["target"]}'},
                request=request,
            )

    for _, b in snapshot_data["branches"].items():
        if b["target_type"] == "alias":
            target = resolve_branch_alias(snapshot_data, b)
            b["target_url"] = target["target_url"]

    assert actual_snapshot == snapshot_data


def test_enrich_origin(api_request_factory, origin):
    url = reverse("api-1-origin", url_args={"origin_url": origin["url"]})
    request = api_request_factory.get(url)

    origin_data = {"url": origin["url"]}
    actual_origin = utils.enrich_origin(origin_data, request)

    origin_data["origin_visits_url"] = reverse(
        "api-1-origin-visits", url_args={"origin_url": origin["url"]}, request=request
    )
    origin_data["metadata_authorities_url"] = reverse(
        "api-1-raw-extrinsic-metadata-swhid-authorities",
        url_args={"target": Origin(url=origin["url"]).swhid()},
        request=request,
    )

    assert actual_origin == origin_data


def test_enrich_origin_search_result(api_request_factory, origin):
    url = reverse("api-1-origin-search", url_args={"url_pattern": origin["url"]})
    request = api_request_factory.get(url)

    origin_visits_url = reverse(
        "api-1-origin-visits", url_args={"origin_url": origin["url"]}, request=request
    )
    metadata_authorities_url = reverse(
        "api-1-raw-extrinsic-metadata-swhid-authorities",
        url_args={"target": Origin(url=origin["url"]).swhid()},
        request=request,
    )

    origin_search_result_data = (
        [{"url": origin["url"]}],
        None,
    )

    enriched_origin_search_result = (
        [
            {
                "url": origin["url"],
                "origin_visits_url": origin_visits_url,
                "metadata_authorities_url": metadata_authorities_url,
            }
        ],
        None,
    )

    assert (
        utils.enrich_origin_search_result(origin_search_result_data, request=request)
        == enriched_origin_search_result
    )


def test_enrich_origin_visit(api_request_factory, origin):

    origin_visit = random.choice(get_origin_visits(origin))

    url = reverse(
        "api-1-origin-visit",
        url_args={"origin_url": origin["url"], "visit_id": origin_visit["visit"]},
    )
    request = api_request_factory.get(url)

    actual_origin_visit = utils.enrich_origin_visit(
        origin_visit,
        with_origin_link=True,
        with_origin_visit_link=True,
        request=request,
    )

    origin_visit["origin_url"] = reverse(
        "api-1-origin", url_args={"origin_url": origin["url"]}, request=request
    )

    origin_visit["origin_visit_url"] = reverse(
        "api-1-origin-visit",
        url_args={"origin_url": origin["url"], "visit_id": origin_visit["visit"]},
        request=request,
    )

    origin_visit["snapshot_url"] = reverse(
        "api-1-snapshot",
        url_args={"snapshot_id": origin_visit["snapshot"]},
        request=request,
    )

    assert actual_origin_visit == origin_visit
