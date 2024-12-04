# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from urllib.parse import urlparse

from django.db import migrations

from swh.web.add_forge_now.models import Request


def _canonicalise_forge_urls(apps, schema_editor):
    for add_forge_request in Request.objects.all():
        parsed_forge_url = urlparse(add_forge_request.forge_url)
        if parsed_forge_url.scheme and parsed_forge_url.netloc:
            add_forge_request.forge_url = (
                f"{parsed_forge_url.scheme}://{parsed_forge_url.netloc}/"
            )
            add_forge_request.save()


class Migration(migrations.Migration):
    dependencies = [
        ("swh_web_add_forge_now", "0008_turn_request_forge_url_into_url_field"),
    ]

    operations = [
        migrations.RunPython(_canonicalise_forge_urls, migrations.RunPython.noop)
    ]
