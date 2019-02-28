# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
import time

from swh.indexer.language import LanguageIndexer
from swh.indexer.fossology_license import FossologyLicenseIndexer
from swh.indexer.mimetype import MimetypeIndexer
from swh.indexer.ctags import CtagsIndexer
from swh.indexer.storage import get_indexer_storage
from swh.model.hashutil import hash_to_hex, hash_to_bytes, DEFAULT_ALGORITHMS
from swh.model.identifiers import directory_identifier
from swh.loader.git.from_disk import GitLoaderFromArchive
from swh.storage.algos.dir_iterators import dir_iterator
from swh.web.browse.utils import (
    get_mimetype_and_encoding_for_content, prepare_content_for_display
)

# Module used to initialize data that will be provided as tests input

# Configuration for git loader
_TEST_LOADER_CONFIG = {
    'storage': {
        'cls': 'memory',
        'args': {}
    },
    'send_contents': True,
    'send_directories': True,
    'send_revisions': True,
    'send_releases': True,
    'send_snapshot': True,

    'content_size_limit': 100 * 1024 * 1024,
    'content_packet_size': 10,
    'content_packet_size_bytes': 100 * 1024 * 1024,
    'directory_packet_size': 10,
    'revision_packet_size': 10,
    'release_packet_size': 10,

    'save_data': False,
}

# Base content indexer configuration
_TEST_INDEXER_BASE_CONFIG = {
    'storage': {
        'cls': 'memory',
        'args': {},
    },
    'objstorage': {
        'cls': 'memory',
        'args': {},
    },
    'indexer_storage': {
        'cls': 'memory',
        'args': {},
    }
}


# MimetypeIndexer with custom configuration for tests
class _MimetypeIndexer(MimetypeIndexer):
    def parse_config_file(self, *args, **kwargs):
        return {
            **_TEST_INDEXER_BASE_CONFIG,
            'tools': {
                'name': 'file',
                'version': '1:5.30-1+deb9u1',
                'configuration': {
                    "type": "library",
                    "debian-package": "python3-magic"
                }
            }
        }


# LanguageIndexer with custom configuration for tests
class _LanguageIndexer(LanguageIndexer):
    def parse_config_file(self, *args, **kwargs):
        return {
            **_TEST_INDEXER_BASE_CONFIG,
            'tools': {
                'name': 'pygments',
                'version': '2.0.1+dfsg-1.1+deb8u1',
                'configuration': {
                    'type': 'library',
                    'debian-package': 'python3-pygments',
                    'max_content_size': 10240,
                }
            }
        }


# FossologyLicenseIndexer with custom configuration for tests
class _FossologyLicenseIndexer(FossologyLicenseIndexer):
    def parse_config_file(self, *args, **kwargs):
        return {
            **_TEST_INDEXER_BASE_CONFIG,
            'workdir': '/tmp/swh/indexer.fossology.license',
            'tools': {
                'name': 'nomos',
                'version': '3.1.0rc2-31-ga2cbb8c',
                'configuration': {
                    'command_line': 'nomossa <filepath>',
                },
            }
        }


# CtagsIndexer with custom configuration for tests
class _CtagsIndexer(CtagsIndexer):
    def parse_config_file(self, *args, **kwargs):
        return {
            **_TEST_INDEXER_BASE_CONFIG,
            'workdir': '/tmp/swh/indexer.ctags',
            'languages': {'c': 'c'},
            'tools': {
                'name': 'universal-ctags',
                'version': '~git7859817b',
                'configuration': {
                    'command_line': '''ctags --fields=+lnz --sort=no --links=no ''' # noqa
                                    '''--output-format=json <filepath>'''
                },
            }
        }


# Lightweight git repositories that will be loaded to generate
# input data for tests
_TEST_ORIGINS = [
    {
        'id': 1,
        'type': 'git',
        'url': 'https://github.com/wcoder/highlightjs-line-numbers.js',
        'archives': ['highlightjs-line-numbers.js.zip',
                     'highlightjs-line-numbers.js_visit2.zip']
    },
    {
        'id': 2,
        'type': 'git',
        'url': 'https://github.com/memononen/libtess2',
        'archives': ['libtess2.zip']
    },
    {
        'id': 3,
        'type': 'git',
        'url': 'repo_with_submodules',
        'archives': ['repo_with_submodules.tgz']
    }
]

_contents = {}


