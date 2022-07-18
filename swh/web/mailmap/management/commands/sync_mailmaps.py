# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import psycopg2
import psycopg2.extensions
from psycopg2.extras import execute_values

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from django.db.models.query import QuerySet
from django.utils import timezone

from swh.web.mailmap.models import UserMailmap

DISABLE_MAILMAPS_QUERY = """\
UPDATE person
   SET displayname = NULL
   FROM (VALUES %s) AS emails (email)
   WHERE person.email = emails.email
"""

REFRESH_MAILMAPS_QUERY = """\
UPDATE person
   SET displayname = displaynames.displayname
   FROM (VALUES %s) AS displaynames (email, displayname)
   WHERE
     person.email = displaynames.email
     AND person.displayname IS DISTINCT FROM displaynames.displayname
"""


class Command(BaseCommand):
    help = "Synchronize the mailmaps with swh.storage"

    def add_arguments(self, parser):
        parser.add_argument("storage_dbconn", type=str)
        parser.add_argument(
            "--perform",
            action="store_true",
            help="Perform actions (instead of the default dry-run)",
        )

    def disable_mailmaps(
        self,
        storage_db: psycopg2.extensions.connection,
        mailmaps: "QuerySet[UserMailmap]",
    ):
        """Return the SQL to disable a set of mailmaps"""

        execute_values(
            storage_db.cursor(),
            DISABLE_MAILMAPS_QUERY,
            ((mailmap.from_email.encode("utf-8"),) for mailmap in mailmaps),
        )

    def refresh_mailmaps(
        self,
        storage_db: psycopg2.extensions.connection,
        mailmaps: "QuerySet[UserMailmap]",
    ):

        execute_values(
            storage_db.cursor(),
            REFRESH_MAILMAPS_QUERY,
            (
                (
                    mailmap.from_email.encode("utf-8"),
                    mailmap.full_display_name.encode("utf-8"),
                )
                for mailmap in mailmaps
            ),
        )

    def handle(self, *args, **options):
        verified_mailmaps = UserMailmap.objects.filter(from_email_verified=True)

        # Always refresh display names for person entries with known emails
        to_refresh = verified_mailmaps.filter(display_name_activated=True)

        # Only remove display_names if they've been deactivated since they've last been
        # processed
        to_disable = verified_mailmaps.filter(
            display_name_activated=False,
            mailmap_last_processing_date__lt=F("last_update_date"),
        )

        process_start = timezone.now()
        with transaction.atomic():
            self.stdout.write(
                "%d mailmaps to disable, %d mailmaps to refresh%s"
                % (
                    to_disable.count(),
                    to_refresh.count(),
                    (" (dry run)" if not options["perform"] else ""),
                )
            )

            with psycopg2.connect(options["storage_dbconn"]) as db:
                self.disable_mailmaps(db, to_disable.select_for_update())
                self.refresh_mailmaps(db, to_refresh.select_for_update())
                if not options["perform"]:
                    db.rollback()
                else:
                    db.commit()

            if options["perform"]:
                updated = to_disable.update(
                    mailmap_last_processing_date=process_start
                ) + to_refresh.update(mailmap_last_processing_date=process_start)
            else:
                updated = to_disable.count() + to_refresh.count()

        self.stdout.write(
            self.style.SUCCESS(f"Synced {updated} mailmaps to swh.storage database")
        )
