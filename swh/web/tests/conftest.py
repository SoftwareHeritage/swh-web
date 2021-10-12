# Copyright (C) 2018-2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from datetime import timedelta
import json
import os
import random
import shutil
from subprocess import PIPE, run
import sys
from typing import Any, Dict, List, Optional

from _pytest.python import Function
from hypothesis import HealthCheck, settings
import pytest

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test.utils import setup_databases  # type: ignore
from rest_framework.test import APIClient, APIRequestFactory

from swh.model.hashutil import (
    ALGORITHMS,
    DEFAULT_ALGORITHMS,
    hash_to_bytes,
    hash_to_hex,
)
from swh.model.model import Content, Directory
from swh.model.swhids import ObjectType
from swh.scheduler.tests.common import TASK_TYPES
from swh.storage.algos.origin import origin_get_latest_visit_status
from swh.storage.algos.snapshot import snapshot_get_all_branches, snapshot_get_latest
from swh.web.auth.utils import OIDC_SWH_WEB_CLIENT_ID
from swh.web.common import converters
from swh.web.common.origin_save import get_scheduler_load_task_types
from swh.web.common.typing import OriginVisitInfo
from swh.web.common.utils import browsers_supported_image_mimes
from swh.web.config import get_config
from swh.web.tests.data import get_tests_data, override_storages

# Used to skip some tests
ctags_json_missing = (
    shutil.which("ctags") is None
    or b"+json" not in run(["ctags", "--version"], stdout=PIPE).stdout
)

fossology_missing = shutil.which("nomossa") is None

# Register some hypothesis profiles
settings.register_profile("default", settings())

# we use getattr here to keep mypy happy regardless hypothesis version
function_scoped_fixture_check = (
    [getattr(HealthCheck, "function_scoped_fixture")]
    if hasattr(HealthCheck, "function_scoped_fixture")
    else []
)

suppress_health_check = [
    HealthCheck.too_slow,
    HealthCheck.filter_too_much,
] + function_scoped_fixture_check


settings.register_profile(
    "swh-web", settings(deadline=None, suppress_health_check=suppress_health_check,),
)

settings.register_profile(
    "swh-web-fast",
    settings(
        deadline=None, max_examples=5, suppress_health_check=suppress_health_check,
    ),
)


def pytest_configure(config):
    # Use fast hypothesis profile by default if none has been
    # explicitly specified in pytest option
    if config.getoption("--hypothesis-profile") is None:
        settings.load_profile("swh-web-fast")

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
    data_dir = os.path.join(sys.prefix, "share/swh/web")
    static_dir = os.path.join(data_dir, "static")

    if not os.path.exists(static_dir):
        # location of the static folder when running tests locally with pytest
        static_dir = os.path.join(test_dir, "../../../static")

    webpack_stats = os.path.join(static_dir, "webpack-stats.json")
    if os.path.exists(webpack_stats):
        return

    bundles_dir = os.path.join(test_dir, "../../../assets/src/bundles")
    if not os.path.exists(bundles_dir):
        # location of the bundles folder when running tests with tox
        bundles_dir = os.path.join(data_dir, "assets/src/bundles")

    _, bundles, _ = next(os.walk(bundles_dir))

    mock_webpack_stats = {
        "status": "done",
        "publicPath": "/static",
        "chunks": {},
        "assets": {},
    }
    for bundle in bundles:
        asset = f"js/{bundle}.js"
        mock_webpack_stats["chunks"][bundle] = [asset]
        mock_webpack_stats["assets"][asset] = {
            "name": asset,
            "publicPath": f"/static/{asset}",
        }

    with open(webpack_stats, "w") as outfile:
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
@pytest.fixture
def api_client():
    return APIClient()


# Fixture to get API request factory from Django REST Framework
@pytest.fixture
def api_request_factory():
    return APIRequestFactory()


# Initialize tests data
@pytest.fixture(scope="function", autouse=True)
def tests_data():
    data = get_tests_data(reset=True)
    # Update swh-web configuration to use the in-memory storages
    # instantiated in the tests.data module
    override_storages(
        data["storage"], data["idx_storage"], data["search"], data["counters"]
    )
    return data


def _known_swh_objects(tests_data, object_type):
    return tests_data[object_type]


