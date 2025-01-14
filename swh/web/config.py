# Copyright (C) 2017-2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import annotations

import importlib
import os
from typing import TYPE_CHECKING, Any

from swh.core import config
from swh.web import settings

if TYPE_CHECKING:
    from swh.counters.interface import CountersInterface
    from swh.indexer.storage.interface import IndexerStorageInterface
    from swh.scheduler.interface import SchedulerInterface
    from swh.search.interface import SearchInterface
    from swh.storage.interface import StorageInterface
    from swh.vault.interface import VaultInterface

SETTINGS_DIR = os.path.dirname(settings.__file__)


class ConfigurationError(Exception):
    pass


class SWHWebConfig(dict[str, Any]):
    def __getitem__(self, key: str) -> Any:
        try:
            return super().__getitem__(key)
        except KeyError:
            raise ConfigurationError(f"Missing '{key}' configuration")


DEFAULT_CONFIG = {
    "allowed_hosts": ("list", []),
    "unauthenticated_api_hosts": ("list", []),
    "search_config": (
        "dict",
        {
            "metadata_backend": "swh-search",
        },  # or "swh-search"
    ),
    "log_dir": ("string", "/tmp/swh/log"),
    "debug": ("bool", False),
    "serve_assets": ("bool", False),
    "host": ("string", "127.0.0.1"),
    "port": ("int", 5004),
    "secret_key": ("string", "development key"),
    "secret_key_fallbacks": ("list[string]", []),
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
                "swh_api_metadata_citation": {
                    "limiter_rate": {"default": "60/m"},
                    "exempted_networks": ["127.0.0.0/8"],
                },
            },
        },
    ),
    "development_db": ("string", os.path.join(SETTINGS_DIR, "db.sqlite3")),
    "test_db": ("dict", {"name": "swh-web-test"}),
    "production_db": ("dict", {"name": "swh-web"}),
    "e2e_tests_mode": ("bool", False),
    "client_config": ("dict", {}),
    "keycloak": ("dict", {"server_url": "", "realm_name": ""}),
    "counters_backend": ("string", "swh-storage"),  # or "swh-counters"
    "instance_name": ("str", "archive-test.softwareheritage.org"),
    "give": ("dict", {"public_key": "", "token": ""}),
    "features": ("dict", {"add_forge_now": True}),
    "add_forge_now": (
        "dict",
        {
            "email_address": "add-forge-now@example.com",
            "gitlab_pipeline": {
                "token": "sometoken",
                "trigger_url": "someurl",
            },
        },
    ),
    "swh_extra_django_apps": (
        "list",
        [
            "swh.web.add_forge_now",
            "swh.web.admin",
            "swh.web.archive_coverage",
            "swh.web.badges",
            "swh.web.banners",
            "swh.web.deposit",
            "swh.web.inbound_email",
            "swh.web.jslicenses",
            "swh.web.mailmap",
            "swh.web.metrics",
            "swh.web.provenance",
            "swh.web.save_bulk",
            "swh.web.save_code_now",
            "swh.web.save_origin_webhooks",
            "swh.web.vault",
        ],
    ),
    "mirror_config": ("dict", {}),
    "top_bar": (
        "dict",
        {
            "links": {
                "Home": "https://www.softwareheritage.org",
                "Development": "https://gitlab.softwareheritage.org",
                "Documentation": "https://docs.softwareheritage.org",
            },
            "donate_link": "https://www.softwareheritage.org/donate",
        },
    ),
    "matomo": ("dict", {}),
    "show_corner_ribbon": ("bool", False),
    "corner_ribbon_text": ("str", ""),
    "save_code_now_webhook_secret": ("str", ""),
    "inbound_email": ("dict", {"shared_key": "shared_key"}),
    "browse_content_rate_limit": ("dict", {"enabled": True, "rate": "60/m"}),
    "activate_citations_ui": ("bool", False),
    "datatables_max_page_size": ("int", 1000),
}

swhweb_config: SWHWebConfig = SWHWebConfig()


def get_config(config_file: str = "web/web") -> SWHWebConfig:
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
    for service, modname in (
        ("search", "search"),
        ("storage", "storage"),
        ("vault", "vault"),
        ("indexer_storage", "indexer.storage"),
        ("scheduler", "scheduler"),
        ("counters", "counters"),
    ):
        if isinstance(swhweb_config.get(service), dict):
            mod = importlib.import_module(f"swh.{modname}")
            getter = getattr(mod, f"get_{service}")
            swhweb_config[service] = getter(**swhweb_config[service])
    return swhweb_config


def oidc_enabled() -> bool:
    try:
        return bool(get_config()["keycloak"]["server_url"])
    except:  # noqa: E722
        return False


def search() -> SearchInterface:
    """Return the current application's search."""
    return get_config()["search"]


def storage() -> StorageInterface:
    """Return the current application's storage."""
    return get_config()["storage"]


def vault() -> VaultInterface:
    """Return the current application's vault."""
    return get_config()["vault"]


def indexer_storage() -> IndexerStorageInterface:
    """Return the current application's indexer storage."""
    return get_config()["indexer_storage"]


def scheduler() -> SchedulerInterface:
    """Return the current application's scheduler."""
    return get_config()["scheduler"]


def counters() -> CountersInterface:
    """Return the current application's counters."""
    return get_config()["counters"]
