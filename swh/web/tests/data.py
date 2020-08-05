# Copyright (C) 2018-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import timedelta
import os
import random
import time

from copy import deepcopy

from swh.indexer.fossology_license import FossologyLicenseIndexer
from swh.indexer.mimetype import MimetypeIndexer
from swh.indexer.ctags import CtagsIndexer
from swh.indexer.storage import get_indexer_storage
from swh.model.model import Content, OriginVisitStatus
from swh.model.hashutil import hash_to_hex, hash_to_bytes, DEFAULT_ALGORITHMS
from swh.model.model import Directory, Origin, OriginVisit
from swh.loader.git.from_disk import GitLoaderFromArchive
from swh.search import get_search
from swh.storage.algos.dir_iterators import dir_iterator
from swh.storage.algos.snapshot import snapshot_get_latest
from swh.storage.utils import now
from swh.web import config
from swh.web.browse.utils import (
    get_mimetype_and_encoding_for_content,
    prepare_content_for_display,
    _re_encode_content,
)
from swh.web.common import service

# Module used to initialize data that will be provided as tests input

# Configuration for git loader
_TEST_LOADER_CONFIG = {
    "storage": {"cls": "memory",},
    "save_data": False,
    "max_content_size": 100 * 1024 * 1024,
}

# Base content indexer configuration
_TEST_INDEXER_BASE_CONFIG = {
    "storage": {"cls": "memory"},
    "objstorage": {"cls": "memory", "args": {},},
    "indexer_storage": {"cls": "memory", "args": {},},
}


def random_sha1():
    return hash_to_hex(bytes(random.randint(0, 255) for _ in range(20)))


def random_sha256():
    return hash_to_hex(bytes(random.randint(0, 255) for _ in range(32)))


def random_blake2s256():
    return hash_to_hex(bytes(random.randint(0, 255) for _ in range(32)))


def random_content():
    return {
        "sha1": random_sha1(),
        "sha1_git": random_sha1(),
        "sha256": random_sha256(),
        "blake2s256": random_blake2s256(),
    }


# MimetypeIndexer with custom configuration for tests
class _MimetypeIndexer(MimetypeIndexer):
    def parse_config_file(self, *args, **kwargs):
        return {
            **_TEST_INDEXER_BASE_CONFIG,
            "tools": {
                "name": "file",
                "version": "1:5.30-1+deb9u1",
                "configuration": {"type": "library", "debian-package": "python3-magic"},
            },
        }


# FossologyLicenseIndexer with custom configuration for tests
class _FossologyLicenseIndexer(FossologyLicenseIndexer):
    def parse_config_file(self, *args, **kwargs):
        return {
            **_TEST_INDEXER_BASE_CONFIG,
            "workdir": "/tmp/swh/indexer.fossology.license",
            "tools": {
                "name": "nomos",
                "version": "3.1.0rc2-31-ga2cbb8c",
                "configuration": {"command_line": "nomossa <filepath>",},
            },
        }


# CtagsIndexer with custom configuration for tests
class _CtagsIndexer(CtagsIndexer):
    def parse_config_file(self, *args, **kwargs):
        return {
            **_TEST_INDEXER_BASE_CONFIG,
            "workdir": "/tmp/swh/indexer.ctags",
            "languages": {"c": "c"},
            "tools": {
                "name": "universal-ctags",
                "version": "~git7859817b",
                "configuration": {
                    "command_line": """ctags --fields=+lnz --sort=no --links=no """
                    """--output-format=json <filepath>"""
                },
            },
        }


# Lightweight git repositories that will be loaded to generate
# input data for tests
_TEST_ORIGINS = [
    {
        "type": "git",
        "url": "https://github.com/wcoder/highlightjs-line-numbers.js",
        "archives": [
            "highlightjs-line-numbers.js.zip",
            "highlightjs-line-numbers.js_visit2.zip",
        ],
    },
    {
        "type": "git",
        "url": "https://github.com/memononen/libtess2",
        "archives": ["libtess2.zip"],
    },
    {
        "type": "git",
        "url": "repo_with_submodules",
        "archives": ["repo_with_submodules.tgz"],
    },
]

_contents = {}


def _add_extra_contents(storage, contents):
    pbm_image_data = b"""P1
# PBM example
24 7
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
0 1 1 1 1 0 0 1 1 1 1 0 0 1 1 1 1 0 0 1 1 1 1 0
0 1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 1 0
0 1 1 1 0 0 0 1 1 1 0 0 0 1 1 1 0 0 0 1 1 1 1 0
0 1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0
0 1 0 0 0 0 0 1 1 1 1 0 0 1 1 1 1 0 0 1 0 0 0 0
0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0"""

    # add file with mimetype image/x-portable-bitmap in the archive content
    pbm_content = Content.from_data(pbm_image_data)
    storage.content_add([pbm_content])
    contents.add(pbm_content.sha1)


