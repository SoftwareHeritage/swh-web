# Copyright (C) 2018-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
import random

from copy import deepcopy
from typing import Dict

from rest_framework.decorators import api_view
from rest_framework.response import Response

from swh.indexer.fossology_license import FossologyLicenseIndexer
from swh.indexer.mimetype import MimetypeIndexer
from swh.indexer.ctags import CtagsIndexer
from swh.indexer.storage import get_indexer_storage
from swh.model.from_disk import Directory
from swh.model.hashutil import hash_to_hex, hash_to_bytes, DEFAULT_ALGORITHMS
from swh.model.identifiers import directory_identifier
from swh.loader.git.from_disk import GitLoaderFromArchive
from swh.storage.algos.dir_iterators import dir_iterator
from swh.web import config
from swh.web.browse.utils import (
    get_mimetype_and_encoding_for_content, prepare_content_for_display
)
from swh.web.common import service
from swh.web.common.highlightjs import get_hljs_language_from_filename

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


def random_sha1():
    return hash_to_hex(bytes(random.randint(0, 255) for _ in range(20)))


def random_sha256():
    return hash_to_hex(bytes(random.randint(0, 255) for _ in range(32)))


def random_blake2s256():
    return hash_to_hex(bytes(random.randint(0, 255) for _ in range(32)))


def random_content():
    return {
        'sha1': random_sha1(),
        'sha1_git': random_sha1(),
        'sha256': random_sha256(),
        'blake2s256': random_blake2s256(),
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
        'type': 'git',
        'url': 'https://github.com/wcoder/highlightjs-line-numbers.js',
        'archives': ['highlightjs-line-numbers.js.zip',
                     'highlightjs-line-numbers.js_visit2.zip'],
        'visit_date': ['Dec 1 2018, 01:00 UTC',
                       'Jan 20 2019, 15:00 UTC']
    },
    {
        'type': 'git',
        'url': 'https://github.com/memononen/libtess2',
        'archives': ['libtess2.zip'],
        'visit_date': ['May 25 2018, 01:00 UTC']
    },
    {
        'type': 'git',
        'url': 'repo_with_submodules',
        'archives': ['repo_with_submodules.tgz'],
        'visit_date': ['Jan 1 2019, 01:00 UTC']
    }
]

_contents = {}


# Tests data initialization
def _init_tests_data():
    # Load git repositories from archives
    loader = GitLoaderFromArchive(config=_TEST_LOADER_CONFIG)

    # Get reference to the memory storage
    storage = loader.storage

    for origin in _TEST_ORIGINS:
        for i, archive in enumerate(origin['archives']):
            origin_repo_archive = \
                os.path.join(os.path.dirname(__file__),
                             'resources/repos/%s' % archive)
            loader.load(origin['url'], origin_repo_archive,
                        origin['visit_date'][i])

        origin.update(storage.origin_get(origin))  # add an 'id' key if enabled

    contents = set()
    directories = set()
    revisions = set()
    releases = set()
    snapshots = set()

    content_path = {}

    # Get all objects loaded into the test archive
    for origin in _TEST_ORIGINS:
        snp = storage.snapshot_get_latest(origin['url'])
        snapshots.add(hash_to_hex(snp['id']))
        for branch_name, branch_data in snp['branches'].items():
            if branch_data['target_type'] == 'revision':
                revisions.add(branch_data['target'])
            elif branch_data['target_type'] == 'release':
                release = next(storage.release_get([branch_data['target']]))
                revisions.add(release['target'])
                releases.add(hash_to_hex(branch_data['target']))

        for rev_log in storage.revision_shortlog(set(revisions)):
            rev_id = rev_log[0]
            revisions.add(rev_id)

        for rev in storage.revision_get(revisions):
            dir_id = rev['directory']
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

    # Add the empty directory to the test archive
    empty_dir_id = directory_identifier({'entries': []})
    empty_dir_id_bin = hash_to_bytes(empty_dir_id)
    storage.directory_add([{'id': empty_dir_id_bin, 'entries': []}])

    # Return tests data
    return {
        'storage': storage,
        'idx_storage': idx_storage,
        'origins': _TEST_ORIGINS,
        'contents': contents,
        'directories': list(directories),
        'releases': list(releases),
        'revisions': list(map(hash_to_hex, revisions)),
        'snapshots': list(snapshots),
        'generated_checksums': set(),
    }


def _init_indexers(tests_data):
    # Instantiate content indexers that will be used in tests
    # and force them to use the memory storages
    indexers = {}
    for idx_name, idx_class in (('mimetype_indexer', _MimetypeIndexer),
                                ('license_indexer', _FossologyLicenseIndexer),
                                ('ctags_indexer', _CtagsIndexer)):
        idx = idx_class()
        idx.storage = tests_data['storage']
        idx.objstorage = tests_data['storage'].objstorage
        idx.idx_storage = tests_data['idx_storage']
        idx.register_tools(idx.config['tools'])
        indexers[idx_name] = idx

    return indexers


def get_content(content_sha1):
    return _contents.get(content_sha1)


_tests_data = None
_current_tests_data = None
_indexer_loggers = {}


