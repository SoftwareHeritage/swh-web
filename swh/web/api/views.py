# Copyright (C) 2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import functools

from django.http import QueryDict
from django.conf.urls import url
from django.urls import reverse
from django.http import HttpResponse

from rest_framework.response import Response
from rest_framework.decorators import api_view

from types import GeneratorType

from swh.web.api import service, utils
from swh.web.api import apidoc as api_doc
from swh.web.api.exc import NotFoundExc, ForbiddenExc
from swh.web.api.apiurls import APIUrls, api_route

# canned doc string snippets that are used in several doc strings
_doc_arg_content_id = """A "[hash_type:]hash" content identifier, where
   hash_type is one of "sha1" (the default), "sha1_git", "sha256", and hash is
   a checksum obtained with the hash_type hashing algorithm."""
_doc_arg_last_elt = 'element to start listing from, for pagination purposes'
_doc_arg_per_page = 'number of elements to list, for pagination purposes'

_doc_exc_bad_id = 'syntax error in the given identifier(s)'
_doc_exc_id_not_found = 'no object matching the given criteria could be found'

_doc_ret_revision_meta = 'metadata of the revision identified by sha1_git'
_doc_ret_revision_log = """list of dictionaries representing the metadata of
    each revision found in the commit log heading to revision sha1_git.
    For each commit at least the following information are returned:
    author/committer, authoring/commit timestamps, revision id, commit message,
    parent (i.e., immediately preceding) commits, "root" directory id."""

_doc_header_link = """indicates that a subsequent result page is available,
    pointing to it"""


def get_url_patterns():
    return APIUrls.get_url_patterns()


def _api_lookup(lookup_fn, *args,
                notfound_msg='Object not found',
                enrich_fn=lambda x: x):
    """Capture a redundant behavior of:
    - looking up the backend with a criteria (be it an identifier or checksum)
    passed to the function lookup_fn
    - if nothing is found, raise an NotFoundExc exception with error
    message notfound_msg.
    - Otherwise if something is returned:
        - either as list, map or generator, map the enrich_fn function to it
        and return the resulting data structure as list.
        - either as dict and pass to enrich_fn and return the dict enriched.

    Args:
        - criteria: discriminating criteria to lookup
        - lookup_fn: function expects one criteria and optional supplementary
        *args.
        - notfound_msg: if nothing matching the criteria is found,
        raise NotFoundExc with this error message.
        - enrich_fn: Function to use to enrich the result returned by
        lookup_fn. Default to the identity function if not provided.
        - *args: supplementary arguments to pass to lookup_fn.

    Raises:
        NotFoundExp or whatever `lookup_fn` raises.

    """
    res = lookup_fn(*args)
    if not res:
        raise NotFoundExc(notfound_msg)
    if isinstance(res, (map, list, GeneratorType)):
        return [enrich_fn(x) for x in res]
    return enrich_fn(res)


@api_view()
def api_home(request):
    return Response({}, template_name='api.html')


APIUrls.urlpatterns.append(url(r'^$', api_home, name='homepage'))


@api_route(r'/', 'endpoints')
def api_endpoints(request):
    """Display the list of opened api endpoints.

    """
    routes = APIUrls.get_app_endpoints().copy()
    for route, doc in routes.items():
        doc['doc_intro'] = doc['docstring'].split('\n\n')[0]
    # Return a list of routes with consistent ordering
    env = {
        'doc_routes': sorted(routes.items())
    }
    return Response(env, template_name="api-endpoints.html")


@api_route(r'/origin/(?P<origin_id>[0-9]+)/', 'origin')
@api_route(r'/origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)',
           'origin')
@api_doc.route('/origin/')
@api_doc.arg('origin_id',
             default=1,
             argtype=api_doc.argtypes.int,
             argdoc='origin identifier (when looking up by ID)')
@api_doc.arg('origin_type',
             default='git',
             argtype=api_doc.argtypes.str,
             argdoc='origin type (when looking up by type+URL)')
