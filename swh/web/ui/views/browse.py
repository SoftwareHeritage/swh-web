# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import dateutil.parser

from encodings.aliases import aliases
from flask import render_template, request, url_for, redirect

from swh.core.utils import grouper
from swh.model.hashutil import ALGORITHMS
from .. import service, utils
from ..exc import BadInputExc, NotFoundExc
from ..main import app
from . import api


hash_filter_keys = ALGORITHMS


def api_lookup(api_fn, query):
    """Lookup api with api_fn function with parameter query.

    Example:
        filetype = api_lookup('api_content_filetype', 'sha1:blah')
        if filetype:
            content['mimetype'] = filetype['mimetype']
    """
    try:
        return api_fn(query)
    except (NotFoundExc, BadInputExc):
        return None


@app.route('/origin/search/')
def search_origin():
    """
    Redirect request with GET params for an origin to our fragmented URI scheme

    """
    if request.method == 'GET':
        data = request.args
        origin_id = data.get('origin_id')
        if origin_id:
            return redirect(url_for('browse_origin', origin_id=origin_id))
        args = ['origin_type', 'origin_url']
        values = {arg: data.get(arg) for arg in args if data.get(arg)}
        if 'origin_type' in values and 'origin_url' in values:
            return redirect(url_for('browse_origin', **values))


@app.route('/directory/search/')
def search_directory():
    """
    Redirect request with GET params for a directory to our fragmented
    URI scheme

    """

    def url_for_filtered(endpoint, **kwargs):
        """Make url_for ignore keyword args that have an empty string for value
        """
        filtered = {k: v for k, v in kwargs.items() if kwargs[k]}
        return url_for(endpoint, **filtered)

    if request.method == 'GET':
        data = request.args
        sha1_git = data.get('sha1_git')
        if sha1_git:
            if 'dir_path' in data:
                # dir_path exists only in requests for a revision's directory
                return redirect(url_for_filtered(
                    'browse_revision_directory',
                    sha1_git=sha1_git,
                    dir_path=data.get('dir_path')
                ))

            return redirect(url_for_filtered(
                'browse_directory',
                sha1_git=sha1_git,
                path=data.get('path')
            ))

        args = ['origin_id', 'branch_name', 'ts', 'path']
        values = {arg: data.get(arg) for arg in args if data.get(arg)}
        if 'origin_id' in values:
            return redirect(url_for('browse_revision_directory_through_origin',
                                    **values))


@app.route('/revision/search/')
def search_revision():
    """
    Redirect request with GET params for a revision to our fragmented
    URI scheme

    """
    if request.method == 'GET':
        data = request.args
        sha1_git = data.get('sha1_git')
        if sha1_git:
            return redirect(url_for('browse_revision', sha1_git=sha1_git))
        args = ['origin_id', 'branch_name', 'ts']
        values = {arg: data.get(arg) for arg in args if data.get(arg)}
        if 'origin_id' in values:
            return redirect(url_for('browse_revision_with_origin', **values))


@app.route('/content/symbol/', methods=['GET'])
def search_symbol():
    """Search for symbols in contents.

    Returns:
        dict representing data to look for in swh storage.

    """
    env = {
        'result': None,
        'per_page': None,
        'message': '',
        'linknext': None,
        'linkprev': None,
    }

    # Read form or get information
    data = request.args
    q = data.get('q')
    per_page = data.get('per_page')

    env['q'] = q
    if per_page:
        env['per_page'] = per_page

    if q:
        try:
            result = api.api_content_symbol(q)
            if result:
                headers = result.get('headers')
                result = utils.prepare_data_for_view(result['results'])
                env['result'] = result
                if headers:
                    if 'link-next' in headers:
                        next_last_sha1 = result[-1]['sha1']
                        params = {
                            'q': q,
                            'last_sha1': next_last_sha1,
                        }
                        if per_page:
                            params['per_page'] = per_page

                        env['linknext'] = url_for('search_symbol', **params)

        except BadInputExc as e:
            env['message'] = str(e)

    return render_template('symbols.html', **env)


