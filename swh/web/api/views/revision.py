# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.http import HttpResponse

from swh.web.common import service
from swh.web.common.utils import reverse
from swh.web.common.utils import parse_timestamp
from swh.web.api import utils
from swh.web.api.apidoc import api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import api_lookup


def _revision_directory_by(revision, path, request_path,
                           limit=100, with_data=False):
    """
    Compute the revision matching criterion's directory or content data.

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


@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/log/',
           'api-revision-origin-log')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)/log/',
           'api-revision-origin-log')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/ts/(?P<ts>.+)/log/',
           'api-revision-origin-log')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)'
           r'/ts/(?P<ts>.+)/log/',
           'api-revision-origin-log')
@api_doc('/revision/origin/log/')
def api_revision_log_by(request, origin_id,
                        branch_name='refs/heads/master',
                        ts=None):
    """
    .. http:get:: /api/1/revision/origin/(origin_id)[/branch/(branch_name)][/ts/(timestamp)]/log

        Show the commit log for a revision, searching for it based on software origin,
        branch name, and/or visit timestamp.

        This endpoint behaves like :http:get:`/api/1/revision/(sha1_git)[/prev/(prev_sha1s)]/log/`,
        but operates on the revision that has been found at a given software origin,
        close to a given point in time, pointed by a given branch.

        :param int origin_id: a software origin identifier
        :param string branch_name: optional parameter specifying a fully-qualified branch name
            associated to the software origin, e.g., "refs/heads/master". Defaults to the master branch.
        :param string timestamp: optional parameter specifying a timestamp close to which the revision
            pointed by the given branch should be looked up. The timestamp can be expressed either
            as an ISO date or as a Unix one (in UTC). Defaults to now.

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        :>jsonarr object author: information about the author of the revision
        :>jsonarr string author_url: link to :http:get:`/api/1/person/(person_id)/` to get
            information about the author of the revision
        :>jsonarr object committer: information about the committer of the revision
        :>jsonarr string committer_url: link to :http:get:`/api/1/person/(person_id)/` to get
            information about the committer of the revision
        :>jsonarr string committer_date: ISO representation of the commit date (in UTC)
        :>jsonarr string date: ISO representation of the revision date (in UTC)
        :>jsonarr string directory: the unique identifier that revision points to
        :>jsonarr string directory_url: link to :http:get:`/api/1/directory/(sha1_git)/[(path)/]`
            to get information about the directory associated to the revision
        :>jsonarr string id: the revision unique identifier
        :>jsonarr boolean merge: whether or not the revision corresponds to a merge commit
        :>jsonarr string message: the message associated to the revision
        :>jsonarr array parents: the parents of the revision, i.e. the previous revisions
            that head directly to it, each entry of that array contains an unique parent
            revision identifier but also a link to :http:get:`/api/1/revision/(sha1_git)/`
            to get more information about it
        :>jsonarr string type: the type of the revision

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: no revision matching the given criteria could be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`revision/origin/723566/ts/2016-01-17T00:00:00+00:00/log/`
    """ # noqa
    result = {}
    per_page = int(request.query_params.get('per_page', '10'))

    if ts:
        ts = parse_timestamp(ts)

    def lookup_revision_log_by_with_limit(o_id, br, ts, limit=per_page+1):
        return service.lookup_revision_log_by(o_id, br, ts, limit)

    error_msg = 'No revision matching origin %s ' % origin_id
    error_msg += ', branch name %s' % branch_name
    error_msg += (' and time stamp %s.' % ts) if ts else '.'

    rev_get = api_lookup(
        lookup_revision_log_by_with_limit, origin_id, branch_name, ts,
        notfound_msg=error_msg,
        enrich_fn=utils.enrich_revision)

    nb_rev = len(rev_get)
    if nb_rev == per_page+1:
        revisions = rev_get[:-1]
        last_sha1_git = rev_get[-1]['id']

        params = {k: v for k, v in {'origin_id': origin_id,
                                    'branch_name': branch_name,
                                    'ts': ts,
                                    }.items() if v is not None}

        query_params = {}
        query_params['sha1_git'] = last_sha1_git

        if request.query_params.get('per_page'):
            query_params['per_page'] = per_page

        result['headers'] = {
            'link-next': reverse('api-revision-origin-log', url_args=params,
                                 query_params=query_params)
        }

    else:
        revisions = rev_get

    result.update({'results': revisions})

    return result


@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)/directory/',
           'api-revision-origin-directory')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)/directory/(?P<path>.+)/',
           'api-revision-origin-directory')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/directory/',
           'api-revision-origin-directory')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/ts/(?P<ts>.+)/directory/',
           'api-revision-origin-directory')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/directory/(?P<path>.+)/',
           'api-revision-origin-directory')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/ts/(?P<ts>.+)'
           r'/directory/(?P<path>.+)/',
           'api-revision-origin-directory')
@api_doc('/revision/origin/directory/', tags=['hidden'])
def api_directory_through_revision_origin(request, origin_id,
                                          branch_name="refs/heads/master",
                                          ts=None,
                                          path=None,
                                          with_data=False):
    """
    Display directory or content information through a revision identified
    by origin/branch/timestamp.
    """
    if ts:
        ts = parse_timestamp(ts)

    return _revision_directory_by({'origin_id': origin_id,
                                   'branch_name': branch_name,
                                   'ts': ts
                                   },
                                  path, request.path,
                                  with_data=with_data)


@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)/',
           'api-revision-origin')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/',
           'api-revision-origin')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)'
           r'/branch/(?P<branch_name>.+)/ts/(?P<ts>.+)/',
           'api-revision-origin')
@api_route(r'/revision/origin/(?P<origin_id>[0-9]+)/ts/(?P<ts>.+)/',
           'api-revision-origin')
@api_doc('/revision/origin/')
def api_revision_with_origin(request, origin_id,
                             branch_name="refs/heads/master",
                             ts=None):
    """
    .. http:get:: /api/1/revision/origin/(origin_id)/[branch/(branch_name)/][ts/(timestamp)/]

        Get information about a revision, searching for it based on software origin,
        branch name, and/or visit timestamp.

        This endpoint behaves like :http:get:`/api/1/revision/(sha1_git)/`,
        but operates on the revision that has been found at a given software origin,
        close to a given point in time, pointed by a given branch.

        :param int origin_id: a software origin identifier
        :param string branch_name: optional parameter specifying a fully-qualified branch name
            associated to the software origin, e.g., "refs/heads/master". Defaults to the master branch.
        :param string timestamp: optional parameter specifying a timestamp close to which the revision
            pointed by the given branch should be looked up. The timestamp can be expressed either
            as an ISO date or as a Unix one (in UTC). Defaults to now.

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        :>json object author: information about the author of the revision
        :>json string author_url: link to :http:get:`/api/1/person/(person_id)/` to get
            information about the author of the revision
        :>json object committer: information about the committer of the revision
        :>json string committer_url: link to :http:get:`/api/1/person/(person_id)/` to get
            information about the committer of the revision
        :>json string committer_date: ISO representation of the commit date (in UTC)
        :>json string date: ISO representation of the revision date (in UTC)
        :>json string directory: the unique identifier that revision points to
        :>json string directory_url: link to :http:get:`/api/1/directory/(sha1_git)/[(path)/]`
            to get information about the directory associated to the revision
        :>json string id: the revision unique identifier
        :>json boolean merge: whether or not the revision corresponds to a merge commit
        :>json string message: the message associated to the revision
        :>json array parents: the parents of the revision, i.e. the previous revisions
            that head directly to it, each entry of that array contains an unique parent
            revision identifier but also a link to :http:get:`/api/1/revision/(sha1_git)/`
            to get more information about it
        :>json string type: the type of the revision

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: no revision matching the given criteria could be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`revision/origin/13706355/branch/refs/heads/2.7/`
    """ # noqa
    ts = parse_timestamp(ts)
    return api_lookup(
        service.lookup_revision_by, origin_id, branch_name, ts,
        notfound_msg=('Revision with (origin_id: {}, branch_name: {}'
                      ', ts: {}) not found.'.format(origin_id,
                                                    branch_name, ts)),
        enrich_fn=utils.enrich_revision)


@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)/prev/(?P<context>[0-9a-f/]+)/',
           'api-revision-context')
@api_doc('/revision/prev/', tags=['hidden'])
def api_revision_with_context(request, sha1_git, context):
    """
    Return information about revision with id sha1_git.
    """
    def _enrich_revision(revision, context=context):
        return utils.enrich_revision(revision, context)

    return api_lookup(
        service.lookup_revision, sha1_git,
        notfound_msg='Revision with sha1_git %s not found.' % sha1_git,
        enrich_fn=_enrich_revision)


@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)/', 'api-revision')
@api_doc('/revision/')
def api_revision(request, sha1_git):
    """
    .. http:get:: /api/1/revision/(sha1_git)/

        Get information about a revision in the archive.
        Revisions are identified by **sha1** checksums, compatible with Git commit identifiers.
        See :func:`swh.model.identifiers.revision_identifier` in our data model module for details
        about how they are computed.

        :param string sha1_git: hexadecimal representation of the revision **sha1_git** identifier

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        :>json object author: information about the author of the revision
        :>json string author_url: link to :http:get:`/api/1/person/(person_id)/` to get
            information about the author of the revision
        :>json object committer: information about the committer of the revision
        :>json string committer_url: link to :http:get:`/api/1/person/(person_id)/` to get
            information about the committer of the revision
        :>json string committer_date: ISO representation of the commit date (in UTC)
        :>json string date: ISO representation of the revision date (in UTC)
        :>json string directory: the unique identifier that revision points to
        :>json string directory_url: link to :http:get:`/api/1/directory/(sha1_git)/[(path)/]`
            to get information about the directory associated to the revision
        :>json string id: the revision unique identifier
        :>json boolean merge: whether or not the revision corresponds to a merge commit
        :>json string message: the message associated to the revision
        :>json array parents: the parents of the revision, i.e. the previous revisions
            that head directly to it, each entry of that array contains an unique parent
            revision identifier but also a link to :http:get:`/api/1/revision/(sha1_git)/`
            to get more information about it
        :>json string type: the type of the revision

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 400: an invalid **sha1_git** value has been provided
        :statuscode 404: requested revision can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`revision/aafb16d69fd30ff58afdd69036a26047f3aebdc6/`
    """ # noqa
    return api_lookup(
        service.lookup_revision, sha1_git,
        notfound_msg='Revision with sha1_git {} not found.'.format(sha1_git),
        enrich_fn=utils.enrich_revision)


@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)/raw/',
           'api-revision-raw-message')
@api_doc('/revision/raw/', tags=['hidden'], handle_response=True)
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
           'api-revision-directory')
@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)/directory/(?P<dir_path>.+)/',
           'api-revision-directory')
@api_doc('/revision/directory/')
def api_revision_directory(request, sha1_git,
                           dir_path=None,
                           with_data=False):
    """
    .. http:get:: /api/1/revision/(sha1_git)/directory/[(path)/]

        Get information about directory (entry) objects associated to revisions.
        Each revision is associated to a single "root" directory.
        This endpoint behaves like :http:get:`/api/1/directory/(sha1_git)/[(path)/]`,
        but operates on the root directory associated to a given revision.

        :param string sha1_git: hexadecimal representation of the revision **sha1_git** identifier
        :param string path: optional parameter to get information about the directory entry
            pointed by that relative path

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        :>json array content: directory entries as returned by :http:get:`/api/1/directory/(sha1_git)/[(path)/]`
        :>json string path: path of directory from the revision root one
        :>json string revision: the unique revision identifier
        :>json string type: the type of the directory

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 400: an invalid **sha1_git** value has been provided
        :statuscode 404: requested revision can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`revision/f1b94134a4b879bc55c3dacdb496690c8ebdc03f/directory/`
    """ # noqa
    return _revision_directory_by({'sha1_git': sha1_git},
                                  dir_path, request.path,
                                  with_data=with_data)


@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)/log/', 'api-revision-log')
@api_route(r'/revision/(?P<sha1_git>[0-9a-f]+)'
           r'/prev/(?P<prev_sha1s>[0-9a-f/]+)/log/',
           'api-revision-log')
@api_doc('/revision/log/')
def api_revision_log(request, sha1_git, prev_sha1s=None):
    """
    .. http:get:: /api/1/revision/(sha1_git)[/prev/(prev_sha1s)]/log/

        Get a list of all revisions heading to a given one, in other words show the commit log.

        :param string sha1_git: hexadecimal representation of the revision **sha1_git** identifier
        :param string prev_sha1s: optional parameter representing the navigation breadcrumbs
            (descendant revisions previously visited). If multiple values, use / as delimiter.
            If provided, revisions information will be added at the beginning of the returned list.
        :query int per_page: number of elements in the returned list, for pagination purpose

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request
        :resheader Link: indicates that a subsequent result page is available and contains
            the url pointing to it

        :>jsonarr object author: information about the author of the revision
        :>jsonarr string author_url: link to :http:get:`/api/1/person/(person_id)/` to get
            information about the author of the revision
        :>jsonarr object committer: information about the committer of the revision
        :>jsonarr string committer_url: link to :http:get:`/api/1/person/(person_id)/` to get
            information about the committer of the revision
        :>jsonarr string committer_date: ISO representation of the commit date (in UTC)
        :>jsonarr string date: ISO representation of the revision date (in UTC)
        :>jsonarr string directory: the unique identifier that revision points to
        :>jsonarr string directory_url: link to :http:get:`/api/1/directory/(sha1_git)/[(path)/]`
            to get information about the directory associated to the revision
        :>jsonarr string id: the revision unique identifier
        :>jsonarr boolean merge: whether or not the revision corresponds to a merge commit
        :>jsonarr string message: the message associated to the revision
        :>jsonarr array parents: the parents of the revision, i.e. the previous revisions
            that head directly to it, each entry of that array contains an unique parent
            revision identifier but also a link to :http:get:`/api/1/revision/(sha1_git)/`
            to get more information about it
        :>jsonarr string type: the type of the revision

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 400: an invalid **sha1_git** value has been provided
        :statuscode 404: requested revision can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`revision/e1a315fa3fa734e2a6154ed7b5b9ae0eb8987aad/log/`
    """ # noqa
    result = {}
    per_page = int(request.query_params.get('per_page', '10'))

    def lookup_revision_log_with_limit(s, limit=per_page+1):
        return service.lookup_revision_log(s, limit)

    error_msg = 'Revision with sha1_git %s not found.' % sha1_git
    rev_get = api_lookup(lookup_revision_log_with_limit, sha1_git,
                         notfound_msg=error_msg,
                         enrich_fn=utils.enrich_revision)

    nb_rev = len(rev_get)
    if nb_rev == per_page+1:
        rev_backward = rev_get[:-1]
        new_last_sha1 = rev_get[-1]['id']
        query_params = {}

        if request.query_params.get('per_page'):
            query_params['per_page'] = per_page

        result['headers'] = {
            'link-next': reverse('api-revision-log',
                                 url_args={'sha1_git': new_last_sha1},
                                 query_params=query_params)
        }

    else:
        rev_backward = rev_get

    if not prev_sha1s:  # no nav breadcrumbs, so we're done
        revisions = rev_backward

    else:
        rev_forward_ids = prev_sha1s.split('/')
        rev_forward = api_lookup(
            service.lookup_revision_multiple, rev_forward_ids,
            notfound_msg=error_msg,
            enrich_fn=utils.enrich_revision)
        revisions = rev_forward + rev_backward

    result.update({
        'results': revisions
    })
    return result
