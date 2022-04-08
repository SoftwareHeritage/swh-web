# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_auth", "0003_delete_oidcuser"),
    ]

    operations = [
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
                ("from_email", models.TextField(unique=True, null=False)),
                ("from_email_verified", models.BooleanField(default=False)),
                (
                    "from_email_verification_request_date",
                    models.DateTimeField(null=True),
                ),
                ("display_name", models.TextField(null=False)),
                ("display_name_activated", models.BooleanField(default=False)),
                ("to_email", models.TextField(null=True)),
                ("to_email_verified", models.BooleanField(default=False)),
                ("to_email_verification_request_date", models.DateTimeField(null=True)),
                ("mailmap_last_processing_date", models.DateTimeField(null=True)),
                ("last_update_date", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "user_mailmap",
            },
        ),
    ]
