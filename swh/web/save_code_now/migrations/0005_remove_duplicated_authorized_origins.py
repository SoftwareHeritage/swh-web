# Copyright (C) 2019  The Software Heritage developers
# See the AUTHORS file at the top-level directory of this distribution
# License: GNU Affero General Public License version 3, or any later version
# See top-level LICENSE file for more information

from __future__ import unicode_literals

from django.db import migrations

from swh.web.save_code_now.models import SaveAuthorizedOrigin


def _remove_duplicated_urls_in_authorized_list(apps, schema_editor):
    sao = SaveAuthorizedOrigin.objects
    for url in sao.values_list("url", flat=True).distinct():
        sao.filter(pk__in=sao.filter(url=url).values_list("id", flat=True)[1:]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("swh_web_save_code_now", "0004_auto_20190204_1324"),
    ]

    operations = [migrations.RunPython(_remove_duplicated_urls_in_authorized_list)]