# Tests data initialization
def _init_tests_data():
    # To hold reference to the memory storage
    storage = None

    # Create search instance
    search = get_search("memory")
    search.initialize()
    search.origin_update({"url": origin["url"]} for origin in _TEST_ORIGINS)

    # Load git repositories from archives
    for origin in _TEST_ORIGINS:
        for i, archive in enumerate(origin["archives"]):
            if i > 0:
                # ensure visit dates will be different when simulating
                # multiple visits of an origin
                time.sleep(1)
            origin_repo_archive = os.path.join(
                os.path.dirname(__file__), "resources/repos/%s" % archive
            )
            loader = GitLoaderFromArchive(
                origin["url"],
                archive_path=origin_repo_archive,
                config=_TEST_LOADER_CONFIG,
            )
            if storage is None:
                storage = loader.storage
            else:
                loader.storage = storage
            loader.load()

        ori = storage.origin_get([origin["url"]])[0]
        origin.update(ori.to_dict())  # add an 'id' key if enabled
        search.origin_update([{"url": origin["url"], "has_visits": True}])

    for i in range(250):
        url = "https://many.origins/%d" % (i + 1)
        # storage.origin_add([{'url': url}])
        storage.origin_add([Origin(url=url)])
        search.origin_update([{"url": url, "has_visits": True}])
        date = now()
        visit = OriginVisit(origin=url, date=date, type="tar")
        visit = storage.origin_visit_add([visit])[0]
        visit_status = OriginVisitStatus(
            origin=url,
            visit=visit.visit,
            date=date + timedelta(minutes=1),
            status="full",
            snapshot=hash_to_bytes("1a8893e6a86f444e8be8e7bda6cb34fb1735a00e"),
        )
        storage.origin_visit_status_add([visit_status])

    contents = set()
    directories = set()
    revisions = set()
    releases = set()
    snapshots = set()

    content_path = {}

    # Get all objects loaded into the test archive
    for origin in _TEST_ORIGINS:
        snp = snapshot_get_latest(storage, origin["url"])
        snapshots.add(hash_to_hex(snp.id))
        for branch_name, branch_data in snp.branches.items():
            target_type = branch_data.target_type.value
            if target_type == "revision":
                revisions.add(branch_data.target)
            elif target_type == "release":
                release = next(storage.release_get([branch_data.target]))
                revisions.add(release["target"])
                releases.add(hash_to_hex(branch_data.target))

        for rev_log in storage.revision_shortlog(set(revisions)):
            rev_id = rev_log[0]
            revisions.add(rev_id)

        for rev in storage.revision_get(revisions):
            dir_id = rev["directory"]
            directories.add(hash_to_hex(dir_id))
            for entry in dir_iterator(storage, dir_id):
                if entry["type"] == "file":
                    contents.add(entry["sha1"])
                    content_path[entry["sha1"]] = "/".join(
                        [hash_to_hex(dir_id), entry["path"].decode("utf-8")]
                    )
                elif entry["type"] == "dir":
                    directories.add(hash_to_hex(entry["target"]))

    _add_extra_contents(storage, contents)

    # Get all checksums for each content
    result = storage.content_get_metadata(contents)
    contents = []
    for sha1, contents_metadata in result.items():
        sha1 = contents_metadata[0]["sha1"]
        content_metadata = {
            algo: hash_to_hex(contents_metadata[0][algo]) for algo in DEFAULT_ALGORITHMS
        }

        path = ""
        if sha1 in content_path:
            path = content_path[sha1]
        cnt = next(storage.content_get([sha1]))
        mimetype, encoding = get_mimetype_and_encoding_for_content(cnt["data"])
        _, _, cnt["data"] = _re_encode_content(mimetype, encoding, cnt["data"])
        content_display_data = prepare_content_for_display(cnt["data"], mimetype, path)

        content_metadata.update(
            {
                "path": path,
                "mimetype": mimetype,
                "encoding": encoding,
                "hljs_language": content_display_data["language"],
                "data": content_display_data["content_data"],
            }
        )
        _contents[hash_to_hex(sha1)] = content_metadata
        contents.append(content_metadata)

    # Create indexer storage instance that will be shared by indexers
    idx_storage = get_indexer_storage("memory", {})

    # Add the empty directory to the test archive
    storage.directory_add([Directory(entries=())])

    # Return tests data
    return {
        "search": search,
        "storage": storage,
        "idx_storage": idx_storage,
        "origins": _TEST_ORIGINS,
        "contents": contents,
        "directories": list(directories),
        "releases": list(releases),
        "revisions": list(map(hash_to_hex, revisions)),
        "snapshots": list(snapshots),
        "generated_checksums": set(),
    }


def _init_indexers(tests_data):
    # Instantiate content indexers that will be used in tests
    # and force them to use the memory storages
    indexers = {}
    for idx_name, idx_class in (
        ("mimetype_indexer", _MimetypeIndexer),
        ("license_indexer", _FossologyLicenseIndexer),
        ("ctags_indexer", _CtagsIndexer),
    ):
        idx = idx_class()
        idx.storage = tests_data["storage"]
        idx.objstorage = tests_data["storage"].objstorage
        idx.idx_storage = tests_data["idx_storage"]
        idx.register_tools(idx.config["tools"])
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


def override_storages(storage, idx_storage, search):
    """
    Helper function to replace the storages from which archive data
    are fetched.
    """
    swh_config = config.get_config()
    swh_config.update(
        {"storage": storage, "indexer_storage": idx_storage, "search": search,}
    )

    service.storage = storage
    service.idx_storage = idx_storage
    service.search = search