@app.route('/content/search/', methods=['GET', 'POST'])
def search_content():
    """Search for hashes in swh-storage.

    One form to submit either:
    - hash query to look up in swh storage
    - file hashes calculated client-side to be queried in swh storage
    - both

    Returns:
        dict representing data to look for in swh storage.
        The following keys are returned:
        - search_stats: {'nbfiles': X, 'pct': Y} the number of total
        queried files and percentage of files not in storage respectively
        - responses: array of {'filename': X, 'sha1': Y, 'found': Z}
        - messages: General messages.
    TODO:
        Batch-process with all checksums, not just sha1
    """
    env = {'search_res': None,
           'search_stats': None,
           'message': []}

    search_stats = {'nbfiles': 0, 'pct': 0}
    search_res = None
    message = ''

    # Get with a single hash request
    if request.method == 'POST':
        # Post form submission with many hash requests
        q = None
    else:
        data = request.args
        q = data.get('q')

    try:
        search = api.api_check_content_known(q)
        search_res = search['search_res']
        search_stats = search['search_stats']
    except BadInputExc as e:
        message = str(e)

    env['search_stats'] = search_stats
    env['search_res'] = search_res
    env['message'] = message
    return render_template('search.html', **env)


@app.route('/browse/')
def browse():
    """Render the user-facing browse view
    """
    return render_template('browse.html')


@app.route('/browse/content/<string:q>/')
def browse_content(q):
    """Given a hash and a checksum, display the content's meta-data.

    Args:
        q is of the form algo_hash:hash with algo_hash in
        (sha1, sha1_git, sha256)

    Returns:
        Information on one possible origin for such content.

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash
        NotFoundExc if the content is not found.

    """
    env = {'q': q,
           'message': None,
           'content': None}

    encoding = request.args.get('encoding', 'utf8')
    if encoding not in aliases:
        env['message'] = 'Encoding %s not supported.' \
                         'Supported Encodings: %s' % (
                             encoding, list(aliases.keys()))
        return render_template('content.html', **env)

    try:
        content = api.api_content_metadata(q)
        filetype = api_lookup(api.api_content_filetype, q)
        if filetype:
            content['mimetype'] = filetype.get('mimetype')
            content['encoding'] = filetype.get('encoding')
        else:
            content['mimetype'] = None
            content['encoding'] = None

        language = api_lookup(api.api_content_language, q)
        if language:
            content['language'] = language.get('lang')
        else:
            content['language'] = None

        licenses = api_lookup(api.api_content_license, q)
        if licenses:
            content['licenses'] = ', '.join(licenses.get('licenses', []))
        else:
            content['licenses'] = None

        content_raw = service.lookup_content_raw(q)
        if content_raw:
            content['data'] = content_raw['data']
        else:
            content['data'] = None

        ctags = api_lookup(api.api_content_ctags, q)
        if ctags:
            url = url_for('browse_content', q=q)
            content['ctags'] = grouper((
                '<a href="%s#l-%s">%s</a>' % (
                    url,
                    ctag['line'],
                    ctag['line'])
                for ctag in ctags
            ), 20)
        else:
            content['ctags'] = None

        env['content'] = utils.prepare_data_for_view(content,
                                                     encoding=encoding)
    except (NotFoundExc, BadInputExc) as e:
        env['message'] = str(e)

    return render_template('content.html', **env)


@app.route('/browse/content/<string:q>/raw/')
def browse_content_raw(q):
    """Given a hash and a checksum, display the content's raw data.

    Args:
        q is of the form algo_hash:hash with algo_hash in
        (sha1, sha1_git, sha256)

    Returns:
        Information on one possible origin for such content.

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash
        NotFoundExc if the content is not found.

    """
    return redirect(url_for('api_content_raw', q=q))