@pytest.fixture(scope="function")
def content(tests_data):
    """Fixture returning a random content ingested into the test archive.
    """
    return random.choice(_known_swh_objects(tests_data, "contents"))


@pytest.fixture(scope="function")
def contents(tests_data):
    """Fixture returning random contents ingested into the test archive.
    """
    return random.choices(
        _known_swh_objects(tests_data, "contents"), k=random.randint(2, 8)
    )


@pytest.fixture(scope="function")
def empty_content():
    """Fixture returning the empty content ingested into the test archive.
    """
    empty_content = Content.from_data(data=b"").to_dict()
    for algo in DEFAULT_ALGORITHMS:
        empty_content[algo] = hash_to_hex(empty_content[algo])
    return empty_content


@pytest.fixture(scope="function")
def content_text(tests_data):
    """
    Fixture returning a random textual content ingested into the test archive.
    """
    return random.choice(
        list(
            filter(
                lambda c: c["mimetype"].startswith("text/"),
                _known_swh_objects(tests_data, "contents"),
            )
        )
    )


@pytest.fixture(scope="function")
def content_text_non_utf8(tests_data):
    """Fixture returning a random textual content not encoded to UTF-8 ingested
    into the test archive.
    """
    return random.choice(
        list(
            filter(
                lambda c: c["mimetype"].startswith("text/")
                and c["encoding"] not in ("utf-8", "us-ascii"),
                _known_swh_objects(tests_data, "contents"),
            )
        )
    )


@pytest.fixture(scope="function")
def content_application_no_highlight(tests_data):
    """Fixture returning a random textual content with mimetype
    starting with application/ and no detected programming language to
    highlight ingested into the test archive.
    """
    return random.choice(
        list(
            filter(
                lambda c: c["mimetype"].startswith("application/")
                and c["encoding"] != "binary"
                and c["hljs_language"] == "nohighlight",
                _known_swh_objects(tests_data, "contents"),
            )
        )
    )


@pytest.fixture(scope="function")
def content_text_no_highlight(tests_data):
    """Fixture returning a random textual content with no detected
    programming language to highlight ingested into the test archive.
    """
    return random.choice(
        list(
            filter(
                lambda c: c["mimetype"].startswith("text/")
                and c["hljs_language"] == "nohighlight",
                _known_swh_objects(tests_data, "contents"),
            )
        )
    )


@pytest.fixture(scope="function")
def content_image_type(tests_data):
    """Fixture returning a random image content ingested into the test archive.
    """
    return random.choice(
        list(
            filter(
                lambda c: c["mimetype"] in browsers_supported_image_mimes,
                _known_swh_objects(tests_data, "contents"),
            )
        )
    )


@pytest.fixture(scope="function")
def content_unsupported_image_type_rendering(tests_data):
    """Fixture returning a random image content ingested into the test archive that
    can not be rendered by browsers.
    """
    return random.choice(
        list(
            filter(
                lambda c: c["mimetype"].startswith("image/")
                and c["mimetype"] not in browsers_supported_image_mimes,
                _known_swh_objects(tests_data, "contents"),
            )
        )
    )


@pytest.fixture(scope="function")
def content_utf8_detected_as_binary(tests_data):
    """Fixture returning a random textual content detected as binary
    by libmagic while they are valid UTF-8 encoded files.
    """

    def utf8_binary_detected(content):
        if content["encoding"] != "binary":
            return False
        try:
            content["raw_data"].decode("utf-8")
        except Exception:
            return False
        else:
            return True

    return random.choice(
        list(filter(utf8_binary_detected, _known_swh_objects(tests_data, "contents")))
    )


