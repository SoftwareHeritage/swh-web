# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from flask import render_template, request, flash, url_for

from flask.ext.api.decorators import set_renderers
from flask.ext.api.renderers import HTMLRenderer

from swh.core.hashutil import ALGORITHMS
from swh.web.ui.main import app
from swh.web.ui import service, renderers, utils
from swh.web.ui.exc import BadInputExc, NotFoundExc


hash_filter_keys = ALGORITHMS


@app.route('/')
@set_renderers(HTMLRenderer)
def main():
    """Home page

    """
    flash('This Web app is still work in progress, use at your own risk',
          'warning')
    # return redirect(url_for('about'))
    return render_template('home.html')


@app.route('/about')
@set_renderers(HTMLRenderer)
def about():
    return render_template('about.html')


@app.route('/search')
@set_renderers(HTMLRenderer)
def search():
    """Search for hashes in swh-storage.

    """
    q = request.args.get('q', '')
    env = {'q': q, 'message': '', 'found': None}

    try:
        if q:
            env.update(service.lookup_hash(q))
    except BadInputExc:
        env['message'] = 'Error: invalid query string'

    return render_template('search.html', **env)


@app.route('/uploadnsearch', methods=['GET', 'POST'])
@set_renderers(HTMLRenderer)
def uploadnsearch():
    """Upload and search for hashes in swh-storage.

    """
    env = {'filename': None, 'message': '', 'found': None}

    if request.method == 'POST':
        file = request.files['filename']
        try:
            filename, sha1, found = service.upload_and_search(file)
            message = 'The file %s with hash %s has%sbeen found.' % (
                filename,
                sha1,
                ' ' if found else ' not ')

            env.update({
                'filename': filename,
                'sha1': sha1,
                'found': found,
                'message': message
            })
        except BadInputExc:
            env['message'] = 'Error: invalid query string'

    return render_template('upload_and_search.html', **env)


def _origin_seen(hash, data):
    """Given an origin, compute a message string with the right information.

    Args:
        origin: a dictionary with keys:
          - origin: a dictionary with type and url keys
          - occurrence: a dictionary with a validity range

    Returns:
        message as a string

    """
    if data is None:
        return 'Content with hash %s is unknown as of now.' % hash

    origin_type = data['origin_type']
    origin_url = data['origin_url']
    revision = data['revision']
    branch = data['branch']
    path = data['path']

    return """The content with hash %s has been seen on origin with type '%s'
at url '%s'. The revision was identified at '%s' on branch '%s'.
The file's path referenced was '%s'.""" % (hash,
                                           origin_type,
                                           origin_url,
                                           revision,
                                           branch,
                                           path)


@app.route('/browse/content/<string:q>')
@set_renderers(HTMLRenderer)
def content_with_origin(q):
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
        content = service.lookup_hash(q)
        found = content['found']

        if not found:
            message = "Hash %s was not found." % content['algo']
        else:
            origin = service.lookup_hash_origin(q)
            message = _origin_seen(hash, origin)
    except BadInputExc as e:  # do not like it but do not duplicate code
        message = e

    env['message'] = message
    return render_template('content.html', **env)


@app.route('/api')
@app.route('/api/')
def api_main_points():
    """List the current api endpoints starting with /api/.

    """
    return utils.filter_endpoints(app.url_map, '/api', blacklist=['/api/'])


@app.route('/api/1')
@app.route('/api/1/')
def api_main_points_v1():
    """List the current api v1 endpoints starting with /api/.

    """
    return utils.filter_endpoints(app.url_map, '/api/1',
                                  blacklist=['/api/1/'])


@app.route('/api/1/stat/counters')
def api_stats():
    """Return statistics as a JSON object"""
    return service.stat_counters()


@app.errorhandler(ValueError)
def value_error_as_bad_request(error):
    """Compute a bad request and add body as payload.

    """
    return renderers.error_response('Bad request', 400, error)


@app.errorhandler(NotFoundExc)
def value_not_found(error):
    """Compute a not found and add body as payload.

    """
    return renderers.error_response('Not found', 404, error)