def _origin_seen(q, data):
    """Given an origin, compute a message string with the right information.

    Args:
        origin: a dictionary with keys:
          - origin: a dictionary with type and url keys
          - occurrence: a dictionary with a validity range

    Returns:
        Message as a string

    """
    origin_type = data['origin_type']
    origin_url = data['origin_url']
    revision = data['revision']
    branch = data['branch']
    path = data['path']

    return """The content with hash %s has been seen on origin with type '%s'
at url '%s'. The revision was identified at '%s' on branch '%s'.
The file's path referenced was '%s'.""" % (q,
                                           origin_type,
                                           origin_url,
                                           revision,
                                           branch,
                                           path)


# @app.route('/browse/content/<string:q>/origin/')
def browse_content_with_origin(q):
    """Show content information.

    Args:
        - q: query string of the form <algo_hash:hash> with
        `algo_hash` in sha1, sha1_git, sha256.

        This means that several different URLs (at least one per
        HASH_ALGO) will point to the same content sha: the sha with
        'hash' format

    Returns:
        The content's information at for a given checksum.

    """
    env = {'q': q}

    try:
        origin = api.api_content_checksum_to_origin(q)
        message = _origin_seen(q, origin)
    except (NotFoundExc, BadInputExc) as e:
        message = str(e)

    env['message'] = message
    return render_template('content-with-origin.html', **env)


@app.route('/browse/directory/<string:sha1_git>/')
@app.route('/browse/directory/<string:sha1_git>/<path:path>/')
def browse_directory(sha1_git, path=None):
    """Show directory information.

    Args:
        - sha1_git: the directory's sha1 git identifier. If path
        is set, the base directory for the relative path to the entry
        - path: the path to the requested entry, relative to
        the directory pointed by sha1_git

    Returns:
        The content's information at sha1_git, or at sha1_git/path if
        path is set.
    """
    env = {'sha1_git': sha1_git,
           'files': []}
    try:
        if path:
            env['message'] = ('Listing for directory with path %s from %s:'
                              % (path, sha1_git))
            dir_or_file = service.lookup_directory_with_path(
                sha1_git, path)
            if dir_or_file['type'] == 'file':
                fsha = 'sha256:%s' % dir_or_file['sha256']
                content = api.api_content_metadata(fsha)
                content_raw = service.lookup_content_raw(fsha)
                if content_raw:  # FIXME: currently assuming utf8 encoding
                    content['data'] = content_raw['data']
                    env['content'] = utils.prepare_data_for_view(
                        content, encoding='utf-8')
                return render_template('content.html', **env)
            else:
                directory_files = api.api_directory(dir_or_file['target'])
                env['files'] = utils.prepare_data_for_view(directory_files)
        else:
            env['message'] = "Listing for directory %s:" % sha1_git
            directory_files = api.api_directory(sha1_git)
        env['files'] = utils.prepare_data_for_view(directory_files)
    except (NotFoundExc, BadInputExc) as e:
        env['message'] = str(e)

    return render_template('directory.html', **env)


@app.route('/browse/origin/<string:origin_type>/url/<path:origin_url>/')
@app.route('/browse/origin/<int:origin_id>/')
def browse_origin(origin_id=None, origin_type=None, origin_url=None):
    """Browse origin matching given criteria - either origin_id or
    origin_type and origin_path.

    Args:
        - origin_id: origin's swh identifier
        - origin_type: origin's type
        - origin_url: origin's URL
    """
    # URLs for the calendar JS plugin
    env = {'browse_url': None,
           'visit_url': None,
           'origin': None}

    try:
        origin = api.api_origin(origin_id, origin_type, origin_url)
        env['origin'] = origin
        env['browse_url'] = url_for('browse_revision_with_origin',
                                    origin_id=origin['id'])
        env['visit_url'] = url_for('browse_origin_visits',
                                   origin_id=origin['id'])

    except (NotFoundExc, BadInputExc) as e:
        env['message'] = str(e)

    return render_template('origin.html', **env)


@app.route('/browse/origin/<int:origin_id>/visits/')
def browse_origin_visits(origin_id):
    origin = api.api_origin_visits(origin_id)['results']
    for v in origin:
        v['date'] = dateutil.parser.parse(v['date']).timestamp()
    return origin


