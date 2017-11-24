# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import re

from datetime import datetime, timezone
from dateutil import parser as date_parser

from swh.web.common.exc import BadInputExc

from django.core import urlresolvers
from django.http import QueryDict


def reverse(viewname, args=None, kwargs=None, query_params=None,
            current_app=None,  urlconf=None):
    """An override of django reverse function supporting query parameters.

    Args:
        viewname: the name of the django view from which to compute a url
        args: list of url arguments ordered according to their position it
        kwargs: dictionnary of url arguments indexed by their names
        query_params: dictionnary of query parameters to append to the
            reversed url
        current_app: the name of the django app tighted to the view
        urlconf: url configuration module

    Returns:
        The url of the requested view with processed arguments and
        query parameters
    """

    url = urlresolvers.reverse(
            viewname, urlconf=urlconf, args=args,
            kwargs=kwargs, current_app=current_app)

    if query_params:
        query_params = {k: v for k, v in query_params.items() if v is not None}

    if query_params and len(query_params) > 0:
        query_dict = QueryDict('', mutable=True)
        for k, v in query_params.items():
            query_dict[k] = v
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


def parse_timestamp(timestamp):
    """Given a time or timestamp (as string), parse the result as datetime.

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
        return date_parser.parse(timestamp, ignoretz=False, fuzzy=True)
    except:
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


def format_utc_iso_date(iso_date):
    """Turns a string reprensation of an UTC iso date
    into a more human readable one.

    More precisely, from the following input
    string: '2017-05-04T13:27:13+02:00' the following one
    is returned: '04 May 2017, 13:27 UTC'.

    Args:
        iso_date (str): a string representation of an UTC iso date

    Returns:
        A human readable string representation of the input iso date
    """
    date = date_parser.parse(iso_date)
    return date.strftime('%d %B %Y, %H:%M UTC')
