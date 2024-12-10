# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_save_code_now", "0015_alter_saveoriginrequest_loading_task_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="saveoriginrequest",
            name="origin_url",
            field=models.CharField(max_length=4096, null=False),
        ),
    ]