@app.route('/browse/person/<int:person_id>/')
def browse_person(person_id):
    """Browse person with id id.

    """
    env = {'person_id': person_id,
           'person': None,
           'message': None}

    try:
        env['person'] = api.api_person(person_id)
    except (NotFoundExc, BadInputExc) as e:
        env['message'] = str(e)

    return render_template('person.html', **env)


@app.route('/browse/release/<string:sha1_git>/')
def browse_release(sha1_git):
    """Browse release with sha1_git.

    """
    env = {'sha1_git': sha1_git,
           'message': None,
           'release': None}

    try:
        rel = api.api_release(sha1_git)
        env['release'] = utils.prepare_data_for_view(rel)
    except (NotFoundExc, BadInputExc) as e:
        env['message'] = str(e)

    return render_template('release.html', **env)


@app.route('/browse/revision/<string:sha1_git>/')
@app.route('/browse/revision/<string:sha1_git>/prev/<path:prev_sha1s>/')
def browse_revision(sha1_git, prev_sha1s=None):
    """Browse the revision with git SHA1 sha1_git_cur, while optionally keeping
    the context from which we came as a list of previous (i.e. later)
    revisions' sha1s.

    Args:
        sha1_git: the requested revision's sha1_git.
        prev_sha1s: an optional string of /-separated sha1s representing our
        context, ordered by descending revision date.

    Returns:
        Information about revision of git SHA1 sha1_git_cur, with relevant URLS
        pointing to the context augmented with sha1_git_cur.

    Example:
        GET /browse/revision/
    """
    env = {'sha1_git': sha1_git,
           'message': None,
           'revision': None}

    try:
        rev = api.api_revision(sha1_git, prev_sha1s)
        env['revision'] = utils.prepare_data_for_view(rev)
    except (NotFoundExc, BadInputExc) as e:
        env['message'] = str(e)
    return render_template('revision.html', **env)


@app.route('/browse/revision/<string:sha1_git>/raw/')
def browse_revision_raw_message(sha1_git):
    """Given a sha1_git, display the corresponding revision's raw message.

    """
    return redirect(url_for('api_revision_raw_message', sha1_git=sha1_git))


@app.route('/browse/revision/<string:sha1_git>/log/')
@app.route('/browse/revision/<string:sha1_git>/prev/<path:prev_sha1s>/log/')
def browse_revision_log(sha1_git, prev_sha1s=None):
    """Browse revision with sha1_git's log. If the navigation path through the
    commit tree is specified, we intersect the earliest revision's log with the
    revisions the user browsed through - ie the path taken to the specified
    revision.

    Args:
        sha1_git: the current revision's SHA1_git checksum
        prev_sha1s: optionally, the path through which we want log information
    """
    env = {'sha1_git': sha1_git,
           'sha1_url': '/browse/revision/%s/' % sha1_git,
           'message': None,
           'revisions': []}

    try:
        revision_data = api.api_revision_log(sha1_git, prev_sha1s)
        revisions = revision_data['revisions']
        next_revs_url = revision_data['next_revs_url']
        env['revisions'] = map(utils.prepare_data_for_view, revisions)
        env['next_revs_url'] = utils.prepare_data_for_view(next_revs_url)

    except (NotFoundExc, BadInputExc) as e:
        env['message'] = str(e)

    return render_template('revision-log.html', **env)


@app.route('/browse/revision'
           '/origin/<int:origin_id>/log/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>/log/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/ts/<string:ts>/log/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/ts/<string:ts>/log/')
