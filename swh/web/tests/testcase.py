# Copyright (C) 2015-2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import shutil
from subprocess import run, PIPE

from django.core.cache import cache
from hypothesis.extra.django import TestCase

from swh.model.hashutil import hash_to_bytes
from swh.web import config
from swh.web.common import converters, service
from swh.web.tests.data import get_tests_data


ctags_json_missing = \
    shutil.which('ctags') is None or \
    b'+json' not in run(['ctags', '--version'], stdout=PIPE).stdout

fossology_missing = shutil.which('nomossa') is None


class WebTestCase(TestCase):
    """Base TestCase class for swh-web.

    It is initialized with references to in-memory storages containing
    raw tests data.

    It also defines class methods to retrieve those tests data in
    a json serializable format in order to ease tests implementation.

    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        tests_data = get_tests_data()
        cls.storage = tests_data['storage']
        cls.idx_storage = tests_data['idx_storage']
        cls.mimetype_indexer = tests_data['mimetype_indexer']
        cls.language_indexer = tests_data['language_indexer']
        cls.license_indexer = tests_data['license_indexer']
        cls.ctags_indexer = tests_data['ctags_indexer']

        # Update swh-web configuration to use the in-memory storage
        # instantiated in the tests.data module
        swh_config = config.get_config()
        swh_config.update({'storage': cls.storage})
        service.storage = cls.storage

        # Update swh-web configuration to use the in-memory indexer storage
        # instantiated in the tests.data modules
        swh_config.update({'indexer_storage': cls.idx_storage})
        service.idx_storage = cls.idx_storage

    @classmethod
    def content_add_mimetype(cls, cnt_id):
        cls.mimetype_indexer.run([hash_to_bytes(cnt_id)],
                                 'update-dups')

    @classmethod
    def content_get_mimetype(cls, cnt_id):
        mimetype = next(cls.idx_storage.content_mimetype_get(
                        [hash_to_bytes(cnt_id)]))
        return converters.from_filetype(mimetype)

    @classmethod
    def content_add_language(cls, cnt_id):
        cls.language_indexer.run([hash_to_bytes(cnt_id)],
                                 'update-dups')

    @classmethod
    def content_get_language(cls, cnt_id):
        lang = next(cls.idx_storage.content_language_get(
                    [hash_to_bytes(cnt_id)]))
        return converters.from_swh(lang, hashess={'id'})

    @classmethod
    def content_add_license(cls, cnt_id):
        cls.license_indexer.run([hash_to_bytes(cnt_id)],
                                'update-dups')

    @classmethod
    def content_get_license(cls, cnt_id):
        cnt_id_bytes = hash_to_bytes(cnt_id)
        lic = next(cls.idx_storage.content_fossology_license_get(
                   [cnt_id_bytes]))
        return converters.from_swh({'id': cnt_id_bytes,
                                    'facts': lic[cnt_id_bytes]},
                                   hashess={'id'})

    @classmethod
    def content_add_ctags(cls, cnt_id):
        cls.ctags_indexer.run([hash_to_bytes(cnt_id)],
                              'update-dups')

    @classmethod
    def content_get_ctags(cls, cnt_id):
        cnt_id_bytes = hash_to_bytes(cnt_id)
        ctags = cls.idx_storage.content_ctags_get([cnt_id_bytes])
        for ctag in ctags:
            yield converters.from_swh(ctag, hashess={'id'})

    @classmethod
    def content_get_metadata(cls, cnt_id):
        cnt_id_bytes = hash_to_bytes(cnt_id)
        metadata = next(cls.storage.content_get_metadata([cnt_id_bytes]))
        return converters.from_swh(metadata,
                                   hashess={'sha1', 'sha1_git', 'sha256',
                                            'blake2s256'})

    @classmethod
    def content_get(cls, cnt_id):
        cnt_id_bytes = hash_to_bytes(cnt_id)
        cnt = next(cls.storage.content_get([cnt_id_bytes]))
        return converters.from_content(cnt)

    @classmethod
    def directory_ls(cls, dir_id):
        cnt_id_bytes = hash_to_bytes(dir_id)
        dir_content = map(converters.from_directory_entry,
                          cls.storage.directory_ls(cnt_id_bytes))
        return list(dir_content)

    @classmethod
    def release_get(cls, rel_id):
        rel_id_bytes = hash_to_bytes(rel_id)
        rel_data = next(cls.storage.release_get([rel_id_bytes]))
        return converters.from_release(rel_data)

    @classmethod
    def revision_get(cls, rev_id):
        rev_id_bytes = hash_to_bytes(rev_id)
        rev_data = next(cls.storage.revision_get([rev_id_bytes]))
        return converters.from_revision(rev_data)

    @classmethod
    def revision_log(cls, rev_id, limit=None):
        rev_id_bytes = hash_to_bytes(rev_id)
        return list(map(converters.from_revision,
                    cls.storage.revision_log([rev_id_bytes], limit=limit)))

    @classmethod
    def snapshot_get_latest(cls, origin_id):
        snp = cls.storage.snapshot_get_latest(origin_id)
        return converters.from_snapshot(snp)

    @classmethod
    def origin_get(cls, origin_info):
        origin = cls.storage.origin_get(origin_info)
        return converters.from_origin(origin)

    @classmethod
    def origin_visit_get(cls, origin_id):
        visits = cls.storage.origin_visit_get(origin_id)
        return list(map(converters.from_origin_visit, visits))

    @classmethod
    def origin_visit_get_by(cls, origin_id, visit_id):
        visit = cls.storage.origin_visit_get_by(origin_id, visit_id)
        return converters.from_origin_visit(visit)

    @classmethod
    def snapshot_get(cls, snapshot_id):
        snp = cls.storage.snapshot_get(hash_to_bytes(snapshot_id))
        return converters.from_snapshot(snp)

    @classmethod
    def snapshot_get_branches(cls, snapshot_id, branches_from='',
                              branches_count=1000, target_types=None):
        snp = cls.storage.snapshot_get_branches(hash_to_bytes(snapshot_id),
                                                branches_from.encode(),
                                                branches_count, target_types)
        return converters.from_snapshot(snp)

    @classmethod
    def person_get(cls, person_id):
        person = next(cls.storage.person_get([person_id]))
        return converters.from_person(person)

    def setUp(self):
        cache.clear()
