# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.db import migrations


def _create_provenance_permissions(apps, schema_editor):
    from swh.web.auth.utils import (
        API_PROVENANCE_PERMISSION,
        get_or_create_django_permission,
    )

    get_or_create_django_permission(API_PROVENANCE_PERMISSION)


class Migration(migrations.Migration):
    dependencies = [
        ("swh_web_auth", "0008_create_webapp_permissions"),
    ]

    operations = [
        migrations.RunPython(_create_provenance_permissions, migrations.RunPython.noop),
    ]
