# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from unittest.mock import patch

from hypothesis import given, strategies
import pytest
from requests.utils import parse_header_links
from rest_framework.test import APITestCase

from swh.storage.exc import StorageDBError, StorageAPIError

from swh.web.common.utils import reverse
from swh.web.common.origin_visits import get_origin_visits
from swh.web.tests.strategies import (
    origin, new_origin, visit_dates, new_snapshots
)
from swh.web.tests.testcase import WebTestCase
from swh.web.tests.data import get_tests_data


class OriginApiTestCase(WebTestCase, APITestCase):
    def _scroll_results(self, url):
        """Iterates through pages of results, and returns them all."""
        results = []

        while True:
            rv = self.client.get(url)
            self.assertEqual(rv.status_code, 200, rv.data)
            self.assertEqual(rv['Content-Type'], 'application/json')

            results.extend(rv.data)

            if 'Link' in rv:
                for link in parse_header_links(rv['Link']):
                    if link['rel'] == 'next':
                        # Found link to next page of results
                        url = link['url']
                        break
                else:
                    # No link with 'rel=next'
                    break
            else:
                # No Link header
                break

        return results

    @patch('swh.web.api.views.origin.get_origin_visits')
    def test_api_lookup_origin_visits_raise_error(
        self, mock_get_origin_visits,
    ):

        err_msg = 'voluntary error to check the bad request middleware.'

        mock_get_origin_visits.side_effect = ValueError(err_msg)

        url = reverse(
            'api-1-origin-visits', url_args={'origin_url': 'http://foo'})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 400, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'ValueError',
            'reason': err_msg})

    @patch('swh.web.api.views.origin.get_origin_visits')
    def test_api_lookup_origin_visits_raise_swh_storage_error_db(
            self, mock_get_origin_visits):

        err_msg = 'Storage exploded! Will be back online shortly!'

        mock_get_origin_visits.side_effect = StorageDBError(err_msg)

        url = reverse(
            'api-1-origin-visits', url_args={'origin_url': 'http://foo'})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 503, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'StorageDBError',
            'reason':
            'An unexpected error occurred in the backend: %s' % err_msg})

    @patch('swh.web.api.views.origin.get_origin_visits')
    def test_api_lookup_origin_visits_raise_swh_storage_error_api(
            self, mock_get_origin_visits):

        err_msg = 'Storage API dropped dead! Will resurrect asap!'

        mock_get_origin_visits.side_effect = StorageAPIError(err_msg)

        url = reverse(
            'api-1-origin-visits', url_args={'origin_url': 'http://foo'})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 503, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'StorageAPIError',
            'reason':
            'An unexpected error occurred in the api backend: %s' % err_msg
        })

    @given(new_origin(), visit_dates(3), new_snapshots(3))
    def test_api_lookup_origin_visits(self, new_origin, visit_dates,
                                      new_snapshots):

        self.storage.origin_add_one(new_origin)
        for i, visit_date in enumerate(visit_dates):
            origin_visit = self.storage.origin_visit_add(
                new_origin['url'], visit_date)
            self.storage.snapshot_add([new_snapshots[i]])
            self.storage.origin_visit_update(
                new_origin['url'], origin_visit['visit'],
                snapshot=new_snapshots[i]['id'])

        all_visits = list(reversed(get_origin_visits(new_origin)))

        for last_visit, expected_visits in (
                (None, all_visits[:2]),
                (all_visits[1]['visit'], all_visits[2:4])):

            url = reverse('api-1-origin-visits',
                          url_args={'origin_url': new_origin['url']},
                          query_params={'per_page': 2,
                                        'last_visit': last_visit})

            rv = self.client.get(url)

            self.assertEqual(rv.status_code, 200, rv.data)
            self.assertEqual(rv['Content-Type'], 'application/json')

            for expected_visit in expected_visits:
                origin_visit_url = reverse(
                    'api-1-origin-visit',
                    url_args={'origin_url': new_origin['url'],
                              'visit_id': expected_visit['visit']})
                snapshot_url = reverse(
                    'api-1-snapshot',
                    url_args={'snapshot_id': expected_visit['snapshot']})
                expected_visit['origin'] = new_origin['url']
                expected_visit['origin_visit_url'] = origin_visit_url
                expected_visit['snapshot_url'] = snapshot_url

            self.assertEqual(rv.data, expected_visits)

    @given(new_origin(), visit_dates(3), new_snapshots(3))
    def test_api_lookup_origin_visits_by_id(self, new_origin, visit_dates,
                                            new_snapshots):

        self.storage.origin_add_one(new_origin)
        for i, visit_date in enumerate(visit_dates):
            origin_visit = self.storage.origin_visit_add(
                new_origin['url'], visit_date)
            self.storage.snapshot_add([new_snapshots[i]])
            self.storage.origin_visit_update(
                new_origin['url'], origin_visit['visit'],
                snapshot=new_snapshots[i]['id'])

        all_visits = list(reversed(get_origin_visits(new_origin)))

        for last_visit, expected_visits in (
                (None, all_visits[:2]),
                (all_visits[1]['visit'], all_visits[2:4])):

            url = reverse('api-1-origin-visits',
                          url_args={'origin_url': new_origin['url']},
                          query_params={'per_page': 2,
                                        'last_visit': last_visit})

            rv = self.client.get(url)

            self.assertEqual(rv.status_code, 200, rv.data)
            self.assertEqual(rv['Content-Type'], 'application/json')

            for expected_visit in expected_visits:
                origin_visit_url = reverse(
                    'api-1-origin-visit',
                    url_args={'origin_url': new_origin['url'],
                              'visit_id': expected_visit['visit']})
                snapshot_url = reverse(
                    'api-1-snapshot',
                    url_args={'snapshot_id': expected_visit['snapshot']})
                expected_visit['origin'] = new_origin['url']
                expected_visit['origin_visit_url'] = origin_visit_url
                expected_visit['snapshot_url'] = snapshot_url

            self.assertEqual(rv.data, expected_visits)

    @given(new_origin(), visit_dates(3), new_snapshots(3))
    def test_api_lookup_origin_visit(self, new_origin, visit_dates,
                                     new_snapshots):

        self.storage.origin_add_one(new_origin)
        for i, visit_date in enumerate(visit_dates):
            origin_visit = self.storage.origin_visit_add(
                new_origin['url'], visit_date)
            visit_id = origin_visit['visit']
            self.storage.snapshot_add([new_snapshots[i]])
            self.storage.origin_visit_update(
                new_origin['url'], origin_visit['visit'],
                snapshot=new_snapshots[i]['id'])
            url = reverse('api-1-origin-visit',
                          url_args={'origin_url': new_origin['url'],
                                    'visit_id': visit_id})

            rv = self.client.get(url)
            self.assertEqual(rv.status_code, 200, rv.data)
            self.assertEqual(rv['Content-Type'], 'application/json')

            expected_visit = self.origin_visit_get_by(
                new_origin['url'], visit_id)

            origin_url = reverse('api-1-origin',
                                 url_args={'origin_url': new_origin['url']})
            snapshot_url = reverse(
                'api-1-snapshot',
                url_args={'snapshot_id': expected_visit['snapshot']})

            expected_visit['origin'] = new_origin['url']
            expected_visit['origin_url'] = origin_url
            expected_visit['snapshot_url'] = snapshot_url

            self.assertEqual(rv.data, expected_visit)

    @given(new_origin(), visit_dates(2), new_snapshots(1))
    def test_api_lookup_origin_visit_latest(
            self, new_origin, visit_dates, new_snapshots):

        self.storage.origin_add_one(new_origin)
        visit_dates.sort()
        visit_ids = []
        for i, visit_date in enumerate(visit_dates):
            origin_visit = self.storage.origin_visit_add(
                new_origin['url'], visit_date)
            visit_ids.append(origin_visit['visit'])

        self.storage.snapshot_add([new_snapshots[0]])
        self.storage.origin_visit_update(
            new_origin['url'], visit_ids[0],
            snapshot=new_snapshots[0]['id'])

        url = reverse('api-1-origin-visit-latest',
                      url_args={'origin_url': new_origin['url']})

        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')

        expected_visit = self.origin_visit_get_by(
            new_origin['url'], visit_ids[1])

        origin_url = reverse('api-1-origin',
                             url_args={'origin_url': new_origin['url']})

        expected_visit['origin'] = new_origin['url']
        expected_visit['origin_url'] = origin_url
        expected_visit['snapshot_url'] = None

        self.assertEqual(rv.data, expected_visit)

    @given(new_origin(), visit_dates(2), new_snapshots(1))
    def test_api_lookup_origin_visit_latest_with_snapshot(
            self, new_origin, visit_dates, new_snapshots):
        self.storage.origin_add_one(new_origin)
        visit_dates.sort()
        visit_ids = []
        for i, visit_date in enumerate(visit_dates):
            origin_visit = self.storage.origin_visit_add(
                new_origin['url'], visit_date)
            visit_ids.append(origin_visit['visit'])

        self.storage.snapshot_add([new_snapshots[0]])
        self.storage.origin_visit_update(
            new_origin['url'], visit_ids[0],
            snapshot=new_snapshots[0]['id'])

        url = reverse('api-1-origin-visit-latest',
                      url_args={'origin_url': new_origin['url']})
        url += '?require_snapshot=true'

        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')

        expected_visit = self.origin_visit_get_by(
            new_origin['url'], visit_ids[0])

        origin_url = reverse('api-1-origin',
                             url_args={'origin_url': new_origin['url']})
        snapshot_url = reverse(
            'api-1-snapshot',
            url_args={'snapshot_id': expected_visit['snapshot']})

        expected_visit['origin'] = new_origin['url']
        expected_visit['origin_url'] = origin_url
        expected_visit['snapshot_url'] = snapshot_url

        self.assertEqual(rv.data, expected_visit)

    @given(origin())
    def test_api_lookup_origin_visit_not_found(self, origin):

        all_visits = list(reversed(get_origin_visits(origin)))

        max_visit_id = max([v['visit'] for v in all_visits])

        url = reverse('api-1-origin-visit',
                      url_args={'origin_url': origin['url'],
                                'visit_id': max_visit_id + 1})

        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Origin %s or its visit with id %s not found!' %
            (origin['url'], max_visit_id+1)
        })

    @pytest.mark.origin_id
    def test_api_origins(self):
        origins = get_tests_data()['origins']
        origin_urls = {origin['url'] for origin in origins}

        # Get only one
        url = reverse('api-1-origins',
                      query_params={'origin_count': 1})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(len(rv.data), 1)
        self.assertLess({origin['url'] for origin in rv.data}, origin_urls)

        # Get all
        url = reverse('api-1-origins',
                      query_params={'origin_count': len(origins)})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(len(rv.data), len(origins))
        self.assertEqual({origin['url'] for origin in rv.data}, origin_urls)

        # Get "all + 10"
        url = reverse('api-1-origins',
                      query_params={'origin_count': len(origins)+10})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(len(rv.data), len(origins))
        self.assertEqual({origin['url'] for origin in rv.data}, origin_urls)

    @pytest.mark.origin_id
    @given(strategies.integers(min_value=1))
    def test_api_origins_scroll(self, origin_count):
        origins = get_tests_data()['origins']
        origin_urls = {origin['url'] for origin in origins}

        url = reverse('api-1-origins',
                      query_params={'origin_count': origin_count})

        results = self._scroll_results(url)

        self.assertEqual(len(results), len(origins))
        self.assertEqual({origin['url'] for origin in results}, origin_urls)

    @given(origin())
    def test_api_origin_by_url(self, origin):

        url = reverse('api-1-origin',
                      url_args={'origin_url': origin['url']})
        rv = self.client.get(url)

        expected_origin = self.origin_get(origin)

        origin_visits_url = reverse('api-1-origin-visits',
                                    url_args={'origin_url': origin['url']})

        expected_origin['origin_visits_url'] = origin_visits_url

        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_origin)

    @given(origin())
    def test_api_origin_by_type_url(self, origin):

        url = reverse('api-1-origin',
                      url_args={'origin_type': origin['type'],
                                'origin_url': origin['url']})
        rv = self.client.get(url)

        expected_origin = self.origin_get(origin)

        origin_visits_url = reverse('api-1-origin-visits',
                                    url_args={'origin_url': origin['url']})

        expected_origin['origin_visits_url'] = origin_visits_url

        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, expected_origin)

    @given(new_origin())
    def test_api_origin_not_found(self, new_origin):

        url = reverse('api-1-origin',
                      url_args={'origin_type': new_origin['type'],
                                'origin_url': new_origin['url']})
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 404, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(rv.data, {
            'exception': 'NotFoundExc',
            'reason': 'Origin %s not found!' % new_origin['url']
        })

    @pytest.mark.origin_id
    def test_api_origin_search(self):
        expected_origins = {
            'https://github.com/wcoder/highlightjs-line-numbers.js',
            'https://github.com/memononen/libtess2',
        }

        # Search for 'github.com', get only one
        url = reverse('api-1-origin-search',
                      url_args={'url_pattern': 'github.com'},
                      query_params={'limit': 1})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual(len(rv.data), 1)
        self.assertLess({origin['url'] for origin in rv.data},
                        expected_origins)

        # Search for 'github.com', get all
        url = reverse('api-1-origin-search',
                      url_args={'url_pattern': 'github.com'},
                      query_params={'limit': 2})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual({origin['url'] for origin in rv.data},
                         expected_origins)

        # Search for 'github.com', get more than available
        url = reverse('api-1-origin-search',
                      url_args={'url_pattern': 'github.com'},
                      query_params={'limit': 10})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual({origin['url'] for origin in rv.data},
                         expected_origins)

    @pytest.mark.origin_id
    def test_api_origin_search_regexp(self):
        expected_origins = {
            'https://github.com/memononen/libtess2',
            'repo_with_submodules'
        }

        url = reverse('api-1-origin-search',
                      url_args={'url_pattern': '(repo|libtess)'},
                      query_params={'limit': 10,
                                    'regexp': True})
        rv = self.client.get(url)
        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertEqual(rv['Content-Type'], 'application/json')
        self.assertEqual({origin['url'] for origin in rv.data},
                         expected_origins)

    @pytest.mark.origin_id
    @given(strategies.integers(min_value=1))
    def test_api_origin_search_scroll(self, limit):
        expected_origins = {
            'https://github.com/wcoder/highlightjs-line-numbers.js',
            'https://github.com/memononen/libtess2',
        }

        url = reverse('api-1-origin-search',
                      url_args={'url_pattern': 'github.com'},
                      query_params={'limit': limit})

        results = self._scroll_results(url)

        self.assertEqual({origin['url'] for origin in results},
                         expected_origins)

    @given(origin())
    def test_api_origin_metadata_search(self, origin):
        with patch('swh.web.common.service.idx_storage') as mock_idx_storage:
            mock_idx_storage.origin_intrinsic_metadata_search_fulltext \
                .side_effect = lambda conjunction, limit: [{
                    'from_revision': (
                        b'p&\xb7\xc1\xa2\xafVR\x1e\x95\x1c\x01\xed '
                        b'\xf2U\xfa\x05B8'),
                    'metadata': {'author': 'Jane Doe'},
                    'origin_url': origin['url'],
                    'tool': {
                        'configuration': {
                            'context': ['NpmMapping', 'CodemetaMapping'],
                            'type': 'local'
                        },
                        'id': 3,
                        'name': 'swh-metadata-detector',
                        'version': '0.0.1'
                    }
                }]

            url = reverse('api-1-origin-metadata-search',
                          query_params={'fulltext': 'Jane Doe'})
            rv = self.client.get(url)

            self.assertEqual(rv.status_code, 200, rv.content)
            self.assertEqual(rv['Content-Type'], 'application/json')
            expected_data = [{
                'type': origin['type'],
                'url': origin['url'],
                'metadata': {
                    'metadata': {'author': 'Jane Doe'},
                    'from_revision': (
                        '7026b7c1a2af56521e951c01ed20f255fa054238'),
                    'tool': {
                        'configuration': {
                            'context': ['NpmMapping', 'CodemetaMapping'],
                            'type': 'local'
                        },
                        'id': 3,
                        'name': 'swh-metadata-detector',
                        'version': '0.0.1',
                    }
                }
            }]
            actual_data = rv.data
            for d in actual_data:
                if 'id' in d:
                    del d['id']
            self.assertEqual(rv.data, expected_data)
            mock_idx_storage.origin_intrinsic_metadata_search_fulltext \
                .assert_called_with(conjunction=['Jane Doe'], limit=70)

    @given(origin())
    def test_api_origin_metadata_search_limit(self, origin):
        with patch('swh.web.common.service.idx_storage') as mock_idx_storage:
            mock_idx_storage.origin_intrinsic_metadata_search_fulltext \
                .side_effect = lambda conjunction, limit: [{
                    'from_revision': (
                        b'p&\xb7\xc1\xa2\xafVR\x1e\x95\x1c\x01\xed '
                        b'\xf2U\xfa\x05B8'),
                    'metadata': {'author': 'Jane Doe'},
                    'origin_url': origin['url'],
                    'tool': {
                        'configuration': {
                            'context': ['NpmMapping', 'CodemetaMapping'],
                            'type': 'local'
                        },
                        'id': 3,
                        'name': 'swh-metadata-detector',
                        'version': '0.0.1'
                    }
                }]

            url = reverse('api-1-origin-metadata-search',
                          query_params={'fulltext': 'Jane Doe'})
            rv = self.client.get(url)

            self.assertEqual(rv.status_code, 200, rv.content)
            self.assertEqual(rv['Content-Type'], 'application/json')
            self.assertEqual(len(rv.data), 1)
            mock_idx_storage.origin_intrinsic_metadata_search_fulltext \
                .assert_called_with(conjunction=['Jane Doe'], limit=70)

            url = reverse('api-1-origin-metadata-search',
                          query_params={'fulltext': 'Jane Doe',
                                        'limit': 10})
            rv = self.client.get(url)

            self.assertEqual(rv.status_code, 200, rv.content)
            self.assertEqual(rv['Content-Type'], 'application/json')
            self.assertEqual(len(rv.data), 1)
            mock_idx_storage.origin_intrinsic_metadata_search_fulltext \
                .assert_called_with(conjunction=['Jane Doe'], limit=10)

            url = reverse('api-1-origin-metadata-search',
                          query_params={'fulltext': 'Jane Doe',
                                        'limit': 987})
            rv = self.client.get(url)

            self.assertEqual(rv.status_code, 200, rv.content)
            self.assertEqual(rv['Content-Type'], 'application/json')
            self.assertEqual(len(rv.data), 1)
            mock_idx_storage.origin_intrinsic_metadata_search_fulltext \
                .assert_called_with(conjunction=['Jane Doe'], limit=100)

    @given(origin())
    def test_api_origin_intrinsic_metadata(self, origin):
        with patch('swh.web.common.service.idx_storage') as mock_idx_storage:
            mock_idx_storage.origin_intrinsic_metadata_get \
                .side_effect = lambda origin_urls: [{
                    'from_revision': (
                        b'p&\xb7\xc1\xa2\xafVR\x1e\x95\x1c\x01\xed '
                        b'\xf2U\xfa\x05B8'),
                    'metadata': {'author': 'Jane Doe'},
                    'origin_url': origin['url'],
                    'tool': {
                        'configuration': {
                            'context': ['NpmMapping', 'CodemetaMapping'],
                            'type': 'local'
                        },
                        'id': 3,
                        'name': 'swh-metadata-detector',
                        'version': '0.0.1'
                    }
                }]

            url = reverse('api-origin-intrinsic-metadata',
                          url_args={'origin_type': origin['type'],
                                    'origin_url': origin['url']})
            rv = self.client.get(url)

            mock_idx_storage.origin_intrinsic_metadata_get \
                            .assert_called_once_with([origin['url']])
            self.assertEqual(rv.status_code, 200, rv.content)
            self.assertEqual(rv['Content-Type'], 'application/json')
            expected_data = {'author': 'Jane Doe'}
            self.assertEqual(rv.data, expected_data)

    @patch('swh.web.common.service.idx_storage')
    def test_api_origin_metadata_search_invalid(self, mock_idx_storage):

        url = reverse('api-1-origin-metadata-search')
        rv = self.client.get(url)

        self.assertEqual(rv.status_code, 400, rv.content)
        mock_idx_storage.assert_not_called()
