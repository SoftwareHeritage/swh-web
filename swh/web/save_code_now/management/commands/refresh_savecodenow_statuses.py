# Copyright (C) 2021-2023  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.core.management.base import BaseCommand

from swh.web.save_code_now.origin_save import (
    refresh_save_origin_request_statuses,
    schedule_origins_recurrent_visits,
)


class Command(BaseCommand):
    help = "Refresh save code now origin request statuses periodically"

    def handle(self, *args, **options):
        """Refresh origin save code now requests.

        For the origin visit types, svn, git, hg, this also installs the origins as
        recurring origins to visit.

        """
        updated_requests = refresh_save_origin_request_statuses()

        # then schedule the origins with meaningful status and type to be ingested
        # regularly
        nb_origins_scheduled = schedule_origins_recurrent_visits(updated_requests)

        if len(updated_requests) > 0:
            msg = f"Successfully updated {len(updated_requests)} save request(s)."
            if nb_origins_scheduled:
                msg += (
                    f"\n{nb_origins_scheduled} origins were also scheduled "
                    "for recurrent visits."
                )
        else:
            msg = "Nothing to do."

        self.stdout.write(self.style.SUCCESS(msg))
