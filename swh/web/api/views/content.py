# Copyright (C) 2015-2017  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import functools

from django.http import QueryDict
from django.http import HttpResponse

from swh.web.api.utils import reverse
from swh.web.api import service, utils
from swh.web.api import apidoc as api_doc
from swh.web.api.exc import NotFoundExc, ForbiddenExc
from swh.web.api.apiurls import api_route
from swh.web.api.views import (
    _api_lookup, _doc_exc_id_not_found, _doc_header_link,
    _doc_arg_last_elt, _doc_arg_per_page, _doc_exc_bad_id,
    _doc_arg_content_id
)


@api_route(r'/content/(?P<q>.+)/provenance/', 'content-provenance')
@api_doc.route('/content/provenance/', tags=['hidden'])
@api_doc.arg('q',
             default='sha1_git:88b9b366facda0b5ff8d8640ee9279bed346f242',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""List of provenance information (dict) for the matched
                        content.""")
def api_content_provenance(request, q):
    """Return content's provenance information if any.

    """
    def _enrich_revision(provenance):
        p = provenance.copy()
        p['revision_url'] = \
            reverse('revision', kwargs={'sha1_git': provenance['revision']})
        p['content_url'] = \
            reverse('content',
                    kwargs={'q': 'sha1_git:%s' % provenance['content']})
        p['origin_url'] = \
            reverse('origin', kwargs={'origin_id': provenance['origin']})
        p['origin_visits_url'] = \
            reverse('origin-visits',
                    kwargs={'origin_id': provenance['origin']})
        p['origin_visit_url'] = \
            reverse('origin-visit', kwargs={'origin_id': provenance['origin'],
                                            'visit_id': provenance['visit']})
        return p

    return _api_lookup(
        service.lookup_content_provenance, q,
        notfound_msg='Content with {} not found.'.format(q),
        enrich_fn=_enrich_revision)


@api_route(r'/content/(?P<q>.+)/filetype/', 'content-filetype')
@api_doc.route('/content/filetype/', tags=['upcoming'])
@api_doc.arg('q',
             default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""Filetype information (dict) for the matched
                        content.""")
def api_content_filetype(request, q):
    """Get information about the detected MIME type of a content object.

    """
    return _api_lookup(
        service.lookup_content_filetype, q,
        notfound_msg='No filetype information found for content {}.'.format(q),
        enrich_fn=utils.enrich_metadata_endpoint)


@api_route(r'/content/(?P<q>.+)/language/', 'content-language')
@api_doc.route('/content/language/', tags=['upcoming'])
@api_doc.arg('q',
             default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""Language information (dict) for the matched
                        content.""")
def api_content_language(request, q):
    """Get information about the detected (programming) language of a content
    object.

    """
    return _api_lookup(
        service.lookup_content_language, q,
        notfound_msg='No language information found for content {}.'.format(q),
        enrich_fn=utils.enrich_metadata_endpoint)


@api_route(r'/content/(?P<q>.+)/license/', 'content-license')
@api_doc.route('/content/license/', tags=['upcoming'])
@api_doc.arg('q',
             default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""License information (dict) for the matched
                        content.""")
def api_content_license(request, q):
    """Get information about the detected license of a content object.

    """
    return _api_lookup(
        service.lookup_content_license, q,
        notfound_msg='No license information found for content {}.'.format(q),
        enrich_fn=utils.enrich_metadata_endpoint)


