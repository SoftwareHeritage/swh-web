# Copyright (C) 2015-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import itertools
import pytest
import random

from collections import defaultdict
from hypothesis import given

from swh.model.hashutil import hash_to_bytes, hash_to_hex
from swh.model.from_disk import DentryPerms

from swh.web.common import service
from swh.web.common.exc import BadInputExc, NotFoundExc
from swh.web.tests.strategies import (
    content, contents, unknown_content, unknown_contents,
    contents_with_ctags, origin, new_origin, visit_dates, directory,
    release, revision, unknown_revision, revisions, unknown_revisions,
    ancestor_revisions, non_ancestor_revisions, invalid_sha1, sha256,
    revision_with_submodules, unknown_directory, empty_directory,
    new_revision, new_origins
)
from swh.web.tests.testcase import (
    WebTestCase, ctags_json_missing, fossology_missing
)


class ServiceTestCase(WebTestCase):

    @given(contents())
    def test_lookup_multiple_hashes_all_present(self, contents):
        input_data = []
        expected_output = []
        for cnt in contents:
            input_data.append({'sha1': cnt['sha1']})
            expected_output.append({'sha1': cnt['sha1'],
                                    'found': True})

        self.assertEqual(service.lookup_multiple_hashes(input_data),
                         expected_output)

    @given(contents(), unknown_contents())
    def test_lookup_multiple_hashes_some_missing(self, contents,
                                                 unknown_contents):
        input_contents = list(itertools.chain(contents, unknown_contents))
        random.shuffle(input_contents)

        input_data = []
        expected_output = []
        for cnt in input_contents:
            input_data.append({'sha1': cnt['sha1']})
            expected_output.append({'sha1': cnt['sha1'],
                                    'found': cnt in contents})

        self.assertEqual(service.lookup_multiple_hashes(input_data),
                         expected_output)

    @given(unknown_content())
    def test_lookup_hash_does_not_exist(self, unknown_content):

        actual_lookup = service.lookup_hash('sha1_git:%s' %
                                            unknown_content['sha1_git'])

        self.assertEqual(actual_lookup, {'found': None,
                                         'algo': 'sha1_git'})

    @given(content())
    def test_lookup_hash_exist(self, content):

        actual_lookup = service.lookup_hash('sha1:%s' % content['sha1'])

        content_metadata = self.content_get_metadata(content['sha1'])

        self.assertEqual({'found': content_metadata,
                          'algo': 'sha1'}, actual_lookup)

    @given(unknown_content())
    def test_search_hash_does_not_exist(self, content):

        actual_lookup = service.search_hash('sha1_git:%s' %
                                            content['sha1_git'])

        self.assertEqual({'found': False}, actual_lookup)

    @given(content())
    def test_search_hash_exist(self, content):

        actual_lookup = service.search_hash('sha1:%s' % content['sha1'])

        self.assertEqual({'found': True}, actual_lookup)

    @pytest.mark.skipif(ctags_json_missing,
                        reason="requires ctags with json output support")
    @given(contents_with_ctags())
    def test_lookup_content_ctags(self, contents_with_ctags):

        content_sha1 = random.choice(contents_with_ctags['sha1s'])
        self.content_add_ctags(content_sha1)
        actual_ctags = \
            list(service.lookup_content_ctags('sha1:%s' % content_sha1))

        expected_data = list(self.content_get_ctags(content_sha1))
        for ctag in expected_data:
            ctag['id'] = content_sha1

        self.assertEqual(actual_ctags, expected_data)

    @given(unknown_content())
    def test_lookup_content_ctags_no_hash(self, unknown_content):

        actual_ctags = \
            list(service.lookup_content_ctags('sha1:%s' %
                                              unknown_content['sha1']))

        self.assertEqual(actual_ctags, [])

    @given(content())
    def test_lookup_content_filetype(self, content):

        self.content_add_mimetype(content['sha1'])
        actual_filetype = service.lookup_content_filetype(content['sha1'])

        expected_filetype = self.content_get_mimetype(content['sha1'])
        self.assertEqual(actual_filetype, expected_filetype)

    @pytest.mark.xfail  # Language indexer is disabled.
    @given(content())
    def test_lookup_content_language(self, content):

        self.content_add_language(content['sha1'])
        actual_language = service.lookup_content_language(content['sha1'])

        expected_language = self.content_get_language(content['sha1'])
        self.assertEqual(actual_language, expected_language)

    @given(contents_with_ctags())
    def test_lookup_expression(self, contents_with_ctags):

        per_page = 10
        expected_ctags = []

        for content_sha1 in contents_with_ctags['sha1s']:
            if len(expected_ctags) == per_page:
                break
            self.content_add_ctags(content_sha1)
            for ctag in self.content_get_ctags(content_sha1):
                if len(expected_ctags) == per_page:
                    break
                if ctag['name'] == contents_with_ctags['symbol_name']:
                    del ctag['id']
                    ctag['sha1'] = content_sha1
                    expected_ctags.append(ctag)

        actual_ctags = \
            list(service.lookup_expression(contents_with_ctags['symbol_name'],
                                           last_sha1=None, per_page=10))

        self.assertEqual(actual_ctags, expected_ctags)

    def test_lookup_expression_no_result(self):

        expected_ctags = []

        actual_ctags = \
            list(service.lookup_expression('barfoo', last_sha1=None,
                                           per_page=10))
        self.assertEqual(actual_ctags, expected_ctags)

    @pytest.mark.skipif(fossology_missing,
                        reason="requires fossology-nomossa installed")
    @given(content())
    def test_lookup_content_license(self, content):

        self.content_add_license(content['sha1'])
        actual_license = service.lookup_content_license(content['sha1'])

        expected_license = self.content_get_license(content['sha1'])
        self.assertEqual(actual_license, expected_license)

    def test_stat_counters(self):
        actual_stats = service.stat_counters()
        self.assertEqual(actual_stats, self.storage.stat_counters())

    @given(new_origin(), visit_dates())
    def test_lookup_origin_visits(self, new_origin, visit_dates):

        origin_id = self.storage.origin_add_one(new_origin)
        for ts in visit_dates:
            self.storage.origin_visit_add(origin_id, ts)

        actual_origin_visits = list(
            service.lookup_origin_visits(origin_id, per_page=100))

        expected_visits = self.origin_visit_get(origin_id)

        self.assertEqual(actual_origin_visits, expected_visits)

    @given(new_origin(), visit_dates())
    def test_lookup_origin_visit(self, new_origin, visit_dates):
        origin_id = self.storage.origin_add_one(new_origin)
        visits = []
        for ts in visit_dates:
            visits.append(self.storage.origin_visit_add(origin_id, ts))

        visit = random.choice(visits)['visit']
        actual_origin_visit = service.lookup_origin_visit(origin_id, visit)

        expected_visit = dict(self.storage.origin_visit_get_by(origin_id,
                                                               visit))
        expected_visit['date'] = expected_visit['date'].isoformat()
        expected_visit['metadata'] = {}

        self.assertEqual(actual_origin_visit, expected_visit)

    @given(new_origin())
    def test_lookup_origin(self, new_origin):
        origin_id = self.storage.origin_add_one(new_origin)

        actual_origin = service.lookup_origin({'id': origin_id})
        expected_origin = self.storage.origin_get({'id': origin_id})
        self.assertEqual(actual_origin, expected_origin)

        actual_origin = service.lookup_origin({'type': new_origin['type'],
                                               'url': new_origin['url']})
        expected_origin = self.storage.origin_get({'type': new_origin['type'],
                                                   'url': new_origin['url']})
        self.assertEqual(actual_origin, expected_origin)

    @given(invalid_sha1())
    def test_lookup_release_ko_id_checksum_not_a_sha1(self, invalid_sha1):
        with self.assertRaises(BadInputExc) as cm:
            service.lookup_release(invalid_sha1)
        self.assertIn('invalid checksum', cm.exception.args[0].lower())

    @given(sha256())
    def test_lookup_release_ko_id_checksum_too_long(self, sha256):
        with self.assertRaises(BadInputExc) as cm:
            service.lookup_release(sha256)
        self.assertEqual('Only sha1_git is supported.', cm.exception.args[0])

    @given(directory())
    def test_lookup_directory_with_path_not_found(self, directory):
        path = 'some/invalid/path/here'
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_directory_with_path(directory, path)
        self.assertEqual('Directory entry with path %s from %s '
                         'not found' % (path, directory),
                         cm.exception.args[0])

    @given(directory())
    def test_lookup_directory_with_path_found(self, directory):
        directory_content = self.directory_ls(directory)
        directory_entry = random.choice(directory_content)
        path = directory_entry['name']
        actual_result = service.lookup_directory_with_path(directory, path)
        self.assertEqual(actual_result, directory_entry)

    @given(release())
    def test_lookup_release(self, release):
        actual_release = service.lookup_release(release)

        self.assertEqual(actual_release,
                         self.release_get(release))

    @given(revision(), invalid_sha1(), sha256())
    def test_lookup_revision_with_context_ko_not_a_sha1(self, revision,
                                                        invalid_sha1,
                                                        sha256):
        sha1_git_root = revision
        sha1_git = invalid_sha1

        with self.assertRaises(BadInputExc) as cm:
            service.lookup_revision_with_context(sha1_git_root, sha1_git)
        self.assertIn('Invalid checksum query string', cm.exception.args[0])

        sha1_git = sha256

        with self.assertRaises(BadInputExc) as cm:
            service.lookup_revision_with_context(sha1_git_root, sha1_git)
        self.assertIn('Only sha1_git is supported', cm.exception.args[0])

    @given(revision(), unknown_revision())
    def test_lookup_revision_with_context_ko_sha1_git_does_not_exist(
            self, revision, unknown_revision):
        sha1_git_root = revision
        sha1_git = unknown_revision

        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_with_context(sha1_git_root, sha1_git)
        self.assertIn('Revision %s not found' % sha1_git, cm.exception.args[0])

    @given(revision(), unknown_revision())
    def test_lookup_revision_with_context_ko_root_sha1_git_does_not_exist(
            self, revision, unknown_revision):
        sha1_git_root = unknown_revision
        sha1_git = revision
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_with_context(sha1_git_root, sha1_git)
        self.assertIn('Revision root %s not found' % sha1_git_root,
                      cm.exception.args[0])

    @given(ancestor_revisions())
    def test_lookup_revision_with_context(self, ancestor_revisions):
        sha1_git = ancestor_revisions['sha1_git']
        root_sha1_git = ancestor_revisions['sha1_git_root']
        for sha1_git_root in (root_sha1_git,
                              {'id': hash_to_bytes(root_sha1_git)}):
            actual_revision = \
                service.lookup_revision_with_context(sha1_git_root,
                                                     sha1_git)

            children = []
            for rev in self.revision_log(root_sha1_git):
                for p_rev in rev['parents']:
                    p_rev_hex = hash_to_hex(p_rev)
                    if p_rev_hex == sha1_git:
                        children.append(rev['id'])

            expected_revision = self.revision_get(sha1_git)
            expected_revision['children'] = children
            self.assertEqual(actual_revision, expected_revision)

    @given(non_ancestor_revisions())
    def test_lookup_revision_with_context_ko(self, non_ancestor_revisions):
        sha1_git = non_ancestor_revisions['sha1_git']
        root_sha1_git = non_ancestor_revisions['sha1_git_root']

        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_with_context(root_sha1_git, sha1_git)
        self.assertIn('Revision %s is not an ancestor of %s' %
                      (sha1_git, root_sha1_git), cm.exception.args[0])

    @given(unknown_revision())
    def test_lookup_directory_with_revision_not_found(self, unknown_revision):

        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_directory_with_revision(unknown_revision)
        self.assertIn('Revision %s not found' % unknown_revision,
                      cm.exception.args[0])

    @given(unknown_content(), unknown_revision(), unknown_directory())
    def test_lookup_directory_with_revision_unknown_content(
            self, unknown_content, unknown_revision, unknown_directory):

        dir_path = 'README.md'
        # Create a revision that points to a directory
        # Which points to unknown content
        revision = {
            'author': {
                'name': b'abcd',
                'email': b'abcd@company.org',
                'fullname': b'abcd abcd'
            },
            'committer': {
                'email': b'aaaa@company.org',
                'fullname': b'aaaa aaa',
                'name': b'aaa'
            },
            'committer_date': {
                'negative_utc': False,
                'offset': 0,
                'timestamp': 1437511651
            },
            'date': {
                'negative_utc': False,
                'offset': 0,
                'timestamp': 1437511651
            },
            'message': b'bleh',
            'metadata': [],
            'parents': [],
            'synthetic': False,
            'type': 'file',
            'id': hash_to_bytes(unknown_revision),
            'directory': hash_to_bytes(unknown_directory)
        }
        # A directory that points to unknown content
        dir = {
            'id': hash_to_bytes(unknown_directory),
            'entries': [{
                'name': bytes(dir_path.encode('utf-8')),
                'type': 'file',
                'target': hash_to_bytes(unknown_content['sha1_git']),
                'perms': DentryPerms.content
            }]
        }
        # Add the directory and revision in mem
        self.storage.directory_add([dir])
        self.storage.revision_add([revision])
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_directory_with_revision(unknown_revision, dir_path)
        self.assertIn('Content not found for revision %s' % unknown_revision,
                      cm.exception.args[0])

    @given(revision())
    def test_lookup_directory_with_revision_ko_path_to_nowhere(
            self, revision):
        invalid_path = 'path/to/something/unknown'
        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_directory_with_revision(revision, invalid_path)
        exception_text = cm.exception.args[0].lower()
        self.assertIn('directory or file', exception_text)
        self.assertIn(invalid_path, exception_text)
        self.assertIn('revision %s' % revision, exception_text)
        self.assertIn('not found', exception_text)

    @given(revision_with_submodules())
    def test_lookup_directory_with_revision_submodules(
            self, revision_with_submodules):

        rev_sha1_git = revision_with_submodules['rev_sha1_git']
        rev_dir_path = revision_with_submodules['rev_dir_rev_path']

        actual_data = service.lookup_directory_with_revision(
                rev_sha1_git, rev_dir_path)

        revision = self.revision_get(revision_with_submodules['rev_sha1_git'])
        directory = self.directory_ls(revision['directory'])
        rev_entry = next(e for e in directory if e['name'] == rev_dir_path)

        expected_data = {
            'content': self.revision_get(rev_entry['target']),
            'path': rev_dir_path,
            'revision': rev_sha1_git,
            'type': 'rev'
        }

        self.assertEqual(actual_data, expected_data)

    @given(revision())
    def test_lookup_directory_with_revision_without_path(self, revision):

        actual_directory_entries = \
            service.lookup_directory_with_revision(revision)

        revision_data = self.revision_get(revision)
        expected_directory_entries = \
            self.directory_ls(revision_data['directory'])

        self.assertEqual(actual_directory_entries['type'], 'dir')
        self.assertEqual(actual_directory_entries['content'],
                         expected_directory_entries)

    @given(revision())
    def test_lookup_directory_with_revision_with_path(self, revision):

        revision_data = self.revision_get(revision)
        dir_entries = [e for e in self.directory_ls(revision_data['directory'])
                       if e['type'] in ('file', 'dir')]
        expected_dir_entry = random.choice(dir_entries)

        actual_dir_entry = \
            service.lookup_directory_with_revision(revision,
                                                   expected_dir_entry['name'])

        self.assertEqual(actual_dir_entry['type'], expected_dir_entry['type'])
        self.assertEqual(actual_dir_entry['revision'], revision)
        self.assertEqual(actual_dir_entry['path'], expected_dir_entry['name'])
        if actual_dir_entry['type'] == 'file':
            del actual_dir_entry['content']['checksums']['blake2s256']
            for key in ('checksums', 'status', 'length'):
                self.assertEqual(actual_dir_entry['content'][key],
                                 expected_dir_entry[key])
        else:
            sub_dir_entries = self.directory_ls(expected_dir_entry['target'])
            self.assertEqual(actual_dir_entry['content'], sub_dir_entries)

    @given(revision())
    def test_lookup_directory_with_revision_with_path_to_file_and_data(
            self, revision):

        revision_data = self.revision_get(revision)
        dir_entries = [e for e in self.directory_ls(revision_data['directory'])
                       if e['type'] == 'file']
        expected_dir_entry = random.choice(dir_entries)
        expected_data = \
            self.content_get(expected_dir_entry['checksums']['sha1'])

        actual_dir_entry = \
            service.lookup_directory_with_revision(revision,
                                                   expected_dir_entry['name'],
                                                   with_data=True)

        self.assertEqual(actual_dir_entry['type'], expected_dir_entry['type'])
        self.assertEqual(actual_dir_entry['revision'], revision)
        self.assertEqual(actual_dir_entry['path'], expected_dir_entry['name'])
        del actual_dir_entry['content']['checksums']['blake2s256']
        for key in ('checksums', 'status', 'length'):
            self.assertEqual(actual_dir_entry['content'][key],
                             expected_dir_entry[key])
        self.assertEqual(actual_dir_entry['content']['data'],
                         expected_data['data'])

    @given(revision())
    def test_lookup_revision(self, revision):
        actual_revision = service.lookup_revision(revision)
        self.assertEqual(actual_revision, self.revision_get(revision))

    @given(new_revision())
    def test_lookup_revision_invalid_msg(self, new_revision):

        new_revision['message'] = b'elegant fix for bug \xff'
        self.storage.revision_add([new_revision])

        revision = service.lookup_revision(hash_to_hex(new_revision['id']))
        self.assertEqual(revision['message'], None)
        self.assertEqual(revision['message_decoding_failed'], True)

    @given(new_revision())
    def test_lookup_revision_msg_ok(self, new_revision):

        self.storage.revision_add([new_revision])

        revision_message = service.lookup_revision_message(
            hash_to_hex(new_revision['id']))

        self.assertEqual(revision_message,
                         {'message': new_revision['message']})

    @given(new_revision())
    def test_lookup_revision_msg_absent(self, new_revision):

        del new_revision['message']
        self.storage.revision_add([new_revision])

        new_revision_id = hash_to_hex(new_revision['id'])

        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_message(new_revision_id)

        self.assertEqual(
            cm.exception.args[0],
            'No message for revision with sha1_git %s.' % new_revision_id
        )

    @given(unknown_revision())
    def test_lookup_revision_msg_no_rev(self, unknown_revision):

        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_revision_message(unknown_revision)

        self.assertEqual(
            cm.exception.args[0],
            'Revision with sha1_git %s not found.' % unknown_revision
        )

    @given(revisions())
    def test_lookup_revision_multiple(self, revisions):

        actual_revisions = list(service.lookup_revision_multiple(revisions))

        expected_revisions = []
        for rev in revisions:
            expected_revisions.append(self.revision_get(rev))

        self.assertEqual(actual_revisions, expected_revisions)

    @given(unknown_revisions())
    def test_lookup_revision_multiple_none_found(self, unknown_revisions):

        actual_revisions = \
            list(service.lookup_revision_multiple(unknown_revisions))

        self.assertEqual(actual_revisions, [None] * len(unknown_revisions))

    @given(revision())
    def test_lookup_revision_log(self, revision):

        actual_revision_log = \
            list(service.lookup_revision_log(revision, limit=25))
        expected_revision_log = self.revision_log(revision, limit=25)

        self.assertEqual(actual_revision_log, expected_revision_log)

    def _get_origin_branches(self, origin):
        origin_visit = self.origin_visit_get(origin['id'])[-1]
        snapshot = self.snapshot_get(origin_visit['snapshot'])
        branches = {k: v for (k, v) in snapshot['branches'].items()
                    if v['target_type'] == 'revision'}
        return branches

    @given(origin())
    def test_lookup_revision_log_by(self, origin):

        branches = self._get_origin_branches(origin)
        branch_name = random.choice(list(branches.keys()))

        actual_log =  \
            list(service.lookup_revision_log_by(origin['id'], branch_name,
                                                None, limit=25))

        expected_log = \
            self.revision_log(branches[branch_name]['target'], limit=25)

        self.assertEqual(actual_log, expected_log)

    @given(origin())
    def test_lookup_revision_log_by_notfound(self, origin):

        with self.assertRaises(NotFoundExc):
            service.lookup_revision_log_by(
                origin['id'], 'unknown_branch_name', None, limit=100)

    @given(unknown_content())
    def test_lookup_content_raw_not_found(self, unknown_content):

        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_content_raw('sha1:' + unknown_content['sha1'])

        self.assertIn(cm.exception.args[0],
                      'Content with %s checksum equals to %s not found!' %
                      ('sha1', unknown_content['sha1']))

    @given(content())
    def test_lookup_content_raw(self, content):

        actual_content = service.lookup_content_raw(
            'sha256:%s' % content['sha256'])

        expected_content = self.content_get(content['sha1'])

        self.assertEqual(actual_content, expected_content)

    @given(unknown_content())
    def test_lookup_content_not_found(self, unknown_content):

        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_content('sha1:%s' % unknown_content['sha1'])

        self.assertIn(cm.exception.args[0],
                      'Content with %s checksum equals to %s not found!' %
                      ('sha1', unknown_content['sha1']))

    @given(content())
    def test_lookup_content_with_sha1(self, content):

        actual_content = service.lookup_content(
            'sha1:%s' % content['sha1'])

        expected_content = self.content_get_metadata(content['sha1'])

        self.assertEqual(actual_content, expected_content)

    @given(content())
    def test_lookup_content_with_sha256(self, content):

        actual_content = service.lookup_content(
            'sha256:%s' % content['sha256'])

        expected_content = self.content_get_metadata(content['sha1'])

        self.assertEqual(actual_content, expected_content)

    @given(revision())
    def test_lookup_person(self, revision):

        rev_data = self.revision_get(revision)

        actual_person = service.lookup_person(rev_data['author']['id'])

        self.assertEqual(actual_person, rev_data['author'])

    def test_lookup_directory_bad_checksum(self):

        with self.assertRaises(BadInputExc):
            service.lookup_directory('directory_id')

    @given(unknown_directory())
    def test_lookup_directory_not_found(self, unknown_directory):

        with self.assertRaises(NotFoundExc) as cm:
            service.lookup_directory(unknown_directory)

        self.assertIn('Directory with sha1_git %s not found'
                      % unknown_directory, cm.exception.args[0])

    @given(directory())
    def test_lookup_directory(self, directory):

        actual_directory_ls = list(service.lookup_directory(
            directory))

        expected_directory_ls = self.directory_ls(directory)

        self.assertEqual(actual_directory_ls, expected_directory_ls)

    @given(empty_directory())
    def test_lookup_directory_empty(self, empty_directory):

        actual_directory_ls = list(service.lookup_directory(empty_directory))

        self.assertEqual(actual_directory_ls, [])

    @given(origin())
    def test_lookup_revision_by_nothing_found(self, origin):

        with self.assertRaises(NotFoundExc):
            service.lookup_revision_by(origin['id'], 'invalid-branch-name')

    @given(origin())
    def test_lookup_revision_by(self, origin):

        branches = self._get_origin_branches(origin)
        branch_name = random.choice(list(branches.keys()))

        actual_revision =  \
            service.lookup_revision_by(origin['id'], branch_name, None)

        expected_revision = \
            self.revision_get(branches[branch_name]['target'])

        self.assertEqual(actual_revision, expected_revision)

    @given(origin(), revision())
    def test_lookup_revision_with_context_by_ko(self, origin, revision):

        with self.assertRaises(NotFoundExc):
            service.lookup_revision_with_context_by(origin['id'],
                                                    'invalid-branch-name',
                                                    None,
                                                    revision)

    @given(origin())
    def test_lookup_revision_with_context_by(self, origin):

        branches = self._get_origin_branches(origin)
        branch_name = random.choice(list(branches.keys()))

        root_rev = branches[branch_name]['target']
        root_rev_log = self.revision_log(root_rev)

        children = defaultdict(list)

        for rev in root_rev_log:
            for rev_p in rev['parents']:
                children[rev_p].append(rev['id'])

        rev = root_rev_log[-1]['id']

        actual_root_rev, actual_rev = service.lookup_revision_with_context_by(
            origin['id'], branch_name, None, rev)

        expected_root_rev = self.revision_get(root_rev)
        expected_rev = self.revision_get(rev)
        expected_rev['children'] = children[rev]

        self.assertEqual(actual_root_rev, expected_root_rev)
        self.assertEqual(actual_rev, expected_rev)

    def test_lookup_revision_through_ko_not_implemented(self):

        with self.assertRaises(NotImplementedError):
            service.lookup_revision_through({
                'something-unknown': 10,
            })

    @given(origin())
    def test_lookup_revision_through_with_context_by(self, origin):

        branches = self._get_origin_branches(origin)
        branch_name = random.choice(list(branches.keys()))

        root_rev = branches[branch_name]['target']
        root_rev_log = self.revision_log(root_rev)
        rev = root_rev_log[-1]['id']

        self.assertEqual(service.lookup_revision_through({
                            'origin_id': origin['id'],
                            'branch_name': branch_name,
                            'ts': None,
                            'sha1_git': rev
                         }),
                         service.lookup_revision_with_context_by(
                            origin['id'], branch_name, None, rev)
                         )

    @given(origin())
    def test_lookup_revision_through_with_revision_by(self, origin):

        branches = self._get_origin_branches(origin)
        branch_name = random.choice(list(branches.keys()))

        self.assertEqual(service.lookup_revision_through({
                            'origin_id': origin['id'],
                            'branch_name': branch_name,
                            'ts': None,
                         }),
                         service.lookup_revision_by(
                            origin['id'], branch_name, None)
                         )

    @given(ancestor_revisions())
    def test_lookup_revision_through_with_context(self, ancestor_revisions):

        sha1_git = ancestor_revisions['sha1_git']
        sha1_git_root = ancestor_revisions['sha1_git_root']

        self.assertEqual(service.lookup_revision_through({
                            'sha1_git_root': sha1_git_root,
                            'sha1_git': sha1_git,
                         }),
                         service.lookup_revision_with_context(
                             sha1_git_root, sha1_git)

                         )

    @given(revision())
    def test_lookup_revision_through_with_revision(self, revision):

        self.assertEqual(service.lookup_revision_through({
                            'sha1_git': revision
                         }),
                         service.lookup_revision(revision)
                         )

    @given(revision())
    def test_lookup_directory_through_revision_ko_not_found(self, revision):

        with self.assertRaises(NotFoundExc):
            service.lookup_directory_through_revision(
                {'sha1_git': revision}, 'some/invalid/path')

    @given(revision())
    def test_lookup_directory_through_revision_ok(self, revision):

        revision_data = self.revision_get(revision)
        dir_entries = [e for e in self.directory_ls(revision_data['directory'])
                       if e['type'] == 'file']
        dir_entry = random.choice(dir_entries)

        self.assertEqual(
            service.lookup_directory_through_revision({'sha1_git': revision},
                                                      dir_entry['name']),
            (revision,
             service.lookup_directory_with_revision(
                revision, dir_entry['name']))
        )

    @given(revision())
    def test_lookup_directory_through_revision_ok_with_data(self, revision):

        revision_data = self.revision_get(revision)
        dir_entries = [e for e in self.directory_ls(revision_data['directory'])
                       if e['type'] == 'file']
        dir_entry = random.choice(dir_entries)

        self.assertEqual(
            service.lookup_directory_through_revision({'sha1_git': revision},
                                                      dir_entry['name'],
                                                      with_data=True),
            (revision,
             service.lookup_directory_with_revision(
                revision, dir_entry['name'], with_data=True))
        )

    @given(new_origins(20))
    def test_lookup_origins(self, new_origins):

        nb_origins = len(new_origins)
        expected_origins = self.storage.origin_add(new_origins)

        origin_from_idx = random.randint(1, nb_origins-1) - 1
        origin_from = expected_origins[origin_from_idx]['id']
        max_origin_idx = expected_origins[-1]['id']
        origin_count = random.randint(1, max_origin_idx - origin_from)

        actual_origins = list(service.lookup_origins(origin_from,
                                                     origin_count))
        expected_origins = list(self.storage.origin_get_range(origin_from,
                                                              origin_count))

        self.assertEqual(actual_origins, expected_origins)
