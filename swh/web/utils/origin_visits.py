# Copyright (C) 2018-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import List, Optional

from django.core.cache import cache

from swh.web.utils import archive, parse_iso8601_date_to_utc
from swh.web.utils.exc import NotFoundExc
from swh.web.utils.typing import OriginInfo, OriginVisitInfo


def get_origin_visits(
    origin_info: OriginInfo, lookup_similar_urls: bool = True
) -> List[OriginVisitInfo]:
    """Function that returns the list of visits for a swh origin.
    That list is put in cache in order to speedup the navigation
    in the swh web browse ui.

    The returned visits are sorted according to their date in
    ascending order.

    Args:
        origin_info: dict describing the origin to fetch visits from
        lookup_similar_urls: if :const:`True`, lookup origin with and
            without trailing slash in its URL

    Returns:
        A list of dict describing the origin visits

    Raises:
        swh.web.utils.exc.NotFoundExc: if the origin is not found
    """

    from swh.web.utils import archive

    origin_url = archive.lookup_origin(
        origin_info, lookup_similar_urls=lookup_similar_urls
    )["url"]

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
        swh.web.utils.exc.NotFoundExc: if no visit can be found
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

    if visit_id:
        return archive.lookup_origin_visit(origin_info["url"], visit_id)

    if visit_ts:
        visit = archive.origin_visit_find_by_date(
            origin_info["url"],
            parse_iso8601_date_to_utc(visit_ts),
            greater_or_equal=False,
        )
        if visit is not None:
            return visit
        else:
            raise NotFoundExc(
                (
                    "Visit with timestamp %s for origin with "
                    "url %s not found!" % (visit_ts, origin_info["url"])
                )
            )

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

    return visits[-1]
