# Copyright (C) 2015-2016  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from types import GeneratorType

from flask import request, url_for

from swh.web.ui import service, utils, apidoc as doc
from swh.web.ui.exc import NotFoundExc
from swh.web.ui.main import app


@app.route('/api/1/stat/counters/')
@doc.route('/api/1/stat/counters/', noargs=True)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="A dictionary of SWH's most important statistics")
def api_stats():
    """Return statistics on SWH storage.

    """
    return service.stat_counters()


@app.route('/api/1/origin/<int:origin_id>/visits/')
@doc.route('/api/1/origin/visits/')
@doc.arg('origin_id',
         default=1,
         argtype=doc.argtypes.int,
         argdoc='The requested SWH origin identifier')
@doc.returns(rettype=doc.rettypes.list,
             retdoc="""All instances of visits of the origin pointed by
             origin_id as POSIX time since epoch (if visit_id is not defined)
""")
def api_origin_visits(origin_id):
    """Return a list of origin visit (dict) for that particular origin
       including date (visit date as posix timestamp), target,
       target_type, status, ...

    """
    def _enrich_origin_visit(origin_visit):
        ov = origin_visit.copy()
        ov['origin_visit_url'] = url_for('api_origin_visit',
                                         origin_id=ov['origin'],
                                         visit_id=ov['visit'])
        return ov

    return _api_lookup(
        origin_id,
        service.lookup_origin_visits,
        error_msg_if_not_found='No origin %s found' % origin_id,
        enrich_fn=_enrich_origin_visit)


@app.route('/api/1/origin/<int:origin_id>/visits/<int:visit_id>/')
@doc.route('/api/1/origin/visits/id/')
@doc.arg('origin_id',
         default=1,
         argtype=doc.argtypes.int,
         argdoc='The requested SWH origin identifier')
@doc.arg('visit_id',
         default=1,
         argtype=doc.argtypes.int,
         argdoc='The requested SWH origin visit identifier')
@doc.returns(rettype=doc.rettypes.list,
             retdoc="""The single instance visit visit_id of the origin pointed
             by origin_id as POSIX time since epoch""")
def api_origin_visit(origin_id, visit_id):
    """Return origin visit (dict) for that particular origin including
       (but not limited to) date (visit date as posix timestamp),
       target, target_type, status, ...

    """
    def _enrich_origin_visit(origin_visit):
        ov = origin_visit.copy()
        ov['origin_url'] = url_for('api_origin', origin_id=ov['origin'])
        if 'occurrences' in ov:
            ov['occurrences'] = {
                k: utils.enrich_object(v)
                for k, v in ov['occurrences'].items()
            }
        return ov

    return _api_lookup(
        origin_id,
        service.lookup_origin_visit,
        'No visit %s for origin %s found' % (visit_id, origin_id),
        _enrich_origin_visit,
        visit_id)


@app.route('/api/1/symbol/', methods=['POST'])
@app.route('/api/1/symbol/<string:q>/')
@doc.route('/api/1/symbol/')
@doc.arg('q',
         default='hello|hy',
         argtype=doc.argtypes.str,
         argdoc="""An expression string to lookup in swh's raw content""")
@doc.returns(rettype=doc.rettypes.list,
             retdoc="""A list of dict whose content matches the expression.
             Each dict has the following keys:
             - id (bytes): identifier of the content
             - name (text): symbol whose content match the expression
             - kind (text): kind of the symbol that matched
             - lang (text): Language for that entry
             - line (int): Number line for the symbol

             """)
def api_content_symbol(q=None):
    """Search a content per expression.

    """
    result = {}
    page = int(request.args.get('page', '1'))
    symbols = _api_lookup(
        q,
        lookup_fn=lambda exp, page=page: service.lookup_expression(exp, page),
        error_msg_if_not_found='No indexed raw content match expression \''
        '%s\'.' % q,
        enrich_fn=lambda x: utils.enrich_content(x, top_url=True))

    if symbols:
        if page > 1:
            result.update({
                'headers': {
                    'link-next': utils.next_page('api_content_symbol',
                                                 q, page),
                    'link-prev': utils.prev_page('api_content_symbol',
                                                 q, page),
                }
            })
        else:
            result.update({
                'headers': {
                    'link-next': utils.next_page('api_content_symbol',
                                                 q, page),
                }
            })

    result.update({
        'results': symbols
    })

    return result


