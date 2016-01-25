# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import flask

from flask import render_template, request, url_for, redirect

from flask.ext.api.decorators import set_renderers
from flask.ext.api.renderers import HTMLRenderer

from swh.core.hashutil import ALGORITHMS
from swh.web.ui import service, utils, api
from swh.web.ui.exc import BadInputExc, NotFoundExc
from swh.web.ui.main import app


hash_filter_keys = ALGORITHMS


@app.route('/')
@set_renderers(HTMLRenderer)
def homepage():
    """Home page

    """
    flask.flash('This Web app is still work in progress, use at your own risk',
                'warning')
    return render_template('home.html')


@app.route('/about/')
@set_renderers(HTMLRenderer)
def about():
    return render_template('about.html')


@app.route('/search/', methods=['GET', 'POST'])
@set_renderers(HTMLRenderer)
def search():
    """Search for hashes in swh-storage.

    One form to submit either:
    - hash query to look up in swh storage
    - some file content to upload, compute its hash and look it up in swh
      storage
    - both

    Returns:
        dict representing data to look for in swh storage.
        The following keys are returned:
        - file: File submitted for upload
        - filename: Filename submitted for upload
        - q: Query on hash to look for
        - message: Message detailing if data has been found or not.

    """
    env = {'filename': None,
           'q': None,
           'file': None}
    data = None
    q = env['q']
    file = env['file']

    if request.method == 'GET':
        data = request.args
    elif request.method == 'POST':
        data = request.data
        # or hash and search a file
        file = request.files.get('filename')

    # could either be a query for sha1 hash
    q = data.get('q')

    messages = []

    if q:
        env['q'] = q

        try:
            r = service.lookup_hash(q)
            messages.append('Content with hash %s%sfound!' % (
                q, ' ' if r.get('found') else ' not '))
        except BadInputExc as e:
            messages.append(str(e))

    if file and file.filename:
        env['file'] = file
        try:
            uploaded_content = service.upload_and_search(file)
            filename = uploaded_content['filename']
            sha1 = uploaded_content['sha1']
            found = uploaded_content['found']

            messages.append('File %s with hash %s%sfound!' % (
                filename, sha1, ' ' if found else ' not '))

            env.update({
                'filename': filename,
                'sha1': sha1,
            })
        except BadInputExc as e:
            messages.append(str(e))

    env['q'] = q if q else ''
    env['messages'] = messages

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


@app.route('/browse/content/')
@app.route('/browse/content/<string:q>/')
@set_renderers(HTMLRenderer)
def browse_content_detail(q='5d448a06f02d9de748b6b0b9620cba1bed8480da'):
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
    env = {}
    message = None
    content = None
    try:
        content = service.lookup_content(q)
        if not content:
            message = 'Content with %s not found.' % q
    except BadInputExc as e:
        message = str(e)

    env['message'] = message
    env['content'] = content
    return render_template('content.html', **env)


@app.route('/browse/content/<string:q>/raw/')
@set_renderers(HTMLRenderer)
def browse_content_data(q):
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
    content = None
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

    env['message'] = message
    env['content'] = content
    return render_template('content-data.html', **env)


# @app.route('/browse/content/<string:q>/origin/')
@set_renderers(HTMLRenderer)
def browse_content_with_origin(
        q='sha1:4320781056e5a735a39de0b8c229aea224590052'):
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
    return render_template('content-with-origin.html', **env)


@app.route('/browse/directory/')
@app.route('/browse/directory/<string:sha1_git>/')
@set_renderers(HTMLRenderer)
def browse_directory(sha1_git='dcf3289b576b1c8697f2a2d46909d36104208ba3'):
    """Show directory information.

    Args:
        - sha1_git: the directory's sha1 git identifier.

    Returns:
        The content's information at sha1_git
    """
    env = {'sha1_git': sha1_git}
    files = []

    try:
        directory_files = service.lookup_directory(sha1_git)
        if directory_files:
            message = "Listing for directory %s:" % sha1_git
            files = utils.prepare_directory_listing(directory_files)
        else:
            message = "Directory %s not found." % sha1_git
    except BadInputExc as e:  # do not like it but do not duplicate code
        message = str(e)

    env['message'] = message
    env['files'] = files
    return render_template('directory.html', **env)


@app.route('/browse/origin/')
@app.route('/browse/origin/<int:origin_id>/')
@set_renderers(HTMLRenderer)
def browse_origin(origin_id=1):
    """Browse origin with id id.

    """
    env = {'origin_id': origin_id,
           'origin': None}

    try:
        ori = service.lookup_origin(origin_id)
        if ori:
            env.update({'origin': ori})
        else:
            env.update({'message': 'Origin %s not found!' % origin_id})
    except BadInputExc as e:
        env.update({'message': str(e)})

    return render_template('origin.html', **env)


@app.route('/browse/person/')
@app.route('/browse/person/<int:person_id>/')
@set_renderers(HTMLRenderer)
def browse_person(person_id=1):
    """Browse person with id id.

    """
    env = {'person_id': person_id,
           'person': None}

    try:
        ori = service.lookup_person(person_id)
        if ori:
            env.update({'person': ori})
        else:
            env.update({'message': 'Person %s not found!' % person_id})
    except BadInputExc as e:
        env.update({'message': str(e)})

    return render_template('person.html', **env)