@pytest.fixture(scope="function")
def contents_with_ctags():
    """
    Fixture returning contents ingested into the test archive.
    Those contents are ctags compatible, that is running ctags on those lay results.
    """
    return {
        "sha1s": [
            "0ab37c02043ebff946c1937523f60aadd0844351",
            "15554cf7608dde6bfefac7e3d525596343a85b6f",
            "2ce837f1489bdfb8faf3ebcc7e72421b5bea83bd",
            "30acd0b47fc25e159e27a980102ddb1c4bea0b95",
            "4f81f05aaea3efb981f9d90144f746d6b682285b",
            "5153aa4b6e4455a62525bc4de38ed0ff6e7dd682",
            "59d08bafa6a749110dfb65ba43a61963d5a5bf9f",
            "7568285b2d7f31ae483ae71617bd3db873deaa2c",
            "7ed3ee8e94ac52ba983dd7690bdc9ab7618247b4",
            "8ed7ef2e7ff9ed845e10259d08e4145f1b3b5b03",
            "9b3557f1ab4111c8607a4f2ea3c1e53c6992916c",
            "9c20da07ed14dc4fcd3ca2b055af99b2598d8bdd",
            "c20ceebd6ec6f7a19b5c3aebc512a12fbdc9234b",
            "e89e55a12def4cd54d5bff58378a3b5119878eb7",
            "e8c0654fe2d75ecd7e0b01bee8a8fc60a130097e",
            "eb6595e559a1d34a2b41e8d4835e0e4f98a5d2b5",
        ],
        "symbol_name": "ABS",
    }


@pytest.fixture(scope="function")
def directory(tests_data):
    """Fixture returning a random directory ingested into the test archive.
    """
    return random.choice(_known_swh_objects(tests_data, "directories"))


def _directory_with_entry_type(tests_data, type_):
    return random.choice(
        list(
            filter(
                lambda d: any(
                    [
                        e["type"] == type_
                        for e in list(
                            tests_data["storage"].directory_ls(hash_to_bytes(d))
                        )
                    ]
                ),
                _known_swh_objects(tests_data, "directories"),
            )
        )
    )


@pytest.fixture(scope="function")
def directory_with_subdirs(tests_data):
    """Fixture returning a random directory containing sub directories ingested
    into the test archive.
    """
    return _directory_with_entry_type(tests_data, "dir")


@pytest.fixture(scope="function")
def directory_with_files(tests_data):
    """Fixture returning a random directory containing at least one regular file.
    """
    return _directory_with_entry_type(tests_data, "file")


@pytest.fixture(scope="function")
def empty_directory():
    """Fixture returning the empty directory ingested into the test archive.
    """
    return Directory(entries=()).id.hex()


@pytest.fixture(scope="function")
def release(tests_data):
    """Fixture returning a random release ingested into the test archive.
    """
    return random.choice(_known_swh_objects(tests_data, "releases"))


@pytest.fixture(scope="function")
def releases(tests_data):
    """Fixture returning random releases ingested into the test archive.
    """
    return random.choices(
        _known_swh_objects(tests_data, "releases"), k=random.randint(2, 8)
    )


@pytest.fixture(scope="function")
def origin(tests_data):
    """Fixturee returning a random origin ingested into the test archive.
    """
    return random.choice(_known_swh_objects(tests_data, "origins"))


@pytest.fixture(scope="function")
def origin_with_multiple_visits(tests_data):
    """Fixture returning a random origin with multiple visits ingested
    into the test archive.
    """
    origins = []
    storage = tests_data["storage"]
    for origin in tests_data["origins"]:
        visit_page = storage.origin_visit_get(origin["url"])
        if len(visit_page.results) > 1:
            origins.append(origin)
    return random.choice(origins)


@pytest.fixture(scope="function")
def origin_with_releases(tests_data):
    """Fixture returning a random origin with releases ingested into the test archive.
    """
    origins = []
    for origin in tests_data["origins"]:
        snapshot = snapshot_get_latest(tests_data["storage"], origin["url"])
        if any([b.target_type.value == "release" for b in snapshot.branches.values()]):
            origins.append(origin)
    return random.choice(origins)


@pytest.fixture(scope="function")
def origin_with_pull_request_branches(tests_data):
    """Fixture returning a random origin with pull request branches ingested
    into the test archive.
    """
    origins = []
    storage = tests_data["storage"]
    for origin in storage.origin_list(limit=1000).results:
        snapshot = snapshot_get_latest(storage, origin.url)
        if any([b"refs/pull/" in b for b in snapshot.branches]):
            origins.append(origin)
    return random.choice(origins)


def _object_type_swhid(tests_data, object_type):
    return random.choice(
        list(
            filter(
                lambda swhid: swhid.object_type == object_type,
                _known_swh_objects(tests_data, "swhids"),
            )
        )
    )


@pytest.fixture(scope="function")
def content_swhid(tests_data):
    """Fixture returning a qualified SWHID for a random content object
    ingested into the test archive.
    """
    return _object_type_swhid(tests_data, ObjectType.CONTENT)