@app.route('/api/1/content/search/', methods=['POST'])
@app.route('/api/1/content/search/<string:q>/')
@doc.route('/api/1/content/search/')
@doc.arg('q',
         default='sha1:adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
         argtype=doc.argtypes.algo_and_hash,
         argdoc="""An algo_hash:hash string, where algo_hash is one of sha1,
         sha1_git or sha256 and hash is the hash to search for in SWH""")
@doc.raises(exc=doc.excs.badinput,
            doc='Raised if q is not well formed')
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""A dict with keys:

             - search_res: a list of dicts corresponding to queried content
               with key 'found' to True if found, 'False' if not
             - search_stats: a dict containing number of files searched and
               percentage of files found
             """)
def api_search(q=None):
    """Search a content per hash.

    This may take the form of:

    - a GET request with a single checksum
    - a POST request with many hashes, with the request body containing
      identifiers (typically filenames) as keys and corresponding hashes as
      values.
    """

    response = {'search_res': None,
                'search_stats': None}
    search_stats = {'nbfiles': 0, 'pct': 0}
    search_res = None

    # Single hash request route
    if q:
        r = service.search_hash(q)
        search_res = [{'filename': None,
                       'sha1': q,
                       'found': r['found']}]
        search_stats['nbfiles'] = 1
        search_stats['pct'] = 100 if r['found'] else 0

    # Post form submission with many hash requests
    elif request.method == 'POST':
        data = request.form
        queries = []
        # Remove potential inputs with no associated value
        for k, v in data.items():
            if v is not None:
                if k == 'q' and len(v) > 0:
                    queries.append({'filename': None, 'sha1': v})
                elif v != '':
                    queries.append({'filename': k, 'sha1': v})

        if len(queries) > 0:
            lookup = service.lookup_multiple_hashes(queries)
            result = []
            for el in lookup:
                result.append({'filename': el['filename'],
                               'sha1': el['sha1'],
                               'found': el['found']})
            search_res = result
            nbfound = len([x for x in lookup if x['found']])
            search_stats['nbfiles'] = len(queries)
            search_stats['pct'] = (nbfound / len(queries))*100

    response['search_res'] = search_res
    response['search_stats'] = search_stats
    return response


def _api_lookup(criteria,
                lookup_fn,
                error_msg_if_not_found,
                enrich_fn=lambda x: x,
                *args):
    """Capture a redundant behavior of:
    - looking up the backend with a criteria (be it an identifier or checksum)
    passed to the function lookup_fn
    - if nothing is found, raise an NotFoundExc exception with error
    message error_msg_if_not_found.
    - Otherwise if something is returned:
        - either as list, map or generator, map the enrich_fn function to it
        and return the resulting data structure as list.
        - either as dict and pass to enrich_fn and return the dict enriched.

    Args:
        - criteria: discriminating criteria to lookup
        - lookup_fn: function expects one criteria and optional supplementary
        *args.
        - error_msg_if_not_found: if nothing matching the criteria is found,
        raise NotFoundExc with this error message.
        - enrich_fn: Function to use to enrich the result returned by
        lookup_fn. Default to the identity function if not provided.
        - *args: supplementary arguments to pass to lookup_fn.

    Raises:
        NotFoundExp or whatever `lookup_fn` raises.

    """
    res = lookup_fn(criteria, *args)
    if not res:
        raise NotFoundExc(error_msg_if_not_found)
    if isinstance(res, (map, list, GeneratorType)):
        return [enrich_fn(x) for x in res]
    return enrich_fn(res)


@app.route('/api/1/origin/<int:origin_id>/')
@app.route('/api/1/origin/<string:origin_type>/url/<path:origin_url>/')
@doc.route('/api/1/origin/')
@doc.arg('origin_id',
         default=1,
         argtype=doc.argtypes.int,
         argdoc="The origin's SWH origin_id.")
@doc.arg('origin_type',
         default='git',
         argtype=doc.argtypes.str,
         argdoc="The origin's type (git, svn..)")
@doc.arg('origin_url',
         default='https://github.com/hylang/hy',
         argtype=doc.argtypes.path,
         argdoc="The origin's URL.")
@doc.raises(exc=doc.excs.notfound,
            doc='Raised if origin_id does not correspond to an origin in SWH')
@doc.returns(rettype=doc.rettypes.dict,
             retdoc='The metadata of the origin identified by origin_id')
def api_origin(origin_id=None, origin_type=None, origin_url=None):
    """Return information about the origin matching the passed criteria.

    Criteria may be:
      - An SWH-specific ID, if you already know it
      - An origin type and its URL, if you do not have the origin's SWH
        identifier
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
            o['origin_visits_url'] = url_for('api_origin_visits',
                                             origin_id=o['id'])
            return o

        return origin

    return _api_lookup(
        ori_dict, lookup_fn=service.lookup_origin,
        error_msg_if_not_found=error_msg,
        enrich_fn=_enrich_origin)


