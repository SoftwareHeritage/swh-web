# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import QueryDict
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from swh.web.api import service, utils
from swh.web.api import apidoc as api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.views import (
    _api_lookup, _doc_exc_id_not_found, _doc_header_link,
    _doc_arg_per_page, _doc_exc_bad_id,
    _doc_ret_revision_log, _doc_ret_revision_meta
)


def _revision_directory_by(revision, path, request_path,
                           limit=100, with_data=False):
    """Compute the revision matching criterion's directory or content data.

    Args:
        revision: dictionary of criterions representing a revision to lookup
        path: directory's path to lookup
        request_path: request path which holds the original context to
        limit: optional query parameter to limit the revisions log
        (default to 100). For now, note that this limit could impede the
        transitivity conclusion about sha1_git not being an ancestor of
        with_data: indicate to retrieve the content's raw data if path resolves
        to a content.

    """
    def enrich_directory_local(dir, context_url=request_path):
        return utils.enrich_directory(dir, context_url)

    rev_id, result = service.lookup_directory_through_revision(
        revision, path, limit=limit, with_data=with_data)

    content = result['content']
    if result['type'] == 'dir':  # dir_entries
        result['content'] = list(map(enrich_directory_local, content))
    else:  # content
        result['content'] = utils.enrich_content(content)

    return result


@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)/log/',
           'revision-origin-log')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/ts/(?P<ts>.+)/log/',
           'revision-origin-log')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)'
           r'/ts/(?P<ts>.+)/log/',
           'revision-origin-log')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/log/',
           'revision-origin-log')
@api_doc.route('/revision/origin/log/')
@api_doc.arg('origin_id',
             default=1,
             argtype=api_doc.argtypes.int,
             argdoc="The revision's SWH origin identifier")
@api_doc.arg('branch_name',
             default='refs/heads/master',
             argtype=api_doc.argtypes.path,
             argdoc="""(Optional) The revision's branch name within the origin specified.
Defaults to 'refs/heads/master'.""")
@api_doc.arg('ts',
             default='2000-01-17T11:23:54+00:00',
             argtype=api_doc.argtypes.ts,
             argdoc="""(Optional) A time or timestamp string to parse""")
@api_doc.header('Link', doc=_doc_header_link)
@api_doc.param('per_page', default=10,
               argtype=api_doc.argtypes.int,
               doc=_doc_arg_per_page)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict, retdoc=_doc_ret_revision_log)
def api_revision_log_by(request, origin_id,
                        branch_name='refs/heads/master',
                        ts=None):
    """Show the commit log for a revision, searching for it based on software
    origin, branch name, and/or visit timestamp.

    This endpoint behaves like ``/log``, but operates on the revision that
    has been found at a given software origin, close to a given point in time,
    pointed by a given branch.
    """
    result = {}
    per_page = int(utils.get_query_params(request).get('per_page', '10'))

    if ts:
        ts = utils.parse_timestamp(ts)

    def lookup_revision_log_by_with_limit(o_id, br, ts, limit=per_page+1):
        return service.lookup_revision_log_by(o_id, br, ts, limit)

    error_msg = 'No revision matching origin %s ' % origin_id
    error_msg += ', branch name %s' % branch_name
    error_msg += (' and time stamp %s.' % ts) if ts else '.'

    rev_get = _api_lookup(
        lookup_revision_log_by_with_limit, origin_id, branch_name, ts,
        notfound_msg=error_msg,
        enrich_fn=utils.enrich_revision)
    l = len(rev_get)
    if l == per_page+1:
        revisions = rev_get[:-1]
        last_sha1_git = rev_get[-1]['id']

        params = {k: v for k, v in {'origin_id': origin_id,
                                    'branch_name': branch_name,
                                    'ts': ts,
                                    }.items() if v is not None}

        query_params = QueryDict('', mutable=True)
        query_params['sha1_git'] = last_sha1_git

        if utils.get_query_params(request).get('per_page'):
            query_params['per_page'] = per_page

        result['headers'] = {
            'link-next': reverse('revision-origin-log', kwargs=params) +
            (('?' + query_params.urlencode()) if len(query_params) > 0 else '')
        }

    else:
        revisions = rev_get

    result.update({'results': revisions})

    return result


@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)/directory/',
           'revision-directory')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)/directory/(?P<path>.+)/',
           'revision-directory')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/directory/',
           'revision-directory')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/ts/(?P<ts>.+)/directory/',
           'revision-directory')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/directory/(?P<path>.+)/',
           'revision-directory')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/ts/(?P<ts>.+)'
           r'/directory/(?P<path>.+)/',
           'revision-directory')
