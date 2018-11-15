# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from swh.web.common import service
from swh.web.api.apidoc import api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import api_lookup


@api_route(r'/person/(?P<person_id>[0-9]+)/', 'api-person')
@api_doc('/person/')
def api_person(request, person_id):
    """
    .. http:get:: /api/1/person/(person_id)/

        Get information about a person in the archive.

        :param int person_id: a person identifier

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        :>json string email: the email of the person
        :>json string fullname: the full name of the person: combination of its name and email
        :>json number id: the unique identifier of the person
        :>json string name: the name of the person

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested person can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`person/8275/`
    """ # noqa
    return api_lookup(
        service.lookup_person, person_id,
        notfound_msg='Person with id {} not found.'.format(person_id))