@app.route('/api/1/person/<int:person_id>/')
@doc.route('/api/1/person/')
@doc.arg('person_id',
         default=1,
         argtype=doc.argtypes.int,
         argdoc="The person's SWH identifier")
@doc.raises(exc=doc.excs.notfound,
            doc='Raised if person_id does not correspond to an origin in SWH')
@doc.returns(rettype=doc.rettypes.dict,
             retdoc='The metadata of the person identified by person_id')
def api_person(person_id):
    """Return information about person with identifier person_id.
    """
    return _api_lookup(
        person_id, lookup_fn=service.lookup_person,
        error_msg_if_not_found='Person with id %s not found.' % person_id)


@app.route('/api/1/release/<string:sha1_git>/')
@doc.route('/api/1/release/')
@doc.arg('sha1_git',
         default='8b137891791fe96927ad78e64b0aad7bded08bdc',
         argtype=doc.argtypes.sha1_git,
         argdoc="The release's sha1_git identifier")
@doc.raises(exc=doc.excs.badinput,
            doc='Raised if the argument is not a sha1')
@doc.raises(exc=doc.excs.notfound,
            doc='Raised if sha1_git does not correspond to a release in SWH')
@doc.returns(rettype=doc.rettypes.dict,
             retdoc='The metadata of the release identified by sha1_git')
def api_release(sha1_git):
    """Return information about release with id sha1_git.
    """
    error_msg = 'Release with sha1_git %s not found.' % sha1_git
    return _api_lookup(
        sha1_git,
        lookup_fn=service.lookup_release,
        error_msg_if_not_found=error_msg,
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


@app.route('/api/1/revision'
           '/origin/<int:origin_id>'
           '/directory/')
@app.route('/api/1/revision'
           '/origin/<int:origin_id>'
           '/directory/<path:path>/')
@app.route('/api/1/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/directory/')
@app.route('/api/1/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/directory/<path:path>/')
@app.route('/api/1/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/ts/<string:ts>'
           '/directory/')
@app.route('/api/1/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/ts/<string:ts>'
           '/directory/<path:path>/')
@doc.route('/api/1/revision/origin/directory/')
@doc.arg('origin_id',
         default=1,
         argtype=doc.argtypes.int,
         argdoc="The revision's origin's SWH identifier")
@doc.arg('branch_name',
         default='refs/heads/master',
         argtype=doc.argtypes.path,
         argdoc="""The optional branch for the given origin (default
         to master""")
@doc.arg('ts',
         default='2000-01-17T11:23:54+00:00',
         argtype=doc.argtypes.ts,
         argdoc="""Optional timestamp (default to the nearest time
         crawl of timestamp)""")
@doc.arg('path',
         default='.',
         argtype=doc.argtypes.path,
         argdoc='The path to the directory or file to display')
@doc.raises(exc=doc.excs.notfound,
            doc="""Raised if a revision matching the passed criteria was
            not found""")
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""The metadata of the revision corresponding to the
             passed criteria""")
def api_directory_through_revision_origin(origin_id,
                                          branch_name="refs/heads/master",
                                          ts=None,
                                          path=None,
                                          with_data=False):
    """Display directory or content information through a revision identified
    by origin/branch/timestamp.
    """
    if ts:
        ts = utils.parse_timestamp(ts)

    return _revision_directory_by(
        {
            'origin_id': origin_id,
            'branch_name': branch_name,
            'ts': ts
        },
        path,
        request.path,
        with_data=with_data)


@app.route('/api/1/revision'
           '/origin/<int:origin_id>/')
@app.route('/api/1/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>/')
@app.route('/api/1/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/ts/<string:ts>/')
@app.route('/api/1/revision'
           '/origin/<int:origin_id>'
           '/ts/<string:ts>/')
@doc.route('/api/1/revision/origin/')
@doc.arg('origin_id',
         default=1,
         argtype=doc.argtypes.int,
         argdoc="The queried revision's origin identifier in SWH")
@doc.arg('branch_name',
         default='refs/heads/master',
         argtype=doc.argtypes.path,
         argdoc="""The optional branch for the given origin (default
         to master)""")
@doc.arg('ts',
         default='2000-01-17T11:23:54+00:00',
         argtype=doc.argtypes.ts,
         argdoc="The time at which the queried revision should be constrained")
@doc.raises(exc=doc.excs.notfound,
            doc="""Raised if a revision matching given criteria was not found
            in SWH""")
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""The metadata of the revision identified by the given
             criteria""")
