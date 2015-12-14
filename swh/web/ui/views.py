# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from flask import render_template, flash, request

from flask.ext.api.decorators import set_renderers
from flask.ext.api.renderers import HTMLRenderer

from swh.core.hashutil import ALGORITHMS
from swh.web.ui import service, utils
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


@app.route('/about/')
@set_renderers(HTMLRenderer)
def about():
    return render_template('about.html')


@app.route('/search/', methods=['GET', 'POST'])
@set_renderers(HTMLRenderer)
def search():
    """Search for hashes in swh-storage.

    """
    env = {'filename': None, 'message': '', 'found': None, 'q': ''}

    q = request.args.get('q', '')
    if q:
        env = {'q': q, 'message': ''}

        try:
            if q:
                r = service.lookup_hash(q)
                env['message'] = 'Content with hash %s%sfound!' % (
                    q,
                    ' ' if r['found'] == True else ' not '
                )
                env['q'] = q
        except BadInputExc as e:
            env['message'] = str(e)

    elif request.method == 'POST':
        file = request.files['filename']

        try:
            uploaded_content = service.upload_and_search(file)
            filename = uploaded_content['filename']
            sha1 = uploaded_content['sha1']
            found = uploaded_content['found']

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
        except BadInputExc as e:
            env['message'] = str(e)

    return render_template('upload_and_search.html', **env)


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


# @app.route('/browse/content/')
# @app.route('/browse/content/<string:q>/')
@set_renderers(HTMLRenderer)
def content_with_origin(q='sha1:4320781056e5a735a39de0b8c229aea224590052'):
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
        if not content.get('found'):
            message = "Hash %s was not found." % q
        else:
            origin = service.lookup_hash_origin(q)
            message = _origin_seen(q, origin)
    except BadInputExc as e:  # do not like it but do not duplicate code
        message = str(e)

    env['message'] = message
    return render_template('content.html', **env)


@app.route('/browse/content/<string:q>/raw/')
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
        if content:
            # FIXME: will break if not utf-8
            content['data'] = content['data'].decode('utf-8')
            message = 'Content %s' % content['sha1']
        else:
            message = 'Content with %s not found.' % q
    except BadInputExc as e:
        message = str(e)
        content = None

    env['message'] = message
    env['content'] = content
    return render_template('display_content.html', **env)


@app.route('/browse/directory/')
@app.route('/browse/directory/<string:sha1_git>/')
@set_renderers(HTMLRenderer)
def browse_directory(sha1_git='828da2b80e41aa958b2c98526f4a1d2cc7d298b7'):
    """Show directory information.

    Args:
        - sha1_git: the directory's sha1 git identifier.

    Returns:
        The content's information at sha1_git
    """
    env = {'sha1_git': sha1_git}

    try:
        directory_files = service.lookup_directory(sha1_git)
        if directory_files:
            message = "Listing for directory %s:" % sha1_git
            files = utils.prepare_directory_listing(directory_files)
        else:
            message = "Directory %s not found." % sha1_git
            files = []
    except BadInputExc as e:  # do not like it but do not duplicate code
        message = str(e)
        files = []

    env['message'] = message
    env['files'] = files
    return render_template('directory.html', **env)
