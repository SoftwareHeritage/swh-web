# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from distutils.util import strtobool

from swh.web.common import service
from swh.web.common.exc import BadInputExc
from swh.web.common.utils import (
    reverse, get_origin_visits
)
from swh.web.api.apidoc import api_doc
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import api_lookup


def _enrich_origin(origin):
    if 'id' in origin:
        o = origin.copy()
        o['origin_visits_url'] = \
            reverse('api-origin-visits', url_args={'origin_id': origin['id']})
        return o

    return origin


@api_route(r'/origin/(?P<origin_id>[0-9]+)/', 'api-origin')
@api_route(r'/origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/',
           'api-origin')
@api_doc('/origin/')
def api_origin(request, origin_id=None, origin_type=None, origin_url=None):
    """
    .. http:get:: /api/1/origin/(origin_id)/

        Get information about a software origin.

        :param int origin_id: a software origin identifier

        :>json number id: the origin unique identifier
        :>json string origin_visits_url: link to in order to get information about the
            visits for that origin
        :>json string type: the type of software origin (possible values are ``git``, ``svn``,
            ``hg``, ``deb``, ``pypi``, ``ftp`` or ``deposit``)
        :>json string url: the origin canonical url

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/1/`

    .. http:get:: /api/1/origin/(origin_type)/url/(origin_url)/

        Get information about a software origin.

        :param string origin_type: the origin type (possible values are ``git``, ``svn``,
            ``hg``, ``deb``, ``pypi``, ``ftp`` or ``deposit``)
        :param string origin_url: the origin url

        :>json number id: the origin unique identifier
        :>json string origin_visits_url: link to in order to get information about the
            visits for that origin
        :>json string type: the type of software origin
        :>json string url: the origin canonical url

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/git/url/https://github.com/python/cpython/`
    """ # noqa
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
           'api-origin-search')
@api_doc('/origin/search/')
def api_origin_search(request, url_pattern):
    """
    .. http:get:: /api/1/origin/search/(url_pattern)/

        Search for software origins whose urls contain a provided string
        pattern or match a provided regular expression.
        The search is performed in a case insensitive way.

        :param string url_pattern: a string pattern or a regular expression
        :query int offset: the number of found origins to skip before returning results
        :query int limit: the maximum number of found origins to return
        :query boolean regexp: if true, consider provided pattern as a regular expression
            and search origins whose urls match it
        :query boolean with_visit: if true, only return origins with at least one visit
            by Software heritage

        :>jsonarr number id: the origin unique identifier
        :>jsonarr string origin_visits_url: link to in order to get information about the
            visits for that origin
        :>jsonarr string type: the type of software origin
        :>jsonarr string url: the origin canonical url

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/search/python/?limit=2`
    """ # noqa
    result = {}
    offset = int(request.query_params.get('offset', '0'))
    limit = int(request.query_params.get('limit', '70'))
    regexp = request.query_params.get('regexp', 'false')
    with_visit = request.query_params.get('with_visit', 'false')

    results = api_lookup(service.search_origin, url_pattern, offset, limit,
                         bool(strtobool(regexp)), bool(strtobool(with_visit)),
                         enrich_fn=_enrich_origin)

    nb_results = len(results)
    if nb_results == limit:
        query_params = {}
        query_params['offset'] = offset + limit
        query_params['limit'] = limit
        query_params['regexp'] = regexp

        result['headers'] = {
            'link-next': reverse('api-origin-search',
                                 url_args={'url_pattern': url_pattern},
                                 query_params=query_params)
        }

    result.update({
        'results': results
    })

    return result


@api_route(r'/origin/metadata-search/',
           'api-origin-metadata-search')
@api_doc('/origin/metadata-search/', noargs=True)
def api_origin_metadata_search(request):
    """
    .. http:get:: /api/1/origin/metadata-search/

        Search for software origins whose metadata (expressed as a
        JSON-LD/CodeMeta dictionary) match the provided criteria.
        For now, only full-text search on this dictionary is supported.

        :query str fulltext: a string that will be matched against origin metadata;
            results are ranked and ordered starting with the best ones.
        :query int limit: the maximum number of found origins to return
            (bounded to 100)

        :>jsonarr number origin_id: the origin unique identifier
        :>jsonarr dict metadata: metadata of the origin (as a JSON-LD/CodeMeta dictionary)
        :>jsonarr string from_revision: the revision used to extract these
            metadata (the current HEAD or one of the former HEADs)
        :>jsonarr dict tool: the tool used to extract these metadata

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/metadata-search/?limit=2&fulltext=Jane%20Doe`
    """ # noqa
    fulltext = request.query_params.get('fulltext', None)
    limit = min(int(request.query_params.get('limit', '70')), 100)

    if not fulltext:
        content = '"fulltext" must be provided and non-empty.'
        raise BadInputExc(content)

    results = api_lookup(service.search_origin_metadata, fulltext, limit)

    return {
        'results': results,
    }


