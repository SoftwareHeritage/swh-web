# Copyright (C) 2025  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_add_forge_now", "0009_canonicalise_forge_urls"),
    ]

    operations = [
        migrations.AlterField(
            model_name="request",
            name="forge_contact_comment",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Where did you find this contact information (url, ...)",
            ),
        ),
    ]
