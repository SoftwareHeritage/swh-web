# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from distutils.util import strtobool
from functools import partial

from swh.web.common import service
from swh.web.common.exc import BadInputExc
from swh.web.common.origin_visits import get_origin_visits
from swh.web.common.utils import reverse
from swh.web.api.apidoc import api_doc, format_docstring
from swh.web.api.apiurls import api_route
from swh.web.api.views.utils import api_lookup


DOC_RETURN_ORIGIN = '''
        :>json string origin_visits_url: link to in order to get information
            about the visits for that origin
        :>json string url: the origin canonical url
        :>json string type: the type of software origin (deprecated value;
            types are now associated to visits instead of origins)
        :>json number id: the origin unique identifier (deprecated value;
            you should only refer to origins based on their URL)
'''

DOC_RETURN_ORIGIN_ARRAY = \
    DOC_RETURN_ORIGIN.replace(':>json', ':>jsonarr')

DOC_RETURN_ORIGIN_VISIT = '''
        :>json string date: ISO representation of the visit date (in UTC)
        :>json str origin: the origin canonical url
        :>json string origin_url: link to get information about the origin
        :>jsonarr string snapshot: the snapshot identifier of the visit
        :>jsonarr string snapshot_url: link to
            :http:get:`/api/1/snapshot/(snapshot_id)/` in order to get
            information about the snapshot of the visit
        :>json string status: status of the visit (either **full**,
            **partial** or **ongoing**)
        :>json number visit: the unique identifier of the visit
'''

DOC_RETURN_ORIGIN_VISIT_ARRAY = \
    DOC_RETURN_ORIGIN_VISIT.replace(':>json', ':>jsonarr')

DOC_RETURN_ORIGIN_VISIT_ARRAY += '''
        :>jsonarr number id: the unique identifier of the origin
        :>jsonarr string origin_visit_url: link to
            :http:get:`/api/1/origin/(origin_url)/visit/(visit_id)/`
            in order to get information about the visit
'''


def _enrich_origin(origin):
    if 'url' in origin:
        o = origin.copy()
        o['origin_visits_url'] = reverse(
            'api-1-origin-visits', url_args={'origin_url': origin['url']})
        return o

    return origin


def _enrich_origin_visit(origin_visit, *,
                         with_origin_link, with_origin_visit_link):
    ov = origin_visit.copy()
    if with_origin_link:
        ov['origin_url'] = reverse('api-1-origin',
                                   url_args={'origin_url': ov['origin']})
    if with_origin_visit_link:
        ov['origin_visit_url'] = reverse('api-1-origin-visit',
                                         url_args={'origin_url': ov['origin'],
                                                   'visit_id': ov['visit']})
    snapshot = ov['snapshot']
    if snapshot:
        ov['snapshot_url'] = reverse('api-1-snapshot',
                                     url_args={'snapshot_id': snapshot})
    else:
        ov['snapshot_url'] = None
    return ov


@api_route(r'/origins/', 'api-1-origins')
@api_doc('/origins/', noargs=True)
@format_docstring(return_origin_array=DOC_RETURN_ORIGIN_ARRAY)
def api_origins(request):
    """
    .. http:get:: /api/1/origins/

        Get list of archived software origins.

        Origins are sorted by ids before returning them.

        :query int origin_from: The first origin id that will be included
            in returned results (default to 1)
        :query int origin_count: The maximum number of origins to return
            (default to 100, can not exceed 10000)

        {return_origin_array}

        {common_headers}
        {resheader_link}

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`,
            :http:method:`options`

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origins?origin_from=50000&origin_count=500`
    """
    origin_from = int(request.query_params.get('origin_from', '1'))
    origin_count = int(request.query_params.get('origin_count', '100'))
    origin_count = min(origin_count, 10000)
    results = api_lookup(
        service.lookup_origins, origin_from, origin_count+1,
        enrich_fn=_enrich_origin)
    response = {'results': results, 'headers': {}}
    if len(results) > origin_count:
        origin_from = results.pop()['id']
        response['headers']['link-next'] = reverse(
            'api-1-origins',
            query_params={'origin_from': origin_from,
                          'origin_count': origin_count})
    return response


