# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import docutils.parsers.rst
import docutils.utils
import re
import requests

from datetime import datetime, timezone
from dateutil import parser as date_parser
from dateutil import tz

from django.core.cache import cache
from django.urls import reverse as django_reverse
from django.http import QueryDict

from swh.model.exceptions import ValidationError
from swh.model.identifiers import (
    persistent_identifier, parse_persistent_identifier,
    CONTENT, DIRECTORY, RELEASE, REVISION, SNAPSHOT
)
from swh.web.common import service
from swh.web.common.exc import BadInputExc
from swh.web.config import get_config

swh_object_icons = {
    'branch': 'fa fa-code-fork',
    'branches': 'fa fa-code-fork',
    'content': 'fa fa-file-text',
    'directory': 'fa fa-folder',
    'person': 'fa fa-user',
    'revisions history': 'fa fa-history',
    'release': 'fa fa-tag',
    'releases': 'fa fa-tag',
    'revision': 'octicon octicon-git-commit',
    'snapshot': 'fa fa-camera',
    'visits': 'fa fa-calendar',
}


def reverse(viewname, url_args=None, query_params=None,
            current_app=None, urlconf=None):
    """An override of django reverse function supporting query parameters.

    Args:
        viewname (str): the name of the django view from which to compute a url
        url_args (dict): dictionary of url arguments indexed by their names
        query_params (dict): dictionary of query parameters to append to the
            reversed url
        current_app (str): the name of the django app tighten to the view
        urlconf (str): url configuration module

    Returns:
        str: the url of the requested view with processed arguments and
        query parameters
    """

    if url_args:
        url_args = {k: v for k, v in url_args.items() if v is not None}

    url = django_reverse(viewname, urlconf=urlconf, kwargs=url_args,
                         current_app=current_app)

    if query_params:
        query_params = {k: v for k, v in query_params.items() if v}

    if query_params and len(query_params) > 0:
        query_dict = QueryDict('', mutable=True)
        for k in sorted(query_params.keys()):
            query_dict[k] = query_params[k]
        url += ('?' + query_dict.urlencode(safe='/;:'))

    return url


def datetime_to_utc(date):
    """Returns datetime in UTC without timezone info

    Args:
        date (datetime.datetime): input datetime with timezone info

    Returns:
        datetime.datetime: datetime in UTC without timezone info
    """
    if date.tzinfo:
        return date.astimezone(tz.gettz('UTC')).replace(tzinfo=timezone.utc)
    else:
        return date


def parse_timestamp(timestamp):
    """Given a time or timestamp (as string), parse the result as UTC datetime.

    Returns:
        datetime.datetime: a timezone-aware datetime representing the
            parsed value or None if the parsing fails.

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
    """Turns a string representation of an ISO 8601 date string
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
        str: a formatted string representation of the input iso date
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
        list: a list of path data for navigation as illustrated above.

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
        list: A list of dict describing the origin visits with the
        following keys:

            * **date**: UTC visit date in ISO format,
            * **origin**: the origin id
            * **status**: the visit status, either **full**, **partial**
              or **ongoing**
            * **visit**: the visit id

    Raises:
        NotFoundExc: if the origin is not found
    """
    cache_entry_id = 'origin_%s_visits' % origin_info['id']
    cache_entry = cache.get(cache_entry_id)

    last_snapshot = service.lookup_latest_origin_snapshot(origin_info['id'])

    if cache_entry and \
        (not last_snapshot or
            last_snapshot['id'] == cache_entry[-1]['snapshot']):
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
        BadInputExc: if the provided parameters do not enable to
            generate a valid identifier
    """
    try:
        swh_id = persistent_identifier(object_type, object_id, scheme_version)
    except ValidationError as e:
        raise BadInputExc('Invalid object (%s) for swh persistent id. %s' %
                          (object_id, e))
    else:
        return swh_id


