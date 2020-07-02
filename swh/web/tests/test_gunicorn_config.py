# Copyright (C) 2019-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os
from unittest.mock import patch

import swh.web.gunicorn_config as gunicorn_config


def test_post_fork_default():
    with patch("sentry_sdk.init") as sentry_sdk_init:
        gunicorn_config.post_fork(None, None)

    sentry_sdk_init.assert_not_called()


def test_post_fork_with_dsn_env():
    django_integration = object()  # unique object to check for equality
    with patch(
        "swh.web.gunicorn_config.DjangoIntegration", new=lambda: django_integration
    ):
        with patch("sentry_sdk.init") as sentry_sdk_init:
            with patch.dict(os.environ, {"SWH_SENTRY_DSN": "test_dsn"}):
                gunicorn_config.post_fork(None, None)

    sentry_sdk_init.assert_called_once_with(
        dsn="test_dsn",
        environment=None,
        integrations=[django_integration],
        debug=False,
        release=None,
    )


def test_post_fork_debug():
    django_integration = object()  # unique object to check for equality
    with patch(
        "swh.web.gunicorn_config.DjangoIntegration", new=lambda: django_integration
    ):
        with patch("sentry_sdk.init") as sentry_sdk_init:
            with patch.dict(
                os.environ, {"SWH_SENTRY_DSN": "test_dsn", "SWH_SENTRY_DEBUG": "1"}
            ):
                gunicorn_config.post_fork(None, None)

    sentry_sdk_init.assert_called_once_with(
        dsn="test_dsn",
        environment=None,
        integrations=[django_integration],
        debug=True,
        release=None,
    )
