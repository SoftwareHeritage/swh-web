# Copyright (C) 2017-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

"""
Django tests settings for cypress e2e tests.
"""
import os

from django.conf import settings
from django.db.backends.signals import connection_created

from swh.scheduler import get_scheduler
from swh.web.config import get_config

swh_web_config = get_config()

swh_web_config.update(
    {
        "debug": False,  # debug must be off for cypress tests; we do not want
        # django to generate the debug page instead of a proper 404 or 50x page...
        "e2e_tests_mode": True,
        "corner_ribbon_text": "Cypress Tests",
        "deposit": {},
        "keycloak": None,
        "scheduler": get_scheduler(cls="memory"),
        "status": {
            "server_url": "https://status.example.org/",
            "json_path": "1.0/status/123456789",
        },
    }
)

from .tests import *  # noqa: F401, F403, E402

from .tests import LOGGING  # noqa, isort: skip

# XXX this import below should not be moved before importing .tests otherwise
# django will complain with an AppRegistryNotReady error...
from swh.web.tests.data import get_tests_data, override_storages  # noqa, isort: skip

# make the webapp fetch data from memory storages
test_data = get_tests_data()
override_storages(
    test_data["storage"],
    test_data["idx_storage"],
    test_data["search"],
    test_data["counters"],
)

# use sqlite3 backend for django database
build_id = os.environ.get("CYPRESS_PARALLEL_BUILD_ID", "")
settings.DATABASES["default"].update(
    {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": f"swh-web-test{build_id}.sqlite3",
    }
)


# to prevent "database is locked" error when running cypress tests
def activate_wal_journal_mode(sender, connection, **kwargs):
    cursor = connection.cursor()
    cursor.execute("PRAGMA journal_mode = WAL;")


connection_created.connect(activate_wal_journal_mode)

DEBUG = swh_web_config["debug"]
DEBUG_PROPAGATE_EXCEPTIONS = swh_web_config["debug"]

# ensure logs are displayed in console when settings.DEBUG is False
LOGGING["handlers"]["console"]["filters"] = []  # type: ignore
# only display logs whose level is >= WARNING when running cypress tests
LOGGING["handlers"]["console"]["level"] = "WARNING"  # type: ignore
LOGGING["loggers"]["django"]["level"] = "DEBUG" if DEBUG else "WARNING"  # type: ignore
LOGGING["loggers"]["django.request"]["level"] = "DEBUG" if DEBUG else "WARNING"  # type: ignore

LOGIN_URL = "login"
LOGOUT_URL = "logout"
