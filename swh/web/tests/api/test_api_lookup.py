# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import pytest

from swh.web.common.exc import NotFoundExc
from swh.web.api.views import utils


def test_genericapi_lookup_nothing_is_found():
    def test_generic_lookup_fn(sha1, another_unused_arg):
        assert another_unused_arg == "unused_arg"
        assert sha1 == "sha1"
        return None

    notfound_msg = "This will be raised because None is returned."

    with pytest.raises(NotFoundExc) as e:
        utils.api_lookup(
            test_generic_lookup_fn, "sha1", "unused_arg", notfound_msg=notfound_msg
        )

    assert e.match(notfound_msg)


def test_generic_api_map_are_enriched_and_transformed_to_list():
    def test_generic_lookup_fn_1(criteria0, param0, param1):
        assert criteria0 == "something"
        return map(lambda x: x + 1, [1, 2, 3])

    actual_result = utils.api_lookup(
        test_generic_lookup_fn_1,
        "something",
        "some param 0",
        "some param 1",
        notfound_msg=(
            "This is not the error message you are looking for. " "Move along."
        ),
        enrich_fn=lambda x, request: x * 2,
    )

    assert actual_result == [4, 6, 8]


def test_generic_api_list_are_enriched_too():
    def test_generic_lookup_fn_2(crit):
        assert crit == "something"
        return ["a", "b", "c"]

    actual_result = utils.api_lookup(
        test_generic_lookup_fn_2,
        "something",
        notfound_msg=(
            "Not the error message you are looking for, it is. " "Along, you move!"
        ),
        enrich_fn=lambda x, request: "".join(["=", x, "="]),
    )

    assert actual_result == ["=a=", "=b=", "=c="]


def test_generic_api_generator_are_enriched_and_returned_as_list():
    def test_generic_lookup_fn_3(crit):
        assert crit == "crit"
        return (i for i in [4, 5, 6])

    actual_result = utils.api_lookup(
        test_generic_lookup_fn_3,
        "crit",
        notfound_msg="Move!",
        enrich_fn=lambda x, request: x - 1,
    )

    assert actual_result == [3, 4, 5]


def test_generic_api_simple_data_are_enriched_and_returned_too():
    def test_generic_lookup_fn_4(crit):
        assert crit == "123"
        return {"a": 10}

    def test_enrich_data(x, request):
        x["a"] = x["a"] * 10
        return x

    actual_result = utils.api_lookup(
        test_generic_lookup_fn_4,
        "123",
        notfound_msg="Nothing to do",
        enrich_fn=test_enrich_data,
    )

    assert actual_result == {"a": 100}


def test_api_lookup_not_found():
    notfound_msg = "this is the error message raised as it is None"
    with pytest.raises(NotFoundExc) as e:
        utils.api_lookup(lambda x: None, "something", notfound_msg=notfound_msg)

    assert e.match(notfound_msg)


def test_api_lookup_with_result():
    actual_result = utils.api_lookup(
        lambda x: x + "!",
        "something",
        notfound_msg="this is the error which won't be used here",
    )

    assert actual_result == "something!"


def test_api_lookup_with_result_as_map():
    actual_result = utils.api_lookup(
        lambda x: map(lambda y: y + 1, x),
        [1, 2, 3],
        notfound_msg="this is the error which won't be used here",
    )

    assert actual_result == [2, 3, 4]
