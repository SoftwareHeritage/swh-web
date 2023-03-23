# Copyright (C) The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import csv
import hashlib

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Dump Save Code Now requests data to CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-file",
            type=str,
            default="",
            help="optional path to dump CSV file, dump to stdout by default",
        )

    def handle(self, *args, **options):
        """Dump Save Code Now requests data to CSV.

        Dump to stdout or to file the following CSV data about Save Code Now requests:

            * date of request
            * requested visit type
            * URL of origin to save
            * status of the request
            * status of visit by SWH
            * whether the request was triggered by a webhook
            * user id (anonymized) that created the request
        """
        from swh.web.save_code_now.models import SaveOriginRequest

        output = self.stdout
        if options["output_file"]:
            output = open(options["output_file"], "w")
        fieldnames = [
            "request_date",
            "visit_type",
            "origin_url",
            "request_status",
            "visit_status",
            "from_webhook",
            "user_id",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        scn_requests = SaveOriginRequest.objects
        for scn_request in scn_requests.iterator():
            users_ids = (
                map(
                    # generate opaque identifier from user id
                    lambda user_id: hashlib.sha1(user_id.encode()).hexdigest()[:7],
                    scn_request.user_ids.split(","),
                )
                if scn_request.user_ids
                else [""]
            )
            for user_id in users_ids:
                writer.writerow(
                    {
                        "request_date": scn_request.request_date,
                        "visit_type": scn_request.visit_type,
                        "origin_url": scn_request.origin_url,
                        "request_status": scn_request.status,
                        "visit_status": scn_request.visit_status,
                        "from_webhook": str(scn_request.from_webhook).lower(),
                        "user_id": user_id,
                    }
                )
        if output != self.stdout:
            output.close()
