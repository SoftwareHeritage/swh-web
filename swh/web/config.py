# Copyright (C) 2017-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
from typing import Any, Dict

from swh.core import config
from swh.indexer.storage import get_indexer_storage
from swh.scheduler import get_scheduler
from swh.search import get_search
from swh.storage import get_storage
from swh.vault import get_vault
from swh.web import settings

SWH_WEB_INTERNAL_SERVER_NAME = "archive.internal.softwareheritage.org"

STAGING_SERVER_NAMES = [
    "webapp.staging.swh.network",
    "webapp.internal.staging.swh.network",
]

ORIGIN_VISIT_TYPES = [
    "cran",
    "deb",
    "deposit",
    "ftp",
    "hg",
    "git",
    "nixguix",
    "npm",
    "pypi",
    "svn",
    "tar",
]


SETTINGS_DIR = os.path.dirname(settings.__file__)

DEFAULT_CONFIG = {
    "allowed_hosts": ("list", []),
    "search": (
        "dict",
        {"cls": "remote", "url": "http://127.0.0.1:5010/", "timeout": 10,},
    ),
    "storage": (
        "dict",
        {"cls": "remote", "url": "http://127.0.0.1:5002/", "timeout": 10,},
    ),
    "indexer_storage": (
        "dict",
        {"cls": "remote", "url": "http://127.0.0.1:5007/", "timeout": 1,},
    ),
    "log_dir": ("string", "/tmp/swh/log"),
    "debug": ("bool", False),
    "serve_assets": ("bool", False),
    "host": ("string", "127.0.0.1"),
    "port": ("int", 5004),
    "secret_key": ("string", "development key"),
    # do not display code highlighting for content > 1MB
    "content_display_max_size": ("int", 5 * 1024 * 1024),
    "snapshot_content_max_size": ("int", 1000),
    "throttling": (
        "dict",
        {
            "cache_uri": None,  # production: memcached as cache (127.0.0.1:11211)
            # development: in-memory cache so None
            "scopes": {
                "swh_api": {
                    "limiter_rate": {"default": "120/h"},
                    "exempted_networks": ["127.0.0.0/8"],
                },
                "swh_api_origin_search": {
                    "limiter_rate": {"default": "10/m"},
                    "exempted_networks": ["127.0.0.0/8"],
                },
                "swh_vault_cooking": {
                    "limiter_rate": {"default": "120/h", "GET": "60/m"},
                    "exempted_networks": ["127.0.0.0/8"],
                },
                "swh_save_origin": {
                    "limiter_rate": {"default": "120/h", "POST": "10/h"},
                    "exempted_networks": ["127.0.0.0/8"],
                },
                "swh_api_origin_visit_latest": {
                    "limiter_rate": {"default": "700/m"},
                    "exempted_networks": ["127.0.0.0/8"],
                },
            },
        },
    ),
    "vault": ("dict", {"cls": "remote", "args": {"url": "http://127.0.0.1:5005/",}}),
    "scheduler": ("dict", {"cls": "remote", "url": "http://127.0.0.1:5008/"}),
    "development_db": ("string", os.path.join(SETTINGS_DIR, "db.sqlite3")),
    "test_db": ("string", os.path.join(SETTINGS_DIR, "testdb.sqlite3")),
    "production_db": ("dict", {"name": "swh-web"}),
    "deposit": (
        "dict",
        {
            "private_api_url": "https://deposit.softwareheritage.org/1/private/",
            "private_api_user": "swhworker",
            "private_api_password": "",
        },
    ),
    "coverage_count_origins": ("bool", False),
    "e2e_tests_mode": ("bool", False),
    "es_workers_index_url": ("string", ""),
    "history_counters_url": (
        "string",
        "https://stats.export.softwareheritage.org/history_counters.json",
    ),
    "client_config": ("dict", {}),
    "keycloak": ("dict", {"server_url": "", "realm_name": ""}),
    "graph": (
        "dict",
        {"server_url": "http://graph.internal.softwareheritage.org:5009/graph/"},
    ),
    "status": (
        "dict",
        {
            "server_url": "https://status.softwareheritage.org/",
            "json_path": "1.0/status/578e5eddcdc0cc7951000520",
        },
    ),
    "metadata_search_backend": ("string", "swh-indexer-storage"),  # or "swh-search"
    "staging_server_names": ("list", STAGING_SERVER_NAMES),
}

swhweb_config = {}  # type: Dict[str, Any]


def get_config(config_file="web/web"):
    """Read the configuration file `config_file`.

       If an environment variable SWH_CONFIG_FILENAME is defined, this
       takes precedence over the config_file parameter.

       In any case, update the app with parameters (secret_key, conf)
       and return the parsed configuration as a dict.

       If no configuration file is provided, return a default
       configuration.

    """

    if not swhweb_config:
        config_filename = os.environ.get("SWH_CONFIG_FILENAME")
        if config_filename:
            config_file = config_filename
        cfg = config.load_named_config(config_file, DEFAULT_CONFIG)
        swhweb_config.update(cfg)
        config.prepare_folders(swhweb_config, "log_dir")
        if swhweb_config.get("search"):
            swhweb_config["search"] = get_search(**swhweb_config["search"])
        else:
            swhweb_config["search"] = None
        swhweb_config["storage"] = get_storage(**swhweb_config["storage"])
        swhweb_config["vault"] = get_vault(**swhweb_config["vault"])
        swhweb_config["indexer_storage"] = get_indexer_storage(
            **swhweb_config["indexer_storage"]
        )
        swhweb_config["scheduler"] = get_scheduler(**swhweb_config["scheduler"])
    return swhweb_config


def search():
    """Return the current application's search.

    """
    return get_config()["search"]


def storage():
    """Return the current application's storage.

    """
    return get_config()["storage"]


def vault():
    """Return the current application's vault.

    """
    return get_config()["vault"]


def indexer_storage():
    """Return the current application's indexer storage.

    """
    return get_config()["indexer_storage"]


def scheduler():
    """Return the current application's scheduler.

    """
    return get_config()["scheduler"]
