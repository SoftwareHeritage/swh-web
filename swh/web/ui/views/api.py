# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from types import GeneratorType

from flask import render_template, request, url_for

from swh.web.ui import service, utils, apidoc as doc
from swh.web.ui.exc import NotFoundExc
from swh.web.ui.main import app


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


@app.route('/api/1/')
def api_endpoints():
    """Display the list of opened api endpoints.

    """
    routes = doc.APIUrls.get_app_endpoints()
    # Return a list of routes with consistent ordering
    env = {
        'doc_routes': sorted(routes.items())
    }
    return render_template('api-endpoints.html', **env)


@app.route('/api/')
def api_doc():
    """Display the API's documentation.

    """
    return render_template('api.html')


@app.route('/api/1/stat/counters/')
@doc.route('/api/1/stat/counters/', noargs=True)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""dictionary mapping object types to the amount of
             corresponding objects currently available in the archive""")
def api_stats():
    """Get statistics about the content of the archive.

    """
    return service.stat_counters()


@app.route('/api/1/origin/<int:origin_id>/visits/')
@doc.route('/api/1/origin/visits/')
@doc.arg('origin_id',
         default=1,
         argtype=doc.argtypes.int,
         argdoc='software origin identifier')
@doc.header('Link', doc=_doc_header_link)
@doc.param('last_visit', default=None,
           argtype=doc.argtypes.int,
           doc=_doc_arg_last_elt)
@doc.param('per_page', default=10,
           argtype=doc.argtypes.int,
           doc=_doc_arg_per_page)
@doc.returns(rettype=doc.rettypes.list,
             retdoc="""a list of dictionaries describing individual visits.
             For each visit, its identifier, timestamp (as UNIX time), outcome,
             and visit-specific URL for more information are given.""")
def api_origin_visits(origin_id):
    """Get information about all visits of a given software origin.

    """
    result = {}
    per_page = int(request.args.get('per_page', '10'))
    last_visit = request.args.get('last_visit')
    if last_visit:
        last_visit = int(last_visit)

    def _lookup_origin_visits(
            origin_id, last_visit=last_visit, per_page=per_page):
        return service.lookup_origin_visits(
            origin_id, last_visit=last_visit, per_page=per_page)

    def _enrich_origin_visit(origin_visit):
        ov = origin_visit.copy()
        ov['origin_visit_url'] = url_for('api_origin_visit',
                                         origin_id=ov['origin'],
                                         visit_id=ov['visit'])
        return ov

    r = _api_lookup(
        origin_id,
        _lookup_origin_visits,
        error_msg_if_not_found='No origin %s found' % origin_id,
        enrich_fn=_enrich_origin_visit)

    if r:
        l = len(r)
        if l == per_page:
            new_last_visit = r[-1]['visit']
            params = {
                'origin_id': origin_id,
                'last_visit': new_last_visit
            }

            if request.args.get('per_page'):
                params['per_page'] = per_page

            result['headers'] = {
                'link-next': url_for('api_origin_visits', **params)
            }

    result.update({
        'results': r
    })

    return result


@app.route('/api/1/origin/<int:origin_id>/visit/<int:visit_id>/')
@doc.route('/api/1/origin/visit/')
@doc.arg('origin_id',
         default=1,
         argtype=doc.argtypes.int,
         argdoc='software origin identifier')
@doc.arg('visit_id',
         default=1,
         argtype=doc.argtypes.int,
         argdoc="""visit identifier, relative to the origin identified by
         origin_id""")
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""dictionary containing both metadata for the entire
             visit (e.g., timestamp as UNIX time, visit outcome, etc.) and what
             was at the software origin during the visit (i.e., a mapping from
             branches to other archive objects)""")
def api_origin_visit(origin_id, visit_id):
    """Get information about a specific visit of a software origin.

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


@app.route('/api/1/content/symbol/', methods=['POST'])
@app.route('/api/1/content/symbol/<string:q>/')
@doc.route('/api/1/content/symbol/', tags=['upcoming'])
@doc.arg('q',
         default='hello',
         argtype=doc.argtypes.str,
         argdoc="""An expression string to lookup in swh's raw content""")
@doc.header('Link', doc=_doc_header_link)
@doc.param('last_sha1', default=None,
           argtype=doc.argtypes.str,
           doc=_doc_arg_last_elt)