@api_doc.arg('origin_url',
             default='https://github.com/hylang/hy',
             argtype=api_doc.argtypes.path,
             argdoc='origin URL (when looking up by type+URL)')
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""The metadata of the origin corresponding to the given
                        criteria""")
def api_origin(request, origin_id=None, origin_type=None, origin_url=None):
    """Get information about a software origin.

    Software origins might be looked up by origin type and canonical URL (e.g.,
    "git" + a "git clone" URL), or by their unique (but otherwise meaningless)
    identifier.

    """
    ori_dict = {
        'id': origin_id,
        'type': origin_type,
        'url': origin_url
    }
    ori_dict = {k: v for k, v in ori_dict.items() if ori_dict[k]}
    if 'id' in ori_dict:
        error_msg = 'Origin with id %s not found.' % ori_dict['id']
    else:
        error_msg = 'Origin with type %s and URL %s not found' % (
            ori_dict['type'], ori_dict['url'])

    def _enrich_origin(origin):
        if 'id' in origin:
            o = origin.copy()
            o['origin_visits_url'] = \
                reverse('origin-visits', kwargs={'origin_id': origin['id']})
            return o

        return origin

    return _api_lookup(
        service.lookup_origin, ori_dict,
        notfound_msg=error_msg,
        enrich_fn=_enrich_origin)


@api_route(r'/stat/counters/', 'stat-counters')
@api_doc.route('/stat/counters/', noargs=True)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""dictionary mapping object types to the amount of
                 corresponding objects currently available in the archive""")
def api_stats(request):
    """Get statistics about the content of the archive.

    """
    return service.stat_counters()


@api_route(r'/origin/(?P<origin_id>[0-9]+)/visits/', 'origin-visits')
@api_doc.route('/origin/visits/')
@api_doc.arg('origin_id',
             default=1,
             argtype=api_doc.argtypes.int,
             argdoc='software origin identifier')
@api_doc.header('Link', doc=_doc_header_link)
@api_doc.param('last_visit', default=None,
               argtype=api_doc.argtypes.int,
               doc=_doc_arg_last_elt)
@api_doc.param('per_page', default=10,
               argtype=api_doc.argtypes.int,
               doc=_doc_arg_per_page)
@api_doc.returns(rettype=api_doc.rettypes.list,
                 retdoc="""a list of dictionaries describing individual visits.
                 For each visit, its identifier, timestamp (as UNIX time),
                 outcome, and visit-specific URL for more information are
                 given.""")
def api_origin_visits(request, origin_id):
    """Get information about all visits of a given software origin.

    """
    result = {}
    per_page = int(request.query_params.get('per_page', '10'))
    last_visit = request.query_params.get('last_visit')
    if last_visit:
        last_visit = int(last_visit)

    def _lookup_origin_visits(
            origin_id, last_visit=last_visit, per_page=per_page):
        return service.lookup_origin_visits(
            origin_id, last_visit=last_visit, per_page=per_page)

    def _enrich_origin_visit(origin_visit):
        ov = origin_visit.copy()
        ov['origin_visit_url'] = reverse('origin-visit',
                                         kwargs={'origin_id': origin_id,
                                                 'visit_id': ov['visit']})
        return ov

    r = _api_lookup(
        _lookup_origin_visits, origin_id,
        notfound_msg='No origin {} found'.format(origin_id),
        enrich_fn=_enrich_origin_visit)

    if r:
        l = len(r)
        if l == per_page:
            new_last_visit = r[-1]['visit']
            query_params = QueryDict('', mutable=True)
            query_params['last_visit'] = new_last_visit

            if request.query_params.get('per_page'):
                query_params['per_page'] = per_page

            result['headers'] = {
                'link-next': reverse('origin-visits',
                                     kwargs={'origin_id': origin_id}) +
                '?' + query_params.urlencode()
            }

    result.update({
        'results': r
    })

    return result


@api_route(r'/origin/(?P<origin_id>[0-9]+)/visit/(?P<visit_id>[0-9]+)/',
           'origin-visit')
@api_doc.route('/origin/visit/')
@api_doc.arg('origin_id',
             default=1,
             argtype=api_doc.argtypes.int,
             argdoc='software origin identifier')
@api_doc.arg('visit_id',
             default=1,
             argtype=api_doc.argtypes.int,
             argdoc="""visit identifier, relative to the origin identified by
             origin_id""")
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""dictionary containing both metadata for the entire
                 visit (e.g., timestamp as UNIX time, visit outcome, etc.) and
                 what was at the software origin during the visit (i.e., a
                 mapping from branches to other archive objects)""")
def api_origin_visit(request, origin_id, visit_id):
    """Get information about a specific visit of a software origin.

    """
    def _enrich_origin_visit(origin_visit):
        ov = origin_visit.copy()
        ov['origin_url'] = reverse('origin',
                                   kwargs={'origin_id': ov['origin']})
        if 'occurrences' in ov:
            ov['occurrences'] = {
                k: utils.enrich_object(v)
                for k, v in ov['occurrences'].items()
            }
        return ov

    return _api_lookup(
        service.lookup_origin_visit, origin_id, visit_id,
        notfound_msg=('No visit {} for origin {} found'
                      .format(visit_id, origin_id)),
        enrich_fn=_enrich_origin_visit)


@api_route(r'/content/symbol/search/', 'content-symbol', methods=['POST'])
@api_route(r'/content/symbol/(?P<q>.+)/', 'content-symbol')
@api_doc.route('/content/symbol/', tags=['upcoming'])
@api_doc.arg('q',
             default='hello',
             argtype=api_doc.argtypes.str,
             argdoc="""An expression string to lookup in swh's raw content""")