@app.route('/api/1/search/<string:q>')
def api_search(q):
    """Return search results as a JSON object"""
    return {'found': service.lookup_hash(q)}


def _api_lookup(criteria, lookup_fn, error_msg_if_not_found):
    """Factorize function regarding the api to lookup for data."""
    res = lookup_fn(criteria)
    if not res:
        raise NotFoundExc(error_msg_if_not_found)
    return res


@app.route('/api/1/origin/<int:origin_id>')
def api_origin(origin_id):
    """Return information about origin."""
    return _api_lookup(
        origin_id, lookup_fn=service.lookup_origin,
        error_msg_if_not_found='Origin with id %s not found.' % origin_id)


@app.route('/api/1/person/<int:person_id>')
def api_person(person_id):
    """Return information about person."""
    return _api_lookup(
        person_id, lookup_fn=service.lookup_person,
        error_msg_if_not_found='Person with id %s not found.' % person_id)


@app.route('/api/1/release/<string:sha1_git>')
def api_release(sha1_git):
    """Return information about release with id sha1_git."""
    error_msg = 'Release with sha1_git %s not found.' % sha1_git
    return _api_lookup(
        sha1_git,
        lookup_fn=service.lookup_release,
        error_msg_if_not_found=error_msg)


@app.route('/api/1/revision/<string:sha1_git>')
def api_revision(sha1_git):
    """Return information about revision with id sha1_git.

    """
    error_msg = 'Revision with sha1_git %s not found.' % sha1_git
    return _api_lookup(
        sha1_git,
        lookup_fn=service.lookup_revision,
        error_msg_if_not_found=error_msg)


@app.route('/api/1/directory/<string:sha1_git>')
def api_directory(sha1_git):
    """Return information about release with id sha1_git."""
    directory_entries = service.lookup_directory(sha1_git)
    if not directory_entries:
        raise NotFoundExc('Directory with sha1_git %s not found.' % sha1_git)
    return list(directory_entries)


@app.route('/api/1/browse/<string:q>')
def api_content_checksum_to_origin(q):
    """Return content information up to one of its origin if the content
    is found.

    Args:
        q is of the form algo_hash:hash with algo_hash in
        (sha1, sha1_git, sha256)

    Returns:
        Information on one possible origin for such content.

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash
        NotFoundExc if the content is not found.

    """
    found = service.lookup_hash(q)['found']
    if not found:
        raise NotFoundExc('Content with %s not found.' % q)

    return service.lookup_hash_origin(q)


@app.route('/api/1/content/<string:q>/raw')
@set_renderers(renderers.PlainRenderer)
def api_content_raw(q):
    """Return content information on the content with provided hash.

    Args:
        q is of the form (algo_hash:)hash with algo_hash in
        (sha1, sha1_git, sha256).
        If no algo_hash is provided, will work with default sha1
        algorithm

    Actual limitation:
        Only works with current sha1

    Raises:
        - BadInputExc in case of unknown algo_hash or bad hash
        - NotFoundExc if the content is not found.

    """
    content = service.lookup_content_raw(q)
    if not content:
        raise NotFoundExc('Content with %s not found.' % q)

    return content['data']


@app.route('/api/1/content/<string:q>')
def api_content_with_details(q):
    """Return content information on the content with provided hash.

    Args:
        q is of the form (algo_hash:)hash with algo_hash in
        (sha1, sha1_git, sha256).
        If no algo_hash is provided, will work with default sha1
        algorithm

    Actual limitation:
        Only works with current sha1

    Raises:
        - BadInputExc in case of unknown algo_hash or bad hash
        - NotFoundExc if the content is not found.

    """
    content = service.lookup_content(q)
    if not content:
        raise NotFoundExc('Content with %s not found.' % q)

    content['data'] = url_for('api_content_raw', q=content['sha1'])
    return content


@app.route('/api/1/uploadnsearch', methods=['POST'])
def api_uploadnsearch():
    """Upload the file's content in the post body request.
       Compute the hash and determine if it exists in the storage.
    """
    file = request.files['filename']
    filename, sha1, found = service.upload_and_search(file)
    return {'sha1': sha1,
            'filename': filename,
            'found': found}