@doc.param('per_page', default=10,
           argtype=doc.argtypes.int,
           doc=_doc_arg_per_page)
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
    """Search content objects by `Ctags <http://ctags.sourceforge.net/>`_-style
    symbol (e.g., function name, data type, method, ...).

    """
    result = {}
    last_sha1 = request.args.get('last_sha1', None)
    per_page = int(request.args.get('per_page', '10'))

    def lookup_exp(exp, last_sha1=last_sha1, per_page=per_page):
        return service.lookup_expression(exp, last_sha1, per_page)

    symbols = _api_lookup(
        q,
        lookup_fn=lookup_exp,
        error_msg_if_not_found='No indexed raw content match expression \''
        '%s\'.' % q,
        enrich_fn=lambda x: utils.enrich_content(x, top_url=True))

    if symbols:
        l = len(symbols)

        if l == per_page:
            new_last_sha1 = symbols[-1]['sha1']
            params = {
                'q': q,
                'last_sha1': new_last_sha1,
            }

            if request.args.get('per_page'):
                params['per_page'] = per_page

            result['headers'] = {
                'link-next': url_for('api_content_symbol', **params),
            }

    result.update({
        'results': symbols
    })

    return result


@app.route('/api/1/content/known/', methods=['POST'])
@app.route('/api/1/content/known/<string:q>/')
@doc.route('/api/1/content/known/', tags=['hidden'])
@doc.arg('q',
         default='adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
         argtype=doc.argtypes.sha1,
         argdoc='content identifier as a sha1 checksum')
# @doc.param('q', default=None,
#            argtype=doc.argtypes.str,
#            doc="""(POST request) An algo_hash:hash string, where algo_hash
#                   is one of sha1, sha1_git or sha256 and hash is the hash to
#                   search for in SWH""")
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""a dictionary with results (found/not found for each given
             identifier) and statistics about how many identifiers were
             found""")
def api_check_content_known(q=None):
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
        data = request.form
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
@app.route('/api/1/origin/<string:origin_type>/url/<path:origin_url>')
@doc.route('/api/1/origin/')
@doc.arg('origin_id',
         default=1,
         argtype=doc.argtypes.int,
         argdoc='origin identifier (when looking up by ID)')
@doc.arg('origin_type',
         default='git',
         argtype=doc.argtypes.str,
         argdoc='origin type (when looking up by type+URL)')
@doc.arg('origin_url',
         default='https://github.com/hylang/hy',
         argtype=doc.argtypes.path,
         argdoc='origin URL (when looking up by type+URL')
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""The metadata of the origin corresponding to the given
             criteria""")
def api_origin(origin_id=None, origin_type=None, origin_url=None):
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
         default=42,
         argtype=doc.argtypes.int,
         argdoc='person identifier')
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc='The metadata of the person identified by person_id')
def api_person(person_id):
    """Get information about a person.

    """
    return _api_lookup(
        person_id, lookup_fn=service.lookup_person,
        error_msg_if_not_found='Person with id %s not found.' % person_id)


@app.route('/api/1/release/<string:sha1_git>/')
@doc.route('/api/1/release/')
@doc.arg('sha1_git',
         default='7045404f3d1c54e6473c71bbb716529fbad4be24',
         argtype=doc.argtypes.sha1_git,
         argdoc='release identifier')
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc='The metadata of the release identified by sha1_git')
def api_release(sha1_git):
    """Get information about a release.

    Releases are identified by SHA1 checksums, compatible with Git tag
    identifiers. See ``release_identifier`` in our `data model module
    <https://forge.softwareheritage.org/source/swh-model/browse/master/swh/model/identifiers.py>`_
    for details about how they are computed.

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
@doc.route('/api/1/revision/origin/directory/', tags=['hidden'])
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
         default='Dockerfile',
         argtype=doc.argtypes.path,
         argdoc='The path to the directory or file to display')
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""The metadata of the revision corresponding to the
             given criteria""")
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
         argdoc='software origin identifier')
@doc.arg('branch_name',
         default='refs/heads/master',
         argtype=doc.argtypes.path,
         argdoc="""(optional) fully-qualified branch name, e.g.,
         "refs/heads/master". Defaults to the master branch.""")