# Tests data initialization
def _init_tests_data():
    # Load git repositories from archives
    loader = GitLoaderFromArchive(config=_TEST_LOADER_CONFIG)
    for origin in _TEST_ORIGINS:
        nb_visits = len(origin['archives'])
        for i, archive in enumerate(origin['archives']):
            origin_repo_archive = \
                os.path.join(os.path.dirname(__file__),
                             'resources/repos/%s' % archive)
            loader.load(origin['url'], origin_repo_archive, None)
            if nb_visits > 1 and i != nb_visits - 1:
                time.sleep(1)

    # Get reference to the memory storage
    storage = loader.storage

    contents = set()
    directories = set()
    revisions = set()
    releases = set()
    snapshots = set()
    persons = set()

    content_path = {}

    # Get all objects loaded into the test archive
    for origin in _TEST_ORIGINS:
        snp = storage.snapshot_get_latest(origin['id'])
        snapshots.add(hash_to_hex(snp['id']))
        for branch_name, branch_data in snp['branches'].items():
            if branch_data['target_type'] == 'revision':
                revisions.add(branch_data['target'])
            elif branch_data['target_type'] == 'release':
                release = next(storage.release_get([branch_data['target']]))
                revisions.add(release['target'])
                releases.add(hash_to_hex(branch_data['target']))
                persons.add(release['author']['id'])

        for rev_log in storage.revision_shortlog(set(revisions)):
            rev_id = rev_log[0]
            revisions.add(rev_id)

        for rev in storage.revision_get(revisions):
            dir_id = rev['directory']
            persons.add(rev['author']['id'])
            persons.add(rev['committer']['id'])
            directories.add(hash_to_hex(dir_id))
            for entry in dir_iterator(storage, dir_id):
                content_path[entry['sha1']] = '/'.join(
                    [hash_to_hex(dir_id), entry['path'].decode('utf-8')])
                if entry['type'] == 'file':
                    contents.add(entry['sha1'])
                elif entry['type'] == 'dir':
                    directories.add(hash_to_hex(entry['target']))

    # Get all checksums for each content
    contents_metadata = storage.content_get_metadata(contents)
    contents = []
    for content_metadata in contents_metadata:
        contents.append({
            algo: hash_to_hex(content_metadata[algo])
            for algo in DEFAULT_ALGORITHMS
        })
        path = content_path[content_metadata['sha1']]
        cnt = next(storage.content_get([content_metadata['sha1']]))
        mimetype, encoding = get_mimetype_and_encoding_for_content(cnt['data'])
        content_display_data = prepare_content_for_display(
            cnt['data'], mimetype, path)
        contents[-1]['path'] = path
        contents[-1]['mimetype'] = mimetype
        contents[-1]['encoding'] = encoding
        contents[-1]['hljs_language'] = content_display_data['language']
        contents[-1]['data'] = content_display_data['content_data']
        _contents[contents[-1]['sha1']] = contents[-1]

    # Create indexer storage instance that will be shared by indexers
    idx_storage = get_indexer_storage('memory', {})

    # Instantiate content indexers that will be used in tests
    # and force them to use the memory storages
    indexers = {}
    for idx_name, idx_class in (('mimetype_indexer', _MimetypeIndexer),
                                ('language_indexer', _LanguageIndexer),
                                ('license_indexer', _FossologyLicenseIndexer),
                                ('ctags_indexer', _CtagsIndexer)):
        idx = idx_class()
        idx.storage = storage
        idx.objstorage = storage.objstorage
        idx.idx_storage = idx_storage
        idx.register_tools(idx.config['tools'])
        indexers[idx_name] = idx

    # Add the empty directory to the test archive
    empty_dir_id = directory_identifier({'entries': []})
    empty_dir_id_bin = hash_to_bytes(empty_dir_id)
    storage.directory_add([{'id': empty_dir_id_bin, 'entries': []}])

    # Return tests data
    return {
        'storage': storage,
        'idx_storage': idx_storage,
        **indexers,
        'origins': _TEST_ORIGINS,
        'contents': contents,
        'directories': list(directories),
        'persons': list(persons),
        'releases': list(releases),
        'revisions': list(map(hash_to_hex, revisions)),
        'snapshots': list(snapshots)
    }


def get_content(content_sha1):
    return _contents.get(content_sha1)


_tests_data = None


def get_tests_data():
    """
    Initialize tests data and return them in a dict.
    """
    global _tests_data
    if _tests_data is None:
        _tests_data = _init_tests_data()
    return _tests_data
