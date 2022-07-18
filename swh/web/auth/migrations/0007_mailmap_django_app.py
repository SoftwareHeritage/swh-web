# Copyright (C) 2022  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_auth", "0006_fix_mailmap_admin_user_id"),
    ]

    operations = [
        # as we simply move the mailmap feature to a dedicated django application,
        # we do not want to remove the tables in database to not lose data
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name="UserMailmap",
                ),
                migrations.DeleteModel(
                    name="UserMailmapEvent",
                ),
            ],
            database_operations=[],
        ),
    ]