@api_doc.header('Link', doc=_doc_header_link)
@api_doc.param('last_sha1', default=None,
               argtype=api_doc.argtypes.str,
               doc=_doc_arg_last_elt)
@api_doc.param('per_page', default=10,
               argtype=api_doc.argtypes.int,
               doc=_doc_arg_per_page)
@api_doc.returns(rettype=api_doc.rettypes.list,
                 retdoc="""A list of dict whose content matches the expression.
                 Each dict has the following keys:
                 - id (bytes): identifier of the content
                 - name (text): symbol whose content match the expression
                 - kind (text): kind of the symbol that matched
                 - lang (text): Language for that entry
                 - line (int): Number line for the symbol
                """)
def api_content_symbol(request, q=None):
    """Search content objects by `Ctags <http://ctags.sourceforge.net/>`_-style
    symbol (e.g., function name, data type, method, ...).

    """
    result = {}
    last_sha1 = request.query_params.get('last_sha1', None)
    per_page = int(request.query_params.get('per_page', '10'))

    def lookup_exp(exp, last_sha1=last_sha1, per_page=per_page):
        return service.lookup_expression(exp, last_sha1, per_page)

    symbols = _api_lookup(
        lookup_exp, q,
        notfound_msg="No indexed raw content match expression '{}'.".format(q),
        enrich_fn=functools.partial(utils.enrich_content, top_url=True))

    if symbols:
        l = len(symbols)

        if l == per_page:
            query_params = QueryDict('', mutable=True)
            new_last_sha1 = symbols[-1]['sha1']
            query_params['last_sha1'] = new_last_sha1
            if request.query_params.get('per_page'):
                query_params['per_page'] = per_page

            result['headers'] = {
                'link-next': reverse('content-symbol', kwargs={'q': q}) + '?' +
                query_params.urlencode()
            }

    result.update({
        'results': symbols
    })

    return result


@api_route(r'/content/known/search/', 'content-known', methods=['POST'])
@api_route(r'/content/known/(?P<q>(?!search).*)/', 'content-known')
@api_doc.route('/content/known/', tags=['hidden'])
@api_doc.arg('q',
             default='adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
             argtype=api_doc.argtypes.sha1,
             argdoc='content identifier as a sha1 checksum')
