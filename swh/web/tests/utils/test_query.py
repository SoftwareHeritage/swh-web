# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.model import hashutil
from swh.web.utils import query
from swh.web.utils.exc import BadInputExc


def test_parse_hash_malformed_query_with_more_than_2_parts():
    with pytest.raises(BadInputExc):
        query.parse_hash("sha1:1234567890987654:other-stuff")


def test_parse_hash_guess_sha1():
    h = "f1d2d2f924e986ac86fdf7b36c94bcdf32beec15"
    r = query.parse_hash(h)
    assert r == ("sha1", hashutil.hash_to_bytes(h))


def test_parse_hash_guess_sha256():
    h = "084C799CD551DD1D8D5C5F9A5D593B2E931F5E36122ee5c793c1d08a19839cc0"
    r = query.parse_hash(h)
    assert r == ("sha256", hashutil.hash_to_bytes(h))


def test_parse_hash_guess_algo_malformed_hash():
    with pytest.raises(BadInputExc):
        query.parse_hash("1234567890987654")


def test_parse_hash_check_sha1():
    h = "f1d2d2f924e986ac86fdf7b36c94bcdf32beec15"
    r = query.parse_hash("sha1:" + h)
    assert r == ("sha1", hashutil.hash_to_bytes(h))


def test_parse_hash_check_sha1_git():
    h = "e1d2d2f924e986ac86fdf7b36c94bcdf32beec15"
    r = query.parse_hash("sha1_git:" + h)
    assert r == ("sha1_git", hashutil.hash_to_bytes(h))


def test_parse_hash_check_sha256():
    h = "084C799CD551DD1D8D5C5F9A5D593B2E931F5E36122ee5c793c1d08a19839cc0"
    r = query.parse_hash("sha256:" + h)
    assert r == ("sha256", hashutil.hash_to_bytes(h))


def test_parse_hash_check_algo_malformed_sha1_hash():
    with pytest.raises(BadInputExc):
        query.parse_hash("sha1:1234567890987654")


def test_parse_hash_check_algo_malformed_sha1_git_hash():
    with pytest.raises(BadInputExc):
        query.parse_hash("sha1_git:1234567890987654")


def test_parse_hash_check_algo_malformed_sha256_hash():
    with pytest.raises(BadInputExc):
        query.parse_hash("sha256:1234567890987654")


def test_parse_hash_check_algo_unknown_one():
    with pytest.raises(BadInputExc):
        query.parse_hash("sha2:1234567890987654")


def test_parse_hash_with_algorithms_or_throws_bad_query(mocker):
    mock_hash = mocker.patch("swh.web.utils.query.parse_hash")
    mock_hash.side_effect = BadInputExc("Error input")

    with pytest.raises(BadInputExc) as e:
        query.parse_hash_with_algorithms_or_throws(
            "sha1:blah", ["sha1"], "useless error message for this use case"
        )
    assert e.match("Error input")

    mock_hash.assert_called_once_with("sha1:blah")


def test_parse_hash_with_algorithms_or_throws_bad_algo(mocker):
    mock_hash = mocker.patch("swh.web.utils.query.parse_hash")
    mock_hash.return_value = "sha1", "123"

    with pytest.raises(BadInputExc) as e:
        query.parse_hash_with_algorithms_or_throws(
            "sha1:431", ["sha1_git"], "Only sha1_git!"
        )
    assert e.match("Only sha1_git!")

    mock_hash.assert_called_once_with("sha1:431")


def test_parse_hash_with_algorithms(mocker):
    mock_hash = mocker.patch("swh.web.utils.query.parse_hash")
    mock_hash.return_value = ("sha256", b"123")

    algo, sha = query.parse_hash_with_algorithms_or_throws(
        "sha256:123", ["sha256", "sha1_git"], "useless error message for this use case"
    )

    assert algo == "sha256"
    assert sha == b"123"

    mock_hash.assert_called_once_with("sha256:123")
