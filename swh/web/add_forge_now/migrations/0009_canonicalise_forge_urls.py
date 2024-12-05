# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import csv
import os

from django.db import migrations

from swh.web.add_forge_now.models import Request


def _canonicalise_forge_urls(apps, schema_editor):
    data_file = os.path.join(os.path.dirname(__file__), "swh-afn-urls-canonicalise.txt")
    canonicalised_forge_urls = {}
    with open(data_file, "r") as csv_file:
        reader = csv.DictReader(
            csv_file,
            dialect="excel-tab",
            fieldnames=["id", "forge_type", "forge_url", "canonicalised_forge_url"],
        )
        for row in reader:
            key = (row["forge_type"], row["forge_url"])
            canonicalised_forge_urls[key] = row["canonicalised_forge_url"]
    for add_forge_request in Request.objects.all():
        key = (add_forge_request.forge_type, add_forge_request.forge_url)
        if key in canonicalised_forge_urls:
            add_forge_request.forge_url = canonicalised_forge_urls[key]
            add_forge_request.save()


class Migration(migrations.Migration):
    dependencies = [
        ("swh_web_add_forge_now", "0008_turn_request_forge_url_into_url_field"),
    ]

    operations = [
        migrations.RunPython(_canonicalise_forge_urls, migrations.RunPython.noop)
    ]
