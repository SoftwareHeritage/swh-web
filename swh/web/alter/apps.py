# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.apps import AppConfig

APP_LABEL = "swh_web_alter"


class AlterConfig(AppConfig):
    name = "swh.web.alter"
    label = APP_LABEL
