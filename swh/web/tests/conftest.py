# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import inspect
import json
import os
import shutil
import sys

from subprocess import run, PIPE

import pytest

from django.core.cache import cache
from hypothesis import settings, HealthCheck
from rest_framework.test import APIClient, APIRequestFactory

from swh.model.hashutil import ALGORITHMS, hash_to_bytes
from swh.web.common import converters
from swh.web.tests.data import get_tests_data, override_storages

# Used to skip some tests
ctags_json_missing = (
    shutil.which('ctags') is None or
    b'+json' not in run(['ctags', '--version'], stdout=PIPE).stdout
)

fossology_missing = shutil.which('nomossa') is None

# Register some hypothesis profiles
settings.register_profile('default', settings())

settings.register_profile(
    'swh-web',
    settings(deadline=None,
             suppress_health_check=[HealthCheck.too_slow,
                                    HealthCheck.filter_too_much]))

settings.register_profile(
    'swh-web-fast',
    settings(deadline=None, max_examples=1,
             suppress_health_check=[HealthCheck.too_slow,
                                    HealthCheck.filter_too_much]))


def pytest_configure(config):
    # Small hack in order to be able to run the unit tests
    # without static assets generated by webpack.
    # Those assets are not really needed for the Python tests
    # but the django templates will fail to load due to missing
    # generated file webpack-stats.json describing the js and css
    # files to include.
    # So generate a dummy webpack-stats.json file to overcome
    # that issue.
    test_dir = os.path.dirname(__file__)
    # location of the static folder when running tests through tox
    static_dir = os.path.join(sys.prefix, 'share/swh/web/static')

    if not os.path.exists(static_dir):
        # location of the static folder when running tests locally with pytest
        static_dir = os.path.join(test_dir, '../../../static')
    webpack_stats = os.path.join(static_dir, 'webpack-stats.json')
    if os.path.exists(webpack_stats):
        return
    bundles_dir = os.path.join(test_dir, '../assets/src/bundles')
    _, dirs, _ = next(os.walk(bundles_dir))
    mock_webpack_stats = {
        'status': 'done',
        'publicPath': '/static',
        'chunks': {}
    }
    for bundle in dirs:
        asset = 'js/%s.js' % bundle
        mock_webpack_stats['chunks'][bundle] = [{
            'name': asset,
            'publicPath': '/static/%s' % asset,
            'path': os.path.join(static_dir, asset)
        }]

    with open(webpack_stats, 'w') as outfile:
        json.dump(mock_webpack_stats, outfile)


# Clear Django cache before each test
@pytest.fixture(autouse=True)
def django_cache_cleared():
    cache.clear()


# Alias rf fixture from pytest-django
@pytest.fixture
def request_factory(rf):
    return rf

# Fixture to get test client from Django REST Framework
@pytest.fixture(scope='module')
def api_client():
    return APIClient()


# Fixture to get API request factory from Django REST Framework
@pytest.fixture(scope='module')
def api_request_factory():
    return APIRequestFactory()


# Initialize tests data
@pytest.fixture(autouse=True)
def tests_data():
    data = get_tests_data(reset=True)
    # Update swh-web configuration to use the in-memory storages
    # instantiated in the tests.data module
    override_storages(data['storage'], data['idx_storage'], data['search'])
    return data


# Fixture to manipulate data from a sample archive used in the tests
@pytest.fixture
def archive_data(tests_data):
    return _ArchiveData(tests_data)


# Fixture to manipulate indexer data from a sample archive used in the tests
@pytest.fixture
def indexer_data(tests_data):
    return _IndexerData(tests_data)


# Custom data directory for requests_mock
@pytest.fixture
def datadir():
    return os.path.join(os.path.abspath(os.path.dirname(__file__)),
                        'resources')


