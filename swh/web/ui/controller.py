# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from flask import request, url_for

from flask.ext.api.decorators import set_renderers

from swh.core.hashutil import ALGORITHMS
from swh.web.ui.main import app
from swh.web.ui import service, renderers, utils
from swh.web.ui.exc import NotFoundExc


hash_filter_keys = ALGORITHMS


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
