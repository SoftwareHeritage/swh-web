# Copyright (C) 2018-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from copy import deepcopy
from datetime import timedelta
import os
import random
import time
from typing import Dict, List, Optional, Set

from swh.core.config import merge_configs
from swh.indexer.ctags import CtagsIndexer
from swh.indexer.fossology_license import FossologyLicenseIndexer
from swh.indexer.mimetype import MimetypeIndexer
from swh.indexer.storage import get_indexer_storage
from swh.indexer.storage.model import OriginIntrinsicMetadataRow
from swh.loader.git.from_disk import GitLoaderFromArchive
from swh.model.hashutil import DEFAULT_ALGORITHMS, hash_to_hex
from swh.model.model import (
    Content,
    Directory,
    Origin,
    OriginVisit,
    OriginVisitStatus,
    Snapshot,
)
from swh.search import get_search
from swh.storage import get_storage
from swh.storage.algos.dir_iterators import dir_iterator
from swh.storage.algos.snapshot import snapshot_get_latest
from swh.storage.interface import Sha1
from swh.storage.utils import now
from swh.web import config
from swh.web.browse.utils import (
    _re_encode_content,
    get_mimetype_and_encoding_for_content,
    prepare_content_for_display,
)
from swh.web.common import archive

# Module used to initialize data that will be provided as tests input

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


_TEST_MIMETYPE_INDEXER_CONFIG = merge_configs(
    _TEST_INDEXER_BASE_CONFIG,
    {
        "tools": {
            "name": "file",
            "version": "1:5.30-1+deb9u1",
            "configuration": {"type": "library", "debian-package": "python3-magic"},
        }
    },
)


_TEST_LICENSE_INDEXER_CONFIG = merge_configs(
    _TEST_INDEXER_BASE_CONFIG,
    {
        "workdir": "/tmp/swh/indexer.fossology.license",
        "tools": {
            "name": "nomos",
            "version": "3.1.0rc2-31-ga2cbb8c",
            "configuration": {"command_line": "nomossa <filepath>",},
        },
    },
)


_TEST_CTAGS_INDEXER_CONFIG = merge_configs(
    _TEST_INDEXER_BASE_CONFIG,
    {
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
    },
)


