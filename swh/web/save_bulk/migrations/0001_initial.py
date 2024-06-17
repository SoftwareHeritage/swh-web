# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SaveBulkRequest",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("request_date", models.DateTimeField(auto_now_add=True)),
                ("user_id", models.CharField(max_length=50)),
            ],
            options={
                "db_table": "save_bulk_request",
                "ordering": ["-id"],
            },
        ),
        migrations.CreateModel(
            name="SaveBulkOrigin",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("origin_url", models.CharField(max_length=200)),
                ("visit_type", models.CharField(max_length=30)),
                (
                    "requests",
                    models.ManyToManyField(to="swh_web_save_bulk.savebulkrequest"),
                ),
            ],
            options={
                "db_table": "save_bulk_origin",
                "ordering": ["-id"],
                "indexes": [
                    models.Index(
                        fields=["origin_url", "visit_type"],
                        name="save_bulk_o_origin__69154d_idx",
                    )
                ],
            },
        ),
        migrations.AddConstraint(
            model_name="savebulkorigin",
            constraint=models.UniqueConstraint(
                fields=("origin_url", "visit_type"), name="unicity"
            ),
        ),
    ]