@api_doc.param('q', default=None,
               argtype=api_doc.argtypes.str,
               doc="""(POST request) An algo_hash:hash string, where algo_hash
                   is one of sha1, sha1_git or sha256 and hash is the hash to
                   search for in SWH""")
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""a dictionary with results (found/not found for each given
                        identifier) and statistics about how many identifiers
                        were found""")
def api_check_content_known(request, q=None):
    """Check whether some content (AKA "blob") is present in the archive.

    Lookup can be performed by various means:

    - a GET request with one or several hashes, separated by ','
    - a POST request with one or several hashes, passed as (multiple) values
      for parameter 'q'

    """
    response = {'search_res': None,
                'search_stats': None}
    search_stats = {'nbfiles': 0, 'pct': 0}
    search_res = None

    queries = []
    # GET: Many hash separated values request
    if q:
        hashes = q.split(',')
        for v in hashes:
            queries.append({'filename': None, 'sha1': v})

    # POST: Many hash requests in post form submission
    elif request.method == 'POST':
        data = request.data
        # Remove potential inputs with no associated value
        for k, v in data.items():
            if v is not None:
                if k == 'q' and len(v) > 0:
                    queries.append({'filename': None, 'sha1': v})
                elif v != '':
                    queries.append({'filename': k, 'sha1': v})

    if queries:
        lookup = service.lookup_multiple_hashes(queries)
        result = []
        l = len(queries)
        for el in lookup:
            res_d = {'sha1': el['sha1'],
                     'found': el['found']}
            if 'filename' in el and el['filename']:
                res_d['filename'] = el['filename']
            result.append(res_d)
            search_res = result
            nbfound = len([x for x in lookup if x['found']])
            search_stats['nbfiles'] = l
            search_stats['pct'] = (nbfound / l) * 100

    response['search_res'] = search_res
    response['search_stats'] = search_stats
    return response


@api_route(r'/person/(?P<person_id>[0-9]+)/', 'person')
@api_doc.route('/person/')
@api_doc.arg('person_id',
             default=42,
             argtype=api_doc.argtypes.int,
             argdoc='person identifier')
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc='The metadata of the person identified by person_id')
def api_person(request, person_id):
    """Get information about a person.

    """
    return _api_lookup(
        service.lookup_person, person_id,
        notfound_msg='Person with id {} not found.'.format(person_id))


@api_route(r'/release/(?P<sha1_git>[0-9a-f]+)/', 'release')
@api_doc.route('/release/')
@api_doc.arg('sha1_git',
             default='7045404f3d1c54e6473c71bbb716529fbad4be24',
             argtype=api_doc.argtypes.sha1_git,
             argdoc='release identifier')
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc='The metadata of the release identified by sha1_git')
def api_release(request, sha1_git):
    """Get information about a release.

    Releases are identified by SHA1 checksums, compatible with Git tag
    identifiers. See ``release_identifier`` in our `data model module
    <https://forge.softwareheritage.org/source/swh-model/browse/master/swh/model/identifiers.py>`_
    for details about how they are computed.

    """
    error_msg = 'Release with sha1_git %s not found.' % sha1_git
    return _api_lookup(
        service.lookup_release, sha1_git,
        notfound_msg=error_msg,
        enrich_fn=utils.enrich_release)


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
    per_page = int(request.query_params.get('per_page', '10'))

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

        if request.query_params.get('per_page'):
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
    per_page = int(request.query_params.get('per_page', '10'))

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

        if request.query_params.get('per_page'):
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


@api_route(r'/directory/(?P<sha1_git>[0-9a-f]+)/', 'directory')
@api_route(r'/directory/(?P<sha1_git>[0-9a-f]+)/(?P<path>.+)/', 'directory')
@api_doc.route('/directory/')
@api_doc.arg('sha1_git',
             default='1bd0e65f7d2ff14ae994de17a1e7fe65111dcad8',
             argtype=api_doc.argtypes.sha1_git,
             argdoc='directory identifier')
@api_doc.arg('path',
             default='codec/demux',
             argtype=api_doc.argtypes.path,
             argdoc='path relative to directory identified by sha1_git')
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""either a list of directory entries with their metadata,
                        or the metadata of a single directory entry""")
def api_directory(request, sha1_git, path=None):
    """Get information about directory or directory entry objects.

    Directories are identified by SHA1 checksums, compatible with Git directory
    identifiers. See ``directory_identifier`` in our `data model module
    <https://forge.softwareheritage.org/source/swh-model/browse/master/swh/model/identifiers.py>`_
    for details about how they are computed.

    When given only a directory identifier, this endpoint returns information
    about the directory itself, returning its content (usually a list of
    directory entries). When given a directory identifier and a path, this
    endpoint returns information about the directory entry pointed by the
    relative path, starting path resolution from the given directory.

    """
    if path:
        error_msg_path = ('Entry with path %s relative to directory '
                          'with sha1_git %s not found.') % (path, sha1_git)
        return _api_lookup(
            service.lookup_directory_with_path, sha1_git, path,
            notfound_msg=error_msg_path,
            enrich_fn=utils.enrich_directory)
    else:
        error_msg_nopath = 'Directory with sha1_git %s not found.' % sha1_git
        return _api_lookup(
            service.lookup_directory, sha1_git,
            notfound_msg=error_msg_nopath,
            enrich_fn=utils.enrich_directory)


@api_route(r'/content/(?P<q>.+)/provenance/', 'content-provenance')
@api_doc.route('/content/provenance/', tags=['hidden'])
@api_doc.arg('q',
             default='sha1_git:88b9b366facda0b5ff8d8640ee9279bed346f242',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""List of provenance information (dict) for the matched
                        content.""")
def api_content_provenance(request, q):
    """Return content's provenance information if any.

    """
    def _enrich_revision(provenance):
        p = provenance.copy()
        p['revision_url'] = \
            reverse('revision', kwargs={'sha1_git': provenance['revision']})
        p['content_url'] = \
            reverse('content',
                    kwargs={'q': 'sha1_git:%s' % provenance['content']})
        p['origin_url'] = \
            reverse('origin', kwargs={'origin_id': provenance['origin']})
        p['origin_visits_url'] = \
            reverse('origin-visits',
                    kwargs={'origin_id': provenance['origin']})
        p['origin_visit_url'] = \
            reverse('origin-visit', kwargs={'origin_id': provenance['origin'],
                                            'visit_id': provenance['visit']})
        return p

    return _api_lookup(
        service.lookup_content_provenance, q,
        notfound_msg='Content with {} not found.'.format(q),
        enrich_fn=_enrich_revision)


@api_route(r'/content/(?P<q>.+)/filetype/', 'content-filetype')
@api_doc.route('/content/filetype/', tags=['upcoming'])
@api_doc.arg('q',
             default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""Filetype information (dict) for the matched
                        content.""")
