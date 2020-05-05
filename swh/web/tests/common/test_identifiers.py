# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given

import pytest

from swh.model.hashutil import hash_to_bytes
from swh.model.identifiers import (
    CONTENT,
    DIRECTORY,
    RELEASE,
    REVISION,
    SNAPSHOT,
    PersistentId,
)

from swh.web.common.exc import BadInputExc
from swh.web.common.identifiers import (
    get_swh_persistent_id,
    resolve_swh_persistent_id,
    get_persistent_identifier,
    group_swh_persistent_identifiers,
)
from swh.web.common.utils import reverse
from swh.web.tests.data import random_sha1
from swh.web.tests.strategies import content, directory, release, revision, snapshot


@given(content())
def test_get_swh_persistent_id(content):
    swh_object_type = CONTENT
    sha1_git = content["sha1_git"]

    expected_swh_id = "swh:1:cnt:" + sha1_git

    assert get_swh_persistent_id(swh_object_type, sha1_git) == expected_swh_id

    with pytest.raises(BadInputExc) as e:
        get_swh_persistent_id("foo", sha1_git)
    assert e.match("Invalid object")

    with pytest.raises(BadInputExc) as e:
        get_swh_persistent_id(swh_object_type, "not a valid id")
    assert e.match("Invalid object")


@given(content(), directory(), release(), revision(), snapshot())
def test_resolve_swh_persistent_id(content, directory, release, revision, snapshot):
    for obj_type, obj_id in (
        (CONTENT, content["sha1_git"]),
        (DIRECTORY, directory),
        (RELEASE, release),
        (REVISION, revision),
        (SNAPSHOT, snapshot),
    ):

        swh_pid = get_swh_persistent_id(obj_type, obj_id)

        url_args = {}
        if obj_type == CONTENT:
            url_args["query_string"] = f"sha1_git:{obj_id}"
        elif obj_type == SNAPSHOT:
            url_args["snapshot_id"] = obj_id
        else:
            url_args["sha1_git"] = obj_id
        query_params = {"origin_url": "some-origin"}
        browse_url = reverse(
            f"browse-{obj_type}", url_args=url_args, query_params=query_params
        )

        resolved_pid = resolve_swh_persistent_id(swh_pid, query_params)

        assert isinstance(resolved_pid["swh_id_parsed"], PersistentId)
        assert str(resolved_pid["swh_id_parsed"]) == swh_pid
        assert resolved_pid["browse_url"] == browse_url

    with pytest.raises(BadInputExc, match="Origin PIDs"):
        resolve_swh_persistent_id(f"swh:1:ori:{random_sha1()}")


@given(content(), directory(), release(), revision(), snapshot())
def test_get_persistent_identifier(content, directory, release, revision, snapshot):
    for obj_type, obj_id in (
        (CONTENT, content["sha1_git"]),
        (DIRECTORY, directory),
        (RELEASE, release),
        (REVISION, revision),
        (SNAPSHOT, snapshot),
    ):
        swh_pid = get_swh_persistent_id(obj_type, obj_id)
        swh_parsed_pid = get_persistent_identifier(swh_pid)

        assert isinstance(swh_parsed_pid, PersistentId)
        assert str(swh_parsed_pid) == swh_pid

    with pytest.raises(BadInputExc, match="Error when parsing identifier"):
        get_persistent_identifier("foo")


@given(content(), directory(), release(), revision(), snapshot())
def test_group_persistent_identifiers(content, directory, release, revision, snapshot):
    swh_pids = []
    expected = {}
    for obj_type, obj_id in (
        (CONTENT, content["sha1_git"]),
        (DIRECTORY, directory),
        (RELEASE, release),
        (REVISION, revision),
        (SNAPSHOT, snapshot),
    ):
        swh_pid = get_swh_persistent_id(obj_type, obj_id)
        swh_pid = get_persistent_identifier(swh_pid)
        swh_pids.append(swh_pid)
        expected[obj_type] = [hash_to_bytes(obj_id)]

    pid_groups = group_swh_persistent_identifiers(swh_pids)

    assert pid_groups == expected
