# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import HttpResponse
from django.views.decorators.cache import never_cache

from swh.model import hashutil
from swh.web.common import service, query
from swh.web.common.utils import reverse
from swh.web.api.apidoc import api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import api_lookup


# XXX: a bit spaghetti. Would be better with class-based views.
def _dispatch_cook_progress(request, obj_type, obj_id):
    hex_id = hashutil.hash_to_hex(obj_id)
    object_name = obj_type.split('_')[0].title()
    if request.method == 'GET':
        return api_lookup(
            service.vault_progress, obj_type, obj_id,
            notfound_msg=("{} '{}' was never requested."
                          .format(object_name, hex_id)))
    elif request.method == 'POST':
        email = request.POST.get('email', request.GET.get('email', None))
        return api_lookup(
            service.vault_cook, obj_type, obj_id, email,
            notfound_msg=("{} '{}' not found."
                          .format(object_name, hex_id)))


@api_route(r'/vault/directory/(?P<dir_id>[a-fA-F0-9]+)/',
           'api-vault-cook-directory', methods=['GET', 'POST'],
           throttle_scope='swh_vault_cooking')
@never_cache
@api_doc('/vault/directory/')
def api_vault_cook_directory(request, dir_id):
    """
    .. http:get:: /api/1/vault/directory/(dir_id)/
    .. http:post:: /api/1/vault/directory/(dir_id)/

        Request the cooking of an archive for a directory or check
        its cooking status.

        That endpoint enables to create a vault cooking task for a directory
        through a POST request or check the status of a previously created one
        through a GET request.

        Once the cooking task has been executed, the resulting archive can
        be downloaded using the dedicated endpoint :http:get:`/api/1/vault/directory/(dir_id)/raw/`.

        Then to extract the cooked directory in the current one, use::

            $ tar xvf path/to/directory.tar.gz

        :param string dir_id: the directory's sha1 identifier

        :query string email: e-mail to notify when the archive is ready

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        :>json string fetch_url: the url from which to download the archive once it has been cooked
            (see :http:get:`/api/1/vault/directory/(dir_id)/raw/`)
        :>json string obj_type: the type of object to cook (directory or revision)
        :>json string progress_message: message describing the cooking task progress
        :>json number id: the cooking task id
        :>json string status: the cooking task status (either **new**, **pending**,
            **done** or **failed**)
        :>json string obj_id: the identifier of the object to cook

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`post`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 400: an invalid directory identifier has been provided
        :statuscode 404: requested directory can not be found in the archive
    """ # noqa
    _, obj_id = query.parse_hash_with_algorithms_or_throws(
        dir_id, ['sha1'], 'Only sha1_git is supported.')

    res = _dispatch_cook_progress(request, 'directory', obj_id)
    res['fetch_url'] = reverse('api-vault-fetch-directory',
                               url_args={'dir_id': dir_id})
    return res


@api_route(r'/vault/directory/(?P<dir_id>[a-fA-F0-9]+)/raw/',
           'api-vault-fetch-directory')
@api_doc('/vault/directory/raw/', handle_response=True)
def api_vault_fetch_directory(request, dir_id):
    """
    .. http:get:: /api/1/vault/directory/(dir_id)/raw/

        Fetch the cooked archive for a directory.

        See :http:get:`/api/1/vault/directory/(dir_id)/` to get more
        details on directory cooking.

        :param string dir_id: the directory's sha1 identifier

        :resheader Content-Type: application/octet-stream

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 400: an invalid directory identifier has been provided
        :statuscode 404: requested directory can not be found in the archive
    """ # noqa
    _, obj_id = query.parse_hash_with_algorithms_or_throws(
        dir_id, ['sha1'], 'Only sha1_git is supported.')
    res = api_lookup(
        service.vault_fetch, 'directory', obj_id,
        notfound_msg="Directory with ID '{}' not found.".format(dir_id))
    fname = '{}.tar.gz'.format(dir_id)
    response = HttpResponse(res, content_type='application/gzip')
    response['Content-disposition'] = 'attachment; filename={}'.format(fname)
    return response


@api_route(r'/vault/revision/(?P<rev_id>[a-fA-F0-9]+)/gitfast/',
           'api-vault-cook-revision_gitfast', methods=['GET', 'POST'],
           throttle_scope='swh_vault_cooking')
@never_cache
@api_doc('/vault/revision/gitfast/')
def api_vault_cook_revision_gitfast(request, rev_id):
    """
    .. http:get:: /api/1/vault/revision/(rev_id)/gitfast/
    .. http:post:: /api/1/vault/revision/(rev_id)/gitfast/

        Request the cooking of a gitfast archive for a revision or check
        its cooking status.

        That endpoint enables to create a vault cooking task for a revision
        through a POST request or check the status of a previously created one
        through a GET request.

        Once the cooking task has been executed, the resulting gitfast archive can
        be downloaded using the dedicated endpoint :http:get:`/api/1/vault/revision/(rev_id)/gitfast/raw/`.

        Then to import the revision in the current directory, use::

            $ git init
            $ zcat path/to/revision.gitfast.gz | git fast-import
            $ git checkout HEAD

        :param string rev_id: the revision's sha1 identifier

        :query string email: e-mail to notify when the gitfast archive is ready

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        :>json string fetch_url: the url from which to download the archive once it has been cooked
            (see :http:get:`/api/1/vault/revision/(rev_id)/gitfast/raw/`)
        :>json string obj_type: the type of object to cook (directory or revision)
        :>json string progress_message: message describing the cooking task progress
        :>json number id: the cooking task id
        :>json string status: the cooking task status (new/pending/done/failed)
        :>json string obj_id: the identifier of the object to cook

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`post`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 400: an invalid revision identifier has been provided
        :statuscode 404: requested revision can not be found in the archive
    """ # noqa
    _, obj_id = query.parse_hash_with_algorithms_or_throws(
        rev_id, ['sha1'], 'Only sha1_git is supported.')

    res = _dispatch_cook_progress(request, 'revision_gitfast', obj_id)
    res['fetch_url'] = reverse('api-vault-fetch-revision_gitfast',
                               url_args={'rev_id': rev_id})
    return res


@api_route(r'/vault/revision/(?P<rev_id>[a-fA-F0-9]+)/gitfast/raw/',
           'api-vault-fetch-revision_gitfast')
@api_doc('/vault/revision/gitfast/raw/', handle_response=True)
def api_vault_fetch_revision_gitfast(request, rev_id):
    """
    .. http:get:: /api/1/vault/revision/(rev_id)/gitfast/raw/

        Fetch the cooked gitfast archive for a revision.

        See :http:get:`/api/1/vault/revision/(rev_id)/gitfast/` to get more
        details on directory cooking.

        :param string rev_id: the revision's sha1 identifier

        :resheader Content-Type: application/octet-stream

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 400: an invalid revision identifier has been provided
        :statuscode 404: requested revision can not be found in the archive
    """ # noqa
    _, obj_id = query.parse_hash_with_algorithms_or_throws(
        rev_id, ['sha1'], 'Only sha1_git is supported.')
    res = api_lookup(
        service.vault_fetch, 'revision_gitfast', obj_id,
        notfound_msg="Revision with ID '{}' not found.".format(rev_id))
    fname = '{}.gitfast.gz'.format(rev_id)
    response = HttpResponse(res, content_type='application/gzip')
    response['Content-disposition'] = 'attachment; filename={}'.format(fname)
    return response
