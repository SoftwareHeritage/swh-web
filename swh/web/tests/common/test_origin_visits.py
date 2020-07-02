# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import timedelta

from hypothesis import given

import pytest

from swh.model.hashutil import hash_to_hex
from swh.model.model import OriginVisit, OriginVisitStatus
from swh.storage.utils import now
from swh.web.common.exc import NotFoundExc
from swh.web.common.origin_visits import get_origin_visits, get_origin_visit
from swh.web.common.typing import OriginInfo
from swh.web.tests.strategies import new_origin, new_snapshots


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


@given(new_origin(), new_snapshots(6))
def test_get_origin_visit_return_first_valid_full_visit(
    archive_data, new_origin, new_snapshots
):
    visits = []
    archive_data.origin_add([new_origin])
    # create 6 visits, the first three have full status while the
    # last three have partial status and set a null snapshot for
    # the last four visits
    for i, snp in enumerate(new_snapshots):
        visit_date = now() + timedelta(days=i * 10)
        visit = archive_data.origin_visit_add(
            [OriginVisit(origin=new_origin.url, date=visit_date, type="git",)]
        )[0]
        archive_data.snapshot_add([new_snapshots[i]])
        visit_status = OriginVisitStatus(
            origin=new_origin.url,
            visit=visit.visit,
            date=visit_date + timedelta(minutes=5),
            status="full" if i < 3 else "partial",
            snapshot=new_snapshots[i].id if i < 2 else None,
        )
        if i < 2:
            archive_data.origin_visit_status_add([visit_status])
        visits.append(visit.visit)

    # should return the second visit
    expected_visit = archive_data.origin_visit_get_by(new_origin.url, visits[1])
    assert get_origin_visit((OriginInfo(url=new_origin.url))) == expected_visit


@given(new_origin(), new_snapshots(6))
def test_get_origin_visit_non_resolvable_snapshots(
    archive_data, new_origin, new_snapshots
):
    visits = []
    archive_data.origin_add([new_origin])
    # create 6 full visits, the first three have resolvable snapshots
    # while the last three have non resolvable snapshots
    for i, snp in enumerate(new_snapshots):
        visit_date = now() + timedelta(days=i * 10)
        visit = archive_data.origin_visit_add(
            [OriginVisit(origin=new_origin.url, date=visit_date, type="git",)]
        )[0]
        archive_data.snapshot_add([new_snapshots[i]])
        visit_status = OriginVisitStatus(
            origin=new_origin.url,
            visit=visit.visit,
            date=visit_date + timedelta(minutes=5),
            status="full",
            snapshot=new_snapshots[i].id,
        )
        if i < 3:
            archive_data.origin_visit_status_add([visit_status])
        visits.append(visit.visit)

    # should return the third visit
    expected_visit = archive_data.origin_visit_get_by(new_origin.url, visits[2])
    assert get_origin_visit((OriginInfo(url=new_origin.url))) == expected_visit


@given(new_origin(), new_snapshots(6))
def test_get_origin_visit_return_first_valid_partial_visit(
    archive_data, new_origin, new_snapshots
):
    visits = []

    archive_data.origin_add([new_origin])
    # create 6 visits, the first three have full status but null snapshot
    # while the last three have partial status with valid snapshot
    for i, snp in enumerate(new_snapshots):
        visit_date = now() + timedelta(days=i * 10)
        visit = archive_data.origin_visit_add(
            [OriginVisit(origin=new_origin.url, date=visit_date, type="git",)]
        )[0]
        archive_data.snapshot_add([new_snapshots[i]])
        visit_status = OriginVisitStatus(
            origin=new_origin.url,
            visit=visit.visit,
            date=visit_date + timedelta(minutes=5),
            status="full" if i < 3 else "partial",
            snapshot=new_snapshots[i].id if i > 2 else None,
        )
        if i > 2:
            archive_data.origin_visit_status_add([visit_status])

        visits.append(visit.visit)

    # should return the last visit
    expected_visit = archive_data.origin_visit_get_by(new_origin.url, visits[-1])
    assert get_origin_visit((OriginInfo(url=new_origin.url))) == expected_visit
