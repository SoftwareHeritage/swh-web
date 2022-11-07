# Copyright (C) 2017-2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
from typing import Any, Dict

from swh.core import config
from swh.counters import get_counters
from swh.indexer.storage import get_indexer_storage
from swh.scheduler import get_scheduler
from swh.search import get_search
from swh.storage import get_storage
from swh.vault import get_vault
from swh.web import settings

SWH_WEB_SERVER_NAME = "archive.softwareheritage.org"
SWH_WEB_INTERNAL_SERVER_NAME = "archive.internal.softwareheritage.org"

SWH_WEB_STAGING_SERVER_NAMES = [
    "webapp.staging.swh.network",
    "webapp.internal.staging.swh.network",
]

SETTINGS_DIR = os.path.dirname(settings.__file__)

DEFAULT_CONFIG = {
    "allowed_hosts": ("list", []),
    "storage": (
        "dict",
        {
            "cls": "remote",
            "url": "http://127.0.0.1:5002/",
            "timeout": 10,
        },
    ),
    "indexer_storage": (
        "dict",
        {
            "cls": "remote",
            "url": "http://127.0.0.1:5007/",
            "timeout": 1,
        },
    ),
    "counters": (
        "dict",
        {
            "cls": "remote",
            "url": "http://127.0.0.1:5011/",
            "timeout": 1,
        },
    ),
    "search": (
        "dict",
        {
            "cls": "remote",
            "url": "http://127.0.0.1:5010/",
            "timeout": 10,
        },
    ),
    "search_config": (
        "dict",
        {
            "metadata_backend": "swh-indexer-storage",
        },  # or "swh-search"
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
    "vault": (
        "dict",
        {
            "cls": "remote",
            "args": {
                "url": "http://127.0.0.1:5005/",
            },
        },
    ),
    "scheduler": ("dict", {"cls": "remote", "url": "http://127.0.0.1:5008/"}),
    "development_db": ("string", os.path.join(SETTINGS_DIR, "db.sqlite3")),
    "test_db": ("dict", {"name": "swh-web-test"}),
    "production_db": ("dict", {"name": "swh-web"}),
    "deposit": (
        "dict",
        {
            "private_api_url": "https://deposit.softwareheritage.org/1/private/",
            "private_api_user": "swhworker",
            "private_api_password": "some-password",
        },
    ),
    "e2e_tests_mode": ("bool", False),
    "es_workers_index_url": ("string", ""),
    "history_counters_url": (
        "string",
        (
            "http://counters1.internal.softwareheritage.org:5011"
            "/counters_history/history.json"
        ),
    ),
    "client_config": ("dict", {}),
    "keycloak": ("dict", {"server_url": "", "realm_name": ""}),
    "graph": (
        "dict",
        {
            "server_url": "http://graph.internal.softwareheritage.org:5009/graph/",
            "max_edges": {"staff": 0, "user": 100000, "anonymous": 1000},
        },
    ),
    "status": (
        "dict",
        {
            "server_url": "https://status.softwareheritage.org/",
            "json_path": "1.0/status/578e5eddcdc0cc7951000520",
        },
    ),
    "counters_backend": ("string", "swh-storage"),  # or "swh-counters"
    "staging_server_names": ("list", SWH_WEB_STAGING_SERVER_NAMES),
    "instance_name": ("str", "archive-test.softwareheritage.org"),
    "give": ("dict", {"public_key": "", "token": ""}),
    "features": ("dict", {"add_forge_now": True}),
    "add_forge_now": ("dict", {"email_address": "add-forge-now@example.com"}),
    "swh_extra_django_apps": (
        "list",
        [
            "swh.web.add_forge_now",
            "swh.web.archive_coverage",
            "swh.web.badges",
            "swh.web.banners",
            "swh.web.deposit",
            "swh.web.inbound_email",
            "swh.web.jslicenses",
            "swh.web.mailmap",
            "swh.web.metrics",
            "swh.web.save_code_now",
            "swh.web.save_origin_webhooks",
            "swh.web.vault",
        ],
    ),
}

swhweb_config: Dict[str, Any] = {}


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
        swhweb_config["counters"] = get_counters(**swhweb_config["counters"])
    return swhweb_config


def search():
    """Return the current application's search."""
    return get_config()["search"]


def storage():
    """Return the current application's storage."""
    return get_config()["storage"]


def vault():
    """Return the current application's vault."""
    return get_config()["vault"]


def indexer_storage():
    """Return the current application's indexer storage."""
    return get_config()["indexer_storage"]


def scheduler():
    """Return the current application's scheduler."""
    return get_config()["scheduler"]


def counters():
    """Return the current application's counters."""
    return get_config()["counters"]
