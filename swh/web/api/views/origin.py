# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from distutils.util import strtobool

from swh.web.common import service
from swh.web.common.utils import reverse
from swh.web.api import utils
from swh.web.api import apidoc as api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import (
    api_lookup, doc_exc_id_not_found, doc_header_link,
    doc_arg_last_elt, doc_arg_per_page
)


def _enrich_origin(origin):
    if 'id' in origin:
        o = origin.copy()
        o['origin_visits_url'] = \
            reverse('origin-visits', kwargs={'origin_id': origin['id']})
        return o

    return origin


@api_route(r'/origin/(?P<origin_id>[0-9]+)/', 'origin')
@api_route(r'/origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)',
           'origin')
@api_doc.route('/origin/')
@api_doc.arg('origin_id',
             default=1,
             argtype=api_doc.argtypes.int,
             argdoc='origin identifier (when looking up by ID)')
@api_doc.arg('origin_type',
             default='git',
             argtype=api_doc.argtypes.str,
             argdoc='origin type (when looking up by type+URL)')
@api_doc.arg('origin_url',
             default='https://github.com/hylang/hy',
             argtype=api_doc.argtypes.path,
             argdoc='origin URL (when looking up by type+URL)')
@api_doc.raises(exc=api_doc.excs.notfound, doc=doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""The metadata of the origin corresponding to the given
                        criteria""")
def api_origin(request, origin_id=None, origin_type=None, origin_url=None):
    """Get information about a software origin.

    Software origins might be looked up by origin type and canonical URL (e.g.,
    "git" + a "git clone" URL), or by their unique (but otherwise meaningless)
    identifier.

    """
    ori_dict = {
        'id': origin_id,
        'type': origin_type,
        'url': origin_url
    }
    ori_dict = {k: v for k, v in ori_dict.items() if ori_dict[k]}
    if 'id' in ori_dict:
        error_msg = 'Origin with id %s not found.' % ori_dict['id']
    else:
        error_msg = 'Origin with type %s and URL %s not found' % (
            ori_dict['type'], ori_dict['url'])

    return api_lookup(
        service.lookup_origin, ori_dict,
        notfound_msg=error_msg,
        enrich_fn=_enrich_origin)


@api_route(r'/origin/search/(?P<url_pattern>.+)/',
           'origin-search')
@api_doc.route('/origin/search/')
@api_doc.arg('url_pattern',
             default='python',
             argtype=api_doc.argtypes.str,
             argdoc='string pattern to search for in origin urls')
@api_doc.header('Link', doc=doc_header_link)
@api_doc.param('offset',
               default=0,
               argtype=api_doc.argtypes.int,
               doc='number of found origins to skip before returning results') # noqa
@api_doc.param('limit',
               default=70,
               argtype=api_doc.argtypes.int,
               doc='the maximum number of found origins to return')
@api_doc.param('regexp',
               default='false',
               argtype=api_doc.argtypes.str,
               doc="""if that query parameter is set to 'true', consider provided
                   pattern as a regular expression and search origins whose
                   urls match it""")
@api_doc.returns(rettype=api_doc.rettypes.list,
                 retdoc="""The metadata of the origins whose urls match
                        the provided string pattern""")
def api_origin_search(request, url_pattern):
    """Search for origins whose urls contain a provided string pattern
    or match a provided regular expression.
    The search is performed in a case insensitive way.

    """
    result = {}
    offset = int(request.query_params.get('offset', '0'))
    limit = int(request.query_params.get('limit', '70'))
    regexp = request.query_params.get('regexp', 'false')

    r = api_lookup(service.search_origin, url_pattern, offset, limit,
                   bool(strtobool(regexp)), enrich_fn=_enrich_origin)

    l = len(r)
    if l == limit:
        query_params = {}
        query_params['offset'] = offset + limit
        query_params['limit'] = limit
        query_params['regexp'] = regexp

        result['headers'] = {
            'link-next': reverse('origin-search',
                                 kwargs={'url_pattern': url_pattern},
                                 query_params=query_params)
        }

    result.update({
        'results': r
    })

    return result


@api_route(r'/origin/(?P<origin_id>[0-9]+)/visits/', 'origin-visits')
@api_doc.route('/origin/visits/')
@api_doc.arg('origin_id',
             default=1,
             argtype=api_doc.argtypes.int,
             argdoc='software origin identifier')
@api_doc.header('Link', doc=doc_header_link)
@api_doc.param('last_visit', default=None,
               argtype=api_doc.argtypes.int,
               doc=doc_arg_last_elt)
@api_doc.param('per_page', default=10,
               argtype=api_doc.argtypes.int,
               doc=doc_arg_per_page)
@api_doc.raises(exc=api_doc.excs.notfound, doc=doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.list,
                 retdoc="""a list of dictionaries describing individual visits.
                 For each visit, its identifier, timestamp (as UNIX time),
                 outcome, and visit-specific URL for more information are
                 given.""")
def api_origin_visits(request, origin_id):
    """Get information about all visits of a given software origin.

    """
    result = {}
    per_page = int(request.query_params.get('per_page', '10'))
    last_visit = request.query_params.get('last_visit')
    if last_visit:
        last_visit = int(last_visit)

    def _lookup_origin_visits(
            origin_id, last_visit=last_visit, per_page=per_page):
        return service.lookup_origin_visits(
            origin_id, last_visit=last_visit, per_page=per_page)

    def _enrich_origin_visit(origin_visit):
        ov = origin_visit.copy()
        ov['origin_visit_url'] = reverse('origin-visit',
                                         kwargs={'origin_id': origin_id,
                                                 'visit_id': ov['visit']})
        snapshot = ov['snapshot']
        if snapshot:
            ov['snapshot_url'] = reverse('snapshot',
                                         kwargs={'snapshot_id': snapshot})
        else:
            ov['snapshot_url'] = None
        return ov

    r = api_lookup(
        _lookup_origin_visits, origin_id,
        notfound_msg='No origin {} found'.format(origin_id),
        enrich_fn=_enrich_origin_visit)

    if r:
        l = len(r)
        if l == per_page:
            new_last_visit = r[-1]['visit']
            query_params = {}
            query_params['last_visit'] = new_last_visit

            if request.query_params.get('per_page'):
                query_params['per_page'] = per_page

            result['headers'] = {
                'link-next': reverse('origin-visits',
                                     kwargs={'origin_id': origin_id},
                                     query_params=query_params)
            }

    result.update({
        'results': r
    })

    return result


@api_route(r'/origin/(?P<origin_id>[0-9]+)/visit/(?P<visit_id>[0-9]+)/',
           'origin-visit')
@api_doc.route('/origin/visit/')
@api_doc.arg('origin_id',
             default=1,
             argtype=api_doc.argtypes.int,
             argdoc='software origin identifier')
@api_doc.arg('visit_id',
             default=1,
             argtype=api_doc.argtypes.int,
             argdoc="""visit identifier, relative to the origin identified by
             origin_id""")
@api_doc.raises(exc=api_doc.excs.notfound, doc=doc_exc_id_not_found)
@api_doc.returns(rettype=api_doc.rettypes.dict,
                 retdoc="""dictionary containing both metadata for the entire
                 visit (e.g., timestamp as UNIX time, visit outcome, etc.) and
                 what was at the software origin during the visit (i.e., a
                 mapping from branches to other archive objects)""")
def api_origin_visit(request, origin_id, visit_id):
    """Get information about a specific visit of a software origin.

    """
    def _enrich_origin_visit(origin_visit):
        ov = origin_visit.copy()
        ov['origin_url'] = reverse('origin',
                                   kwargs={'origin_id': ov['origin']})
        snapshot = ov['snapshot']
        if snapshot:
            ov['snapshot_url'] = reverse('snapshot',
                                         kwargs={'snapshot_id': snapshot})
        else:
            ov['snapshot_url'] = None

        # TODO: remove that piece of code once the snapshot migration
        # is totally effective in storage (no more occurrences)
        if 'occurrences' in ov:
            ov['occurrences'] = {
                k: utils.enrich_object(v) if v else None
                for k, v in ov['occurrences'].items()
            }
        return ov

    return api_lookup(
        service.lookup_origin_visit, origin_id, visit_id,
        notfound_msg=('No visit {} for origin {} found'
                      .format(visit_id, origin_id)),
        enrich_fn=_enrich_origin_visit)