@api_route(r'/origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)/',
           'api-1-origin')
@api_route(r'/origin/(?P<origin_url>.+)/get/', 'api-1-origin')
@api_route(r'/origin/(?P<origin_id>[0-9]+)/', 'api-1-origin')
@api_doc('/origin/')
@format_docstring(return_origin=DOC_RETURN_ORIGIN)
def api_origin(request, origin_id=None, origin_type=None, origin_url=None):
    """
    .. http:get:: /api/1/origin/(origin_url)/get/

        Get information about a software origin.

        :param string origin_url: the origin url

        {return_origin}

        {common_headers}

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`,
            :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/git/url/https://github.com/python/cpython/`

    .. http:get:: /api/1/origin/(origin_id)/

        Get information about a software origin.

        .. warning::

            All endpoints using an ``origin_id`` or an ``origin_type`` are
            deprecated and will be removed in the near future. Only those
            using an ``origin_url`` will remain available.
            You should use :http:get:`/api/1/origin/(origin_url)/get/` instead.

        :param int origin_id: a software origin identifier

        {return_origin}

        {common_headers}

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`,
            :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/1/`

    .. http:get:: /api/1/origin/(origin_type)/url/(origin_url)/

        Get information about a software origin.

        .. warning::

            All endpoints using an ``origin_id`` or an ``origin_type`` are
            deprecated and will be removed in the near future. Only those
            using an ``origin_url`` will remain available.
            You should use :http:get:`/api/1/origin/(origin_url)/get/` instead.

        :param string origin_type: the origin type (possible values are
            ``git``, ``svn``, ``hg``, ``deb``, ``pypi``, ``npm``, ``ftp`` or
            ``deposit``)
        :param string origin_url: the origin url

        {return_origin}

        {common_headers}

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`,
            :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/git/url/https://github.com/python/cpython/`
    """
    ori_dict = {
        'id': int(origin_id) if origin_id else None,
        'type': origin_type,
        'url': origin_url
    }
    ori_dict = {k: v for k, v in ori_dict.items() if ori_dict[k]}
    error_msg = 'Origin %s not found.' % \
        (ori_dict.get('id') or ori_dict['url'])

    return api_lookup(
        service.lookup_origin, ori_dict,
        notfound_msg=error_msg,
        enrich_fn=_enrich_origin)


@api_route(r'/origin/search/(?P<url_pattern>.+)/',
           'api-1-origin-search')
@api_doc('/origin/search/')
@format_docstring(return_origin_array=DOC_RETURN_ORIGIN_ARRAY)
def api_origin_search(request, url_pattern):
    """
    .. http:get:: /api/1/origin/search/(url_pattern)/

        Search for software origins whose urls contain a provided string
        pattern or match a provided regular expression.
        The search is performed in a case insensitive way.

        :param string url_pattern: a string pattern or a regular expression
        :query int offset: the number of found origins to skip before returning
            results
        :query int limit: the maximum number of found origins to return
        :query boolean regexp: if true, consider provided pattern as a regular
            expression and search origins whose urls match it
        :query boolean with_visit: if true, only return origins with at least
            one visit by Software heritage

        {return_origin_array}

        {common_headers}

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`,
            :http:method:`options`

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/search/python/?limit=2`
    """
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
            'link-next': reverse('api-1-origin-search',
                                 url_args={'url_pattern': url_pattern},
                                 query_params=query_params)
        }

    result.update({
        'results': results
    })

    return result


@api_route(r'/origin/metadata-search/',
           'api-1-origin-metadata-search')
