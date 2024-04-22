# Copyright (C) 2024  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.db import migrations


def _create_webapp_permissions(apps, schema_editor):
    from swh.web.auth.utils import WEBAPP_PERMISSIONS, get_or_create_django_permission

    for permission in WEBAPP_PERMISSIONS:
        get_or_create_django_permission(permission)


class Migration(migrations.Migration):
    dependencies = [
        ("swh_web_auth", "0007_mailmap_django_app"),
    ]

    operations = [
        migrations.RunPython(_create_webapp_permissions, migrations.RunPython.noop),
    ]
