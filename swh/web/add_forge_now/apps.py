# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.apps import AppConfig

APP_LABEL = "swh_web_add_forge_now"


class AddForgeNowConfig(AppConfig):
    name = "swh.web.add_forge_now"
    label = APP_LABEL

    def ready(self):
        from ..inbound_email.signals import email_received
        from .signal_receivers import handle_inbound_message

        email_received.connect(handle_inbound_message)
