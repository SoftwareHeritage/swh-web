# Copyright (C) 2021  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from typing import Set

from django.core.management.base import BaseCommand

from swh.scheduler.model import ListedOrigin
from swh.web.config import get_config
from swh.web.config import scheduler as get_scheduler
from swh.web.save_code_now.models import VISIT_STATUS_FULL, VISIT_STATUS_PARTIAL
from swh.web.save_code_now.origin_save import refresh_save_origin_request_statuses


class Command(BaseCommand):
    help = "Refresh save code now origin request statuses periodically"

    def handle(self, *args, **options):
        """Refresh origin save code now requests.

        For the origin visit types, svn, git, hg, this also installs the origins as
        recurring origins to visit.

        """
        refreshed_statuses = refresh_save_origin_request_statuses()
        scheduler = get_scheduler()

        # then schedule the origins with meaningful status and type to be ingested
        # regularly
        lister = scheduler.get_or_create_lister(
            name="save-code-now", instance_name=get_config()["instance_name"]
        )

        origins: Set[str, str] = set()
        listed_origins = []
        for status in refreshed_statuses:
            visit_type = status["visit_type"]
            # only deal with git, svn, hg visit types
            if visit_type == "archives":
                continue
            # only keep satisfying visit statuses
            if status["visit_status"] not in (VISIT_STATUS_PARTIAL, VISIT_STATUS_FULL):
                continue
            origin = status["origin_url"]
            # drop duplicates within the same batch
            if (visit_type, origin) in origins:
                continue
            origins.add((visit_type, origin))
            listed_origins.append(
                ListedOrigin(lister_id=lister.id, visit_type=visit_type, url=origin)
            )

        if listed_origins:
            scheduler.record_listed_origins(listed_origins)

        if len(refreshed_statuses) > 0:
            msg = f"Successfully updated {len(refreshed_statuses)} save request(s)."
        else:
            msg = "Nothing to do."

        self.stdout.write(self.style.SUCCESS(msg))
