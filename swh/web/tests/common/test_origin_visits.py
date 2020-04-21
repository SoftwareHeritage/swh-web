# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from hypothesis import given

import pytest

from swh.model.hashutil import hash_to_hex
from swh.web.common.exc import NotFoundExc
from swh.web.common.origin_visits import get_origin_visits, get_origin_visit
from swh.web.tests.strategies import new_snapshots


@given(new_snapshots(3))
def test_get_origin_visits(mocker, snapshots):
    mock_service = mocker.patch("swh.web.common.service")
    mock_service.MAX_LIMIT = 2

    def _lookup_origin_visits(*args, **kwargs):
        if kwargs["last_visit"] is None:
            return [
                {
                    "visit": 1,
                    "date": "2017-05-06T00:59:10+00:00",
                    "status": "full",
                    "snapshot": hash_to_hex(snapshots[0].id),
                    "type": "git",
                },
                {
                    "visit": 2,
                    "date": "2017-08-06T00:59:10+00:00",
                    "status": "full",
                    "snapshot": hash_to_hex(snapshots[1].id),
                    "type": "git",
                },
            ]
        else:
            return [
                {
                    "visit": 3,
                    "date": "2017-09-06T00:59:10+00:00",
                    "status": "full",
                    "snapshot": hash_to_hex(snapshots[2].id),
                    "type": "git",
                }
            ]

    mock_service.lookup_origin_visits.side_effect = _lookup_origin_visits

    origin_info = {
        "url": "https://github.com/foo/bar",
    }

    origin_visits = get_origin_visits(origin_info)

    assert len(origin_visits) == 3


@given(new_snapshots(5))
def test_get_origin_visit(mocker, snapshots):
    mock_origin_visits = mocker.patch("swh.web.common.origin_visits.get_origin_visits")
    origin_info = {
        "url": "https://github.com/foo/bar",
    }
    visits = [
        {
            "status": "full",
            "date": "2015-07-09T21:09:24+00:00",
            "visit": 1,
            "origin": "https://github.com/foo/bar",
            "type": "git",
            "snapshot": hash_to_hex(snapshots[0].id),
        },
        {
            "status": "full",
            "date": "2016-02-23T18:05:23.312045+00:00",
            "visit": 2,
            "origin": "https://github.com/foo/bar",
            "type": "git",
            "snapshot": hash_to_hex(snapshots[1].id),
        },
        {
            "status": "full",
            "date": "2016-03-28T01:35:06.554111+00:00",
            "visit": 3,
            "origin": "https://github.com/foo/bar",
            "type": "git",
            "snapshot": hash_to_hex(snapshots[2].id),
        },
        {
            "status": "full",
            "date": "2016-06-18T01:22:24.808485+00:00",
            "visit": 4,
            "origin": "https://github.com/foo/bar",
            "type": "git",
            "snapshot": hash_to_hex(snapshots[3].id),
        },
        {
            "status": "full",
            "date": "2016-08-14T12:10:00.536702+00:00",
            "visit": 5,
            "origin": "https://github.com/foo/bar",
            "type": "git",
            "snapshot": hash_to_hex(snapshots[4].id),
        },
    ]
    mock_origin_visits.return_value = visits

    visit_id = 12
    with pytest.raises(NotFoundExc) as e:
        visit = get_origin_visit(origin_info, visit_id=visit_id)

    assert e.match("Visit with id %s" % visit_id)
    assert e.match("url %s" % origin_info["url"])

    visit = get_origin_visit(origin_info, visit_id=2)
    assert visit == visits[1]

    visit = get_origin_visit(origin_info, visit_ts="2016-02-23T18:05:23.312045+00:00")
    assert visit == visits[1]

    visit = get_origin_visit(origin_info, visit_ts="2016-02-20")
    assert visit == visits[1]

    visit = get_origin_visit(origin_info, visit_ts="2016-06-18T01:22")
    assert visit == visits[3]

    visit = get_origin_visit(origin_info, visit_ts="2016-06-18 01:22")
    assert visit == visits[3]

    visit = get_origin_visit(origin_info, visit_ts=1466208000)
    assert visit == visits[3]

    visit = get_origin_visit(origin_info, visit_ts="2014-01-01")
    assert visit == visits[0]

    visit = get_origin_visit(origin_info, visit_ts="2018-01-01")
    assert visit == visits[-1]


def test_get_origin_visit_latest_valid_snapshot(mocker):
    mock_origin_visits = mocker.patch("swh.web.common.origin_visits.get_origin_visits")
    origin_info = {
        "url": "https://nix-community.github.io/nixpkgs-swh/sources-unstable.json",
    }
    visits = [
        {
            "date": "2020-04-15T12:42:52.936520+00:00",
            "origin": origin_info["url"],
            "snapshot": "d820451681c74eec63693b6ea4e4b8417c76bb7a",
            "status": "partial",
            "type": "nixguix",
            "visit": 16,
        },
        {
            "date": "2020-04-17T17:25:13.738789+00:00",
            "origin": origin_info["url"],
            "snapshot": "d20627c1ae2b5e553e8adcf625f37e37cc5190dd",
            "status": "partial",
            "type": "nixguix",
            "visit": 17,
        },
        {
            "date": "2020-04-19T19:02:42.906079+00:00",
            "origin": origin_info["url"],
            "snapshot": None,
            "status": "partial",
            "type": "nixguix",
            "visit": 18,
        },
        {
            "date": "2020-04-20T12:43:41.120422+00:00",
            "origin": origin_info["url"],
            "snapshot": None,
            "status": "partial",
            "type": "nixguix",
            "visit": 19,
        },
        {
            "date": "2020-04-20T12:46:40.255418+00:00",
            "origin": origin_info["url"],
            "snapshot": None,
            "status": "partial",
            "type": "nixguix",
            "visit": 20,
        },
    ]

    mock_origin_visits.return_value = visits

    visit = get_origin_visit(origin_info)

    assert visit["snapshot"] is not None
    assert visit["visit"] == 17
