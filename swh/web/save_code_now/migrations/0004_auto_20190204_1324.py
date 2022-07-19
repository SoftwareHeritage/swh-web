# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_save_code_now", "0003_saveoriginrequest_loading_task_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="saveoriginrequest",
            name="loading_task_status",
            field=models.TextField(
                choices=[
                    ("not created", "not created"),
                    ("not yet scheduled", "not yet scheduled"),
                    ("scheduled", "scheduled"),
                    ("succeed", "succeed"),
                    ("failed", "failed"),
                    ("running", "running"),
                ],
                default="not created",
            ),
        ),
    ]
