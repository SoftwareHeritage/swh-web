# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.apps import AppConfig


class InboundEmailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "inbound_email"
