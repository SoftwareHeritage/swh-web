# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []  # type: ignore

    operations = [
        migrations.SeparateDatabaseAndState(
            # as we move the mailmap feature to a dedicated django application,
            # no need to recreate database tables as they already exist
            state_operations=[
                migrations.CreateModel(
                    name="UserMailmap",
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
                        ("user_id", models.CharField(max_length=50, null=True)),
                        ("from_email", models.TextField(unique=True)),
                        ("from_email_verified", models.BooleanField(default=False)),
                        (
                            "from_email_verification_request_date",
                            models.DateTimeField(null=True),
                        ),
                        ("display_name", models.TextField()),
                        ("display_name_activated", models.BooleanField(default=False)),
                        ("to_email", models.TextField(null=True)),
                        ("to_email_verified", models.BooleanField(default=False)),
                        (
                            "to_email_verification_request_date",
                            models.DateTimeField(null=True),
                        ),
                        (
                            "mailmap_last_processing_date",
                            models.DateTimeField(null=True),
                        ),
                        ("last_update_date", models.DateTimeField(auto_now=True)),
                    ],
                    options={
                        "db_table": "user_mailmap",
                    },
                ),
                migrations.CreateModel(
                    name="UserMailmapEvent",
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
                        ("timestamp", models.DateTimeField(auto_now=True)),
                        ("user_id", models.CharField(max_length=50)),
                        ("request_type", models.CharField(max_length=50)),
                        ("request", models.TextField()),
                        ("successful", models.BooleanField(default=False)),
                    ],
                    options={
                        "db_table": "user_mailmap_event",
                    },
                ),
                migrations.AddIndex(
                    model_name="usermailmapevent",
                    index=models.Index(
                        fields=["timestamp"], name="user_mailma_timesta_1f7aef_idx"
                    ),
                ),
            ],
            database_operations=[],
        ),
    ]
