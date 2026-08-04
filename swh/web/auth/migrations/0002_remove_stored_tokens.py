# Copyright (C) 2020-2026  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information


from django.db import migrations


def _remove_stored_encrypted_tokens(apps, schema_editor):
    OIDCUserOfflineTokens = apps.get_model("swh_web_auth", "OIDCUserOfflineTokens")
    OIDCUserOfflineTokens.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("swh_web_auth", "0001_initial"),
    ]

    operations = [migrations.RunPython(_remove_stored_encrypted_tokens)]
