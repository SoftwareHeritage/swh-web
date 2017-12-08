# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import base64
import magic
import math
import stat
import textwrap

from django.core.cache import cache
from django.utils.safestring import mark_safe

from swh.web.common import highlightjs, service
from swh.web.common.exc import NotFoundExc
from swh.web.common.utils import (
    reverse, format_utc_iso_date, parse_timestamp
)


def get_directory_entries(sha1_git):
    """Function that retrieves the content of a SWH directory
    from the SWH archive.

    The directories entries are first sorted in lexicographical order.
    Sub-directories and regular files are then extracted.

    Args:
        sha1_git: sha1_git identifier of the directory

    Returns:
        A tuple whose first member corresponds to the sub-directories list
        and second member the regular files list

    Raises:
        NotFoundExc if the directory is not found
    """
    cache_entry_id = 'directory_entries_%s' % sha1_git
    cache_entry = cache.get(cache_entry_id)

    if cache_entry:
        return cache_entry

    entries = list(service.lookup_directory(sha1_git))
    entries = sorted(entries, key=lambda e: e['name'])
    for entry in entries:
        entry['perms'] = stat.filemode(entry['perms'])
    dirs = [e for e in entries if e['type'] == 'dir']
    files = [e for e in entries if e['type'] == 'file']

    cache.set(cache_entry_id, (dirs, files))

    return dirs, files


def get_mimetype_and_encoding_for_content(content):
    """Function that returns the mime type and the encoding associated to
    a content buffer using the magic module under the hood.

    Args:
        content (bytes): a content buffer

    Returns:
        A tuple (mimetype, encoding), for instance ('text/plain', 'us-ascii'),
        associated to the provided content.

    """
    magic_result = magic.detect_from_content(content)
    return magic_result.mime_type, magic_result.encoding


def request_content(query_string):
    """Function that retrieves a SWH content from the SWH archive.

    Raw bytes content is first retrieved, then the content mime type.
    If the mime type is not stored in the archive, it will be computed
    using Python magic module.

    Args:
        query_string: a string of the form "[ALGO_HASH:]HASH" where
            optional ALGO_HASH can be either *sha1*, *sha1_git*, *sha256*,
            or *blake2s256* (default to *sha1*) and HASH the hexadecimal
            representation of the hash value

    Returns:
        A tuple whose first member corresponds to the content raw bytes
        and second member the content mime type

    Raises:
        NotFoundExc if the content is not found
    """
    content_data = service.lookup_content(query_string)
    content_raw = service.lookup_content_raw(query_string)
    content_data['raw_data'] = content_raw['data']
    filetype = service.lookup_content_filetype(query_string)
    language = service.lookup_content_language(query_string)
    license = service.lookup_content_license(query_string)
    if filetype:
        mimetype = filetype['mimetype']
        encoding = filetype['encoding']
    else:
        mimetype, encoding = \
            get_mimetype_and_encoding_for_content(content_data['raw_data'])
    content_data['mimetype'] = mimetype
    content_data['encoding'] = encoding

    # encode textual content to utf-8 if needed
    if mimetype.startswith('text/') and 'ascii' not in encoding \
       and 'utf-8' not in encoding:
        content_data['raw_data'] = \
            content_data['raw_data'].decode(encoding).encode('utf-8')

    if language:
        content_data['language'] = language['lang']
    else:
        content_data['language'] = 'not detected'
    if license:
        content_data['licenses'] = ', '.join(license['licenses'])
    else:
        content_data['licenses'] = 'not detected'
    return content_data


_browsers_supported_image_mimes = set(['image/gif', 'image/png',
                                       'image/jpeg', 'image/bmp',
                                       'image/webp'])


def prepare_content_for_display(content_data, mime_type, path):
    """Function that prepares a content for HTML display.

    The function tries to associate a programming language to a
    content in order to perform syntax highlighting client-side
    using highlightjs. The language is determined using either
    the content filename or its mime type.
    If the mime type corresponds to an image format supported
    by web browsers, the content will be encoded in base64
    for displaying the image.

    Args:
        content_data (bytes): raw bytes of the content
        mime_type (string): mime type of the content
        path (string): path of the content including filename

    Returns:
        A dict containing the content bytes (possibly different from the one
        provided as parameter if it is an image) under the key 'content_data
        and the corresponding highlightjs language class under the
        key 'language'.
    """

    language = highlightjs.get_hljs_language_from_filename(path)

    if not language:
        language = highlightjs.get_hljs_language_from_mime_type(mime_type)

    if not language:
        language = 'nohighlight-swh'
    elif mime_type.startswith('application/'):
        mime_type = mime_type.replace('application/', 'text/')

    if mime_type.startswith('image/'):
        if mime_type in _browsers_supported_image_mimes:
            content_data = base64.b64encode(content_data)
        else:
            content_data = None

    return {'content_data': content_data,
            'language': language}


