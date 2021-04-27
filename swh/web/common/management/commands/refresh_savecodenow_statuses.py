# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.core.management.base import BaseCommand

from swh.web.common.origin_save import refresh_save_origin_request_statuses


class Command(BaseCommand):
    help = "Refresh save code now origin request statuses periodically"

    def handle(self, *args, **options):
        refreshed_statuses = refresh_save_origin_request_statuses()

        if len(refreshed_statuses) > 0:
            msg = f"Successfully updated {len(refreshed_statuses)} save request(s)."
        else:
            msg = "Nothing to do."

        self.stdout.write(self.style.SUCCESS(msg))