@doc.arg('ts',
         default=None,
         argtype=doc.argtypes.ts,
         argdoc="""(optional) timestamp close to which the revision pointed by
         the given branch should be looked up. Defaults to now.""")
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict, retdoc=_doc_ret_revision_meta)
def api_revision_with_origin(origin_id,
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
        origin_id,
        service.lookup_revision_by,
        'Revision with (origin_id: %s, branch_name: %s'
        ', ts: %s) not found.' % (origin_id,
                                  branch_name,
                                  ts),
        utils.enrich_revision,
        branch_name,
        ts)


@app.route('/api/1/revision/<string:sha1_git>/prev/<path:context>/')
@doc.route('/api/1/revision/prev/', tags=['hidden'])
@doc.arg('sha1_git',
         default='ec72c666fb345ea5f21359b7bc063710ce558e39',
         argtype=doc.argtypes.sha1_git,
         argdoc="The revision's sha1_git identifier")
@doc.arg('context',
         default='6adc4a22f20bbf3bbc754f1ec8c82be5dfb5c71a',
         argtype=doc.argtypes.path,
         argdoc='The navigation breadcrumbs -- use at your own risk')
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc='The metadata of the revision identified by sha1_git')
def api_revision_with_context(sha1_git, context):
    """Return information about revision with id sha1_git.
    """
    def _enrich_revision(revision, context=context):
        return utils.enrich_revision(revision, context)

    return _api_lookup(
        sha1_git,
        service.lookup_revision,
        'Revision with sha1_git %s not found.' % sha1_git,
        _enrich_revision)


@app.route('/api/1/revision/<string:sha1_git>/')
@doc.route('/api/1/revision/')
@doc.arg('sha1_git',
         default='aafb16d69fd30ff58afdd69036a26047f3aebdc6',
         argtype=doc.argtypes.sha1_git,
         argdoc="revision identifier")
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict, retdoc=_doc_ret_revision_meta)
def api_revision(sha1_git):
    """Get information about a revision.

    Revisions are identified by SHA1 checksums, compatible with Git commit
    identifiers. See ``revision_identifier`` in our `data model module
    <https://forge.softwareheritage.org/source/swh-model/browse/master/swh/model/identifiers.py>`_
    for details about how they are computed.

    """
    return _api_lookup(
        sha1_git,
        service.lookup_revision,
        'Revision with sha1_git %s not found.' % sha1_git,
        utils.enrich_revision)


@app.route('/api/1/revision/<string:sha1_git>/raw/')
@doc.route('/api/1/revision/raw/', tags=['hidden'])
@doc.arg('sha1_git',
         default='ec72c666fb345ea5f21359b7bc063710ce558e39',
         argtype=doc.argtypes.sha1_git,
         argdoc="The queried revision's sha1_git identifier")
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
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
         argdoc='revision identifier')
@doc.arg('dir_path',
         default='Documentation/BUG-HUNTING',
         argtype=doc.argtypes.path,
         argdoc="""path relative to the root directory of revision identifier by
         sha1_git""")
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""either a list of directory entries with their metadata,
             or the metadata of a single directory entry""")
def api_revision_directory(sha1_git,
                           dir_path=None,
                           with_data=False):
    """Get information about directory (entry) objects associated to revisions.

    Each revision is associated to a single "root" directory. This endpoint
    behaves like ``/directory/``, but operates on the root directory associated
    to a given revision.

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
         default='37fc9e08d0c4b71807a4f1ecb06112e78d91c283',
         argtype=doc.argtypes.sha1_git,
         argdoc='revision identifier')