def resolve_swh_persistent_id(swh_id, query_params=None):
    """
    Try to resolve a Software Heritage persistent id into an url for
    browsing the pointed object.

    Args:
        swh_id (str): a Software Heritage persistent identifier
        query_params (django.http.QueryDict): optional dict filled with
            query parameters to append to the browse url

    Returns:
        dict: a dict with the following keys:

            * **swh_id_parsed (swh.model.identifiers.PersistentId)**: the parsed identifier
            * **browse_url (str)**: the url for browsing the pointed object

    Raises:
        BadInputExc: if the provided identifier can not be parsed
    """ # noqa
    try:
        swh_id_parsed = parse_persistent_identifier(swh_id)
        object_type = swh_id_parsed.object_type
        object_id = swh_id_parsed.object_id
        browse_url = None
        query_dict = QueryDict('', mutable=True)
        if query_params and len(query_params) > 0:
            for k in sorted(query_params.keys()):
                query_dict[k] = query_params[k]
        if 'origin' in swh_id_parsed.metadata:
            query_dict['origin'] = swh_id_parsed.metadata['origin']
        if object_type == CONTENT:
            query_string = 'sha1_git:' + object_id
            fragment = ''
            if 'lines' in swh_id_parsed.metadata:
                lines = swh_id_parsed.metadata['lines'].split('-')
                fragment += '#L' + lines[0]
                if len(lines) > 1:
                    fragment += '-L' + lines[1]
            browse_url = reverse('browse-content',
                                 url_args={'query_string': query_string},
                                 query_params=query_dict) + fragment
        elif object_type == DIRECTORY:
            browse_url = reverse('browse-directory',
                                 url_args={'sha1_git': object_id},
                                 query_params=query_dict)
        elif object_type == RELEASE:
            browse_url = reverse('browse-release',
                                 url_args={'sha1_git': object_id},
                                 query_params=query_dict)
        elif object_type == REVISION:
            browse_url = reverse('browse-revision',
                                 url_args={'sha1_git': object_id},
                                 query_params=query_dict)
        elif object_type == SNAPSHOT:
            browse_url = reverse('browse-snapshot',
                                 url_args={'snapshot_id': object_id},
                                 query_params=query_dict)
    except ValidationError as ve:
        raise BadInputExc('Error when parsing identifier. %s' %
                          ' '.join(ve.messages))
    else:
        return {'swh_id_parsed': swh_id_parsed,
                'browse_url': browse_url}


def parse_rst(text, report_level=2):
    """
    Parse a reStructuredText string with docutils.

    Args:
        text (str): string with reStructuredText markups in it
        report_level (int): level of docutils report messages to print
            (1 info 2 warning 3 error 4 severe 5 none)

    Returns:
        docutils.nodes.document: a parsed docutils document
    """
    parser = docutils.parsers.rst.Parser()
    components = (docutils.parsers.rst.Parser,)
    settings = docutils.frontend.OptionParser(
        components=components).get_default_values()
    settings.report_level = report_level
    document = docutils.utils.new_document('rst-doc', settings=settings)
    parser.parse(text, document)
    return document


def get_client_ip(request):
    """
    Return the client IP address from an incoming HTTP request.

    Args:
        request (django.http.HttpRequest): the incoming HTTP request

    Returns:
        str: The client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def is_recaptcha_valid(request, recaptcha_response):
    """
    Verify if the response for Google reCAPTCHA is valid.

    Args:
        request (django.http.HttpRequest): the incoming HTTP request
        recaptcha_response (str): the reCAPTCHA response

    Returns:
        bool: Whether the reCAPTCHA response is valid or not
    """
    config = get_config()
    return requests.post(
        config['grecaptcha']['validation_url'],
        data={
            'secret': config['grecaptcha']['private_key'],
            'response': recaptcha_response,
            'remoteip': get_client_ip(request)
        },
        verify=True
    ).json().get("success", False)


def context_processor(request):
    """
    Django context processor used to inject variables
    in all swh-web templates.
    """
    return {'swh_object_icons': swh_object_icons}