def browse_revision_log_by(origin_id,
                           branch_name='refs/heads/master',
                           timestamp=None):
    """Browse the revision described by origin, branch name and timestamp's
    log

    Args:
        origin_id: the revision's origin
        branch_name: the revision's branch
        timestamp: the requested timeframe for the revision

    Returns:
        The revision log of the described revision as a list of revisions
        if it is found.
    """
    env = {'sha1_git': None,
           'origin_id': origin_id,
           'origin_url': '/browse/origin/%d/' % origin_id,
           'branch_name': branch_name,
           'timestamp': timestamp,
           'message': None,
           'revisions': []}

    try:
        revisions = api.api_revision_log_by(
            origin_id, branch_name, timestamp)
        env['revisions'] = map(utils.prepare_data_for_view, revisions)
    except (NotFoundExc, BadInputExc) as e:
        env['message'] = str(e)

    return render_template('revision-log.html', **env)


@app.route('/browse/revision/<string:sha1_git_cur>/prev/<path:sha1s>/')
def browse_with_rev_context(sha1_git_cur, sha1s):
    """Browse the revision with git SHA1 sha1_git_cur, while keeping the context
    from which we came as a list of previous  (i.e. later) revisions' sha1s.

    Args:
        sha1_git_cur: the requested revision's sha1_git.
        sha1s: a string of /-separated sha1s representing our context, ordered
        by descending revision date.

    Returns:
        Information about revision of git SHA1 sha1_git_cur, with relevant URLS
        pointing to the context augmented with sha1_git_cur.

    Example:
        GET /browse/revision/
    """
    env = {'sha1_git': sha1_git_cur,
           'message': None,
           'revision': None}

    try:
        revision = api.api_revision(
            sha1_git_cur, sha1s)
        env['revision'] = utils.prepare_data_for_view(revision)
    except (BadInputExc, NotFoundExc) as e:
        env['message'] = str(e)

    return render_template('revision.html', **env)


@app.route('/browse/revision/<string:sha1_git_root>/history/<sha1_git>/')
def browse_revision_history(sha1_git_root, sha1_git):
    """Display information about revision sha1_git, limited to the
    sub-graph of all transitive parents of sha1_git_root.

    In other words, sha1_git is an ancestor of sha1_git_root.

    Args:
        sha1_git_root: latest revision of the browsed history.
        sha1_git: one of sha1_git_root's ancestors.
        limit: optional query parameter to limit the revisions log
        (default to 100). For now, note that this limit could impede the
        transitivity conclusion about sha1_git not being an ancestor of
        sha1_git_root (even if it is).

    Returns:
        Information on sha1_git if it is an ancestor of sha1_git_root
        including children leading to sha1_git_root.

    """
    env = {'sha1_git_root': sha1_git_root,
           'sha1_git': sha1_git,
           'message': None,
           'keys': [],
           'revision': None}

    if sha1_git == sha1_git_root:
        return redirect(url_for('browse_revision',
                                sha1_git=sha1_git))

    try:
        revision = api.api_revision_history(sha1_git_root,
                                            sha1_git)
        env['revision'] = utils.prepare_data_for_view(revision)
    except (BadInputExc, NotFoundExc) as e:
        env['message'] = str(e)

    return render_template('revision.html', **env)


@app.route('/browse/revision/<string:sha1_git>/directory/')
@app.route('/browse/revision/<string:sha1_git>/directory/<path:dir_path>/')
def browse_revision_directory(sha1_git, dir_path=None):
    """Browse directory from revision with sha1_git.

    """
    env = {
        'sha1_git': sha1_git,
        'path': '.' if not dir_path else dir_path,
        'message': None,
        'result': None
    }

    encoding = request.args.get('encoding', 'utf8')
    if encoding not in aliases:
        env['message'] = 'Encoding %s not supported.' \
                         'Supported Encodings: %s' % (
                             encoding, list(aliases.keys()))
        return render_template('revision-directory.html', **env)

    try:
        result = api.api_revision_directory(sha1_git, dir_path, with_data=True)
        result['content'] = utils.prepare_data_for_view(result['content'],
                                                        encoding=encoding)
        env['revision'] = result['revision']
        env['result'] = result
    except (BadInputExc, NotFoundExc) as e:
        env['message'] = str(e)

    return render_template('revision-directory.html', **env)


@app.route('/browse/revision/<string:sha1_git_root>'
           '/history/<sha1_git>'
           '/directory/')