@api_doc.route('/revision/origin/directory/', tags=['hidden'])
@api_doc.arg('origin_id',
             default=1,
             argtype=api_doc.argtypes.int,
             argdoc="The revision's origin's SWH identifier")
@api_doc.arg('branch_name',
             default='refs/heads/master',
             argtype=api_doc.argtypes.path,
             argdoc="""The optional branch for the given origin (default
                    to master""")
@api_doc.arg('ts',
             default='2000-01-17T11:23:54+00:00',
             argtype=api_doc.argtypes.ts,
             argdoc="""Optional timestamp (default to the nearest time
                    crawl of timestamp)""")
@api_doc.arg('path',
             default='Dockerfile',
             argtype=api_doc.argtypes.path,
             argdoc='The path to the directory or file to display')
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""The metadata of the revision corresponding to the
                        given criteria""")
def api_directory_through_revision_origin(request, origin_id,
                                          branch_name="refs/heads/master",
                                          ts=None,
                                          path=None,
                                          with_data=False):
    """Display directory or content information through a revision identified
    by origin/branch/timestamp.
    """
    if ts:
        ts = utils.parse_timestamp(ts)

    return _revision_directory_by({'origin_id': origin_id,
                                   'branch_name': branch_name,
                                   'ts': ts
                                   },
                                  path, request.path,
                                  with_data=with_data)


@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)/',
           'revision-origin')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/',
           'revision-origin')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/ts/(?P<ts>.+)/',
           'revision-origin')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)/ts/(?P<ts>.+)/',
           'revision-origin')
@api_doc.route('/revision/origin/')
@api_doc.arg('origin_id',
             default=1,
             argtype=api_doc.argtypes.int,
             argdoc='software origin identifier')
@api_doc.arg('branch_name',
             default='refs/heads/master',
             argtype=api_doc.argtypes.path,
             argdoc="""(optional) fully-qualified branch name, e.g.,
                    "refs/heads/master". Defaults to the master branch.""")
@api_doc.arg('ts',
             default=None,
             argtype=api_doc.argtypes.ts,
             argdoc="""(optional) timestamp close to which the revision pointed by
             the given branch should be looked up. Defaults to now.""")
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict, retdoc=_doc_ret_revision_meta)
def api_revision_with_origin(request, origin_id,
                             branch_name="refs/heads/master",
                             ts=None):
    """Get information about a revision, searching for it based on software
    origin, branch name, and/or visit timestamp.

    This endpoint behaves like ``/revision``, but operates on the revision that
    has been found at a given software origin, close to a given point in time,
    pointed by a given branch.

    """
    ts = utils.parse_timestamp(ts)
    return _api_lookup(
        service.lookup_revision_by, origin_id, branch_name, ts,
        notfound_msg=('Revision with (origin_id: {}, branch_name: {}'
                      ', ts: {}) not found.'.format(origin_id,
                                                    branch_name, ts)),
        enrich_fn=utils.enrich_revision)


@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)/prev/(?P<context>[0-9a-f/]+)/',
           'revision-context')
@api_doc.route('/revision/prev/', tags=['hidden'])
@api_doc.arg('sha1_git',
             default='ec72c666fb345ea5f21359b7bc063710ce558e39',
             argtype=api_doc.argtypes.sha1_git,
             argdoc="The revision's sha1_git identifier")
@api_doc.arg('context',
             default='6adc4a22f20bbf3bbc754f1ec8c82be5dfb5c71a',
             argtype=api_doc.argtypes.path,
             argdoc='The navigation breadcrumbs -- use at your own risk')
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc='The metadata of the revision identified by sha1_git')
def api_revision_with_context(request, sha1_git, context):
    """Return information about revision with id sha1_git.
    """
    def _enrich_revision(revision, context=context):
        return utils.enrich_revision(revision, context)

    return _api_lookup(
        service.lookup_revision, sha1_git,
        notfound_msg='Revision with sha1_git %s not found.' % sha1_git,
        enrich_fn=_enrich_revision)


@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)/', 'revision')
@api_doc.route('/revision/')
@api_doc.arg('sha1_git',
             default='aafb16d69fd30ff58afdd69036a26047f3aebdc6',
             argtype=api_doc.argtypes.sha1_git,
             argdoc="revision identifier")
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict, retdoc=_doc_ret_revision_meta)
def api_revision(request, sha1_git):
    """Get information about a revision.

    Revisions are identified by SHA1 checksums, compatible with Git commit
    identifiers. See ``revision_identifier`` in our `data model module
    <https://forge.softwareheritage.org/source/swh-model/browse/master/swh/model/identifiers.py>`_
    for details about how they are computed.

    """
    return _api_lookup(
        service.lookup_revision, sha1_git,
        notfound_msg='Revision with sha1_git {} not found.'.format(sha1_git),
        enrich_fn=utils.enrich_revision)


@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)/raw/', 'revision-raw-message')
@api_doc.route('/revision/raw/', tags=['hidden'], handle_response=True)
@api_doc.arg('sha1_git',
             default='ec72c666fb345ea5f21359b7bc063710ce558e39',
             argtype=api_doc.argtypes.sha1_git,
             argdoc="The queried revision's sha1_git identifier")
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.octet_stream,
                 retdoc="""The message of the revision identified by sha1_git
                        as a downloadable octet stream""")
def api_revision_raw_message(request, sha1_git):
    """Return the raw data of the message of revision identified by sha1_git
    """
    raw = service.lookup_revision_message(sha1_git)
    response = HttpResponse(raw['message'],
                            content_type='application/octet-stream')
    response['Content-disposition'] = \
        'attachment;filename=rev_%s_raw' % sha1_git
    return response


@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)/directory/',
           'revision-directory')
@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)/directory/(?P<dir_path>.+)/',
           'revision-directory')
@api_doc.route('/revision/directory/')
@api_doc.arg('sha1_git',
             default='ec72c666fb345ea5f21359b7bc063710ce558e39',
             argtype=api_doc.argtypes.sha1_git,
             argdoc='revision identifier')
@api_doc.arg('dir_path',
             default='Documentation/BUG-HUNTING',
             argtype=api_doc.argtypes.path,
             argdoc="""path relative to the root directory of revision identifier by
                    sha1_git""")
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""either a list of directory entries with their metadata,
                        or the metadata of a single directory entry""")
