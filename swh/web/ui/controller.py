# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


import json

from flask import render_template, jsonify, request, flash
from flask import make_response

from swh.core.hashutil import ALGORITHMS
from swh.web.ui.main import app
from swh.web.ui import service
from swh.web.ui.decorators import jsonp
from swh.web.ui.exc import BadInputExc, NotFoundExc


hash_filter_keys = ALGORITHMS


@app.route('/')
def main():
    """Home page

    """
    flash('This Web app is still work in progress, use at your own risk',
          'warning')
    # return redirect(url_for('about'))
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/search')
def search():
    """Search for hashes in swh-storage.

    """
    q = request.args.get('q', '')
    env = {'q': q, 'message': '', 'found': None}

    try:
        if q:
            env['found'] = service.lookup_hash(q)
    except BadInputExc:
        env['message'] = 'Error: invalid query string'

    return render_template('search.html', **env)


@app.route('/uploadnsearch', methods=['GET', 'POST'])
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


@app.route('/browse/content/<hash>:<sha>')
def content(hash, sha):
    """Show content information.

    Args:
        hash: hash according to HASH_ALGO, where HASH_ALGO is
    one of: sha1, sha1_git, sha256. This means that several different URLs (at
    least one per HASH_ALGO) will point to the same content
        sha: the sha with 'hash' format

    Returns:
        The content's information at sha1_git

    """
    if hash not in hash_filter_keys:
        message = 'The checksum must be one of sha1, sha1_git, sha256'
    else:
        q = "%s:%s" % (hash, sha)
        found = service.lookup_hash(q)
        if not found:
            message = "Hash %s was not found." % hash
        else:
            origin = service.lookup_hash_origin(q)
            message = _origin_seen(hash, origin)

    return render_template('content.html',
                           hash=hash,
                           sha=sha,
                           message=message)


@app.route('/api/1/stat/counters')
@jsonp
def api_stats():
    """Return statistics as a JSON object"""
    return jsonify(service.stat_counters())


def _make_error_response(default_error_msg, error_code, error):
    """Private function to create a custom error response.

    """
    response = make_response(default_error_msg, error_code)
    response.headers['Content-Type'] = 'application/json'
    response.data = json.dumps({"error": str(error)})
    return response


@app.errorhandler(ValueError)
def value_error_as_bad_request(error):
    """Compute a bad request and add body as payload.

    """
    return _make_error_response('Bad request', 400, error)


@app.errorhandler(NotFoundExc)
def value_not_found(error):
    """Compute a not found and add body as payload.

    """
    return _make_error_response('Not found', 404, error)


@app.route('/api/1/search/<string:q>/')
@jsonp
def api_search(q):
    """Return search results as a JSON object"""
    return jsonify({'found': service.lookup_hash(q)})


def _api_lookup(criteria, lookup_fn, error_msg_if_not_found):
    """Factorize function regarding the api to lookup for data."""
    res = lookup_fn(criteria)
    if not res:
        raise NotFoundExc(error_msg_if_not_found)
    return jsonify(res)


@app.route('/api/1/origin/<int:origin_id>')
@jsonp
def api_origin(origin_id):
    """Return information about origin."""
    return _api_lookup(
        origin_id, lookup_fn=service.lookup_origin,
        error_msg_if_not_found='Origin with id %s not found.' % origin_id)


@app.route('/api/1/person/<int:person_id>')
@jsonp
def api_person(person_id):
    """Return information about person."""
    return _api_lookup(
        person_id, lookup_fn=service.lookup_person,
        error_msg_if_not_found='Person with id %s not found.' % person_id)


@app.route('/api/1/release/<string:sha1_git>')
@jsonp
def api_release(sha1_git):
    """Return information about release with id sha1_git."""
    error_msg = 'Release with sha1_git %s not found.' % sha1_git
    return _api_lookup(
        sha1_git,
        lookup_fn=service.lookup_release,
        error_msg_if_not_found=error_msg)


@app.route('/api/1/revision/<string:sha1_git>')
@jsonp
def api_revision(sha1_git):
    """Return information about revision with id sha1_git.

    """
    error_msg = 'Revision with sha1_git %s not found.' % sha1_git
    return _api_lookup(
        sha1_git,
        lookup_fn=service.lookup_revision,
        error_msg_if_not_found=error_msg)


@app.route('/api/1/directory/<string:sha1_git>')
@jsonp
def api_directory(sha1_git):
    """Return information about release with id sha1_git."""
    recursive_flag = request.args.get('recursive', False)
    directory_entries = service.lookup_directory(sha1_git,
                                                 recursive_flag)
    if not directory_entries:
        raise NotFoundExc('Directory with sha1_git %s not found.' % sha1_git)
    return jsonify({'directory_entries': list(directory_entries)})


@app.route('/api/1/content/<string:q>/')
@jsonp
def api_content_with_details(q):
    """Return content information up to its origin if found.

    Args:
        q is of the form algo_hash:hash

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash
        NotFoundExc if the content is not found.

    """
    content = service.lookup_content(q)
    if not content:
        raise NotFoundExc('Content with %s not found.' % q)

    origin_detail = service.lookup_hash_origin(q)
    output = {'origin': origin_detail if origin_detail else None}
    for key, value in content.items():
        output[key] = value
    return jsonify(output)


@app.route('/api/1/uploadnsearch/', methods=['POST'])
@jsonp
def api_uploadnsearch():
    """Upload the file's content in the post body request.
       Compute the hash and determine if it exists in the storage.
    """
    file = request.files['filename']
    filename, sha1, found = service.upload_and_search(file)
    return jsonify({'sha1': sha1,
                    'filename': filename,
                    'found': found})
