# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import dateutil

from django.shortcuts import render

from swh.web.common import service
from swh.web.common.utils import reverse
from swh.web.common.exc import handle_view_exception
from swh.web.browse.utils import get_origin_visits


def origin_browse(request, origin_id=None, origin_type=None,
                  origin_url=None):
    """Django view that produces an HTML display of a swh origin identified
    by its id or its url.

    The url scheme that points to it is the following:

        * /browse/origin/<origin_id>/
        * /browse/origin/<origin_type>/url/<origin_url>/

    The view displays the origin metadata and contains links
    for browsing its directories and contents for each swh visit.

    Args:
        request: input django http request
        origin_id: a swh origin id
        origin_type: type of origin (git, svn, ...)
        origin_url: url of the origin (e.g. https://github.com/<user>/<repo>)

    Returns:
        The HMTL rendering for the metadata of the provided origin.
    """
    try:
        if origin_id:
            origin_request_params = {
                'id': origin_id,
            }
        else:
            origin_request_params = {
                'type': origin_type,
                'url': origin_url
            }
        origin_info = service.lookup_origin(origin_request_params)
        origin_id = origin_info['id']
        origin_visits = get_origin_visits(origin_id)
    except Exception as exc:
        return handle_view_exception(exc)

    origin_info['last swh visit browse url'] = \
        reverse('browse-origin-directory',
                kwargs={'origin_id': origin_id})

    origin_visits_data = []
    for visit in origin_visits:
        visit_date = dateutil.parser.parse(visit['date'])
        visit['date'] = visit_date.strftime('%d %B %Y, %H:%M UTC')
        visit['browse_url'] = reverse('browse-origin-directory',
                                      kwargs={'origin_id': origin_id,
                                              'visit_id': visit['visit']})
        origin_visits_data.append(
            {'date': visit_date.timestamp()})

    return render(request, 'origin.html',
                  {'origin': origin_info,
                   'origin_visits_data': origin_visits_data,
                   'visits': origin_visits,
                   'browse_url_base': '/browse/origin/%s/' % origin_id})