@app.route('/browse/release/')
@app.route('/browse/release/<string:sha1_git>/')
@set_renderers(HTMLRenderer)
def browse_release(sha1_git='1e951912027ea6873da6985b91e50c47f645ae1a'):
    """Browse release with sha1_git.

    """
    env = {'sha1_git': sha1_git,
           'release': None}

    try:
        rel = service.lookup_release(sha1_git)
        if rel:
            author = rel.get('author')
            if author:
                rel['author'] = utils.person_to_string(author)

            target_type = rel.get('target_type')
            if target_type == 'revision':
                rel['target'] = url_for('browse_revision',
                                        sha1_git=rel['target'])

            env.update({'release': rel,
                        'keys': ['id', 'name', 'date', 'message', 'author',
                                 'target', 'target_type']})
        else:
            env.update({'message': 'Release %s not found!' % sha1_git})
    except BadInputExc as e:
        env.update({'message': str(e)})

    return render_template('release.html', **env)


@app.route('/browse/revision/')
@app.route('/browse/revision/<string:sha1_git>/')
@set_renderers(HTMLRenderer)
def browse_revision(sha1_git='d770e558e21961ad6cfdf0ff7df0eb5d7d4f0754'):
    """Browse revision with sha1_git.

    """
    env = {'sha1_git': sha1_git,
           'keys': [],
           'revision': None}

    try:
        rev = service.lookup_revision(sha1_git)
        if rev:
            env['revision'] = utils.prepare_revision_view(rev)
        else:
            env['message'] = 'Revision %s not found!' % sha1_git
    except BadInputExc as e:
        env.update({'message': str(e)})

    return render_template('revision.html', **env)


@app.route('/browse/revision/<string:sha1_git_root>/history/<sha1_git>/')
@set_renderers(HTMLRenderer)
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
    limit = int(request.args.get('limit', '100'))

    env = {'sha1_git_root': sha1_git_root,
           'sha1_git': sha1_git,
           'message': None,
           'keys': [],
           'revision': None}

    if sha1_git == sha1_git_root:
        return redirect(url_for('browse_revision',
                                sha1_git=sha1_git,
                                limit=limit))

    try:
        revision = service.lookup_revision_with_context(sha1_git_root,
                                                        sha1_git,
                                                        limit)
        if revision:
            revision = utils.prepare_revision_view(revision)
            env.update({
                'sha1_git': revision['id'],
                'revision': revision,
            })
        else:
            env['message'] = "Possibly sha1_git '%s' is not an ancestor " \
                             "of sha1_git_root '%s'" % (sha1_git,
                                                        sha1_git_root)

    except (BadInputExc, NotFoundExc) as e:
        env['message'] = str(e)

    return render_template('revision.html', **env)


@app.route('/browse/revision/<string:sha1_git>/directory/')
@app.route('/browse/revision/<string:sha1_git>/directory/<path:path>/')
@set_renderers(HTMLRenderer)
def browse_revision_directory(sha1_git, path=None):
    """Browse directory from revision with sha1_git.

    """
    env = {
        'sha1_git': sha1_git,
        'path': '.' if not path else path,
        'message': None,
        'result': None
    }

    try:
        result = api.api_directory_with_revision(sha1_git, path)
        result['content'] = utils.prepare_data_for_view(result['content'])
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
@set_renderers(HTMLRenderer)
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

    if sha1_git == sha1_git_root:
        return redirect(url_for('browse_revision_directory',
                                sha1_git=sha1_git,
                                path=path),
                        code=301)

    try:
        result = api.api_directory_revision_history(sha1_git_root,
                                                    sha1_git,
                                                    path)
        env['revision'] = result['revision']
        env['content'] = utils.prepare_data_for_view(result['content'])
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
@set_renderers(HTMLRenderer)
def browse_revision_with_origin(origin_id=1,
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
        env['revision'] = api.api_revision_with_origin(origin_id,
                                                       branch_name,
                                                       ts)
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
@set_renderers(HTMLRenderer)
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
        env['revision'] = api.api_history_through_revision_with_origin(
            origin_id,
            branch_name,
            ts,
            sha1_git)
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
@set_renderers(HTMLRenderer)
def browse_revision_directory_through_origin(origin_id,
                                             branch_name='refs/heads/master',
                                             ts=None,
                                             path=None):

    env = {'message': None,
           'origin_id': origin_id,
           'ts': ts,
           'path': '.' if not path else path,
           'result': None}
    try:
        result = api.api_directory_through_revision_with_origin(
            origin_id,
            branch_name,
            ts,
            path)

        result['content'] = utils.prepare_data_for_view(result['content'])
        env['revision'] = result['revision']
        env['result'] = result
    except (ValueError, BadInputExc, NotFoundExc) as e:
        env['message'] = str(e)

    return render_template('revision-directory.html', **env)


@app.route('/browse/entity/')
@app.route('/browse/entity/<string:uuid>/')
@set_renderers(HTMLRenderer)
def browse_entity(uuid='5f4d4c51-498a-4e28-88b3-b3e4e8396cba'):
    env = {'entities': [],
           'message': None}
    entities = env['entities']

    try:
        entities = service.lookup_entity_by_uuid(uuid)
        if not entities:
            env['message'] = "Entity '%s' not found!" % uuid
    except BadInputExc as e:
        env.update({'message': str(e)})

    env['entities'] = entities
    return render_template('entity.html', **env)
