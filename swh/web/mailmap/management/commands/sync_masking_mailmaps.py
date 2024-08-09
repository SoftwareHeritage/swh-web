# Copyright (C) 2022-2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from swh.storage.proxies.masking.db import MaskingAdmin
from swh.web.mailmap.models import UserMailmap


class Command(BaseCommand):
    help = "Synchronize the mailmaps with the masking proxy"

    def add_arguments(self, parser):
        parser.add_argument("proxy_dbconn", type=str)
        parser.add_argument(
            "--perform",
            action="store_true",
            help="Perform actions (instead of the default dry-run)",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help=(
                "Perform actions even if no new update has been "
                "recorded since last processing"
            ),
        )

    def handle(self, *args, **options):
        # only refresh mailmaps if something changed since last processing date
        verified_mailmaps = UserMailmap.objects.filter(from_email_verified=True)

        # if there is nothing new since last mailmap processing date, do nothing
        if (
            not options["force"]
            and not verified_mailmaps.filter(
                mailmap_last_processing_date__lt=F("last_update_date")
            )
            and not verified_mailmaps.filter(
                display_name_activated=True, mailmap_last_processing_date=None
            )
        ):
            self.stdout.write("No mailmap to update")
            return

        # Always refresh display names for person entries with known emails
        mailmaps = verified_mailmaps.filter(display_name_activated=True)

        # Only used for logging purpose (and tracking last_processing_update field)
        to_disable = verified_mailmaps.filter(
            display_name_activated=False,
            mailmap_last_processing_date__lt=F("last_update_date"),
        )
        process_start = timezone.now()
        with transaction.atomic():
            self.stdout.write(
                "%d mailmaps to disable, %d mailmaps to set/refresh%s"
                % (
                    to_disable.count(),
                    mailmaps.count(),
                    (" (dry run)" if not options["perform"] else ""),
                )
            )
            if options["perform"]:
                masking_db = MaskingAdmin.connect(options["proxy_dbconn"])
                dsp = [
                    (
                        mailmap.from_email.encode("utf-8"),
                        mailmap.full_display_name.encode("utf-8"),
                    )
                    for mailmap in mailmaps
                ]
                masking_db.set_display_names(
                    dsp,
                    clear=True,
                )
                updated = to_disable.update(
                    mailmap_last_processing_date=process_start
                ) + mailmaps.update(mailmap_last_processing_date=process_start)
            else:
                updated = to_disable.count() + mailmaps.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Synced {updated} mailmaps to the masking proxy database"
            )
        )