def api_revision_with_origin(origin_id,
                             branch_name="refs/heads/master",
                             ts=None):
    """Display revision information through its identification by
    origin/branch/timestamp.
    """
    if ts:
        ts = utils.parse_timestamp(ts)

    return _api_lookup(
        origin_id,
        service.lookup_revision_by,
        'Revision with (origin_id: %s, branch_name: %s'
        ', ts: %s) not found.' % (origin_id,
                                  branch_name,
                                  ts),
        utils.enrich_revision,
        branch_name,
        ts)


@app.route('/api/1/revision/<string:sha1_git>/')
@app.route('/api/1/revision/<string:sha1_git>/prev/<path:context>/')
@doc.route('/api/1/revision/')
@doc.arg('sha1_git',
         default='ec72c666fb345ea5f21359b7bc063710ce558e39',
         argtype=doc.argtypes.sha1_git,
         argdoc="The revision's sha1_git identifier")
@doc.arg('context',
         default='6adc4a22f20bbf3bbc754f1ec8c82be5dfb5c71a',
         argtype=doc.argtypes.path,
         argdoc='The navigation breadcrumbs -- use at your own risk')
@doc.raises(exc=doc.excs.badinput,
            doc='Raised if sha1_git is not well formed')
@doc.raises(exc=doc.excs.notfound,
            doc='Raised if a revision matching sha1_git was not found in SWH')
@doc.returns(rettype=doc.rettypes.dict,
             retdoc='The metadata of the revision identified by sha1_git')
def api_revision(sha1_git, context=None):
    """Return information about revision with id sha1_git.
    """
    def _enrich_revision(revision, context=context):
        return utils.enrich_revision(revision, context)

    return _api_lookup(
        sha1_git,
        service.lookup_revision,
        'Revision with sha1_git %s not found.' % sha1_git,
        _enrich_revision)


@app.route('/api/1/revision/<string:sha1_git>/raw/')
@doc.route('/api/1/revision/raw/')
@doc.arg('sha1_git',
         default='ec72c666fb345ea5f21359b7bc063710ce558e39',
         argtype=doc.argtypes.sha1_git,
         argdoc="The queried revision's sha1_git identifier")
@doc.raises(exc=doc.excs.badinput,
            doc='Raised if sha1_git is not well formed')
@doc.raises(exc=doc.excs.notfound,
            doc='Raised if a revision matching sha1_git was not found in SWH')
@doc.returns(rettype=doc.rettypes.octet_stream,
             retdoc="""The message of the revision identified by sha1_git
             as a downloadable octet stream""")