@pytest.fixture(scope="function")
def directory_swhid(tests_data):
    """Fixture returning a qualified SWHID for a random directory object
    ingested into the test archive.
    """
    return _object_type_swhid(tests_data, ObjectType.DIRECTORY)


@pytest.fixture(scope="function")
def release_swhid(tests_data):
    """Fixture returning a qualified SWHID for a random release object
    ingested into the test archive.
    """
    return _object_type_swhid(tests_data, ObjectType.RELEASE)


# Fixture to manipulate data from a sample archive used in the tests
@pytest.fixture(scope="function")
def archive_data(tests_data):
    return _ArchiveData(tests_data)


# Fixture to manipulate indexer data from a sample archive used in the tests
@pytest.fixture(scope="function")
def indexer_data(tests_data):
    return _IndexerData(tests_data)


# Custom data directory for requests_mock
@pytest.fixture
def datadir():
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), "resources")


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
        self.storage = tests_data["storage"]

    def __getattr__(self, key):
        if key == "storage":
            raise AttributeError(key)
        # Forward calls to non overridden Storage methods to wrapped
        # storage instance
        return getattr(self.storage, key)

    def content_find(self, content: Dict[str, Any]) -> Dict[str, Any]:
        cnt_ids_bytes = {
            algo_hash: hash_to_bytes(content[algo_hash])
            for algo_hash in ALGORITHMS
            if content.get(algo_hash)
        }
        cnt = self.storage.content_find(cnt_ids_bytes)
        return converters.from_content(cnt[0].to_dict()) if cnt else cnt

    def content_get(self, cnt_id: str) -> Dict[str, Any]:
        cnt_id_bytes = hash_to_bytes(cnt_id)
        content = self.storage.content_get([cnt_id_bytes])[0]
        if content:
            content_d = content.to_dict()
            content_d.pop("ctime", None)
        else:
            content_d = None
        return converters.from_swh(
            content_d, hashess={"sha1", "sha1_git", "sha256", "blake2s256"}
        )

    def content_get_data(self, cnt_id: str) -> Optional[Dict[str, Any]]:
        cnt_id_bytes = hash_to_bytes(cnt_id)
        cnt_data = self.storage.content_get_data(cnt_id_bytes)
        if cnt_data is None:
            return None
        return converters.from_content({"data": cnt_data, "sha1": cnt_id_bytes})

    def directory_get(self, dir_id):
        return {"id": dir_id, "content": self.directory_ls(dir_id)}

    def directory_ls(self, dir_id):
        cnt_id_bytes = hash_to_bytes(dir_id)
        dir_content = map(
            converters.from_directory_entry, self.storage.directory_ls(cnt_id_bytes)
        )
        return list(dir_content)

    def release_get(self, rel_id: str) -> Optional[Dict[str, Any]]:
        rel_id_bytes = hash_to_bytes(rel_id)
        rel_data = self.storage.release_get([rel_id_bytes])[0]
        return converters.from_release(rel_data) if rel_data else None

    def revision_get(self, rev_id: str) -> Optional[Dict[str, Any]]:
        rev_id_bytes = hash_to_bytes(rev_id)
        rev_data = self.storage.revision_get([rev_id_bytes])[0]
        return converters.from_revision(rev_data) if rev_data else None

    def revision_log(self, rev_id, limit=None):
        rev_id_bytes = hash_to_bytes(rev_id)
        return list(
            map(
                converters.from_revision,
                self.storage.revision_log([rev_id_bytes], limit=limit),
            )
        )

    def snapshot_get_latest(self, origin_url):
        snp = snapshot_get_latest(self.storage, origin_url)
        return converters.from_snapshot(snp.to_dict())

    def origin_get(self, origin_urls):
        origins = self.storage.origin_get(origin_urls)
        return [converters.from_origin(o.to_dict()) for o in origins]

    def origin_visit_get(self, origin_url):
        next_page_token = None
        visits = []
        while True:
            visit_page = self.storage.origin_visit_get(
                origin_url, page_token=next_page_token
            )
            next_page_token = visit_page.next_page_token

            for visit in visit_page.results:
                visit_status = self.storage.origin_visit_status_get_latest(
                    origin_url, visit.visit
                )
                visits.append(
                    converters.from_origin_visit(
                        {**visit_status.to_dict(), "type": visit.type}
                    )
                )
            if not next_page_token:
                break
        return visits

    def origin_visit_get_by(self, origin_url: str, visit_id: int) -> OriginVisitInfo:
        visit = self.storage.origin_visit_get_by(origin_url, visit_id)
        assert visit is not None
        visit_status = self.storage.origin_visit_status_get_latest(origin_url, visit_id)
        assert visit_status is not None
        return converters.from_origin_visit(
            {**visit_status.to_dict(), "type": visit.type}
        )

    def origin_visit_status_get_latest(
        self,
        origin_url,
        type: Optional[str] = None,
        allowed_statuses: Optional[List[str]] = None,
        require_snapshot: bool = False,
    ):
        visit_status = origin_get_latest_visit_status(
            self.storage,
            origin_url,
            type=type,
            allowed_statuses=allowed_statuses,
            require_snapshot=require_snapshot,
        )
        return (
            converters.from_origin_visit(visit_status.to_dict())
            if visit_status
            else None
        )

    def snapshot_get(self, snapshot_id):
        snp = snapshot_get_all_branches(self.storage, hash_to_bytes(snapshot_id))
        return converters.from_snapshot(snp.to_dict())

    def snapshot_get_branches(
        self, snapshot_id, branches_from="", branches_count=1000, target_types=None
    ):
        partial_branches = self.storage.snapshot_get_branches(
            hash_to_bytes(snapshot_id),
            branches_from.encode(),
            branches_count,
            target_types,
        )
        return converters.from_partial_branches(partial_branches)

    def snapshot_get_head(self, snapshot):
        if snapshot["branches"]["HEAD"]["target_type"] == "alias":
            target = snapshot["branches"]["HEAD"]["target"]
            head = snapshot["branches"][target]["target"]
        else:
            head = snapshot["branches"]["HEAD"]["target"]
        return head

    def snapshot_count_branches(self, snapshot_id):
        counts = dict.fromkeys(("alias", "release", "revision"), 0)
        counts.update(self.storage.snapshot_count_branches(hash_to_bytes(snapshot_id)))
        counts.pop(None, None)
        return counts