# @doc.arg('prev_sha1s',
#          default='6adc4a22f20bbf3bbc754f1ec8c82be5dfb5c71a',
#          argtype=doc.argtypes.path,
#          argdoc="""(Optional) Navigation breadcrumbs (descendant revisions
# previously visited).  If multiple values, use / as delimiter.  """)
@doc.header('Link', doc=_doc_header_link)
@doc.param('per_page', default=10,
           argtype=doc.argtypes.int,
           doc=_doc_arg_per_page)
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict, retdoc=_doc_ret_revision_log)
def api_revision_log(sha1_git, prev_sha1s=None):
    """Get a list of all revisions heading to a given one, i.e., show the
    commit log.

    """
    result = {}
    per_page = int(request.args.get('per_page', '10'))

    def lookup_revision_log_with_limit(s, limit=per_page+1):
        return service.lookup_revision_log(s, limit)

    error_msg = 'Revision with sha1_git %s not found.' % sha1_git
    rev_get = _api_lookup(sha1_git,
                          lookup_fn=lookup_revision_log_with_limit,
                          error_msg_if_not_found=error_msg,
                          enrich_fn=utils.enrich_revision)

    l = len(rev_get)
    if l == per_page+1:
        rev_backward = rev_get[:-1]
        new_last_sha1 = rev_get[-1]['id']
        params = {
            'sha1_git': new_last_sha1,
        }

        if request.args.get('per_page'):
            params['per_page'] = per_page

        result['headers'] = {
            'link-next': url_for('api_revision_log', **params)
        }

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

    result.update({
        'results': revisions
    })
    return result


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
         argdoc="""(Optional) The revision's branch name within the origin specified.
Defaults to 'refs/heads/master'.""")
@doc.arg('ts',
         default='2000-01-17T11:23:54+00:00',
         argtype=doc.argtypes.ts,
         argdoc="""(Optional) A time or timestamp string to parse""")
@doc.header('Link', doc=_doc_header_link)
@doc.param('per_page', default=10,
           argtype=doc.argtypes.int,
           doc=_doc_arg_per_page)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict, retdoc=_doc_ret_revision_log)
def api_revision_log_by(origin_id,
                        branch_name='refs/heads/master',
                        ts=None):
    """Show the commit log for a revision, searching for it based on software
    origin, branch name, and/or visit timestamp.

    This endpoint behaves like ``/log``, but operates on the revision that
    has been found at a given software origin, close to a given point in time,
    pointed by a given branch.
    """
    result = {}
    per_page = int(request.args.get('per_page', '10'))

    if ts:
        ts = utils.parse_timestamp(ts)

    def lookup_revision_log_by_with_limit(o_id, br, ts, limit=per_page+1):
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
    l = len(rev_get)
    if l == per_page+1:
        revisions = rev_get[:-1]
        last_sha1_git = rev_get[-1]['id']

        params = {
            'origin_id': origin_id,
            'branch_name': branch_name,
            'ts': ts,
            'sha1_git': last_sha1_git,
        }

        if request.args.get('per_page'):
            params['per_page'] = per_page

        result['headers'] = {
            'link-next': url_for('api_revision_log_by', **params),
        }

    else:
        revisions = rev_get

    result.update({'results': revisions})

    return result


@app.route('/api/1/directory/<string:sha1_git>/')
@app.route('/api/1/directory/<string:sha1_git>/<path:path>/')
@doc.route('/api/1/directory/')
@doc.arg('sha1_git',
         default='1bd0e65f7d2ff14ae994de17a1e7fe65111dcad8',
         argtype=doc.argtypes.sha1_git,
         argdoc='directory identifier')
@doc.arg('path',
         default='codec/demux',
         argtype=doc.argtypes.path,
         argdoc='path relative to directory identified by sha1_git')
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""either a list of directory entries with their metadata,
             or the metadata of a single directory entry""")
def api_directory(sha1_git,
                  path=None):
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


@app.route('/api/1/content/<string:q>/provenance/')
@doc.route('/api/1/content/provenance/', tags=['hidden'])
@doc.arg('q',
         default='sha1_git:88b9b366facda0b5ff8d8640ee9279bed346f242',
         argtype=doc.argtypes.algo_and_hash,
         argdoc=_doc_arg_content_id)
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
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


@app.route('/api/1/content/<string:q>/filetype/')
@doc.route('/api/1/content/filetype/', tags=['upcoming'])
@doc.arg('q',
         default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
         argtype=doc.argtypes.algo_and_hash,
         argdoc=_doc_arg_content_id)
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""Filetype information (dict) for the matched
content.""")
def api_content_filetype(q):
    """Get information about the detected MIME type of a content object.

    """
    return _api_lookup(
        q,
        lookup_fn=service.lookup_content_filetype,
        error_msg_if_not_found='No filetype information found '
        'for content %s.' % q,
        enrich_fn=utils.enrich_metadata_endpoint)