class _ArchiveData:
    """
    Helper class to manage data from a sample test archive.

    It is initialized with a reference to an in-memory storage
    containing raw tests data.

    It is basically a proxy to Storage interface but it overrides some methods
    to retrieve those tests data in a json serializable format in order to ease
    tests implementation.
    """

    def __init__(self, tests_data):
        self.storage = tests_data['storage']

        def _call_storage_method(method):
            def call_storage_method(*args, **kwargs):
                return method(*args, **kwargs)

            return call_storage_method

        # Forward calls to non overridden Storage methods to wrapped
        # storage instance
        for method_name, method in inspect.getmembers(
                self.storage, predicate=inspect.ismethod):
            if (not hasattr(self, method_name) and
                    not method_name.startswith('_')):
                setattr(self, method_name, _call_storage_method(method))

    def content_find(self, content):
        cnt_ids_bytes = {algo_hash: hash_to_bytes(content[algo_hash])
                         for algo_hash in ALGORITHMS
                         if content.get(algo_hash)}
        cnt = self.storage.content_find(cnt_ids_bytes)
        return converters.from_content(cnt[0]) if cnt else cnt

    def content_get_metadata(self, cnt_id):
        cnt_id_bytes = hash_to_bytes(cnt_id)
        metadata = next(self.storage.content_get_metadata([cnt_id_bytes]))
        return converters.from_swh(metadata,
                                   hashess={'sha1', 'sha1_git', 'sha256',
                                            'blake2s256'})

    def content_get(self, cnt_id):
        cnt_id_bytes = hash_to_bytes(cnt_id)
        cnt = next(self.storage.content_get([cnt_id_bytes]))
        return converters.from_content(cnt)

    def directory_get(self, dir_id):
        return {
            'id': dir_id,
            'content': self.directory_ls(dir_id)
        }

    def directory_ls(self, dir_id):
        cnt_id_bytes = hash_to_bytes(dir_id)
        dir_content = map(converters.from_directory_entry,
                          self.storage.directory_ls(cnt_id_bytes))
        return list(dir_content)

    def release_get(self, rel_id):
        rel_id_bytes = hash_to_bytes(rel_id)
        rel_data = next(self.storage.release_get([rel_id_bytes]))
        return converters.from_release(rel_data)

    def revision_get(self, rev_id):
        rev_id_bytes = hash_to_bytes(rev_id)
        rev_data = next(self.storage.revision_get([rev_id_bytes]))
        return converters.from_revision(rev_data)

    def revision_log(self, rev_id, limit=None):
        rev_id_bytes = hash_to_bytes(rev_id)
        return list(map(converters.from_revision,
                        self.storage.revision_log([rev_id_bytes],
                                                  limit=limit)))

    def snapshot_get_latest(self, origin_url):
        snp = self.storage.snapshot_get_latest(origin_url)
        return converters.from_snapshot(snp)

    def origin_get(self, origin_info):
        origin = self.storage.origin_get(origin_info)
        return converters.from_origin(origin)

    def origin_visit_get(self, origin_url):
        visits = self.storage.origin_visit_get(origin_url)
        return list(map(converters.from_origin_visit, visits))

    def origin_visit_get_by(self, origin_url, visit_id):
        visit = self.storage.origin_visit_get_by(origin_url, visit_id)
        return converters.from_origin_visit(visit)

    def snapshot_get(self, snapshot_id):
        snp = self.storage.snapshot_get(hash_to_bytes(snapshot_id))
        return converters.from_snapshot(snp)

    def snapshot_get_branches(self, snapshot_id, branches_from='',
                              branches_count=1000, target_types=None):
        snp = self.storage.snapshot_get_branches(
            hash_to_bytes(snapshot_id), branches_from.encode(),
            branches_count, target_types)
        return converters.from_snapshot(snp)

    def snapshot_get_head(self, snapshot):
        if snapshot['branches']['HEAD']['target_type'] == 'alias':
            target = snapshot['branches']['HEAD']['target']
            head = snapshot['branches'][target]['target']
        else:
            head = snapshot['branches']['HEAD']['target']
        return head


class _IndexerData:
    """
    Helper class to manage indexer tests data

    It is initialized with a reference to an in-memory indexer storage
    containing raw tests data.

    It also defines class methods to retrieve those tests data in
    a json serializable format in order to ease tests implementation.

    """

    def __init__(self, tests_data):
        self.idx_storage = tests_data['idx_storage']
        self.mimetype_indexer = tests_data['mimetype_indexer']
        self.license_indexer = tests_data['license_indexer']
        self.ctags_indexer = tests_data['ctags_indexer']

    def content_add_mimetype(self, cnt_id):
        self.mimetype_indexer.run([hash_to_bytes(cnt_id)],
                                  'update-dups')

    def content_get_mimetype(self, cnt_id):
        mimetype = next(self.idx_storage.content_mimetype_get(
                        [hash_to_bytes(cnt_id)]))
        return converters.from_filetype(mimetype)

    def content_add_language(self, cnt_id):
        raise NotImplementedError('Language indexer is disabled.')
        self.language_indexer.run([hash_to_bytes(cnt_id)],
                                  'update-dups')

    def content_get_language(self, cnt_id):
        lang = next(self.idx_storage.content_language_get(
                    [hash_to_bytes(cnt_id)]))
        return converters.from_swh(lang, hashess={'id'})

    def content_add_license(self, cnt_id):
        self.license_indexer.run([hash_to_bytes(cnt_id)],
                                 'update-dups')

    def content_get_license(self, cnt_id):
        cnt_id_bytes = hash_to_bytes(cnt_id)
        lic = next(self.idx_storage.content_fossology_license_get(
                   [cnt_id_bytes]))
        return converters.from_swh({'id': cnt_id_bytes,
                                    'facts': lic[cnt_id_bytes]},
                                   hashess={'id'})

    def content_add_ctags(self, cnt_id):
        self.ctags_indexer.run([hash_to_bytes(cnt_id)],
                               'update-dups')

    def content_get_ctags(self, cnt_id):
        cnt_id_bytes = hash_to_bytes(cnt_id)
        ctags = self.idx_storage.content_ctags_get([cnt_id_bytes])
        for ctag in ctags:
            yield converters.from_swh(ctag, hashess={'id'})