class _IndexerData:
    """
    Helper class to manage indexer tests data

    It is initialized with a reference to an in-memory indexer storage
    containing raw tests data.

    It also defines class methods to retrieve those tests data in
    a json serializable format in order to ease tests implementation.

    """

    def __init__(self, tests_data):
        self.idx_storage = tests_data["idx_storage"]
        self.mimetype_indexer = tests_data["mimetype_indexer"]
        self.license_indexer = tests_data["license_indexer"]
        self.ctags_indexer = tests_data["ctags_indexer"]

    def content_add_mimetype(self, cnt_id):
        self.mimetype_indexer.run([hash_to_bytes(cnt_id)])

    def content_get_mimetype(self, cnt_id):
        mimetype = self.idx_storage.content_mimetype_get([hash_to_bytes(cnt_id)])[
            0
        ].to_dict()
        return converters.from_filetype(mimetype)

    def content_add_license(self, cnt_id):
        self.license_indexer.run([hash_to_bytes(cnt_id)])

    def content_get_license(self, cnt_id):
        cnt_id_bytes = hash_to_bytes(cnt_id)
        licenses = self.idx_storage.content_fossology_license_get([cnt_id_bytes])
        for license in licenses:
            yield converters.from_swh(license.to_dict(), hashess={"id"})

    def content_add_ctags(self, cnt_id):
        self.ctags_indexer.run([hash_to_bytes(cnt_id)])

    def content_get_ctags(self, cnt_id):
        cnt_id_bytes = hash_to_bytes(cnt_id)
        ctags = self.idx_storage.content_ctags_get([cnt_id_bytes])
        for ctag in ctags:
            yield converters.from_swh(ctag, hashess={"id"})


@pytest.fixture
def keycloak_oidc(keycloak_oidc, mocker):
    keycloak_config = get_config()["keycloak"]

    keycloak_oidc.server_url = keycloak_config["server_url"]
    keycloak_oidc.realm_name = keycloak_config["realm_name"]
    keycloak_oidc.client_id = OIDC_SWH_WEB_CLIENT_ID

    keycloak_oidc_client = mocker.patch("swh.web.auth.views.keycloak_oidc_client")
    keycloak_oidc_client.return_value = keycloak_oidc

    return keycloak_oidc


