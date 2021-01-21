# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import unicode_literals

from django.db import migrations, models

_authorized_origins = [
    "https://github.com/",
    "https://gitlab.com/",
    "https://bitbucket.org/",
    "https://git.code.sf.net/",
    "http://git.code.sf.net/",
    "https://hg.code.sf.net/",
    "http://hg.code.sf.net/",
    "https://svn.code.sf.net/",
    "http://svn.code.sf.net/",
]


def _populate_save_authorized_origins(apps, schema_editor):
    SaveAuthorizedOrigin = apps.get_model("swh_web_common", "SaveAuthorizedOrigin")
    for origin_url in _authorized_origins:
        SaveAuthorizedOrigin.objects.create(url=origin_url)


class Migration(migrations.Migration):

    initial = True

    operations = [
        migrations.CreateModel(
            name="SaveAuthorizedOrigin",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("url", models.CharField(max_length=200)),
            ],
            options={"db_table": "save_authorized_origin",},
        ),
        migrations.CreateModel(
            name="SaveOriginRequest",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("request_date", models.DateTimeField(auto_now_add=True)),
                ("origin_type", models.CharField(max_length=200)),
                ("origin_url", models.CharField(max_length=200)),
                (
                    "status",
                    models.TextField(
                        choices=[
                            ("accepted", "accepted"),
                            ("rejected", "rejected"),
                            ("pending", "pending"),
                        ],
                        default="pending",
                    ),
                ),
                ("loading_task_id", models.IntegerField(default=-1)),
            ],
            options={"db_table": "save_origin_request", "ordering": ["-id"],},
        ),
        migrations.CreateModel(
            name="SaveUnauthorizedOrigin",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("url", models.CharField(max_length=200)),
            ],
            options={"db_table": "save_unauthorized_origin",},
        ),
        migrations.RunPython(_populate_save_authorized_origins),
    ]
