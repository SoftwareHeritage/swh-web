# Copyright (C) 2018  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("swh.web.common", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="saveoriginrequest",
            name="visit_date",
            field=models.DateTimeField(null=True),
        ),
    ]