def api_revision_raw_message(sha1_git):
    """Return the raw data of the message of revision identified by sha1_git
    """
    raw = service.lookup_revision_message(sha1_git)
    return app.response_class(raw['message'],
                              headers={'Content-disposition': 'attachment;'
                                       'filename=rev_%s_raw' % sha1_git},
                              mimetype='application/octet-stream')


@app.route('/api/1/revision/<string:sha1_git>/directory/')
@app.route('/api/1/revision/<string:sha1_git>/directory/<path:dir_path>/')
@doc.route('/api/1/revision/directory/')
@doc.arg('sha1_git',
         default='ec72c666fb345ea5f21359b7bc063710ce558e39',
         argtype=doc.argtypes.sha1_git,
         argdoc="The revision's sha1_git identifier.")
@doc.arg('dir_path',
         default='.',
         argtype=doc.argtypes.path,
         argdoc='The path from the top level directory')
@doc.raises(exc=doc.excs.badinput,
            doc='Raised if sha1_git is not well formed')
@doc.raises(exc=doc.excs.notfound,
            doc="""Raised if a revision matching sha1_git was not found in SWH
            , or if the path specified does not exist""")
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""The metadata of the directory pointed by revision id
             sha1-git and dir_path""")
def api_revision_directory(sha1_git,
                           dir_path=None,
                           with_data=False):
    """Return information on directory pointed by revision with sha1_git.
    If dir_path is not provided, display top level directory.
    Otherwise, display the directory pointed by dir_path (if it exists).
    """
    return _revision_directory_by(
        {
            'sha1_git': sha1_git
        },
        dir_path,
        request.path,
        with_data=with_data)


@app.route('/api/1/revision/<string:sha1_git>/log/')
@app.route('/api/1/revision/<string:sha1_git>/prev/<path:prev_sha1s>/log/')
@doc.route('/api/1/revision/log/')
@doc.arg('sha1_git',
         default='ec72c666fb345ea5f21359b7bc063710ce558e39',
         argtype=doc.argtypes.sha1_git,
         argdoc='The sha1_git of the revision queried')
@doc.arg('prev_sha1s',
         default='6adc4a22f20bbf3bbc754f1ec8c82be5dfb5c71a',
         argtype=doc.argtypes.path,
         argdoc='The navigation breadcrumbs -- use at your own risk!')
@doc.raises(exc=doc.excs.badinput,
            doc='Raised if sha1_git or prev_sha1s is not well formed')
@doc.raises(exc=doc.excs.notfound,
            doc='Raised if a revision matching sha1_git was not found in SWH')
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""The log data starting at the revision identified by
             sha1_git, completed with the navigation breadcrumbs,
             if any""")
def api_revision_log(sha1_git, prev_sha1s=None):
    """Show all revisions (~git log) starting from sha1_git.
    The first element returned is the given sha1_git, or the first
    breadcrumb, if any.

    """
    limit = app.config['conf']['max_log_revs']

    response = {'revisions': None, 'next_revs_url': None}
    revisions = None
    next_revs_url = None

    def lookup_revision_log_with_limit(s, limit=limit+1):
        return service.lookup_revision_log(s, limit)

    error_msg = 'Revision with sha1_git %s not found.' % sha1_git
    rev_get = _api_lookup(sha1_git,
                          lookup_fn=lookup_revision_log_with_limit,
                          error_msg_if_not_found=error_msg,
                          enrich_fn=utils.enrich_revision)

    if len(rev_get) == limit+1:
        rev_backward = rev_get[:-1]
        next_revs_url = url_for('api_revision_log',
                                sha1_git=rev_get[-1]['id'])
    else:
        rev_backward = rev_get

    if not prev_sha1s:  # no nav breadcrumbs, so we're done
        revisions = rev_backward

    else:
        rev_forward_ids = prev_sha1s.split('/')
        rev_forward = _api_lookup(rev_forward_ids,
                                  lookup_fn=service.lookup_revision_multiple,
                                  error_msg_if_not_found=error_msg,
                                  enrich_fn=utils.enrich_revision)
        revisions = rev_forward + rev_backward

    response['revisions'] = revisions
    response['next_revs_url'] = next_revs_url

    return response


