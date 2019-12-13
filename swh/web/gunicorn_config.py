# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from sentry_sdk.integrations.django import DjangoIntegration

from swh.core.api.gunicorn_config import *  # noqa
from swh.core.api.gunicorn_config import post_fork as _post_fork


def post_fork(server, worker):  # type: ignore
    _post_fork(server, worker,
               flask=False, sentry_integrations=[DjangoIntegration()])
