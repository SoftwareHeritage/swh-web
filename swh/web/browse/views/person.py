# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.shortcuts import render
from swh.web.common import service
from swh.web.common.exc import handle_view_exception
from swh.web.browse.browseurls import browse_route
from swh.web.browse.utils import get_snapshot_context


@browse_route(r'person/(?P<person_id>[0-9]+)/',
              view_name='browse-person')
def person_browse(request, person_id):
    """
    Django view that produces an HTML display of a swh person
    identified by its id.

    The url that points to it is :http:get:`/browse/person/(person_id)/`.
    """
    try:
        snapshot_context = None
        origin_type = request.GET.get('origin_type', None)
        origin_url = request.GET.get('origin_url', None)
        if not origin_url:
            origin_url = request.GET.get('origin', None)
        snapshot_id = request.GET.get('snapshot_id', None)
        if origin_url:
            snapshot_context = get_snapshot_context(None, origin_type,
                                                    origin_url)
        elif snapshot_id:
            snapshot_context = get_snapshot_context(snapshot_id)
        person = service.lookup_person(person_id)
    except Exception as exc:
        return handle_view_exception(request, exc)

    heading = 'Person - %s' % person['fullname']
    if snapshot_context:
        context_found = 'snapshot: %s' % snapshot_context['snapshot_id']
        if origin_url:
            context_found = 'origin: %s' % origin_url
        heading += ' - %s' % context_found

    return render(request, 'browse/person.html',
                  {'heading': heading,
                   'swh_object_name': 'Person',
                   'swh_object_metadata': person,
                   'snapshot_context': snapshot_context,
                   'vault_cooking': None,
                   'show_actions_menu': False})