@app.route('/api/1/revision'
           '/origin/<int:origin_id>/log/')
@app.route('/api/1/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>/log/')
@app.route('/api/1/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/ts/<string:ts>/log/')
@app.route('/api/1/revision'
           '/origin/<int:origin_id>'
           '/ts/<string:ts>/log/')
@doc.route('/api/1/revision/origin/log/')
@doc.arg('origin_id',
         default=1,
         argtype=doc.argtypes.int,
         argdoc="The revision's SWH origin identifier")
@doc.arg('branch_name',
         default='refs/heads/master',
         argtype=doc.argtypes.path,
         argdoc="The revision's branch name within the origin specified")
@doc.arg('ts',
         default='2000-01-17T11:23:54+00:00',
         argtype=doc.argtypes.ts,
         argdoc="""A time or timestamp string to parse""")
@doc.raises(exc=doc.excs.notfound,
            doc="""Raised if a revision matching the given criteria was not
            found in SWH""")
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""The metadata of the revision log starting at the revision
             matching the given criteria.""")
def api_revision_log_by(origin_id,
                        branch_name='refs/heads/master',
                        ts=None):
    """Show all revisions (~git log) starting from the revision
    described by its origin_id, optional branch name and timestamp.
    The first element returned is the described revision.

    """
    limit = app.config['conf']['max_log_revs']
    response = {'revisions': None, 'next_revs_url': None}
    next_revs_url = None

    if ts:
        ts = utils.parse_timestamp(ts)

    def lookup_revision_log_by_with_limit(o_id, br, ts, limit=limit+1):
        return service.lookup_revision_log_by(o_id, br, ts, limit)

    error_msg = 'No revision matching origin %s ' % origin_id
    error_msg += ', branch name %s' % branch_name
    error_msg += (' and time stamp %s.' % ts) if ts else '.'

    rev_get = _api_lookup(origin_id,
                          lookup_revision_log_by_with_limit,
                          error_msg,
                          utils.enrich_revision,
                          branch_name,
                          ts)
    if len(rev_get) == limit+1:
        revisions = rev_get[:-1]
        next_revs_url = url_for('api_revision_log',
                                sha1_git=rev_get[-1]['id'])
    else:
        revisions = rev_get
    response['revisions'] = revisions
    response['next_revs_url'] = next_revs_url

    return response


@app.route('/api/1/directory/<string:sha1_git>/')
@app.route('/api/1/directory/<string:sha1_git>/<path:path>/')
@doc.route('/api/1/directory/')
@doc.arg('sha1_git',
         default='adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
         argtype=doc.argtypes.sha1_git,
         argdoc="The queried directory's corresponding sha1_git hash")
@doc.arg('path',
         default='.',
         argtype=doc.argtypes.path,
         argdoc="A path relative to the queried directory's top level")
@doc.raises(exc=doc.excs.badinput,
            doc='Raised if sha1_git is not well formed')
@doc.raises(exc=doc.excs.notfound,
            doc='Raised if a directory matching sha1_git was not found in SWH')
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""The metadata and contents of the release identified by
             sha1_git""")
def api_directory(sha1_git,
                  path=None):
    """Return information about release with id sha1_git.

    """
    if path:
        error_msg_path = ('Entry with path %s relative to directory '
                          'with sha1_git %s not found.') % (path, sha1_git)
        return _api_lookup(
            sha1_git,
            service.lookup_directory_with_path,
            error_msg_path,
            utils.enrich_directory,
            path)
    else:
        error_msg_nopath = 'Directory with sha1_git %s not found.' % sha1_git
        return _api_lookup(
            sha1_git,
            service.lookup_directory,
            error_msg_nopath,
            utils.enrich_directory)