@app.route('/browse/revision/<string:sha1_git_root>'
           '/history/<sha1_git>'
           '/directory/<path:path>/')
def browse_revision_history_directory(sha1_git_root, sha1_git, path=None):
    """Return information about directory pointed to by the revision
    defined as: revision sha1_git, limited to the sub-graph of all
    transitive parents of sha1_git_root.

    Args:
        sha1_git_root: latest revision of the browsed history.
        sha1_git: one of sha1_git_root's ancestors.
        path: optional directory pointed to by that revision.
        limit: optional query parameter to limit the revisions log
        (default to 100). For now, note that this limit could impede the
        transitivity conclusion about sha1_git not being an ancestor of
        sha1_git_root (even if it is).

    Returns:
        Information on the directory pointed to by that revision.

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash.
        NotFoundExc if either revision is not found or if sha1_git is not an
        ancestor of sha1_git_root or the path referenced does not exist

    """
    env = {
        'sha1_git_root': sha1_git_root,
        'sha1_git': sha1_git,
        'path': '.' if not path else path,
        'message': None,
        'result': None
    }

    encoding = request.args.get('encoding', 'utf8')
    if encoding not in aliases:
        env['message'] = 'Encoding %s not supported.' \
                         'Supported Encodings: %s' % (
                             encoding, list(aliases.keys()))
        return render_template('revision-directory.html', **env)

    if sha1_git == sha1_git_root:
        return redirect(url_for('browse_revision_directory',
                                sha1_git=sha1_git,
                                path=path,
                                encoding=encoding),
                        code=301)

    try:
        result = api.api_revision_history_directory(sha1_git_root,
                                                    sha1_git,
                                                    path,
                                                    with_data=True)
        env['revision'] = result['revision']
        env['content'] = utils.prepare_data_for_view(result['content'],
                                                     encoding=encoding)
        env['result'] = result
    except (BadInputExc, NotFoundExc) as e:
        env['message'] = str(e)

    return render_template('revision-directory.html', **env)


@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/history/<sha1_git>'
           '/directory/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/history/<sha1_git>'
           '/directory/<path:path>/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/history/<sha1_git>'
           '/directory/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/history/<sha1_git>'
           '/directory/<path:path>/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/ts/<string:ts>'
           '/history/<sha1_git>'
           '/directory/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/ts/<string:ts>'
           '/history/<sha1_git>'
           '/directory/<path:path>/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/ts/<string:ts>'
           '/history/<sha1_git>'
           '/directory/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/ts/<string:ts>'
           '/history/<sha1_git>'
           '/directory/<path:path>/')
def browse_directory_through_revision_with_origin_history(
        origin_id,
        branch_name="refs/heads/master",
        ts=None,
        sha1_git=None,
        path=None):
    env = {
        'origin_id': origin_id,
        'branch_name': branch_name,
        'ts': ts,
        'sha1_git': sha1_git,
        'path': '.' if not path else path,
        'message': None,
        'result': None
    }

    encoding = request.args.get('encoding', 'utf8')
    if encoding not in aliases:
        env['message'] = (('Encoding %s not supported.'
                           'Supported Encodings: %s') % (
                            encoding, list(aliases.keys())))
        return render_template('revision-directory.html', **env)

    try:
        result = api.api_directory_through_revision_with_origin_history(
            origin_id, branch_name, ts, sha1_git, path, with_data=True)
        env['revision'] = result['revision']
        env['content'] = utils.prepare_data_for_view(result['content'],
                                                     encoding=encoding)
        env['result'] = result
    except (BadInputExc, NotFoundExc) as e:
        env['message'] = str(e)

    return render_template('revision-directory.html', **env)


@app.route('/browse/revision'
           '/origin/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/ts/<string:ts>/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/ts/<string:ts>/')
