# Copyright (C) 2019-2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from sentry_sdk.integrations.django import DjangoIntegration

from swh.core.sentry import init_sentry


def post_fork(server, worker):
    init_sentry(sentry_dsn=None, integrations=[DjangoIntegration()])
