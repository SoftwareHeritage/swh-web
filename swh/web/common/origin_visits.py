# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import math
from typing import List, Optional

from django.core.cache import cache

from swh.web.common import archive
from swh.web.common.exc import NotFoundExc
from swh.web.common.typing import OriginInfo, OriginVisitInfo
from swh.web.common.utils import parse_iso8601_date_to_utc


def get_origin_visits(origin_info: OriginInfo) -> List[OriginVisitInfo]:
    """Function that returns the list of visits for a swh origin.
    That list is put in cache in order to speedup the navigation
    in the swh web browse ui.

    The returned visits are sorted according to their date in
    ascending order.

    Args:
        origin_info: dict describing the origin to fetch visits from

    Returns:
        A list of dict describing the origin visits

    Raises:
        swh.web.common.exc.NotFoundExc: if the origin is not found
    """

    from swh.web.common import archive

    if "url" in origin_info:
        origin_url = origin_info["url"]
    else:
        origin_url = archive.lookup_origin(origin_info)["url"]

    cache_entry_id = "origin_visits_%s" % origin_url
    cache_entry = cache.get(cache_entry_id)

    last_visit = 0
    origin_visits = []
    new_visits = []
    per_page = archive.MAX_LIMIT
    if cache_entry:
        origin_visits = cache_entry
        last_visit = cache_entry[-1]["visit"]
        new_visits = list(
            archive.lookup_origin_visits(
                origin_url, last_visit=last_visit, per_page=per_page
            )
        )
        last_visit += len(new_visits)
        if not new_visits:
            last_snp = archive.lookup_latest_origin_snapshot(origin_url)
            if not last_snp or last_snp["id"] == cache_entry[-1]["snapshot"]:
                return cache_entry

    # get new visits that we did not retrieve yet
    while 1:
        visits = list(
            archive.lookup_origin_visits(
                origin_url, last_visit=last_visit, per_page=per_page
            )
        )
        new_visits += visits
        if len(visits) < per_page:
            break
        last_visit += per_page

    def _visit_sort_key(visit):
        ts = parse_iso8601_date_to_utc(visit["date"]).timestamp()
        return ts + (float(visit["visit"]) / 10e3)

    # cache entry is already sorted with oldest visits
    origin_visits += sorted(new_visits, key=lambda v: _visit_sort_key(v))

    cache.set(cache_entry_id, origin_visits)

    return origin_visits


def get_origin_visit(
    origin_info: OriginInfo,
    visit_ts: Optional[str] = None,
    visit_id: Optional[int] = None,
    snapshot_id: Optional[str] = None,
) -> OriginVisitInfo:
    """Function that returns information about a visit for a given origin.

    If a timestamp is provided, the closest visit from that
    timestamp is returned.

    If a snapshot identifier is provided, the first visit with that snapshot
    is returned.

    If no search hints are provided, return the most recent full visit with
    a valid snapshot or the most recent partial visit with a valid snapshot
    otherwise.

    Args:
        origin_info: a dict filled with origin information
        visit_ts: an ISO 8601 datetime string to parse
        snapshot_id: a snapshot identifier

    Returns:
        A dict containing the visit info.

    Raises:
        swh.web.common.exc.NotFoundExc: if no visit can be found
    """
    # returns the latest full visit with a valid snapshot
    visit = archive.lookup_origin_visit_latest(
        origin_info["url"], allowed_statuses=["full"], require_snapshot=True
    )
    if not visit:
        # or the latest partial visit with a valid snapshot otherwise
        visit = archive.lookup_origin_visit_latest(
            origin_info["url"], allowed_statuses=["partial"], require_snapshot=True
        )

    if not visit_ts and not visit_id and not snapshot_id:
        if visit:
            return visit
        else:
            raise NotFoundExc(
                f"No valid visit for origin with url {origin_info['url']} found!"
            )

    # no need to fetch all visits list and search in it if the latest
    # visit matches some criteria
    if visit and (visit["snapshot"] == snapshot_id or visit["visit"] == visit_id):
        return visit

    visits = get_origin_visits(origin_info)

    if not visits:
        raise NotFoundExc(
            f"No visits associated to origin with url {origin_info['url']}!"
        )

    if snapshot_id:
        visits = [v for v in visits if v["snapshot"] == snapshot_id]
        if len(visits) == 0:
            raise NotFoundExc(
                (
                    "Visit for snapshot with id %s for origin with"
                    " url %s not found!" % (snapshot_id, origin_info["url"])
                )
            )
        return visits[0]

    if visit_id:
        visits = [v for v in visits if v["visit"] == int(visit_id)]
        if len(visits) == 0:
            raise NotFoundExc(
                (
                    "Visit with id %s for origin with"
                    " url %s not found!" % (visit_id, origin_info["url"])
                )
            )
        return visits[0]

    if visit_ts:

        target_visit_ts = math.floor(parse_iso8601_date_to_utc(visit_ts).timestamp())

        # Find the visit with date closest to the target (in absolute value)
        (abs_time_delta, visit_idx) = min(
            (
                (math.floor(parse_iso8601_date_to_utc(visit["date"]).timestamp()), i)
                for (i, visit) in enumerate(visits)
            ),
            key=lambda ts_and_i: abs(ts_and_i[0] - target_visit_ts),
        )

        if visit_idx is not None:
            visit = visits[visit_idx]
            # If multiple visits have the same date, select the one with
            # the largest id.
            while (
                visit_idx < len(visits) - 1
                and visit["date"] == visits[visit_idx + 1]["date"]
            ):
                visit_idx = visit_idx + 1
                visit = visits[visit_idx]
            return visit
        else:
            raise NotFoundExc(
                (
                    "Visit with timestamp %s for origin with "
                    "url %s not found!" % (visit_ts, origin_info["url"])
                )
            )
    return visits[-1]