# Lightweight git repositories that will be loaded to generate
# input data for tests
_TEST_ORIGINS = [
    {
        "type": "git",
        "url": "https://github.com/memononen/libtess2",
        "archives": ["libtess2.zip"],
    },
    {
        "type": "git",
        "url": "https://github.com/wcoder/highlightjs-line-numbers.js",
        "archives": [
            "highlightjs-line-numbers.js.zip",
            "highlightjs-line-numbers.js_visit2.zip",
        ],
        "metadata": {"description": "Line numbering plugin for Highlight.js",},
    },
    {
        "type": "git",
        "url": "repo_with_submodules",
        "archives": ["repo_with_submodules.tgz"],
        "metadata": {
            "description": "This is just a sample repository with submodules",
        },
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


INDEXER_TOOL = {
    "tool_name": "swh-web tests",
    "tool_version": "1.0",
    "tool_configuration": {},
}

ORIGIN_METADATA_KEY = "vcs"
ORIGIN_METADATA_VALUE = "git"

ORIGIN_MASTER_REVISION = {}


def _add_origin(storage, search, origin_url, visit_type="git", snapshot_branches={}):
    storage.origin_add([Origin(url=origin_url)])
    search.origin_update(
        [{"url": origin_url, "has_visits": True, "visit_types": [visit_type]}]
    )
    date = now()
    visit = OriginVisit(origin=origin_url, date=date, type=visit_type)
    visit = storage.origin_visit_add([visit])[0]
    snapshot = Snapshot.from_dict({"branches": snapshot_branches})
    storage.snapshot_add([snapshot])
    visit_status = OriginVisitStatus(
        origin=origin_url,
        visit=visit.visit,
        date=date + timedelta(minutes=1),
        type=visit.type,
        status="full",
        snapshot=snapshot.id,
    )
    storage.origin_visit_status_add([visit_status])


# Tests data initialization
def _init_tests_data():
    # To hold reference to the memory storage
    storage = get_storage("memory")

    # Create search instance
    search = get_search("memory")
    search.initialize()
    search.origin_update({"url": origin["url"]} for origin in _TEST_ORIGINS)

    # Create indexer storage instance that will be shared by indexers
    idx_storage = get_indexer_storage("memory")

    # Declare a test tool for origin intrinsic metadata tests
    idx_tool = idx_storage.indexer_configuration_add([INDEXER_TOOL])[0]
    INDEXER_TOOL["id"] = idx_tool["id"]

    # Load git repositories from archives
    for origin in _TEST_ORIGINS:
        for i, archive_ in enumerate(origin["archives"]):
            if i > 0:
                # ensure visit dates will be different when simulating
                # multiple visits of an origin
                time.sleep(1)
            origin_repo_archive = os.path.join(
                os.path.dirname(__file__), "resources/repos/%s" % archive_
            )
            loader = GitLoaderFromArchive(
                storage, origin["url"], archive_path=origin_repo_archive,
            )

            result = loader.load()
            assert result["status"] == "eventful"

        ori = storage.origin_get([origin["url"]])[0]
        origin.update(ori.to_dict())  # add an 'id' key if enabled
        search.origin_update(
            [{"url": origin["url"], "has_visits": True, "visit_types": ["git"]}]
        )

    for i in range(250):
        _add_origin(
            storage, search, origin_url=f"https://many.origins/{i+1}", visit_type="tar"
        )

    sha1s: Set[Sha1] = set()
    directories = set()
    revisions = set()
    releases = set()
    snapshots = set()

    content_path = {}

    # Get all objects loaded into the test archive
    common_metadata = {ORIGIN_METADATA_KEY: ORIGIN_METADATA_VALUE}
    for origin in _TEST_ORIGINS:
        snp = snapshot_get_latest(storage, origin["url"])
        snapshots.add(hash_to_hex(snp.id))
        for branch_name, branch_data in snp.branches.items():
            target_type = branch_data.target_type.value
            if target_type == "revision":
                revisions.add(branch_data.target)
                if b"master" in branch_name:
                    # Add some origin intrinsic metadata for tests
                    metadata = common_metadata
                    metadata.update(origin.get("metadata", {}))
                    origin_metadata = OriginIntrinsicMetadataRow(
                        id=origin["url"],
                        from_revision=branch_data.target,
                        indexer_configuration_id=idx_tool["id"],
                        metadata=metadata,
                        mappings=[],
                    )
                    idx_storage.origin_intrinsic_metadata_add([origin_metadata])
                    search.origin_update(
                        [{"url": origin["url"], "intrinsic_metadata": metadata}]
                    )

                    ORIGIN_MASTER_REVISION[origin["url"]] = hash_to_hex(
                        branch_data.target
                    )
            elif target_type == "release":
                release = storage.release_get([branch_data.target])[0]
                revisions.add(release.target)
                releases.add(hash_to_hex(branch_data.target))

        for rev_log in storage.revision_shortlog(set(revisions)):
            rev_id = rev_log[0]
            revisions.add(rev_id)

        for rev in storage.revision_get(revisions):
            if rev is None:
                continue
            dir_id = rev.directory
            directories.add(hash_to_hex(dir_id))
            for entry in dir_iterator(storage, dir_id):
                if entry["type"] == "file":
                    sha1s.add(entry["sha1"])
                    content_path[entry["sha1"]] = "/".join(
                        [hash_to_hex(dir_id), entry["path"].decode("utf-8")]
                    )
                elif entry["type"] == "dir":
                    directories.add(hash_to_hex(entry["target"]))

    _add_extra_contents(storage, sha1s)

    # Get all checksums for each content
    result: List[Optional[Content]] = storage.content_get(list(sha1s))

    contents: List[Dict] = []
    for content in result:
        assert content is not None
        sha1 = hash_to_hex(content.sha1)
        content_metadata = {
            algo: hash_to_hex(getattr(content, algo)) for algo in DEFAULT_ALGORITHMS
        }

        path = ""
        if content.sha1 in content_path:
            path = content_path[content.sha1]

        cnt_data = storage.content_get_data(content.sha1)
        assert cnt_data is not None
        mimetype, encoding = get_mimetype_and_encoding_for_content(cnt_data)
        _, _, cnt_data = _re_encode_content(mimetype, encoding, cnt_data)
        content_display_data = prepare_content_for_display(cnt_data, mimetype, path)

        content_metadata.update(
            {
                "path": path,
                "mimetype": mimetype,
                "encoding": encoding,
                "hljs_language": content_display_data["language"],
                "data": content_display_data["content_data"],
            }
        )
        _contents[sha1] = content_metadata
        contents.append(content_metadata)

    # Add the empty directory to the test archive
    storage.directory_add([Directory(entries=())])

    # Add empty content to the test archive
    storage.content_add([Content.from_data(data=b"")])

    # Add fake git origin with pull request branches
    _add_origin(
        storage,
        search,
        origin_url="https://git.example.org/project",
        snapshot_branches={
            b"refs/heads/master": {
                "target_type": "revision",
                "target": next(iter(revisions)),
            },
            **{
                f"refs/pull/{i}".encode(): {
                    "target_type": "revision",
                    "target": next(iter(revisions)),
                }
                for i in range(300)
            },
        },
    )

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
    for idx_name, idx_class, idx_config in (
        ("mimetype_indexer", MimetypeIndexer, _TEST_MIMETYPE_INDEXER_CONFIG),
        ("license_indexer", FossologyLicenseIndexer, _TEST_LICENSE_INDEXER_CONFIG),
        ("ctags_indexer", CtagsIndexer, _TEST_CTAGS_INDEXER_CONFIG),
    ):
        idx = idx_class(config=idx_config)
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

    archive.storage = storage
    archive.idx_storage = idx_storage
    archive.search = search