@api_route(r'/origin/(?P<origin_id>[0-9]+)/visits/', 'api-origin-visits')
@api_doc('/origin/visits/')
def api_origin_visits(request, origin_id):
    """
    .. http:get:: /api/1/origin/(origin_id)/visits/

        Get information about all visits of a software origin.
        Visits are returned sorted in descending order according
        to their date.

        :param int origin_id: a software origin identifier
        :query int per_page: specify the number of visits to list, for pagination purposes
        :query int last_visit: visit to start listing from, for pagination purposes

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request
        :resheader Link: indicates that a subsequent result page is available and contains
            the url pointing to it

        :>jsonarr string date: ISO representation of the visit date (in UTC)
        :>jsonarr number id: the unique identifier of the origin
        :>jsonarr string origin_visit_url: link to :http:get:`/api/1/origin/(origin_id)/visit/(visit_id)/`
            in order to get information about the visit
        :>jsonarr string snapshot: the snapshot identifier of the visit
        :>jsonarr string snapshot_url: link to :http:get:`/api/1/snapshot/(snapshot_id)/`
            in order to get information about the snapshot of the visit
        :>jsonarr string status: status of the visit (either **full**, **partial** or **ongoing**)
        :>jsonarr number visit: the unique identifier of the visit

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/1/visits/`
    """ # noqa
    result = {}
    per_page = int(request.query_params.get('per_page', '10'))
    last_visit = request.query_params.get('last_visit')
    if last_visit:
        last_visit = int(last_visit)

    def _lookup_origin_visits(
            origin_id, last_visit=last_visit, per_page=per_page):
        all_visits = get_origin_visits({'id': origin_id})
        all_visits.reverse()
        visits = []
        if not last_visit:
            visits = all_visits[:per_page]
        else:
            for i, v in enumerate(all_visits):
                if v['visit'] == last_visit:
                    visits = all_visits[i+1:i+1+per_page]
                    break
        for v in visits:
            yield v

    def _enrich_origin_visit(origin_visit):
        ov = origin_visit.copy()
        ov['origin_visit_url'] = reverse('api-origin-visit',
                                         url_args={'origin_id': origin_id,
                                                   'visit_id': ov['visit']})
        snapshot = ov['snapshot']
        if snapshot:
            ov['snapshot_url'] = reverse('api-snapshot',
                                         url_args={'snapshot_id': snapshot})
        else:
            ov['snapshot_url'] = None
        return ov

    results = api_lookup(_lookup_origin_visits, origin_id,
                         notfound_msg='No origin {} found'.format(origin_id),
                         enrich_fn=_enrich_origin_visit)

    if results:
        nb_results = len(results)
        if nb_results == per_page:
            new_last_visit = results[-1]['visit']
            query_params = {}
            query_params['last_visit'] = new_last_visit

            if request.query_params.get('per_page'):
                query_params['per_page'] = per_page

            result['headers'] = {
                'link-next': reverse('api-origin-visits',
                                     url_args={'origin_id': origin_id},
                                     query_params=query_params)
            }

    result.update({
        'results': results
    })

    return result


@api_route(r'/origin/(?P<origin_id>[0-9]+)/visit/(?P<visit_id>[0-9]+)/',
           'api-origin-visit')
@api_doc('/origin/visit/')
def api_origin_visit(request, origin_id, visit_id):
    """
    .. http:get:: /api/1/origin/(origin_id)/visit/(visit_id)/

        Get information about a specific visit of a software origin.

        :param int origin_id: a software origin identifier
        :param int visit_id: a visit identifier

        :reqheader Accept: the requested response content type,
            either ``application/json`` (default) or ``application/yaml``
        :resheader Content-Type: this depends on :http:header:`Accept` header of request

        :>json string date: ISO representation of the visit date (in UTC)
        :>json number origin: the origin unique identifier
        :>json string origin_url: link to get information about the origin
        :>jsonarr string snapshot: the snapshot identifier of the visit
        :>jsonarr string snapshot_url: link to :http:get:`/api/1/snapshot/(snapshot_id)/`
            in order to get information about the snapshot of the visit
        :>json string status: status of the visit (either **full**, **partial** or **ongoing**)
        :>json number visit: the unique identifier of the visit

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin or visit can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/1500/visit/1/`
    """ # noqa
    def _enrich_origin_visit(origin_visit):
        ov = origin_visit.copy()
        ov['origin_url'] = reverse('api-origin',
                                   url_args={'origin_id': ov['origin']})
        snapshot = ov['snapshot']
        if snapshot:
            ov['snapshot_url'] = reverse('api-snapshot',
                                         url_args={'snapshot_id': snapshot})
        else:
            ov['snapshot_url'] = None

        return ov

    return api_lookup(
        service.lookup_origin_visit, origin_id, visit_id,
        notfound_msg=('No visit {} for origin {} found'
                      .format(visit_id, origin_id)),
        enrich_fn=_enrich_origin_visit)