@app.route('/api/1/provenance/<string:q>/')
@doc.route('/api/1/provenance/')
@doc.arg('q',
         default='sha1_git:88b9b366facda0b5ff8d8640ee9279bed346f242',
         argtype=doc.argtypes.algo_and_hash,
         argdoc="""The queried content's corresponding hash (supported hash
 algorithms: sha1_git, sha1, sha256)""")
@doc.raises(exc=doc.excs.badinput,
            doc="""Raised if hash algorithm is incorrect  or if the hash
 value is badly formatted.""")
@doc.raises(exc=doc.excs.notfound,
            doc="""Raised if a content matching the hash was not found
 in SWH""")
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""List of provenance information (dict) for the matched
content.""")
def api_content_provenance(q):
    """Return content's provenance information if any.

    """
    def _enrich_revision(provenance):
        p = provenance.copy()
        p['revision_url'] = url_for('api_revision',
                                    sha1_git=provenance['revision'])
        p['content_url'] = url_for('api_content_metadata',
                                   q='sha1_git:%s' % provenance['content'])
        p['origin_url'] = url_for('api_origin',
                                  origin_id=provenance['origin'])
        p['origin_visits_url'] = url_for('api_origin_visits',
                                         origin_id=provenance['origin'])
        p['origin_visit_url'] = url_for('api_origin_visit',
                                        origin_id=provenance['origin'],
                                        visit_id=provenance['visit'])
        return p

    return _api_lookup(
        q,
        lookup_fn=service.lookup_content_provenance,
        error_msg_if_not_found='Content with %s not found.' % q,
        enrich_fn=_enrich_revision)


@app.route('/api/1/filetype/<string:q>/')
@doc.route('/api/1/filetype/')
@doc.arg('q',
         default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
         argtype=doc.argtypes.algo_and_hash,
         argdoc="""The queried content's corresponding hash (supported hash
 algorithms: sha1_git, sha1, sha256)""")
@doc.raises(exc=doc.excs.badinput,
            doc="""Raised if hash algorithm is incorrect or if the hash
 value is badly formatted.""")
@doc.raises(exc=doc.excs.notfound,
            doc="""Raised if a content matching the hash was not found
 in SWH""")
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""Filetype information (dict) for the matched
content.""")
def api_content_filetype(q):
    """Return content's filetype information if any.

    """
    return _api_lookup(
        q,
        lookup_fn=service.lookup_content_filetype,
        error_msg_if_not_found='No filetype information found '
        'for content %s.' % q,
        enrich_fn=utils.enrich_metadata_endpoint)


@app.route('/api/1/language/<string:q>/')
@doc.route('/api/1/language/')
@doc.arg('q',
         default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
         argtype=doc.argtypes.algo_and_hash,
         argdoc="""The queried content's corresponding hash (supported hash
 algorithms: sha1_git, sha1, sha256)""")
@doc.raises(exc=doc.excs.badinput,
            doc="""Raised if hash algorithm is incorrect or if the hash
 value is badly formatted.""")
@doc.raises(exc=doc.excs.notfound,
            doc="""Raised if a content matching the hash was not found
 in SWH""")
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""Language information (dict) for the matched
content.""")
def api_content_language(q):
    """Return content's language information if any.

    """
    return _api_lookup(
        q,
        lookup_fn=service.lookup_content_language,
        error_msg_if_not_found='No language information found '
        'for content %s.' % q,
        enrich_fn=utils.enrich_metadata_endpoint)


@app.route('/api/1/license/<string:q>/')
@doc.route('/api/1/license/')
@doc.arg('q',
         default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
         argtype=doc.argtypes.algo_and_hash,
         argdoc="""The queried content's corresponding hash (supported hash
 algorithms: sha1_git, sha1, sha256)""")
@doc.raises(exc=doc.excs.badinput,
            doc="""Raised if hash algorithm is incorrect or if the hash
 value is badly formatted.""")
@doc.raises(exc=doc.excs.notfound,
            doc="""Raised if a content matching the hash was not found
 in SWH""")
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""License information (dict) for the matched
content.""")
def api_content_license(q):
    """Return content's license information if any.

    """
    return _api_lookup(
        q,
        lookup_fn=service.lookup_content_license,
        error_msg_if_not_found='No license information found '
        'for content %s.' % q,
        enrich_fn=utils.enrich_metadata_endpoint)