@app.route('/api/1/content/<string:q>/language/')
@doc.route('/api/1/content/language/', tags=['upcoming'])
@doc.arg('q',
         default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
         argtype=doc.argtypes.algo_and_hash,
         argdoc=_doc_arg_content_id)
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""Language information (dict) for the matched
content.""")
def api_content_language(q):
    """Get information about the detected (programming) language of a content
    object.

    """
    return _api_lookup(
        q,
        lookup_fn=service.lookup_content_language,
        error_msg_if_not_found='No language information found '
        'for content %s.' % q,
        enrich_fn=utils.enrich_metadata_endpoint)


@app.route('/api/1/content/<string:q>/license/')
@doc.route('/api/1/content/license/', tags=['upcoming'])
@doc.arg('q',
         default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
         argtype=doc.argtypes.algo_and_hash,
         argdoc=_doc_arg_content_id)
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""License information (dict) for the matched
content.""")
def api_content_license(q):
    """Get information about the detected license of a content object.

    """
    return _api_lookup(
        q,
        lookup_fn=service.lookup_content_license,
        error_msg_if_not_found='No license information found '
        'for content %s.' % q,
        enrich_fn=utils.enrich_metadata_endpoint)


@app.route('/api/1/content/<string:q>/ctags/')
@doc.route('/api/1/content/ctags/', tags=['upcoming'])
@doc.arg('q',
         default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
         argtype=doc.argtypes.algo_and_hash,
         argdoc=_doc_arg_content_id)
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""Ctags symbol (dict) for the matched
content.""")
def api_content_ctags(q):
    """Get information about all `Ctags <http://ctags.sourceforge.net/>`_-style
    symbols defined in a content object.

    """
    return _api_lookup(
        q,
        lookup_fn=service.lookup_content_ctags,
        error_msg_if_not_found='No ctags symbol found '
        'for content %s.' % q,
        enrich_fn=utils.enrich_metadata_endpoint)


@app.route('/api/1/content/<string:q>/raw/')
@doc.route('/api/1/content/raw/', tags=['upcoming'])
@doc.arg('q',
         default='adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
         argtype=doc.argtypes.algo_and_hash,
         argdoc=_doc_arg_content_id)
@doc.param('filename', default=None,
           argtype=doc.argtypes.str,
           doc='User\'s desired filename.')
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.octet_stream,
             retdoc='The raw content data as an octet stream')
def api_content_raw(q):
    """Get the raw content of a content object (AKA "blob"), as a byte sequence.

    """
    def generate(content):
        yield content['data']

    content_raw = service.lookup_content_raw(q)
    if not content_raw:
        raise NotFoundExc('Content %s is not found.' % q)

    content_filetype = service.lookup_content_filetype(q)
    if not content_filetype or 'text/' not in content_filetype['mimetype']:
        raise NotFoundExc('Content %s is not available for download.' % q)

    filename = request.args.get('filename')
    if not filename:
        filename = 'content_%s_raw' % q.replace(':', '_')

    return app.response_class(generate(content_raw),
                              headers={'Content-disposition': 'attachment;'
                                       'filename=%s' % filename},
                              mimetype='application/octet-stream')


@app.route('/api/1/content/<string:q>/')
@doc.route('/api/1/content/')
@doc.arg('q',
         default='adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
         argtype=doc.argtypes.algo_and_hash,
         argdoc=_doc_arg_content_id)
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
@doc.returns(rettype=doc.rettypes.dict,
             retdoc="""known metadata for content identified by q""")
def api_content_metadata(q):
    """Get information about a content (AKA "blob") object.

    """
    return _api_lookup(
        q,
        lookup_fn=service.lookup_content,
        error_msg_if_not_found='Content with %s not found.' % q,
        enrich_fn=utils.enrich_content)


@app.route('/api/1/entity/<string:uuid>/')
@doc.route('/api/1/entity/', tags=['hidden'])
@doc.arg('uuid',
         default='5f4d4c51-498a-4e28-88b3-b3e4e8396cba',
         argtype=doc.argtypes.uuid,
         argdoc="The entity's uuid identifier")
@doc.raises(exc=doc.excs.badinput, doc=_doc_exc_bad_id)
@doc.raises(exc=doc.excs.notfound, doc=_doc_exc_id_not_found)
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
