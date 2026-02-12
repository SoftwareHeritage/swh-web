# Copyright (C) 2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_save_code_now", "0016_alter_saveoriginrequest_origin_url"),
    ]

    operations = [
        migrations.AlterField(
            model_name="saveoriginrequest",
            name="note",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="saveoriginrequest",
            name="snapshot_swhid",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AlterField(
            model_name="saveoriginrequest",
            name="user_ids",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AlterField(
            model_name="saveoriginrequest",
            name="webhook_origin",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
    ]