@api_route(r'/content/(?P<q>.+)/ctags/', 'content-ctags')
@api_doc.route('/content/ctags/', tags=['upcoming'])
@api_doc.arg('q',
             default='sha1:1fc6129a692e7a87b5450e2ba56e7669d0c5775d',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""Ctags symbol (dict) for the matched
                        content.""")
def api_content_ctags(request, q):
    """Get information about all `Ctags <http://ctags.sourceforge.net/>`_-style
    symbols defined in a content object.

    """
    return _api_lookup(
        service.lookup_content_ctags, q,
        notfound_msg='No ctags symbol found for content {}.'.format(q),
        enrich_fn=utils.enrich_metadata_endpoint)


@api_route(r'/content/(?P<q>.+)/raw/', 'content-raw')
@api_doc.route('/content/raw/', handle_response=True)
@api_doc.arg('q',
             default='adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.param('filename', default=None,
               argtype=api_doc.argtypes.str,
               doc='User\'s desired filename. If provided, the downloaded'
                   ' content will get that filename.')
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.octet_stream,
                 retdoc='The raw content data as an octet stream')
def api_content_raw(request, q):
    """Get the raw content of a content object (AKA "blob"), as a byte
    sequence.

    """
    def generate(content):
        yield content['data']

    content_raw = service.lookup_content_raw(q)
    if not content_raw:
        raise NotFoundExc('Content %s is not found.' % q)

    content_filetype = service.lookup_content_filetype(q)
    if not content_filetype:
        raise NotFoundExc('Content %s is not available for download.' % q)

    mimetype = content_filetype['mimetype']
    if 'text/' not in mimetype:
        raise ForbiddenExc('Only textual content is available for download. '
                           'Actual content mimetype is %s.' % mimetype)

    filename = utils.get_query_params(request).get('filename')
    if not filename:
        filename = 'content_%s_raw' % q.replace(':', '_')

    response = HttpResponse(generate(content_raw),
                            content_type='application/octet-stream')
    response['Content-disposition'] = 'attachment; filename=%s' % filename
    return response


@api_route(r'/content/symbol/(?P<q>.+)/', 'content-symbol')
@api_doc.route('/content/symbol/', tags=['upcoming'])
@api_doc.arg('q',
             default='hello',
             argtype=api_doc.argtypes.str,
             argdoc="""An expression string to lookup in swh's raw content""")
@api_doc.header('Link', doc=_doc_header_link)
@api_doc.param('last_sha1', default=None,
               argtype=api_doc.argtypes.str,
               doc=_doc_arg_last_elt)
@api_doc.param('per_page', default=10,
               argtype=api_doc.argtypes.int,
               doc=_doc_arg_per_page)
@api_doc.returns(rettype=api_doc.rettypes.list,
                 retdoc="""A list of dict whose content matches the expression.
                 Each dict has the following keys:
                 - id (bytes): identifier of the content
                 - name (text): symbol whose content match the expression
                 - kind (text): kind of the symbol that matched
                 - lang (text): Language for that entry
                 - line (int): Number line for the symbol
                """)
def api_content_symbol(request, q=None):
    """Search content objects by `Ctags <http://ctags.sourceforge.net/>`_-style
    symbol (e.g., function name, data type, method, ...).

    """
    result = {}
    last_sha1 = utils.get_query_params(request).get('last_sha1', None)
    per_page = int(utils.get_query_params(request).get('per_page', '10'))

    def lookup_exp(exp, last_sha1=last_sha1, per_page=per_page):
        return service.lookup_expression(exp, last_sha1, per_page)

    symbols = _api_lookup(
        lookup_exp, q,
        notfound_msg="No indexed raw content match expression '{}'.".format(q),
        enrich_fn=functools.partial(utils.enrich_content, top_url=True))

    if symbols:
        l = len(symbols)

        if l == per_page:
            query_params = QueryDict('', mutable=True)
            new_last_sha1 = symbols[-1]['sha1']
            query_params['last_sha1'] = new_last_sha1
            if utils.get_query_params(request).get('per_page'):
                query_params['per_page'] = per_page

            result['headers'] = {
                'link-next': reverse('content-symbol', kwargs={'q': q}) + '?' +
                query_params.urlencode()
            }

    result.update({
        'results': symbols
    })

    return result


@api_route(r'/content/known/search/', 'content-known', methods=['POST'])
@api_route(r'/content/known/(?P<q>(?!search).*)/', 'content-known')
@api_doc.route('/content/known/', tags=['hidden'])
@api_doc.arg('q',
             default='adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
             argtype=api_doc.argtypes.sha1,
             argdoc='content identifier as a sha1 checksum')
@api_doc.param('q', default=None,
               argtype=api_doc.argtypes.str,
               doc="""(POST request) An algo_hash:hash string, where algo_hash
                   is one of sha1, sha1_git or sha256 and hash is the hash to
                   search for in SWH""")
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""a dictionary with results (found/not found for each given
                        identifier) and statistics about how many identifiers
                        were found""")
def api_check_content_known(request, q=None):
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
        data = request.data if hasattr(request, 'data') else request.DATA
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


@api_route(r'/content/(?P<q>.+)/', 'content')
@api_doc.route('/content/')
@api_doc.arg('q',
             default='adc83b19e793491b1c6ea0fd8b46cd9f32e592fc',
             argtype=api_doc.argtypes.algo_and_hash,
             argdoc=_doc_arg_content_id)
@api_doc.raises(exc=api_doc.excs.badinput, doc=_doc_exc_bad_id)
@api_doc.raises(exc=api_doc.excs.notfound, doc=_doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""known metadata for content identified by q""")
def api_content_metadata(request, q):
    """Get information about a content (AKA "blob") object.

    """
    return _api_lookup(
        service.lookup_content, q,
        notfound_msg='Content with {} not found.'.format(q),
        enrich_fn=utils.enrich_content)
