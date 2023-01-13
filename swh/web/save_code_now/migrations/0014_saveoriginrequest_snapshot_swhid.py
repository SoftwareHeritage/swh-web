# Copyright (C) 2022 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_save_code_now", "0013_saveoriginrequest_webhook_info"),
    ]

    operations = [
        migrations.AddField(
            model_name="saveoriginrequest",
            name="snapshot_swhid",
            field=models.CharField(max_length=200, null=True),
        ),
    ]
