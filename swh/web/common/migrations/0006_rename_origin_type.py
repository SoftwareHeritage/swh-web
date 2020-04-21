# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("swh.web.common", "0005_remove_duplicated_authorized_origins"),
    ]

    operations = [
        migrations.RenameField(
            model_name="saveoriginrequest",
            old_name="origin_type",
            new_name="visit_type",
        ),
    ]
