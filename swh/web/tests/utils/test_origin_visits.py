# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import timedelta

from hypothesis import given, settings
import iso8601
import pytest

from swh.model.model import OriginVisit, OriginVisitStatus
from swh.storage.utils import now
from swh.web.tests.strategies import new_origin, new_snapshots
from swh.web.utils.exc import NotFoundExc
from swh.web.utils.origin_visits import get_origin_visit, get_origin_visits
from swh.web.utils.typing import OriginInfo


@settings(max_examples=1)
@given(new_origin(), new_snapshots(3))
def test_get_origin_visits(mocker, archive_data, new_origin, new_snapshots):
    from swh.web.utils import archive

    mocker.patch.object(archive, "MAX_LIMIT", 2)

    archive_data.origin_add([new_origin])
    archive_data.snapshot_add(new_snapshots)
    for i, snapshot in enumerate(new_snapshots):
        visit_date = now() + timedelta(days=i * 10)
        visit = archive_data.origin_visit_add(
            [
                OriginVisit(
                    origin=new_origin.url,
                    date=visit_date,
                    type="git",
                )
            ]
        )[0]
        visit_status = OriginVisitStatus(
            origin=new_origin.url,
            visit=visit.visit,
            date=visit_date + timedelta(minutes=5),
            status="full",
            snapshot=snapshot.id,
        )
        archive_data.origin_visit_status_add([visit_status])

    origin_visits = get_origin_visits(new_origin.to_dict())

    assert len(origin_visits) == len(new_snapshots)


@given(new_origin(), new_snapshots(5))
def test_get_origin_visit(archive_data, new_origin, new_snapshots):

    archive_data.origin_add([new_origin])
    archive_data.snapshot_add(new_snapshots)
    visits = []
    for i, visit_date in enumerate(
        map(
            iso8601.parse_date,
            [
                "2015-07-09T21:09:24+00:00",
                "2016-02-23T18:05:23.312045+00:00",
                "2016-03-28T01:35:06.554111+00:00",
                "2016-06-18T01:22:24.808485+00:00",
                "2016-08-14T12:10:00.536702+00:00",
            ],
        )
    ):
        visit = archive_data.origin_visit_add(
            [
                OriginVisit(
                    origin=new_origin.url,
                    date=visit_date,
                    type="git",
                )
            ]
        )[0]
        visits.append(visit)
        visit_status = OriginVisitStatus(
            origin=new_origin.url,
            visit=visit.visit,
            date=visit_date + timedelta(minutes=5),
            status="full",
            snapshot=new_snapshots[i].id,
        )
        archive_data.origin_visit_status_add([visit_status])

    origin_info = new_origin.to_dict()

    visit_id = visits[-1].visit + 1
    with pytest.raises(NotFoundExc) as e:
        visit = get_origin_visit(origin_info, visit_id=visit_id)

    assert e.match("visit with id %s" % visit_id)
    assert e.match("Origin %s" % origin_info["url"])

    visit_id = visits[1].visit
    visit = get_origin_visit(origin_info, visit_id=visit_id)
    assert visit == archive_data.origin_visit_get_by(new_origin.url, visit_id=visit_id)

    visit = get_origin_visit(origin_info, visit_ts="2016-02-23T18:05:23.312045+00:00")
    assert visit == archive_data.origin_visit_get_by(new_origin.url, visit_id=visit_id)

    visit = get_origin_visit(origin_info, visit_ts="2016-02-20")
    assert visit == archive_data.origin_visit_get_by(new_origin.url, visit_id=visit_id)

    visit_id = visits[3].visit
    visit = get_origin_visit(origin_info, visit_ts="2016-06-18T01:22")
    assert visit == archive_data.origin_visit_get_by(new_origin.url, visit_id=visit_id)

    visit = get_origin_visit(origin_info, visit_ts="2016-06-18 01:22")
    assert visit == archive_data.origin_visit_get_by(new_origin.url, visit_id=visit_id)

    visit_id = visits[0].visit
    visit = get_origin_visit(origin_info, visit_ts="2014-01-01")
    assert visit == archive_data.origin_visit_get_by(new_origin.url, visit_id=visit_id)

    visit_id = visits[-1].visit
    visit = get_origin_visit(origin_info, visit_ts="2018-01-01")
    assert visit == archive_data.origin_visit_get_by(new_origin.url, visit_id=visit_id)


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
            [
                OriginVisit(
                    origin=new_origin.url,
                    date=visit_date,
                    type="git",
                )
            ]
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
            [
                OriginVisit(
                    origin=new_origin.url,
                    date=visit_date,
                    type="git",
                )
            ]
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
            [
                OriginVisit(
                    origin=new_origin.url,
                    date=visit_date,
                    type="git",
                )
            ]
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


def test_get_origin_visit_latest_snapshot(mocker, origin_with_multiple_visits):
    origin_visits = get_origin_visits(origin_with_multiple_visits)
    first_visit = origin_visits[0]
    latest_visit = origin_visits[-1]
    mock_get_origin_visits = mocker.patch(
        "swh.web.utils.origin_visits.get_origin_visits"
    )
    mock_get_origin_visits.return_value = origin_visits

    visit = get_origin_visit(
        origin_with_multiple_visits, snapshot_id=latest_visit["snapshot"]
    )
    assert visit == latest_visit
    assert not mock_get_origin_visits.called

    visit = get_origin_visit(
        origin_with_multiple_visits, snapshot_id=first_visit["snapshot"]
    )
    assert visit == first_visit
    assert mock_get_origin_visits.called