def api_revision_directory(request, sha1_git,
                           dir_path=None,
                           with_data=False):
    """Get information about directory (entry) objects associated to revisions.

    Each revision is associated to a single "root" directory. This endpoint
    behaves like ``/directory/``, but operates on the root directory associated
    to a given revision.

    """
    return _revision_directory_by({'sha1_git': sha1_git},
                                  dir_path, request.path,
                                  with_data=with_data)


@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)/log/', 'revision-log')
@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)'
           r'/prev/(?P<prev_sha1s>[0-9a-f/]+)/log/',
           'revision-log')
@api_doc.route('/revision/log/')
@api_doc.arg('sha1_git',
             default='37fc9e08d0c4b71807a4f1ecb06112e78d91c283',
             argtype=api_doc.argtypes.sha1_git,
             argdoc='revision identifier')
@api_doc.arg('prev_sha1s',
             default='6adc4a22f20bbf3bbc754f1ec8c82be5dfb5c71a',
             argtype=api_doc.argtypes.path,
             argdoc="""(Optional) Navigation breadcrumbs (descendant revisions
previously visited).  If multiple values, use / as delimiter.  """)
@api_doc.header('Link', doc=_doc_header_link)
@api_doc.param('per_page', default=10,
               argtype=api_doc.argtypes.int,
               doc=_doc_arg_per_page)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict, retdoc=_doc_ret_revision_log)
def api_revision_log(request, sha1_git, prev_sha1s=None):
    """Get a list of all revisions heading to a given one, i.e., show the
    commit log.

    """
    result = {}
    per_page = int(utils.get_query_params(request).get('per_page', '10'))

    def lookup_revision_log_with_limit(s, limit=per_page+1):
        return service.lookup_revision_log(s, limit)

    error_msg = 'Revision with sha1_git %s not found.' % sha1_git
    rev_get = _api_lookup(lookup_revision_log_with_limit, sha1_git,
                          notfound_msg=error_msg,
                          enrich_fn=utils.enrich_revision)

    l = len(rev_get)
    if l == per_page+1:
        rev_backward = rev_get[:-1]
        new_last_sha1 = rev_get[-1]['id']
        query_params = QueryDict('', mutable=True)

        if utils.get_query_params(request).get('per_page'):
            query_params['per_page'] = per_page

        result['headers'] = {
            'link-next': reverse('revision-log',
                                 kwargs={'sha1_git': new_last_sha1}) +
            (('?' + query_params.urlencode()) if len(query_params) > 0 else '')
        }

    else:
        rev_backward = rev_get

    if not prev_sha1s:  # no nav breadcrumbs, so we're done
        revisions = rev_backward

    else:
        rev_forward_ids = prev_sha1s.split('/')
        rev_forward = _api_lookup(
            service.lookup_revision_multiple, rev_forward_ids,
            notfound_msg=error_msg,
            enrich_fn=utils.enrich_revision)
        revisions = rev_forward + rev_backward

    result.update({
        'results': revisions
    })
    return result