@pytest.fixture
def subtest(request):
    """A hack to explicitly set up and tear down fixtures.

    This fixture allows you to set up and tear down fixtures within the test
    function itself. This is useful (necessary!) for using Hypothesis inside
    pytest, as hypothesis will call the test function multiple times, without
    setting up or tearing down fixture state as it is normally the case.

    Copied from the pytest-subtesthack project, public domain license
    (https://github.com/untitaker/pytest-subtesthack).
    """
    parent_test = request.node

    def inner(func):
        if hasattr(Function, "from_parent"):
            item = Function.from_parent(
                parent_test,
                name=request.function.__name__ + "[]",
                originalname=request.function.__name__,
                callobj=func,
            )
        else:
            item = Function(
                name=request.function.__name__ + "[]", parent=parent_test, callobj=func
            )
        nextitem = parent_test  # prevents pytest from tearing down module fixtures

        item.ihook.pytest_runtest_setup(item=item)
        item.ihook.pytest_runtest_call(item=item)
        item.ihook.pytest_runtest_teardown(item=item, nextitem=nextitem)

    return inner


@pytest.fixture
def swh_scheduler(swh_scheduler):
    config = get_config()
    scheduler = config["scheduler"]
    config["scheduler"] = swh_scheduler
    # create load-git and load-hg task types
    for task_type in TASK_TYPES.values():
        swh_scheduler.create_task_type(task_type)
    # create load-svn task type
    swh_scheduler.create_task_type(
        {
            "type": "load-svn",
            "description": "Update a Subversion repository",
            "backend_name": "swh.loader.svn.tasks.DumpMountAndLoadSvnRepository",
            "default_interval": timedelta(days=64),
            "min_interval": timedelta(hours=12),
            "max_interval": timedelta(days=64),
            "backoff_factor": 2,
            "max_queue_length": None,
            "num_retries": 7,
            "retry_delay": timedelta(hours=2),
        }
    )
    # create load-cvs task type
    swh_scheduler.create_task_type(
        {
            "type": "load-cvs",
            "description": "Update a CVS repository",
            "backend_name": "swh.loader.cvs.tasks.DumpMountAndLoadSvnRepository",
            "default_interval": timedelta(days=64),
            "min_interval": timedelta(hours=12),
            "max_interval": timedelta(days=64),
            "backoff_factor": 2,
            "max_queue_length": None,
            "num_retries": 7,
            "retry_delay": timedelta(hours=2),
        }
    )

    # add method to add load-archive-files task type during tests
    def add_load_archive_task_type():
        swh_scheduler.create_task_type(
            {
                "type": "load-archive-files",
                "description": "Load tarballs",
                "backend_name": "swh.loader.package.archive.tasks.LoadArchive",
                "default_interval": timedelta(days=64),
                "min_interval": timedelta(hours=12),
                "max_interval": timedelta(days=64),
                "backoff_factor": 2,
                "max_queue_length": None,
                "num_retries": 7,
                "retry_delay": timedelta(hours=2),
            }
        )

    swh_scheduler.add_load_archive_task_type = add_load_archive_task_type

    yield swh_scheduler
    config["scheduler"] = scheduler
    get_scheduler_load_task_types.cache_clear()


@pytest.fixture(scope="session")
def django_db_setup(request, django_db_blocker, postgresql_proc):
    from django.conf import settings

    settings.DATABASES["default"].update(
        {
            ("ENGINE", "django.db.backends.postgresql"),
            ("NAME", get_config()["test_db"]["name"]),
            ("USER", postgresql_proc.user),
            ("HOST", postgresql_proc.host),
            ("PORT", postgresql_proc.port),
        }
    )
    with django_db_blocker.unblock():
        setup_databases(
            verbosity=request.config.option.verbose, interactive=False, keepdb=False
        )


@pytest.fixture
def staff_user():
    return User.objects.create_user(username="admin", password="", is_staff=True)


@pytest.fixture
def regular_user():
    return User.objects.create_user(username="johndoe", password="")


@pytest.fixture
def regular_user2():
    return User.objects.create_user(username="janedoe", password="")
