# Copyright (C) 2017-2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""
Django tests settings for swh-web.
"""

import os
import sys

from swh.web.config import SWH_WEB_INTERNAL_SERVER_NAME, get_config

scope1_limiter_rate = 3
scope1_limiter_rate_post = 1
scope2_limiter_rate = 5
scope2_limiter_rate_post = 2
scope3_limiter_rate = 1
scope3_limiter_rate_post = 1
save_origin_rate_post = 10

swh_web_config = get_config()

swh_web_config.update(
    {
        # disable django debug mode when running cypress tests
        "debug": "pytest" in sys.argv[0] or "PYTEST_XDIST_WORKER" in os.environ,
        "secret_key": "test",
        "history_counters_url": "",
        "throttling": {
            "cache_uri": None,
            "scopes": {
                "swh_api": {
                    "limiter_rate": {"default": "60/min"},
                    "exempted_networks": ["127.0.0.0/8"],
                },
                "swh_api_origin_search": {
                    "limiter_rate": {"default": "100/min"},
                    "exempted_networks": ["127.0.0.0/8"],
                },
                "swh_api_origin_visit_latest": {
                    "limiter_rate": {"default": "6000/min"},
                    "exempted_networks": ["127.0.0.0/8"],
                },
                "swh_vault_cooking": {
                    "limiter_rate": {"default": "120/h", "GET": "60/m"},
                    "exempted_networks": ["127.0.0.0/8"],
                },
                "swh_save_origin": {
                    "limiter_rate": {
                        "default": "120/h",
                        "POST": "%s/h" % save_origin_rate_post,
                    }
                },
                "scope1": {
                    "limiter_rate": {
                        "default": "%s/min" % scope1_limiter_rate,
                        "POST": "%s/min" % scope1_limiter_rate_post,
                    }
                },
                "scope2": {
                    "limiter_rate": {
                        "default": "%s/min" % scope2_limiter_rate,
                        "POST": "%s/min" % scope2_limiter_rate_post,
                    }
                },
                "scope3": {
                    "limiter_rate": {
                        "default": "%s/min" % scope3_limiter_rate,
                        "POST": "%s/min" % scope3_limiter_rate_post,
                    },
                    "exempted_networks": ["127.0.0.0/8"],
                },
            },
        },
        "keycloak": {
            "server_url": "http://localhost:8080/auth/",
            "realm_name": "SoftwareHeritage",
        },
    }
)


from .common import *  # noqa

from .common import ALLOWED_HOSTS, LOGGING  # noqa, isort: skip

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": swh_web_config["test_db"],
    }
}

# when not running unit tests, make the webapp fetch data from memory storages
if "pytest" not in sys.argv[0] and "PYTEST_XDIST_WORKER" not in os.environ:
    swh_web_config.update({"debug": True, "e2e_tests_mode": True})
    from swh.web.tests.data import get_tests_data, override_storages

    test_data = get_tests_data()
    override_storages(
        test_data["storage"],
        test_data["idx_storage"],
        test_data["search"],
        test_data["counters"],
    )
else:
    ALLOWED_HOSTS += ["testserver", SWH_WEB_INTERNAL_SERVER_NAME]
    ALLOWED_HOSTS += get_config()["staging_server_names"]

    # Silent DEBUG output when running unit tests
    LOGGING["handlers"]["console"]["level"] = "INFO"  # type: ignore