@api_doc('/origin/metadata-search/', noargs=True, need_params=True)
@format_docstring(return_origin_array=DOC_RETURN_ORIGIN_ARRAY)
def api_origin_metadata_search(request):
    """
    .. http:get:: /api/1/origin/metadata-search/

        Search for software origins whose metadata (expressed as a
        JSON-LD/CodeMeta dictionary) match the provided criteria.
        For now, only full-text search on this dictionary is supported.

        :query str fulltext: a string that will be matched against origin
            metadata; results are ranked and ordered starting with the best
            ones.
        :query int limit: the maximum number of found origins to return
            (bounded to 100)

        {return_origin_array}

        {common_headers}

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`,
            :http:method:`options`

        :statuscode 200: no error

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/metadata-search/?limit=2&fulltext=Jane%20Doe`
    """
    fulltext = request.query_params.get('fulltext', None)
    limit = min(int(request.query_params.get('limit', '70')), 100)

    if not fulltext:
        content = '"fulltext" must be provided and non-empty.'
        raise BadInputExc(content)

    results = api_lookup(service.search_origin_metadata, fulltext, limit)

    return {
        'results': results,
    }


@api_route(r'/origin/(?P<origin_url>.*)/visits/', 'api-1-origin-visits')
@api_route(r'/origin/(?P<origin_id>[0-9]+)/visits/', 'api-1-origin-visits')
@api_doc('/origin/visits/')
@format_docstring(
    return_origin_visit_array=DOC_RETURN_ORIGIN_VISIT_ARRAY)
def api_origin_visits(request, origin_id=None, origin_url=None):
    """
    .. http:get:: /api/1/origin/(origin_url)/visits/

        Get information about all visits of a software origin.
        Visits are returned sorted in descending order according
        to their date.

        :param str origin_url: a software origin URL
        :query int per_page: specify the number of visits to list, for
            pagination purposes
        :query int last_visit: visit to start listing from, for pagination
            purposes

        {common_headers}
        {resheader_link}

        {return_origin_visit_array}

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`,
            :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/https://github.com/hylang/hy/visits/`

    .. http:get:: /api/1/origin/(origin_id)/visits/

        Get information about all visits of a software origin.
        Visits are returned sorted in descending order according
        to their date.

        .. warning::

            All endpoints using an ``origin_id`` are  deprecated and will be
            removed in the near future. Only those using an ``origin_url``
            will remain available.
            Use :http:get:`/api/1/origin/(origin_url)/visits/` instead.

        :param int origin_id: a software origin identifier
        :query int per_page: specify the number of visits to list, for
            pagination purposes
        :query int last_visit: visit to start listing from, for pagination
            purposes

        {common_headers}
        {resheader_link}

        {return_origin_visit_array}

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`,
            :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/1/visits/`
    """
    result = {}
    if origin_url:
        origin_query = {'url': origin_url}
        notfound_msg = 'No origin {} found'.format(origin_url)
        url_args_next = {'origin_url': origin_url}
    else:
        origin_query = {'id': int(origin_id)}
        notfound_msg = 'No origin {} found'.format(origin_id)
        url_args_next = {'origin_id': origin_id}
    per_page = int(request.query_params.get('per_page', '10'))
    last_visit = request.query_params.get('last_visit')
    if last_visit:
        last_visit = int(last_visit)

    def _lookup_origin_visits(
            origin_query, last_visit=last_visit, per_page=per_page):
        all_visits = get_origin_visits(origin_query)
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

    results = api_lookup(_lookup_origin_visits, origin_query,
                         notfound_msg=notfound_msg,
                         enrich_fn=partial(_enrich_origin_visit,
                                           with_origin_link=False,
                                           with_origin_visit_link=True))

    if results:
        nb_results = len(results)
        if nb_results == per_page:
            new_last_visit = results[-1]['visit']
            query_params = {}
            query_params['last_visit'] = new_last_visit

            if request.query_params.get('per_page'):
                query_params['per_page'] = per_page

            result['headers'] = {
                'link-next': reverse('api-1-origin-visits',
                                     url_args=url_args_next,
                                     query_params=query_params)
            }

    result.update({
        'results': results
    })

    return result


@api_route(r'/origin/(?P<origin_url>.*)/visit/latest/',
           'api-1-origin-visit-latest',
           throttle_scope='swh_api_origin_visit_latest')