def get_origin_visits(origin_id):
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
    cache_entry_id = 'origin_%s_visits' % origin_id
    cache_entry = cache.get(cache_entry_id)

    if cache_entry:
        return cache_entry

    origin_visits = []

    per_page = service.MAX_LIMIT
    last_visit = None
    while 1:
        visits = list(service.lookup_origin_visits(origin_id,
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

    cache.set(cache_entry_id, origin_visits)

    return origin_visits


def get_origin_visit(origin_id, visit_id=None, visit_ts=None):
    """Function that returns information about a SWH visit for
    a given origin.
    The visit is retrieved from the visits list using either:
        * a visit id
        * a provided timestamp, in that case, the closest visit from
          that timestamp is selected

    Args:
        origin_id (int): the id of the swh origin to fetch branches from
        visit_id (int): the id of the origin visit
        visit_ts (int or str): an ISO date string or Unix timestamp to parse

    Returns:
        A dict containing the visit info as described below::

            {'origin': 2,
             'date': '2017-10-08T11:54:25.582463+00:00',
             'metadata': {},
             'visit': 25,
             'status': 'full'}

    """
    visits = get_origin_visits(origin_id)
    if not visit_id and visit_ts:
        parsed_visit_ts = math.floor(parse_timestamp(visit_ts).timestamp())
        for i, visit in enumerate(visits):
            ts = math.floor(parse_timestamp(visit['date']).timestamp())
            if i == 0 and parsed_visit_ts <= ts:
                return visit
            elif i == len(visits) - 1:
                if parsed_visit_ts >= ts:
                    return visit
            else:
                next_ts = math.floor(
                    parse_timestamp(visits[i+1]['date']).timestamp())
                if parsed_visit_ts >= ts and parsed_visit_ts < next_ts:
                    if (parsed_visit_ts - ts) < (next_ts - parsed_visit_ts):
                        return visit
                    else:
                        return visits[i+1]
        raise NotFoundExc(
            'Visit with timestamp %s for origin with id %s not found!' %
            (visit_ts, origin_id))

    visit = [v for v in visits if v['visit'] == int(visit_id)]
    if len(visit) == 0:
        raise NotFoundExc(
            'Visit with id %s for origin with id %s not found!' %
            (visit_id, origin_id))

    return visit[0]


def get_origin_visit_branches(origin_id, visit_id=None, visit_ts=None):
    """Function that returns the list of branches associated to
    a swh origin for a given visit.
    The visit can be expressed by its id or a timestamp. In the latter case,
    the closest visit from the provided timestamp will be used.
    If no visit parameter is provided, it returns the list of branches
    found for the latest visit.
    That list is put in  cache in order to speedup the navigation
    in the swh web browse ui.

    Args:
        origin_id (int): the id of the swh origin to fetch branches from
        visit_id (int): the id of the origin visit
        visit_ts (int or str): an ISO date string or Unix timestamp to parse

    Returns:
        A tuple with two members. The first one is a list of dict describing
        the origin branches for the given visit::

            [{'name': <branch name>,
              'revision': <sha1_git of the associated revision>,
              'directory': <sha1_git of the associated root directory>
             },
             ...
            ]

        The second one is the ISO date string corresponding to the associated
        SWH visit.

    Raises:
        NotFoundExc if the origin or its visit are not found
    """

    visit_info = get_origin_visit(origin_id, visit_id, visit_ts)
    visit_id = visit_info['visit']

    cache_entry_id = 'origin_%s_visit_%s_branches' % (origin_id, visit_id)
    cache_entry = cache.get(cache_entry_id)

    if cache_entry:
        return cache_entry

    origin_visit_data = service.lookup_origin_visit(origin_id, visit_id)
    branches = []
    revision_ids = []
    occurrences = origin_visit_data['occurrences']
    for key in sorted(occurrences.keys()):
        if occurrences[key]['target_type'] == 'revision':
            branches.append({'name': key,
                             'revision': occurrences[key]['target']})
            revision_ids.append(occurrences[key]['target'])

    revisions = service.lookup_revision_multiple(revision_ids)

    branches_to_remove = []

    for idx, revision in enumerate(revisions):
        if revision:
            branches[idx]['directory'] = revision['directory']
        else:
            branches_to_remove.append(branches[idx])

    for b in branches_to_remove:
        branches.remove(b)

    cache.set(cache_entry_id, branches)

    return branches


def gen_link(url, link_text):
    """
    Utility function for generating an HTML link to insert
    in Django templates.

    Args:
        url (str): an url
        link_text (str): the text for the produced link

    Returns:
        An HTML link in the form '<a href="url">link_text</a>'

    """
    link = '<a href="%s">%s</a>' % (url, link_text)
    return mark_safe(link)


def gen_person_link(person_id, person_name):
    """
    Utility function for generating a link to a SWH person HTML view
    to insert in Django templates.

    Args:
        person_id (int): a SWH person id
        person_name (str): the associated person name

    Returns:
        An HTML link in the form '<a href="person_view_url">person_name</a>'

    """
    person_url = reverse('browse-person', kwargs={'person_id': person_id})
    return gen_link(person_url, person_name)


def gen_revision_link(revision_id, shorten_id=False, origin_id=None):
    """
    Utility function for generating a link to a SWH revision HTML view
    to insert in Django templates.

    Args:
        revision_id (int): a SWH revision id
        shorten_id (boolean): wheter to shorten the revision id to 7
            characters for the link text

    Returns:
        An HTML link in the form '<a href="revision_view_url">revision_id</a>'

    """
    query_params = None
    if origin_id:
        query_params = {'origin_id': origin_id}
    revision_url = reverse('browse-revision',
                           kwargs={'sha1_git': revision_id},
                           query_params=query_params)
    if shorten_id:
        return gen_link(revision_url, revision_id[:7])
    else:
        return gen_link(revision_url, revision_id)


def gen_origin_link(origin_id, origin_url):
    """
    Utility function for generating a link to a SWH origin HTML view
    to insert in Django templates.

    Args:
        origin_id (int): a SWH origin id
        origin_url (str): the url of the origin

    Returns:
        An HTML link in the form '<a href="origin_view_url">Origin: origin_url</a>'

    """ # noqa
    origin_browse_url = reverse('browse-origin',
                                kwargs={'origin_id': origin_id})
    return gen_link(origin_browse_url,
                    'Origin: ' + origin_url)


def _format_log_entries(revision_log, per_page, origin_id=None):
    revision_log_data = []
    for i, log in enumerate(revision_log):
        if i == per_page:
            break
        revision_log_data.append(
            {'author': gen_person_link(log['author']['id'],
                                       log['author']['name']),
             'revision': gen_revision_link(log['id'], True, origin_id),
             'message': log['message'],
             'message_shorten': textwrap.shorten(log['message'],
                                                 width=80,
                                                 placeholder='...'),
             'date': format_utc_iso_date(log['date']),
             'directory': log['directory']})
    return revision_log_data


def prepare_revision_log_for_display(revision_log, per_page, revs_breadcrumb,
                                     origin_context=False, origin_id=None):
    """
    Utility functions that process raw revision log data for HTML display.
    Its purpose is to:

        * add links to relevant SWH browse views
        * format date in human readable format
        * truncate the message log

    It also computes the data needed to generate the links for navigating back
    and forth in the history log.

    Args:
        revision_log (list): raw revision log as returned by the SWH web api
        per_page (int): number of log entries per page
        revs_breadcrumb (str): breadcrumbs of revisions navigated so far,
            in the form 'rev1[/rev2/../revN]'. Each revision corresponds to
            the first one displayed in the HTML view for history log.
        origin_context (boolean): wheter or not the revision log is browsed
            from an origin view.


    """
    current_rev = revision_log[0]['id']
    next_rev = None
    prev_rev = None
    next_revs_breadcrumb = None
    prev_revs_breadcrumb = None
    if len(revision_log) == per_page + 1:
        prev_rev = revision_log[-1]['id']

    prev_rev_bc = current_rev
    if origin_context:
        prev_rev_bc = prev_rev

    if revs_breadcrumb:
        revs = revs_breadcrumb.split('/')
        next_rev = revs[-1]
        if len(revs) > 1:
            next_revs_breadcrumb = '/'.join(revs[:-1])
        if len(revision_log) == per_page + 1:
            prev_revs_breadcrumb = revs_breadcrumb + '/' + prev_rev_bc
    else:
        prev_revs_breadcrumb = prev_rev_bc

    return {'revision_log_data': _format_log_entries(revision_log, per_page,
                                                     origin_id),
            'prev_rev': prev_rev,
            'prev_revs_breadcrumb': prev_revs_breadcrumb,
            'next_rev': next_rev,
            'next_revs_breadcrumb': next_revs_breadcrumb}
