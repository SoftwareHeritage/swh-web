# Copyright (C) 2015  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from flask import request, url_for

from flask.ext.api.decorators import set_renderers

from swh.web.ui.main import app
from swh.web.ui import service, renderers, utils
from swh.web.ui.exc import BadInputExc, NotFoundExc


@app.route('/browse/')
def api_browse_endpoints():
    """List the current api endpoints starting with /api or /api/.

    Returns:
        List of endpoints at /api

    """
    return utils.filter_endpoints(app.url_map, '/browse')


@app.route('/api/')
def api_main_endpoints():
    """List the current api endpoints starting with /api or /api/.

    Returns:
        List of endpoints at /api

    """
    return utils.filter_endpoints(app.url_map, '/api')


@app.route('/api/1/')
def api_main_v1_endpoints():
    """List the current api v1 endpoints starting with /api/1 or /api/1/.

    Returns:
        List of endpoints at /api/1

    """
    return utils.filter_endpoints(app.url_map, '/api/1')


@app.route('/api/1/stat/counters/')
def api_stats():
    """Return statistics on SWH storage.

    Returns:
        SWH storage's statistics

    """
    return service.stat_counters()


@app.route('/api/1/search/<string:q>/')
def api_search(q):
    """Search a content per hash.

    Args:
        q is of the form algo_hash:hash with algo_hash in
        (sha1, sha1_git, sha256)

    Returns:
        Dictionary with 'found' key and the associated result.

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash

    """
    return {'found': service.lookup_hash(q)}


def _api_lookup(criteria, lookup_fn, error_msg_if_not_found):
    """Factorize function regarding the api to lookup for data."""
    res = lookup_fn(criteria)
    if not res:
        raise NotFoundExc(error_msg_if_not_found)
    return res


@app.route('/api/1/origin/<int:origin_id>/')
def api_origin(origin_id):
    """Return information about origin with id origin_id.


    Args:
        origin_id: the origin's identifier

    Returns:
        Information on the origin if found.

    Raises:
        NotFoundExc if the origin is not found.

    """
    return _api_lookup(
        origin_id, lookup_fn=service.lookup_origin,
        error_msg_if_not_found='Origin with id %s not found.' % origin_id)


@app.route('/api/1/person/<int:person_id>/')
def api_person(person_id):
    """Return information about person with identifier person_id.

    Args:
        person_id: the person's identifier

    Returns:
        Information on the person if found.

    Raises:
        NotFoundExc if the person is not found.

    """
    return _api_lookup(
        person_id, lookup_fn=service.lookup_person,
        error_msg_if_not_found='Person with id %s not found.' % person_id)


@app.route('/api/1/release/<string:sha1_git>/')
def api_release(sha1_git):
    """Return information about release with id sha1_git.

    Args:
        sha1_git: the release's hash

    Returns:
        Information on the release if found.

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash
        NotFoundExc if the release is not found.

    """
    error_msg = 'Release with sha1_git %s not found.' % sha1_git
    return _api_lookup(
        sha1_git,
        lookup_fn=service.lookup_release,
        error_msg_if_not_found=error_msg)


@app.route('/api/1/revision/<string:sha1_git>/')
def api_revision(sha1_git):
    """Return information about revision with id sha1_git.

    Args:
        sha1_git: the revision's hash

    Returns:
        Information on the revision if found.

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash
        NotFoundExc if the revision is not found.

    """
    error_msg = 'Revision with sha1_git %s not found.' % sha1_git
    return _api_lookup(
        sha1_git,
        lookup_fn=service.lookup_revision,
        error_msg_if_not_found=error_msg)


@app.route('/api/1/directory/<string:sha1_git>/')
def api_directory(sha1_git):
    """Return information about release with id sha1_git.

    Args:
        Directory's sha1_git

    Raises:
        BadInputExc in case of unknown algo_hash or bad hash
        NotFoundExc if the content is not found.

    """
    directory_entries = service.lookup_directory(sha1_git)
    if not directory_entries:
        raise NotFoundExc('Directory with sha1_git %s not found.' % sha1_git)
    return list(directory_entries)


@app.route('/api/1/browse/<string:q>/')
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


@app.route('/api/1/content/<string:q>/raw/')
@set_renderers(renderers.BytesRenderer)
def api_content_raw(q):
    """Return content's raw data if content is found.

    Args:
        q is of the form (algo_hash:)hash with algo_hash in
        (sha1, sha1_git, sha256).
        When algo_hash is not provided, 'hash' is considered sha1.

    Returns:
        Content's raw data in text/plain.

    Raises:
        - BadInputExc in case of unknown algo_hash or bad hash
        - NotFoundExc if the content is not found.

    """
    content = service.lookup_content_raw(q)
    if not content:
        raise NotFoundExc('Content with %s not found.' % q)

    return content['data']


@app.route('/api/1/content/<string:q>/')
def api_content_with_details(q):
    """Return content information if content is found.

    Args:
        q is of the form (algo_hash:)hash with algo_hash in
        (sha1, sha1_git, sha256).
        When algo_hash is not provided, 'hash' is considered sha1.

    Returns:
        Content's information.

    Raises:
        - BadInputExc in case of unknown algo_hash or bad hash
        - NotFoundExc if the content is not found.

    """
    content = service.lookup_content(q)
    if not content:
        raise NotFoundExc('Content with %s not found.' % q)

    content['data'] = url_for('api_content_raw', q=content['sha1'])
    return content


@app.route('/api/1/uploadnsearch/', methods=['POST'])
def api_uploadnsearch():
    """Upload the file's content in the post body request.
       Compute its hash and determine if it exists in the storage.

    Args:
        request.files filled with the filename's data to upload.

    Returns:
        Dictionary with 'sha1', 'filename' and 'found' predicate depending
        on whether we find it or not.

    Raises:
        BadInputExc in case of the form submitted is incorrect.

    """
    file = request.files.get('filename')
    if not file:
        raise BadInputExc('Bad request, missing \'filename\' entry in form.')

    return service.upload_and_search(file)
