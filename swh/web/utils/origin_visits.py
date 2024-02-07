# Copyright (C) 2018-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import List, Optional

from swh.web.utils import archive, cache_get, cache_set, parse_iso8601_date_to_utc
from swh.web.utils.exc import NotFoundExc
from swh.web.utils.typing import OriginVisitInfo


def get_origin_visits(
    origin_url: str,
    lookup_similar_urls: bool = True,
    visit_type: Optional[str] = None,
) -> List[OriginVisitInfo]:
    """Function that returns the list of visits for a swh origin.
    That list is put in cache in order to speedup the navigation
    in the swh web browse ui.

    The returned visits are sorted according to their date in
    ascending order.

    Args:
        origin_url: URL of origin
        lookup_similar_urls: if :const:`True`, lookup origin with and
            without trailing slash in its URL

    Returns:
        A list of dict describing the origin visits

    Raises:
        swh.web.utils.exc.NotFoundExc: if the origin is not found
    """

    from swh.web.utils import archive

    def _filter_visits_by_type(
        visits: List[OriginVisitInfo], visit_type: Optional[str] = None
    ) -> List[OriginVisitInfo]:
        return [
            visit
            for visit in visits
            if visit_type is None or visit["type"] == visit_type
        ]

    origin_url = archive.lookup_origin(
        origin_url, lookup_similar_urls=lookup_similar_urls
    )["url"]

    cache_entry_id = "origin_visits_%s" % origin_url
    cache_entry = cache_get(cache_entry_id)

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
                return _filter_visits_by_type(cache_entry, visit_type=visit_type)

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

    cache_set(cache_entry_id, origin_visits)

    return _filter_visits_by_type(origin_visits, visit_type=visit_type)


def get_origin_visit(
    origin_url: str,
    visit_ts: Optional[str] = None,
    visit_id: Optional[int] = None,
    snapshot_id: Optional[str] = None,
    visit_type: Optional[str] = None,
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
        origin_url: URL of origin
        visit_ts: an ISO 8601 datetime string to parse
        snapshot_id: a snapshot identifier

    Returns:
        A dict containing the visit info.

    Raises:
        swh.web.utils.exc.NotFoundExc: if no visit can be found
    """
    # returns the latest full visit with a valid snapshot
    visit = archive.lookup_origin_visit_latest(
        origin_url,
        allowed_statuses=["full"],
        require_snapshot=True,
        type=visit_type,
    )
    if not visit:
        # or the latest partial visit with a valid snapshot otherwise
        visit = archive.lookup_origin_visit_latest(
            origin_url,
            allowed_statuses=["partial"],
            require_snapshot=True,
            type=visit_type,
        )

    if not visit_ts and not visit_id and not snapshot_id:
        if visit:
            return visit
        else:
            raise NotFoundExc(f"No valid visit for origin with url {origin_url} found!")

    # no need to fetch all visits list and search in it if the latest
    # visit matches some criteria
    if visit and (visit["snapshot"] == snapshot_id or visit["visit"] == visit_id):
        return visit

    if visit_id:
        return archive.lookup_origin_visit(origin_url, visit_id)

    error_message_prefix = "Visit"
    if visit_type is not None:
        error_message_prefix += f" of type {visit_type}"

    if visit_ts:
        visit = archive.origin_visit_find_by_date(
            origin_url,
            parse_iso8601_date_to_utc(visit_ts),
            greater_or_equal=False,
            type=visit_type,
        )
        if visit is not None:
            return visit
        else:
            raise NotFoundExc(
                (
                    f"{error_message_prefix} with timestamp {visit_ts} for origin with "
                    f"url {origin_url} not found!"
                )
            )

    visits = get_origin_visits(origin_url, visit_type=visit_type)

    if not visits:
        raise NotFoundExc(f"No visits associated to origin with url {origin_url}!")

    if snapshot_id:
        visits = [v for v in visits if v["snapshot"] == snapshot_id]
        if len(visits) == 0:
            raise NotFoundExc(
                (
                    f"{error_message_prefix} with snapshot id {snapshot_id} "
                    f"for origin with url {origin_url} not found!"
                )
            )
        return visits[0]

    return visits[-1]