def api_content_filetype(request, q):
    """Get information about the detected MIME type of a content object.

    """
    return _api_lookup(
        service.lookup_content_filetype, q,
        notfound_msg='No filetype information found for content {}.'.format(q),
        enrich_fn=utils.enrich_metadata_endpoint)


@api_route(r'/content/(?P<q>.+)/language/', 'content-language')
@api_doc.route('/content/language/', tags=['upcoming'])
@api_doc.arg('q',
             default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""Language information (dict) for the matched
                        content.""")
def api_content_language(request, q):
    """Get information about the detected (programming) language of a content
    object.

    """
    return _api_lookup(
        service.lookup_content_language, q,
        notfound_msg='No language information found for content {}.'.format(q),
        enrich_fn=utils.enrich_metadata_endpoint)


@api_route(r'/content/(?P<q>.+)/license/', 'content-license')
@api_doc.route('/content/license/', tags=['upcoming'])
@api_doc.arg('q',
             default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""License information (dict) for the matched
                        content.""")
def api_content_license(request, q):
    """Get information about the detected license of a content object.

    """
    return _api_lookup(
        service.lookup_content_license, q,
        notfound_msg='No license information found for content {}.'.format(q),
        enrich_fn=utils.enrich_metadata_endpoint)


@api_route(r'/content/(?P<q>.+)/ctags/', 'content-ctags')
@api_doc.route('/content/ctags/', tags=['upcoming'])
@api_doc.arg('q',
             default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""Ctags symbol (dict) for the matched
                        content.""")
def api_content_ctags(request, q):
    """Get information about all `Ctags <http://ctags.sourceforge.net/>`_-style
    symbols defined in a content object.

    """
    return _api_lookup(
        service.lookup_content_ctags, q,
        notfound_msg='No ctags symbol found for content {}.'.format(q),
        enrich_fn=utils.enrich_metadata_endpoint)


@api_route(r'/content/(?P<q>.+)/raw/', 'content-raw')
@api_doc.route('/content/raw/', handle_response=True)
@api_doc.arg('q',
             default='adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.param('filename', default=None,
               argtype=api_doc.argtypes.str,
               doc='User\'s desired filename. If provided, the downloaded'
                   ' content will get that filename.')
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.octet_stream,
                 retdoc='The raw content data as an octet stream')
def api_content_raw(request, q):
    """Get the raw content of a content object (AKA "blob"), as a byte
    sequence.

    """
    def generate(content):
        yield content['data']

    content_raw = service.lookup_content_raw(q)
    if not content_raw:
        raise NotFoundExc('Content %s is not found.' % q)

    content_filetype = service.lookup_content_filetype(q)
    if not content_filetype:
        raise NotFoundExc('Content %s is not available for download.' % q)

    mimetype = content_filetype['mimetype']
    if 'text/' not in mimetype:
        raise ForbiddenExc('Only textual content is available for download. '
                           'Actual content mimetype is %s.' % mimetype)

    filename = request.query_params.get('filename')
    if not filename:
        filename = 'content_%s_raw' % q.replace(':', '_')

    response = HttpResponse(generate(content_raw),
                            content_type='application/octet-stream')
    response['Content-disposition'] = 'attachment; filename=%s' % filename
    return response


@api_route(r'/content/(?P<q>.+)/', 'content')
@api_doc.route('/content/')
@api_doc.arg('q',
             default='adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""known metadata for content identified by q""")
def api_content_metadata(request, q):
    """Get information about a content (AKA "blob") object.

    """
    return _api_lookup(
        service.lookup_content, q,
        notfound_msg='Content with {} not found.'.format(q),
        enrich_fn=utils.enrich_content)


@api_route(r'/entity/(?P<uuid>.+)/', 'entity')
@api_doc.route('/entity/', tags=['hidden'])
@api_doc.arg('uuid',
             default='5f4d4c51-498a-4e28-88b3-b3e4e8396cba',
             argtype=api_doc.argtypes.uuid,
             argdoc="The entity's uuid identifier")
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc='The metadata of the entity identified by uuid')
def api_entity_by_uuid(request, uuid):
    """Return content information if content is found.

    """
    return _api_lookup(
        service.lookup_entity_by_uuid, uuid,
        notfound_msg="Entity with uuid '%s' not found." % uuid,
        enrich_fn=utils.enrich_entity)