def browse_revision_with_origin(origin_id,
                                branch_name="refs/heads/master",
                                ts=None):
    """Instead of having to specify a (root) revision by SHA1_GIT, users
    might want to specify a place and a time. In SWH a "place" is an
    origin; a "time" is a timestamp at which some place has been
    observed by SWH crawlers.

    Args:
        origin_id: origin's identifier (default to 1).
        branch_name: the optional branch for the given origin (default
        to master).
        timestamp: optional timestamp (default to the nearest time
        crawl of timestamp).

    Returns:
        Information on the revision if found.

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash.
        NotFoundExc if the revision is not found.

    """
    env = {'message': None,
           'revision': None}
    try:
        revision = api.api_revision_with_origin(origin_id,
                                                branch_name,
                                                ts)
        env['revision'] = utils.prepare_data_for_view(revision)
    except (ValueError, NotFoundExc, BadInputExc) as e:
        env['message'] = str(e)

    return render_template('revision.html', **env)


@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/history/<sha1_git>/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/history/<sha1_git>/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/ts/<string:ts>'
           '/history/<sha1_git>/')
def browse_revision_history_through_origin(origin_id,
                                           branch_name='refs/heads/master',
                                           ts=None,
                                           sha1_git=None):
    """Return information about revision sha1_git, limited to the
    sub-graph of all transitive parents of the revision root identified
    by (origin_id, branch_name, ts).
    Given sha1_git_root such root revision's identifier, in other words,
    sha1_git is an ancestor of sha1_git_root.

    Args:
        origin_id: origin's identifier (default to 1).
        branch_name: the optional branch for the given origin (default
        to master).
        timestamp: optional timestamp (default to the nearest time
        crawl of timestamp).
        sha1_git: one of sha1_git_root's ancestors.
        limit: optional query parameter to limit the revisions log
        (default to 100). For now, note that this limit could impede the
        transitivity conclusion about sha1_git not being an ancestor of
        sha1_git_root (even if it is).

    Returns:
        Information on sha1_git if it is an ancestor of sha1_git_root
        including children leading to sha1_git_root.

    """
    env = {'message': None,
           'revision': None}
    try:
        revision = api.api_revision_history_through_origin(
            origin_id,
            branch_name,
            ts,
            sha1_git)
        env['revision'] = utils.prepare_data_for_view(revision)
    except (ValueError, BadInputExc, NotFoundExc) as e:
        env['message'] = str(e)

    return render_template('revision.html', **env)


@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/directory/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/directory/<path:path>')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/directory/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/directory/<path:path>/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/ts/<string:ts>'
           '/directory/')
@app.route('/browse/revision'
           '/origin/<int:origin_id>'
           '/branch/<path:branch_name>'
           '/ts/<string:ts>'
           '/directory/<path:path>/')
def browse_revision_directory_through_origin(origin_id,
                                             branch_name='refs/heads/master',
                                             ts=None,
                                             path=None):

    env = {'message': None,
           'origin_id': origin_id,
           'ts': ts,
           'path': '.' if not path else path,
           'result': None}

    encoding = request.args.get('encoding', 'utf8')
    if encoding not in aliases:
        env['message'] = 'Encoding %s not supported.' \
                         'Supported Encodings: %s' % (
                             encoding, list(aliases.keys()))
        return render_template('revision-directory.html', **env)

    try:
        result = api.api_directory_through_revision_origin(
            origin_id,
            branch_name,
            ts,
            path,
            with_data=True)

        result['content'] = utils.prepare_data_for_view(result['content'],
                                                        encoding=encoding)
        env['revision'] = result['revision']
        env['result'] = result
    except (ValueError, BadInputExc, NotFoundExc) as e:
        env['message'] = str(e)

    return render_template('revision-directory.html', **env)


@app.route('/browse/entity/')
@app.route('/browse/entity/<string:uuid>/')
def browse_entity(uuid):
    env = {'entities': [],
           'message': None}

    try:
        entities = api.api_entity_by_uuid(uuid)
        env['entities'] = entities
    except (NotFoundExc, BadInputExc) as e:
        env['message'] = str(e)

    return render_template('entity.html', **env)
