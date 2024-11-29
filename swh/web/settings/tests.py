# Copyright (C) 2017-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""
Django tests settings for swh-web.
"""

from swh.web.config import get_config

scope1_limiter_rate = 3
scope1_limiter_rate_post = 1
scope2_limiter_rate = 5
scope2_limiter_rate_post = 2
scope3_limiter_rate = 1
scope3_limiter_rate_post = 1
save_origin_rate_post = 5
api_raw_object_rate = 5

swh_web_config = get_config()

# swh_web_config needs to be adapted before importing settings/common: this
# later does initialization/config steps that depends on the config entries
swh_web_config.update(
    {
        # enable django DEBUG mode only when running pytest
        "debug": True,
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
                "swh_raw_object": {
                    "limiter_rate": {"default": f"{api_raw_object_rate}/h"},
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
                "swh_api_metadata_citation": {
                    "limiter_rate": {"default": "60/m"},
                    "exempted_networks": ["127.0.0.0/8"],
                },
            },
        },
        "keycloak": {
            # disable keycloak use when not running pytest
            "server_url": "http://localhost:8080/auth/",
            "realm_name": "SoftwareHeritage",
        },
        # use a stricter browse content views rate limit for the tests
        "browse_content_rate_limit": {"enabled": True, "rate": "1/m"},
    }
)


from .common import *  # noqa

from .common import INSTALLED_APPS, LOGGING, MIDDLEWARE  # noqa, isort: skip


ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": swh_web_config["test_db"]["name"],
    }
}

# silent DEBUG output when running unit tests
LOGGING["handlers"]["console"]["level"] = "INFO"  # type: ignore

LOGIN_URL = "oidc-login"
LOGOUT_URL = "oidc-logout"
