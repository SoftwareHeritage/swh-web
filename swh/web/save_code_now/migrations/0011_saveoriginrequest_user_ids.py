# Copyright (C) 2021 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_save_code_now", "0010_saveoriginrequest_user_id"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="saveoriginrequest",
            name="user_id",
        ),
        migrations.AddField(
            model_name="saveoriginrequest",
            name="user_ids",
            field=models.TextField(null=True),
        ),
    ]