@app.route('/api/1/ctags/<string:q>/')
@doc.route('/api/1/ctags/')
@doc.arg('q',
         default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
         argtype=doc.argtypes.algo_and_hash,
         argdoc="""The queried content's corresponding hash (supported hash
 algorithms: sha1_git, sha1, sha256)""")
@doc.raises(exc=doc.excs.badinput,
            doc="""Raised if hash algorithm is incorrect or if the hash
 value is badly formatted.""")
@doc.raises(exc=doc.excs.notfound,
            doc="""Raised if a content matching the hash was not found
 in SWH""")
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""Ctags symbol (dict) for the matched
content.""")
def api_content_ctags(q):
    """Return content's ctags symbols if any.

    """
    return _api_lookup(
        q,
        lookup_fn=service.lookup_content_ctags,
        error_msg_if_not_found='No ctags symbol found '
        'for content %s.' % q,
        enrich_fn=utils.enrich_metadata_endpoint)


@app.route('/api/1/content/<string:q>/raw/')
@doc.route('/api/1/content/raw/')
@doc.arg('q',
         default='adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
         argtype=doc.argtypes.algo_and_hash,
         argdoc="""An algo_hash:hash string, where algo_hash is one of sha1,
         sha1_git or sha256 and hash is the hash to search for in SWH. Defaults
         to sha1 in the case of a missing algo_hash
         """)
@doc.raises(exc=doc.excs.badinput,
            doc='Raised if q is not well formed')
@doc.raises(exc=doc.excs.notfound,
            doc='Raised if a content matching q was not found in SWH')
@doc.returns(rettype=doc.rettypes.octet_stream,
             retdoc='The raw content data as an octet stream')
def api_content_raw(q):
    """Return content's raw data if content is found.

    """
    def generate(content):
        yield content['data']

    content = service.lookup_content_raw(q)
    if not content:
        raise NotFoundExc('Content with %s not found.' % q)

    return app.response_class(generate(content),
                              headers={'Content-disposition': 'attachment;'
                                       'filename=content_%s_raw' % q},
                              mimetype='application/octet-stream')


@app.route('/api/1/content/<string:q>/')
@doc.route('/api/1/content/')
@doc.arg('q',
         default='adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
         argtype=doc.argtypes.algo_and_hash,
         argdoc="""An algo_hash:hash string, where algo_hash is one of sha1,
         sha1_git or sha256 and hash is the hash to search for in SWH. Defaults
         to sha1 in the case of a missing algo_hash
         """)
@doc.raises(exc=doc.excs.badinput,
            doc='Raised if q is not well formed')
@doc.raises(exc=doc.excs.notfound,
            doc='Raised if a content matching q was not found in SWH')
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""The metadata of the content identified by q. If content
             decoding was successful, it also returns the data""")
def api_content_metadata(q):
    """Return content information if content is found.

    """
    return _api_lookup(
        q,
        lookup_fn=service.lookup_content,
        error_msg_if_not_found='Content with %s not found.' % q,
        enrich_fn=utils.enrich_content)


@app.route('/api/1/entity/<string:uuid>/')
@doc.route('/api/1/entity/')
@doc.arg('uuid',
         default='5f4d4c51-498a-4e28-88b3-b3e4e8396cba',
         argtype=doc.argtypes.uuid,
         argdoc="The entity's uuid identifier")
@doc.raises(exc=doc.excs.badinput,
            doc='Raised if uuid is not well formed')
@doc.raises(exc=doc.excs.notfound,
            doc='Raised if an entity matching uuid was not found in SWH')
@doc.returns(rettype=doc.rettypes.dict,
             retdoc='The metadata of the entity identified by uuid')
def api_entity_by_uuid(uuid):
    """Return content information if content is found.

    """
    return _api_lookup(
        uuid,
        lookup_fn=service.lookup_entity_by_uuid,
        error_msg_if_not_found="Entity with uuid '%s' not found." % uuid,
        enrich_fn=utils.enrich_entity)
