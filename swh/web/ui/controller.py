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
    except ValueError:
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
        except ValueError:
            env['message'] = 'Error: invalid query string'

    return render_template('upload_and_search.html', **env)


@app.route('/browse/revision/<sha1_git>')
def revision(sha1_git):
    """Show commit information.

    Args:
        sha1_git: the revision's sha1

    Returns:
        Revision information
    """
    return render_template('revision.html',
                           sha1_git=sha1_git)


@app.route('/browse/directory/<sha1_git>')
def directory(sha1_git):
    """Show directory information.

    Args:
        sha1_git: the directory's sha1

    Returns:
        Directory information
    """
    return render_template('directory.html',
                           sha1_git=sha1_git)


@app.route('/browse/directory/<sha1_git>/<path:p>')
def directory_at_path(sha1_git, p):
    """Show directory information for the sha1_git at path.

    Args:
        sha1_git: the directory's sha1
        path: file or directory pointed to

    Returns:
        Directory information at sha1_git + path
    """
    return render_template('directory.html',
                           sha1_git=sha1_git,
                           path=p)


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


@app.route('/browse/release/<sha1_git>')
def release(sha1_git):
    """Show release's information.

    Args:
        sha1_git: sha1_git for this particular release

    Returns:
        Release's information

    """
    return 'Release information at %s' % sha1_git


@app.route('/browse/person/<int:id>')
def person(id):
    """Show Person's information at id.

    Args:
        id: person's unique identifier

    Returns:
        Person's information

    """
    return 'Person information at %s' % id


@app.route('/browse/origin/<int:id>')
def origin(id):
    """Show origin's information at id.

    Args:
        id: origin's unique identifier

    Returns:
        Origin's information

    """
    return 'Origin information at %s' % id


@app.route('/browse/project/<int:id>')
def project(id):
    """Show project's information at id.

    Args:
        id: project's unique identifier

    Returns:
        Project's information

    """
    return 'Project information at %s' % id


@app.route('/browse/organization/<int:id>')
def organization(id):
    """Show organization's information at id.

    Args:
        id: organization's unique identifier

    Returns:
        Organization's information

    """
    return 'Organization information at %s' % id


@app.route('/browse/directory/<string:timestamp>/'
           '<string:origin_type>+<path:origin_url>|/'
           '<path:branch>|/<path:path>')
def directory_at_origin(timestamp, origin_type, origin_url, branch, path):
    """Show directory information at timestamp, origin-type, origin-url, branch
    and path.

    Those parameters are separated by the `|` terminator.

    Args:
        timestamp: the timestamp to look for. can be latest or some iso8601
    date format. (TODO: decide the time matching policy.)
        origin_type: origin's type
        origin_url: origin's url (can contain `/`)
        branch: branch name which can contain `/`
        path: path to directory or file

    Returns:
        Directory information at the given parameters.

    """
    return 'Directory at (%s, %s, %s, %s, %s)' % (timestamp,
                                                  origin_type,
                                                  origin_url,
                                                  branch,
                                                  path)


@app.route('/browse/revision/<string:timestamp>/'
           '<string:origin_type>+<path:origin_url>|/<path:branch>')
def revision_at_origin_and_branch(timestamp, origin_type, origin_url, branch):
    """Show revision information at timestamp, origin, and branch.

    Those parameters are separated by the `|` terminator.

    Args:
        timestamp: the timestamp to look for. can be latest or some iso8601
    date format. (TODO: decide the time matching policy.)
        origin_type: origin's type
        origin_url: origin's url (can contain `/`)
        branch: branch name which can contain /

    Returns:
        Revision information at the given parameters.

    """
    return 'Revision at (ts=%s, type=%s, url=%s, branch=%s)' % (timestamp,
                                                                origin_type,
                                                                origin_url,
                                                                branch)


@app.route('/browse/revision/<string:timestamp>/'
           '<string:origin_type>+<path:origin_url>|')
def revision_at_origin(timestamp, origin_type, origin_url):
    """Show revision information at timestamp, origin, and branch.

    Those parameters are separated by the `|` terminator.

    Args:
        timestamp: the timestamp to look for. can be latest or iso8601
        date
        format. (TODO: decide the time matching policy.)
        origin_type: origin's type
        origin_url: origin's url (can contain `/`)

    Returns:
        Revision information at the given parameters.

    """
    return 'Revision at (timestamp=%s, type=%s, url=%s)' % (timestamp,
                                                            origin_type,
                                                            origin_url)


@app.route('/api/1/stat/counters')
@jsonp
def api_stats():
    """Return statistics as a JSON object"""
    return jsonify(service.stat_counters())


@app.errorhandler(ValueError)
def value_error_as_bad_request(error):
    """Compute a bad request and add body as payload.

    """
    response = make_response(
        'Bad request',
        400)
    response.headers['Content-Type'] = 'application/json'
    response.data = json.dumps({"error": str(error)})
    return response


@app.route('/api/1/search/<string:q>/')
@jsonp
def api_search(q):
    """Return search results as a JSON object"""
    return jsonify({'found': service.lookup_hash(q)})


@app.route('/api/1/browse/<string:q>/')
@jsonp
def api_browse(q):
    """Return search results as a JSON object"""
    return jsonify({'origin': service.lookup_hash_origin(q)})


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
