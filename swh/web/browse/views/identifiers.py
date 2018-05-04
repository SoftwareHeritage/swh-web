# Copyright (C) 2017-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.shortcuts import redirect

from swh.model.identifiers import parse_persistent_identifier

from swh.web.browse.browseurls import browse_route
from swh.web.common.utils import reverse
from swh.web.common.exc import BadInputExc, handle_view_exception


@browse_route(r'(?P<swh_id>swh:[0-9]+:[a-z]+:[0-9a-f]+)/',
              view_name='browse-swh-id')
def swh_id_browse(request, swh_id):
    """
    Django view enabling to browse the SWH archive using
    :ref:`persistent-identifiers`.

    The url that points to it is :http:get:`/browse/(swh_id)/`.
    """
    try:
        swh_id_parsed = parse_persistent_identifier(swh_id)
        object_type = swh_id_parsed['object_type']
        object_id = swh_id_parsed['object_id']
        view_url = None
        if object_type == 'cnt':
            query_string = 'sha1_git:' + object_id
            view_url = reverse('browse-content',
                               kwargs={'query_string': query_string},
                               query_params=request.GET)
        elif object_type == 'dir':
            view_url = reverse('browse-directory',
                               kwargs={'sha1_git': object_id},
                               query_params=request.GET)
        elif object_type == 'rel':
            view_url = reverse('browse-release',
                               kwargs={'sha1_git': object_id},
                               query_params=request.GET)
        elif object_type == 'rev':
            view_url = reverse('browse-revision',
                               kwargs={'sha1_git': object_id},
                               query_params=request.GET)
        elif object_type == 'snp':
            view_url = reverse('browse-snapshot',
                               kwargs={'snapshot_id': object_id},
                               query_params=request.GET)
        else:
            msg = '\'%s\' is not a valid SWH persistent identifier!' % swh_id
            raise BadInputExc(msg)
    except Exception as exc:
        return handle_view_exception(request, exc)

    return redirect(view_url)
