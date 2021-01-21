# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.apps import AppConfig


class AuthConfig(AppConfig):
    name = "swh.web.auth"
    label = "swh_web_auth"
