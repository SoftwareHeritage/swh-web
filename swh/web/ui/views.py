# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from flask import render_template, flash, request, url_for

from flask.ext.api.decorators import set_renderers
from flask.ext.api.renderers import HTMLRenderer

from swh.core.hashutil import ALGORITHMS
from swh.web.ui import service
from swh.web.ui.exc import BadInputExc
from swh.web.ui.main import app


hash_filter_keys = ALGORITHMS


@app.route('/')
@set_renderers(HTMLRenderer)
def homepage():
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
    env = {'q': q, 'message': ''}

    try:
        if q:
            r = service.lookup_hash(q)
            env['message'] = 'Content with hash %s%sfound!' % (
                q, ''
                if r['found'] == True else ' not ')

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


@app.route('/browse/content/<string:q>/raw')
@set_renderers(HTMLRenderer)
def show_content(q):
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
    env = {}
    try:
        content = service.lookup_content_raw(q)
        if content is None:
            message = 'Content with %s not found.'

        message = 'Content %s' % content['sha1']
        env['content'] = content
    except BadInputExc as e:
        message = e

    env['message'] = message
    return render_template('display_content.html', **env)


def prepare_directory_listing(files):
    """Given a list of dictionary files, return a view ready dictionary.

    """
    ls = []
    for entry in files:
        new_entry = {}
        if entry['type'] == 'dir':
            new_entry['link'] = url_for('browse_directory',
                                        sha1_git=entry['target'])
        else:
            new_entry['link'] = url_for('show_content',
                                        q=entry['sha1'])
        new_entry['name'] = entry['name']
        ls.append(new_entry)

    return ls


@app.route('/browse/directory/<string:sha1_git>')
@set_renderers(HTMLRenderer)
def browse_directory(sha1_git):
    """Show directory information.

    Args:
        - sha1_git: the directory's sha1 git identifier.

    Returns:
        The content's information at sha1_git
    """
    env = {'sha1_git': sha1_git}

    try:
        files = service.lookup_directory(sha1_git)
        if not files:
            message = "Directory %s was not found." % sha1_git
        else:
            message = "Listing for directory %s:" % sha1_git
            env['ls'] = prepare_directory_listing(files)

    except BadInputExc as e:  # do not like it but do not duplicate code
        message = e

    env['message'] = message

    return render_template('directory.html', **env)
