# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.apps import AppConfig


class AdminConfig(AppConfig):
    name = "swh.web.admin"
    label = "swh_web_admin"