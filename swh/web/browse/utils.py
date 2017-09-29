# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import dateutil
import magic
import math

from django.core.cache import cache

from swh.web.common import service
from swh.web.common.exc import NotFoundExc


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


_mime_magic = magic.open(magic.MAGIC_MIME_TYPE)
_mime_magic.load()


def get_mimetype_for_content(content):
    """Function that returns the mime type associated to
    a content buffer using the magic module under the hood.

    Args:
        content (bytes): a content buffer

    Returns:
        The mime type (e.g. text/plain) associated to the provided content.

    """
    return _mime_magic.buffer(content)


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


def get_origin_visit_branches(origin_id, visit_id=None, visit_ts=None):
    """Function that returns the list of branches associated to
    a swh origin for a given visit.
    The visit can be expressed by its id or its timestamp.
    If no visit parameter is provided, it returns the list of branches
    found for the latest visit.
    That list is put in  cache in order to speedup the navigation
    in the swh web browse ui.

    Args:
        origin_id (int): the id of the swh origin to fetch branches from
        visit_id (int): the id of the origin visit
        visit_ts (Unix timestamp): the timestamp of the origin visit

    Returns:
        A list of dict describing the origin branches for the given visit::

            [{'name': <branch name>,
              'revision': <sha1_git of the associated revision>,
              'directory': <sha1_git of the associated root directory>
             },
             ...
            ]

    Raises:
        NotFoundExc if the origin or its visit are not found
    """

    if not visit_id and visit_ts:
        visits = get_origin_visits(origin_id)
        for visit in visits:
            ts = dateutil.parser.parse(visit['date']).timestamp()
            ts = str(math.floor(ts))
            if ts == visit_ts:
                return get_origin_visit_branches(origin_id, visit['visit'])
        raise NotFoundExc(
            'Visit with timestamp %s for origin with id %s not found!' %
            (visit_ts, origin_id))

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
