# Copyright (C) 2019-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

import os

import swh.web.gunicorn_config as gunicorn_config

django_integration = object()  # unique object to check for equality


def test_post_fork_default(mocker):
    mocker.patch(
        "swh.web.gunicorn_config.DjangoIntegration", new=lambda: django_integration
    )
    sentry_sdk_init = mocker.patch("sentry_sdk.init")
    gunicorn_config.post_fork(None, None)
    sentry_sdk_init.assert_called_once_with(
        dsn=None,
        environment=None,
        integrations=[django_integration],
        debug=False,
        release="0.0.0",
        traces_sample_rate=None,
    )


def test_post_fork_with_dsn_env(mocker):
    mocker.patch(
        "swh.web.gunicorn_config.DjangoIntegration", new=lambda: django_integration
    )
    sentry_sdk_init = mocker.patch("sentry_sdk.init")
    mocker.patch.dict(os.environ, {"SWH_SENTRY_DSN": "test_dsn"})
    gunicorn_config.post_fork(None, None)
    sentry_sdk_init.assert_called_once_with(
        dsn="test_dsn",
        environment=None,
        integrations=[django_integration],
        debug=False,
        release=None,
        traces_sample_rate=None,
    )


def test_post_fork_debug(mocker):
    mocker.patch(
        "swh.web.gunicorn_config.DjangoIntegration", new=lambda: django_integration
    )
    sentry_sdk_init = mocker.patch("sentry_sdk.init")
    mocker.patch.dict(
        os.environ, {"SWH_SENTRY_DSN": "test_dsn", "SWH_SENTRY_DEBUG": "1"}
    )
    gunicorn_config.post_fork(None, None)
    sentry_sdk_init.assert_called_once_with(
        dsn="test_dsn",
        environment=None,
        integrations=[django_integration],
        debug=True,
        release=None,
        traces_sample_rate=None,
    )
