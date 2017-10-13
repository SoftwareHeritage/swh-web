# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.shortcuts import render
from swh.web.common import service
from swh.web.common.exc import handle_view_exception
from swh.web.browse.browseurls import browse_route


@browse_route(r'person/(?P<person_id>[0-9]+)/',
              view_name='browse-person')
def person_browse(request, person_id):
    """
    Django view that produces an HTML display of a swh person
    identified by its id.

    The url that points to it is :http:get:`/browse/person/(person_id)/`.

    Args:
        request: input django http request
        person_id (int): a swh person id

    Returns:
        The HMTL rendering for the metadata of the provided person.
    """
    try:
        person = service.lookup_person(person_id)
    except Exception as exc:
        return handle_view_exception(exc)

    return render(request, 'person.html', {'person': person})