@api_doc('/origin/visit/')
@format_docstring(return_origin_visit=DOC_RETURN_ORIGIN_VISIT)
def api_origin_visit_latest(request, origin_url=None):
    """
    .. http:get:: /api/1/origin/(origin_url)/visit/latest/

        Get information about a specific visit of a software origin.

        :param str origin_url: a software origin URL
        :query boolean require_snapshot: if true, only return a visit
            with a snapshot

        {common_headers}

        {return_origin_visit}

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`,
            :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin or visit can not be found in the
            archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/https://github.com/hylang/hy/visit/latest/`
    """
    require_snapshot = request.query_params.get('require_snapshot', 'false')
    return api_lookup(
        service.lookup_origin_visit_latest, origin_url,
        bool(strtobool(require_snapshot)),
        notfound_msg=('No visit for origin {} found'
                      .format(origin_url)),
        enrich_fn=partial(_enrich_origin_visit,
                          with_origin_link=True,
                          with_origin_visit_link=False))


@api_route(r'/origin/(?P<origin_url>.*)/visit/(?P<visit_id>[0-9]+)/',
           'api-1-origin-visit')
@api_route(r'/origin/(?P<origin_id>[0-9]+)/visit/(?P<visit_id>[0-9]+)/',
           'api-1-origin-visit')
@api_doc('/origin/visit/')
@format_docstring(return_origin_visit=DOC_RETURN_ORIGIN_VISIT)
def api_origin_visit(request, visit_id, origin_url=None, origin_id=None):
    """
    .. http:get:: /api/1/origin/(origin_url)/visit/(visit_id)/

        Get information about a specific visit of a software origin.

        :param str origin_url: a software origin URL
        :param int visit_id: a visit identifier

        {common_headers}

        {return_origin_visit}

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`,
            :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin or visit can not be found in the
            archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/https://github.com/hylang/hy/visit/1/`

    .. http:get:: /api/1/origin/(origin_id)/visit/(visit_id)/

        Get information about a specific visit of a software origin.

        .. warning::

            All endpoints using an ``origin_id`` are  deprecated and will be
            removed in the near future. Only those using an ``origin_url``
            will remain available.
            Use :http:get:`/api/1/origin/(origin_url)/visit/(visit_id)`
            instead.

        :param int origin_id: a software origin identifier
        :param int visit_id: a visit identifier

        {common_headers}

        {return_origin_visit}

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`,
            :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin or visit can not be found in the
            archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/1500/visit/1/`
    """
    if not origin_url:
        origin_url = service.lookup_origin({'id': int(origin_id)})['url']
    return api_lookup(
        service.lookup_origin_visit, origin_url, int(visit_id),
        notfound_msg=('No visit {} for origin {} found'
                      .format(visit_id, origin_url)),
        enrich_fn=partial(_enrich_origin_visit,
                          with_origin_link=True,
                          with_origin_visit_link=False))


@api_route(r'/origin/(?P<origin_type>[a-z]+)/url/(?P<origin_url>.+)'
           '/intrinsic-metadata', 'api-origin-intrinsic-metadata')
@api_doc('/origin/intrinsic-metadata/')
@format_docstring()
def api_origin_intrinsic_metadata(request, origin_type, origin_url):
    """
    .. http:get:: /api/1/origin/(origin_type)/url/(origin_url)/intrinsic-metadata

        Get intrinsic metadata of a software origin (as a JSON-LD/CodeMeta dictionary).

        :param string origin_type: the origin type (possible values are ``git``, ``svn``,
            ``hg``, ``deb``, ``pypi``, ``npm``, ``ftp`` or ``deposit``)
        :param string origin_url: the origin url

        :>json string ???: intrinsic metadata field of the origin

        {common_headers}

        **Allowed HTTP Methods:** :http:method:`get`, :http:method:`head`, :http:method:`options`

        :statuscode 200: no error
        :statuscode 404: requested origin can not be found in the archive

        **Example:**

        .. parsed-literal::

            :swh_web_api:`origin/git/url/https://github.com/python/cpython/intrinsic-metadata`
    """ # noqa
    ori_dict = {
        'type': origin_type,
        'url': origin_url
    }

    error_msg = 'Origin with URL %s not found' % ori_dict['url']

    return api_lookup(
        service.lookup_origin_intrinsic_metadata, ori_dict,
        notfound_msg=error_msg,
        enrich_fn=_enrich_origin)
