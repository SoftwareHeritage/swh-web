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
    def _pre_setup(self):
        cache.clear()

        tests_data = get_tests_data(reset=True)
        self.storage = tests_data['storage']
        self.idx_storage = tests_data['idx_storage']
        self.mimetype_indexer = tests_data['mimetype_indexer']
        self.license_indexer = tests_data['license_indexer']
        self.ctags_indexer = tests_data['ctags_indexer']

        # Update swh-web configuration to use the in-memory storage
        # instantiated in the tests.data module
        swh_config = config.get_config()
        swh_config.update({'storage': self.storage})
        service.storage = self.storage

        # Update swh-web configuration to use the in-memory indexer storage
        # instantiated in the tests.data modules
        swh_config.update({'indexer_storage': self.idx_storage})
        service.idx_storage = self.idx_storage

        super()._pre_setup()

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
                    self.storage.revision_log([rev_id_bytes], limit=limit)))

    def snapshot_get_latest(self, origin_id):
        snp = self.storage.snapshot_get_latest(origin_id)
        return converters.from_snapshot(snp)

    def origin_get(self, origin_info):
        origin = self.storage.origin_get(origin_info)
        return converters.from_origin(origin)

    def origin_visit_get(self, origin_id):
        visits = self.storage.origin_visit_get(origin_id)
        return list(map(converters.from_origin_visit, visits))

    def origin_visit_get_by(self, origin_id, visit_id):
        visit = self.storage.origin_visit_get_by(origin_id, visit_id)
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

    def person_get(self, person_id):
        person = next(self.storage.person_get([person_id]))
        return converters.from_person(person)
