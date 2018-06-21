# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re

from datetime import datetime, timezone
from dateutil import parser as date_parser
from dateutil import tz

from django.core.cache import cache
from django.core import urlresolvers
from django.http import QueryDict

from swh.model.exceptions import ValidationError
from swh.model.identifiers import persistent_identifier
from swh.web.common import service
from swh.web.common.exc import BadInputExc


def reverse(viewname, args=None, kwargs=None, query_params=None,
            current_app=None, urlconf=None):
    """An override of django reverse function supporting query parameters.

    Args:
        viewname: the name of the django view from which to compute a url
        args: list of url arguments ordered according to their position it
        kwargs: dictionary of url arguments indexed by their names
        query_params: dictionary of query parameters to append to the
            reversed url
        current_app: the name of the django app tighted to the view
        urlconf: url configuration module

    Returns:
        The url of the requested view with processed arguments and
        query parameters
    """

    if kwargs:
        kwargs = {k: v for k, v in kwargs.items() if v is not None}

    url = urlresolvers.reverse(
            viewname, urlconf=urlconf, args=args,
            kwargs=kwargs, current_app=current_app)

    if query_params:
        query_params = {k: v for k, v in query_params.items() if v is not None}

    if query_params and len(query_params) > 0:
        query_dict = QueryDict('', mutable=True)
        for k in sorted(query_params.keys()):
            query_dict[k] = query_params[k]
        url += ('?' + query_dict.urlencode(safe='/'))

    return url


def fmap(f, data):
    """Map f to data at each level.

    This must keep the origin data structure type:
    - map -> map
    - dict -> dict
    - list -> list
    - None -> None

    Args:
        f: function that expects one argument.
        data: data to traverse to apply the f function.
              list, map, dict or bare value.

    Returns:
        The same data-structure with modified values by the f function.

    """
    if data is None:
        return data
    if isinstance(data, map):
        return map(lambda y: fmap(f, y), (x for x in data))
    if isinstance(data, list):
        return [fmap(f, x) for x in data]
    if isinstance(data, dict):
        return {k: fmap(f, v) for (k, v) in data.items()}
    return f(data)


def datetime_to_utc(date):
    """Returns datetime in UTC without timezone info

    Args:
        date (datetime.datetime): input datetime with timezone info

    Returns:
        datetime.datime: datetime in UTC without timezone info
    """
    if date.tzinfo:
        return date.astimezone(tz.gettz('UTC')).replace(tzinfo=timezone.utc)
    else:
        return date


def parse_timestamp(timestamp):
    """Given a time or timestamp (as string), parse the result as UTC datetime.

    Returns:
        a timezone-aware datetime representing the parsed value.
        None if the parsing fails.

    Samples:
        - 2016-01-12
        - 2016-01-12T09:19:12+0100
        - Today is January 1, 2047 at 8:21:00AM
        - 1452591542

    """
    if not timestamp:
        return None

    try:
        date = date_parser.parse(timestamp, ignoretz=False, fuzzy=True)
        return datetime_to_utc(date)
    except Exception:
        try:
            return datetime.utcfromtimestamp(float(timestamp)).replace(
                tzinfo=timezone.utc)
        except (ValueError, OverflowError) as e:
            raise BadInputExc(e)


def shorten_path(path):
    """Shorten the given path: for each hash present, only return the first
    8 characters followed by an ellipsis"""

    sha256_re = r'([0-9a-f]{8})[0-9a-z]{56}'
    sha1_re = r'([0-9a-f]{8})[0-9a-f]{32}'

    ret = re.sub(sha256_re, r'\1...', path)
    return re.sub(sha1_re, r'\1...', ret)


def format_utc_iso_date(iso_date, fmt='%d %B %Y, %H:%M UTC'):
    """Turns a string reprensation of an ISO 8601 date string
    to UTC and format it into a more human readable one.

    For instance, from the following input
    string: '2017-05-04T13:27:13+02:00' the following one
    is returned: '04 May 2017, 11:27 UTC'.
    Custom format string may also be provided
    as parameter

    Args:
        iso_date (str): a string representation of an ISO 8601 date
        fmt (str): optional date formatting string

    Returns:
        A formatted string representation of the input iso date
    """
    if not iso_date:
        return iso_date
    date = parse_timestamp(iso_date)
    return date.strftime(fmt)


def gen_path_info(path):
    """Function to generate path data navigation for use
    with a breadcrumb in the swh web ui.

    For instance, from a path /folder1/folder2/folder3,
    it returns the following list::

        [{'name': 'folder1', 'path': 'folder1'},
         {'name': 'folder2', 'path': 'folder1/folder2'},
         {'name': 'folder3', 'path': 'folder1/folder2/folder3'}]

    Args:
        path: a filesystem path

    Returns:
        A list of path data for navigation as illustrated above.

    """
    path_info = []
    if path:
        sub_paths = path.strip('/').split('/')
        path_from_root = ''
        for p in sub_paths:
            path_from_root += '/' + p
            path_info.append({'name': p,
                              'path': path_from_root.strip('/')})
    return path_info


def get_origin_visits(origin_info):
    """Function that returns the list of visits for a swh origin.
    That list is put in cache in order to speedup the navigation
    in the swh web browse ui.

    Args:
        origin_id (int): the id of the swh origin to fetch visits from

    Returns:
        A list of dict describing the origin visits::

            [{'date': <UTC visit date in ISO format>,
              'origin': <origin id>,
              'status': <'full' | 'partial'>,
              'visit': <visit id>
             },
             ...
            ]

    Raises:
        NotFoundExc if the origin is not found
    """
    cache_entry_id = 'origin_%s_visits' % origin_info['id']
    cache_entry = cache.get(cache_entry_id)

    if cache_entry:
        return cache_entry

    origin_visits = []

    per_page = service.MAX_LIMIT
    last_visit = None
    while 1:
        visits = list(service.lookup_origin_visits(origin_info['id'],
                                                   last_visit=last_visit,
                                                   per_page=per_page))
        origin_visits += visits
        if len(visits) < per_page:
            break
        else:
            if not last_visit:
                last_visit = per_page
            else:
                last_visit += per_page

    def _visit_sort_key(visit):
        ts = parse_timestamp(visit['date']).timestamp()
        return ts + (float(visit['visit']) / 10e3)

    for v in origin_visits:
        if 'metadata' in v:
            del v['metadata']
    origin_visits = [dict(t) for t in set([tuple(d.items())
                                           for d in origin_visits])]
    origin_visits = sorted(origin_visits, key=lambda v: _visit_sort_key(v))

    cache.set(cache_entry_id, origin_visits)

    return origin_visits


def get_swh_persistent_id(object_type, object_id, scheme_version=1):
    """
    Returns the persistent identifier for a swh object based on:

        * the object type
        * the object id
        * the swh identifiers scheme version

    Args:
        object_type (str): the swh object type
            (content/directory/release/revision/snapshot)
        object_id (str): the swh object id (hexadecimal representation
            of its hash value)
        scheme_version (int): the scheme version of the swh
            persistent identifiers

    Returns:
        str: the swh object persistent identifier

    Raises:
        BadInputExc if the provided parameters do not enable to
            generate a valid identifier
    """
    try:
        swh_id = persistent_identifier(object_type, object_id, scheme_version)
    except ValidationError as e:
        raise BadInputExc('Invalid object (%s) for swh persistent id. %s' %
                          (object_id, e))
    else:
        return swh_id
