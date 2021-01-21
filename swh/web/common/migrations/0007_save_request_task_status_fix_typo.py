# Copyright (C) 2020  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import migrations, models


def _rename_request_status_from_succeed_to_succeeded(apps, schema_editor):
    """
    Fix a typo in save request status value.
    """
    SaveOriginRequest = apps.get_model("swh_web_common", "SaveOriginRequest")
    for sor in SaveOriginRequest.objects.all():
        if sor.loading_task_status == "succeed":
            sor.loading_task_status = "succeeded"
            sor.save()


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_common", "0006_rename_origin_type"),
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
                ],
                default="not created",
            ),
        ),
        migrations.RunPython(_rename_request_status_from_succeed_to_succeeded),
    ]
