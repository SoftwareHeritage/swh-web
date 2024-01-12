# Copyright (C) 2024 The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import migrations, models


def _rename_not_yet_scheduled_loading_task_status(apps, schema_editor):
    SaveOriginRequest = apps.get_model("swh_web_save_code_now", "SaveOriginRequest")
    for sor in SaveOriginRequest.objects.all():
        if sor.loading_task_status == "not yet scheduled":
            sor.loading_task_status = "pending"
            sor.save()


class Migration(migrations.Migration):
    dependencies = [
        ("swh_web_save_code_now", "0014_saveoriginrequest_snapshot_swhid"),
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
                    ("succeeded", "succeeded"),
                    ("failed", "failed"),
                    ("running", "running"),
                    ("pending", "pending"),
                ],
                default="not created",
            ),
        ),
        migrations.RunPython(_rename_not_yet_scheduled_loading_task_status),
    ]