def get_tests_data(reset=False):
    """
    Initialize tests data and return them in a dict.
    """
    global _tests_data, _current_tests_data
    if _tests_data is None:
        _tests_data = _init_tests_data()
        indexers = _init_indexers(_tests_data)
        for (name, idx) in indexers.items():
            # pytest makes the loggers use a temporary file; and deepcopy
            # requires serializability. So we remove them, and add them
            # back after the copy.
            _indexer_loggers[name] = idx.log
            del idx.log
        _tests_data.update(indexers)
    if reset or _current_tests_data is None:
        _current_tests_data = deepcopy(_tests_data)
        for (name, logger) in _indexer_loggers.items():
            _current_tests_data[name].log = logger
    return _current_tests_data


def override_storages(storage, idx_storage):
    """
    Helper function to replace the storages from which archive data
    are fetched.
    """
    swh_config = config.get_config()
    swh_config.update({'storage': storage})
    service.storage = storage

    swh_config.update({'indexer_storage': idx_storage})
    service.idx_storage = idx_storage


# Implement some special endpoints used to provide input tests data
# when executing end to end tests with cypress

_content_code_data_exts = {}  # type: Dict[str, Dict[str, str]]
_content_code_data_filenames = {}  # type: Dict[str, Dict[str, str]]
_content_other_data_exts = {}  # type: Dict[str, Dict[str, str]]


def _init_content_tests_data(data_path, data_dict, ext_key):
    """
    Helper function to read the content of a directory, store it
    into a test archive and add some files metadata (sha1 and/or
    expected programming language) in a dict.

    Args:
        data_path (str): path to a directory relative to the tests
            folder of swh-web
        data_dict (dict): the dict that will store files metadata
        ext_key (bool): whether to use file extensions or filenames
            as dict keys
    """
    test_contents_dir = os.path.join(
        os.path.dirname(__file__), data_path).encode('utf-8')
    directory = Directory.from_disk(path=test_contents_dir, data=True,
                                    save_path=True)
    objects = directory.collect()
    for c in objects['content'].values():
        c['status'] = 'visible'
        sha1 = hash_to_hex(c['sha1'])
        if ext_key:
            key = c['path'].decode('utf-8').split('.')[-1]
            filename = 'test.' + key
        else:
            filename = c['path'].decode('utf-8').split('/')[-1]
            key = filename
        language = get_hljs_language_from_filename(filename)
        data_dict[key] = {'sha1': sha1,
                          'language': language}
        del c['path']
        del c['perms']
    storage = get_tests_data()['storage']
    storage.content_add(objects['content'].values())


def _init_content_code_data_exts():
    """
    Fill a global dictionary which maps source file extension to
    a code content example.
    """
    global _content_code_data_exts
    _init_content_tests_data('resources/contents/code/extensions',
                             _content_code_data_exts, True)


def _init_content_other_data_exts():
    """
    Fill a global dictionary which maps a file extension to
    a content example.
    """
    global _content_other_data_exts
    _init_content_tests_data('resources/contents/other/extensions',
                             _content_other_data_exts, True)


def _init_content_code_data_filenames():
    """
    Fill a global dictionary which maps a filename to
    a content example.
    """
    global _content_code_data_filenames
    _init_content_tests_data('resources/contents/code/filenames',
                             _content_code_data_filenames, False)


if config.get_config()['e2e_tests_mode']:
    _init_content_code_data_exts()
    _init_content_other_data_exts()
    _init_content_code_data_filenames()


@api_view(['GET'])
def get_content_code_data_all_exts(request):
    """
    Endpoint implementation returning a list of all source file
    extensions to test for highlighting using cypress.
    """
    return Response(sorted(_content_code_data_exts.keys()),
                    status=200, content_type='application/json')


@api_view(['GET'])
def get_content_code_data_by_ext(request, ext):
    """
    Endpoint implementation returning metadata of a code content example
    based on the source file extension.
    """
    data = None
    status = 404
    if ext in _content_code_data_exts:
        data = _content_code_data_exts[ext]
        status = 200
    return Response(data, status=status, content_type='application/json')


@api_view(['GET'])
def get_content_other_data_by_ext(request, ext):
    """
    Endpoint implementation returning metadata of a content example
    based on the file extension.
    """
    _init_content_other_data_exts()
    data = None
    status = 404
    if ext in _content_other_data_exts:
        data = _content_other_data_exts[ext]
        status = 200
    return Response(data, status=status, content_type='application/json')


@api_view(['GET'])
def get_content_code_data_all_filenames(request):
    """
    Endpoint implementation returning a list of all source filenames
    to test for highlighting using cypress.
    """
    return Response(sorted(_content_code_data_filenames.keys()),
                    status=200, content_type='application/json')


@api_view(['GET'])
def get_content_code_data_by_filename(request, filename):
    """
    Endpoint implementation returning metadata of a code content example
    based on the source filename.
    """
    data = None
    status = 404
    if filename in _content_code_data_filenames:
        data = _content_code_data_filenames[filename]
        status = 200
    return Response(data, status=status, content_type='application/json')
