# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import unicode_literals

from django.db import migrations, models

from swh.web.config import scheduler


def _remove_archived_tasks_with_no_saved_status(apps, schema_editor):
    """
    Scheduler tasks are archived on a regular basis so their completion
    state could not be known anymore as previous to this migration,
    the loading task status was not stored in the database.
    So remove the rows associated to already archived tasks as
    the loading status can not be retrieved anymore.
    """
    SaveOriginRequest = apps.get_model("swh.web.common", "SaveOriginRequest")
    no_saved_status_tasks = []
    for sor in SaveOriginRequest.objects.all():
        tasks = scheduler().get_tasks([sor.loading_task_id])
        if not tasks:
            no_saved_status_tasks.append(sor.loading_task_id)
    SaveOriginRequest.objects.filter(loading_task_id__in=no_saved_status_tasks).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("swh.web.common", "0002_saveoriginrequest_visit_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="saveoriginrequest",
            name="loading_task_status",
            field=models.TextField(
                choices=[
                    ("not created", "not created"),
                    ("not yet scheduled", "not yet scheduled"),
                    ("scheduled", "scheduled"),
                    ("succeed", "succeed"),
                    ("failed", "failed"),
                ],
                default="not created",
            ),
        ),
        migrations.RunPython(_remove_archived_tasks_with_no_saved_status),
    ]
