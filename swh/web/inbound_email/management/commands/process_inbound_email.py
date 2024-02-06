# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import sys

from django.core.management.base import BaseCommand

from ...handle_message import MessageHandler


class Command(BaseCommand):
    help = "Process a new inbound email"

    def handle(self, *args, **options):
        MessageHandler(
            raw_message=sys.stdin.buffer.read(), sender=self.__class__
        ).handle()
