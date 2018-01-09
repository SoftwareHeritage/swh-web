# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import HttpResponse
from django.views.decorators.cache import never_cache

from swh.model import hashutil
from swh.web.common import service, query
from swh.web.common.utils import reverse
from swh.web.api import apidoc as api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import (
    api_lookup, doc_exc_id_not_found, doc_exc_bad_id,
)


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


@api_route('/vault/directory/(?P<dir_id>[a-fA-F0-9]+)/',
           'vault-cook-directory', methods=['GET', 'POST'])
@never_cache
@api_doc.route('/vault/directory/', tags=['hidden'])
@api_doc.arg('dir_id',
             default='d4a96ba891017d0d26c15e509b4e6515e40d75ee',
             argtype=api_doc.argtypes.sha1_git,
             argdoc="The directory's sha1 identifier")
@api_doc.param('email', default=None,
               argtype=api_doc.argtypes.int,
               doc="e-mail to notify when the bundle is ready")
@api_doc.raises(exc=api_doc.excs.badinput, doc=doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc=('dictionary mapping containing the status of '
                         'the cooking'))
def api_vault_cook_directory(request, dir_id):
    """Requests an archive of the directoy identified by dir_id.

    To import the directory in the current directory, use::

        $ tar xvf path/to/directory.tar.gz
    """
    _, obj_id = query.parse_hash_with_algorithms_or_throws(
        dir_id, ['sha1'], 'Only sha1_git is supported.')

    res = _dispatch_cook_progress(request, 'directory', obj_id)
    res['fetch_url'] = reverse('vault-fetch-directory',
                               kwargs={'dir_id': dir_id})
    return res


@api_route(r'/vault/directory/(?P<dir_id>[a-fA-F0-9]+)/raw/',
           'vault-fetch-directory')
@api_doc.route('/vault/directory/raw/', tags=['hidden'], handle_response=True)
@api_doc.arg('dir_id',
             default='d4a96ba891017d0d26c15e509b4e6515e40d75ee',
             argtype=api_doc.argtypes.sha1_git,
             argdoc="The directory's sha1 identifier")
@api_doc.raises(exc=api_doc.excs.badinput, doc=doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.octet_stream,
                 retdoc='the cooked directory tarball')
def api_vault_fetch_directory(request, dir_id):
    """Fetch the archive of the directoy identified by dir_id."""
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
           'vault-cook-revision_gitfast', methods=['GET', 'POST'])
@never_cache
@api_doc.route('/vault/revision/gitfast/', tags=['hidden'])
@api_doc.arg('rev_id',
             default='9174026cfe69d73ef80b27890615f8b2ef5c265a',
             argtype=api_doc.argtypes.sha1_git,
             argdoc="The revision's sha1_git identifier")
@api_doc.param('email', default=None,
               argtype=api_doc.argtypes.int,
               doc="e-mail to notify when the bundle is ready")
@api_doc.raises(exc=api_doc.excs.badinput, doc=doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc='dictionary mapping containing the status of '
                        'the cooking')
def api_vault_cook_revision_gitfast(request, rev_id):
    """Requests an archive of the revision identified by rev_id.

    To import the revision in the current directory, use::

        $ git init
        $ zcat path/to/revision.gitfast.gz | git fast-import
    """
    _, obj_id = query.parse_hash_with_algorithms_or_throws(
        rev_id, ['sha1'], 'Only sha1_git is supported.')

    res = _dispatch_cook_progress(request, 'revision_gitfast', obj_id)
    res['fetch_url'] = reverse('vault-fetch-revision_gitfast',
                               kwargs={'rev_id': rev_id})
    return res


@api_route('/vault/revision/(?P<rev_id>[a-fA-F0-9]+)/gitfast/raw/',
           'vault-fetch-revision_gitfast')
@api_doc.route('/vault/revision/gitfast/raw/', tags=['hidden'],
               handle_response=True)
@api_doc.arg('rev_id',
             default='9174026cfe69d73ef80b27890615f8b2ef5c265a',
             argtype=api_doc.argtypes.sha1_git,
             argdoc="The revision's sha1_git identifier")
@api_doc.raises(exc=api_doc.excs.badinput, doc=doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.octet_stream,
                 retdoc='the cooked revision git fast-export')
def api_vault_fetch_revision_gitfast(request, rev_id):
    """Fetch the archive of the revision identified by rev_id."""
    _, obj_id = query.parse_hash_with_algorithms_or_throws(
        rev_id, ['sha1'], 'Only sha1_git is supported.')
    res = api_lookup(
        service.vault_fetch, 'revision_gitfast', obj_id,
        notfound_msg="Revision with ID '{}' not found.".format(rev_id))
    fname = '{}.gitfast.gz'.format(rev_id)
    response = HttpResponse(res, content_type='application/gzip')
    response['Content-disposition'] = 'attachment; filename={}'.format(fname)
    return response
